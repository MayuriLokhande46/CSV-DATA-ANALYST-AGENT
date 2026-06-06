import subprocess
import os
import uuid
import sys
import re

# Patterns that are dangerous and should be blocked before execution
DANGEROUS_PATTERNS = [
    r"os\.system\s*\(",
    r"os\.remove\s*\(",
    r"os\.rmdir\s*\(",
    r"shutil\.rmtree\s*\(",
    r"subprocess\.run\s*\(",
    r"subprocess\.call\s*\(",
    r"subprocess\.Popen\s*\(",
    r"__import__\s*\(\s*['\"]os['\"]",
    r"open\s*\(.*['\"]w['\"]",   # Block writing to arbitrary files
    r"exec\s*\(",
    r"eval\s*\(",
]

def _sanitize_code(code: str) -> str:
    """
    1. Remove plt.show() / fig.show() calls that would hang execution.
    2. Inject matplotlib backend so no GUI window is opened.
    """
    # Remove show() calls that hang in headless mode
    code = re.sub(r'\bplt\.show\s*\(\s*\)', '# plt.show() suppressed', code)
    code = re.sub(r'\bfig\.show\s*\(\s*\)', '# fig.show() suppressed', code)

    # Inject non-interactive backend at the very top (before any matplotlib import)
    backend_header = "import matplotlib\nmatplotlib.use('Agg')\n"
    if "matplotlib.use" not in code:
        code = backend_header + code

    return code


def _check_dangerous_patterns(code: str):
    """
    Raises ValueError if potentially destructive code patterns are detected.
    Returns None if code is safe.
    """
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code):
            raise ValueError(
                f"❌ Security block: Detected potentially unsafe pattern `{pattern}` in generated code. "
                "Execution was aborted."
            )


class ExecutionSandbox:
    def __init__(self, image_name="statbot-sandbox", volume_path=None):
        self.image_name = image_name
        self.volume_path = volume_path or os.getcwd()
        self.is_docker_available = self._check_docker()

    def _check_docker(self):
        """Checks if Docker is installed and running."""
        try:
            subprocess.run(["docker", "ps"], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def execute_code(self, code: str, session_id: str = "default"):
        """
        Executes the provided python code inside a Docker container (if available)
        or locally (fallback). Session-isolated figures directory is used.

        Returns a dictionary with result and list of artifacts (plots).
        """
        # --- Step 1: Security scan ---
        try:
            _check_dangerous_patterns(code)
        except ValueError as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "success": False,
                "is_sandbox": self.is_docker_available,
                "artifacts": [],
                "blocked": True,
            }

        # --- Step 2: Sanitize code (remove plt.show, inject Agg backend) ---
        code = _sanitize_code(code)

        # --- Step 3: Per-session figure isolation ---
        figures_dir = os.path.join(self.volume_path, "exports", "figures", session_id)
        os.makedirs(figures_dir, exist_ok=True)

        # Patch the code so the AI saves figures into the session-specific folder
        # Replace generic 'exports/figures/' with the session-specific path
        session_figures_rel = f"exports/figures/{session_id}"
        code = code.replace("exports/figures/", f"{session_figures_rel}/")

        task_id = str(uuid.uuid4())[:8]
        temp_script = os.path.join(self.volume_path, f"temp_task_{task_id}.py")

        # Track initial state of figures
        pre_execution_files = set(os.listdir(figures_dir))

        # Write the sanitized script
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            if self.is_docker_available:
                # Mount ONLY temp_uploads and exports — NOT the full project
                exports_host = os.path.join(self.volume_path, "exports")
                uploads_host = os.path.join(self.volume_path, "temp_uploads")
                os.makedirs(exports_host, exist_ok=True)
                os.makedirs(uploads_host, exist_ok=True)

                command = [
                    "docker", "run", "--rm",
                    "--network", "none",           # No internet access inside container
                    "--memory", "512m",            # Memory limit
                    "--cpus", "1",                 # CPU limit
                    "-v", f"{exports_host}:/app/exports",
                    "-v", f"{uploads_host}:/app/temp_uploads",
                    "-v", f"{temp_script}:/app/task.py",
                    "-w", "/app",
                    self.image_name,
                    "python", "task.py"
                ]
            else:
                # Local fallback — warn in stderr, still execute
                print(
                    "⚠️  WARNING: Docker is not available. Running code locally. "
                    "This is less secure. Enable Docker for full sandboxing.",
                    file=sys.stderr
                )
                command = [sys.executable, temp_script]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,    # Increased from 30s to 60s
                cwd=self.volume_path
            )

            # Identify newly created artifact files
            post_execution_files = set(os.listdir(figures_dir))
            new_files = list(post_execution_files - pre_execution_files)
            artifact_paths = [
                os.path.join("exports", "figures", session_id, f) for f in new_files
            ]

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "is_sandbox": self.is_docker_available,
                "artifacts": artifact_paths,
                "blocked": False,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "⏱️ Execution timed out (60s limit). Try a simpler query.",
                "success": False,
                "is_sandbox": self.is_docker_available,
                "artifacts": [],
                "blocked": False,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "success": False,
                "is_sandbox": self.is_docker_available,
                "artifacts": [],
                "blocked": False,
            }
        finally:
            if os.path.exists(temp_script):
                os.remove(temp_script)


# Example usage
if __name__ == "__main__":
    sandbox = ExecutionSandbox()
    print(f"Docker available: {sandbox.is_docker_available}")
    test_code = "print('Hello from StatBot!')\nimport pandas as pd\nprint('Pandas ready.')"
    res = sandbox.execute_code(test_code, session_id="test_session")
    print(res)
