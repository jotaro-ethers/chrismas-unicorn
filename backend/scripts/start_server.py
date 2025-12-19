#!/usr/bin/env python3
"""
FastAPI Supabase Backend Startup Script
Cross-platform Python script to start the FastAPI server
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main function to start the FastAPI server."""
    # Get project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    # Check for virtual environment
    venv_dir = project_dir / "venv"
    if not venv_dir.exists():
        print("Error: Virtual environment not found!")
        print("Please run: python -m venv venv")
        sys.exit(1)

    # Determine python executable
    if os.name == "nt":  # Windows
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:  # Unix-like
        python_exe = venv_dir / "bin" / "python"

    # Check for .env file
    env_file = project_dir / ".env"
    if not env_file.exists():
        print("Warning: .env file not found!")
        print("Creating from template...")

        env_example = project_dir / ".env.example"
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("Please edit .env with your Supabase credentials")
        else:
            print("No .env.example found. Creating basic .env...")
            with open(env_file, "w") as f:
                f.write("""# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# FastAPI Configuration
API_V1_STR=/api/v1
PROJECT_NAME=FastAPI Supabase Backend
ENVIRONMENT=development

# Development
DEBUG=True
HOST=0.0.0.0
PORT=8000
""")

    # Install package in editable mode
    print("Ensuring package is installed in editable mode...")
    subprocess.run([str(python_exe), "-m", "pip", "install", "-e", "."], check=True)

    # Get environment variables for host and port
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")

    # Start uvicorn
    print(f"\nStarting FastAPI server...")
    print(f"Server will be available at: http://{host}:{port}")
    print(f"API docs at: http://{host}:{port}/docs")
    print("\nPress Ctrl+C to stop the server\n")

    # Run uvicorn
    try:
        subprocess.run([
            str(python_exe), "-m", "uvicorn",
            "main_app.main:app",
            "--reload",
            "--host", host,
            "--port", port
        ], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except subprocess.CalledProcessError as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()