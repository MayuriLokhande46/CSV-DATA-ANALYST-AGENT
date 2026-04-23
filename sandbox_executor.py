import subprocess
import os
import uuid
import sys

class ExecutionSandbox:
    def __init__(self, image_name="statbot-sandbox", volume_path=None):
        self.image_name = image_name
        self.volume_path = volume_path or os.getcwd()
        self.is_docker_available = self._check_docker()

    def _check_docker(self):
        """Checks if Docker is installed and running."""
        try:
            subprocess.run(["docker", "ps"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def execute_code(self, code: str):
        """
        Executes the provided python code inside a Docker container (if available)
        or locally (fallback).
        Returns a dictionary with result and list of artifacts (plots).
        """
        task_id = str(uuid.uuid4())[:8]
        temp_script = f"temp_task_{task_id}.py"
        
        # Ensure exports directory exists
        figures_dir = os.path.join(self.volume_path, "exports", "figures")
        os.makedirs(figures_dir, exist_ok=True)
        
        # Track initial state of figures
        pre_execution_files = set(os.listdir(figures_dir))
        
        # Ensure we write the script to the current directory
        with open(temp_script, "w") as f:
            f.write(code)
            
        try:
            if self.is_docker_available:
                command = [
                    "docker", "run", "--rm",
                    "-v", f"{self.volume_path}:/app",
                    "-w", "/app",
                    self.image_name,
                    "python", temp_script
                ]
            else:
                # Local Fallback
                command = [sys.executable, temp_script]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            
            # Identify new artifacts
            post_execution_files = set(os.listdir(figures_dir))
            new_files = list(post_execution_files - pre_execution_files)
            artifact_paths = [os.path.join("exports", "figures", f) for f in new_files]
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "is_sandbox": self.is_docker_available,
                "artifacts": artifact_paths
            }
            
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Execution timed out (30s limit)", "success": False, "is_sandbox": self.is_docker_available, "artifacts": []}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "success": False, "is_sandbox": self.is_docker_available, "artifacts": []}
        finally:
            if os.path.exists(temp_script):
                os.remove(temp_script)

# Example usage
if __name__ == "__main__":
    sandbox = ExecutionSandbox()
    print(f"Docker available: {sandbox.is_docker_available}")
    test_code = "print('Hello from StatBot!')\nimport pandas as pd\nprint('Pandas ready.')"
    res = sandbox.execute_code(test_code)
    print(res)
