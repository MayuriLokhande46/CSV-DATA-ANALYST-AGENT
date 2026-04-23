import subprocess
import sys
import os

def check_docker():
    """Checks if docker is installed and running."""
    try:
        subprocess.run(["docker", "ps"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def build_sandbox():
    print("🚀 Starting StatBot Pro Sandbox Setup...")
    
    if not check_docker():
        print("❌ Error: Docker is not installed or not running.")
        print("Please install Docker Desktop (https://www.docker.com/products/docker-desktop/) and try again.")
        return False
    
    print("✅ Docker detected.")
    
    dockerfile_path = "sandbox"
    if not os.path.exists(os.path.join(dockerfile_path, "Dockerfile")):
        print(f"❌ Error: Dockerfile not found in {dockerfile_path}/")
        return False
    
    print("🔨 Building Docker image 'statbot-sandbox'...")
    try:
        # Build the image
        subprocess.run(
            ["docker", "build", "-t", "statbot-sandbox", dockerfile_path],
            check=True
        )
        print("🎉 Success! StatBot Pro sandbox is now ready for secure execution.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building image: {e}")
        return False

if __name__ == "__main__":
    success = build_sandbox()
    if not success:
        sys.exit(1)
