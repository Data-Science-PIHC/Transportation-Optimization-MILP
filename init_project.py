#!/usr/bin/env python3
"""
Project Initialization Script

This script helps set up the development environment for the Transportation Optimization project.
"""
import os
import sys
import subprocess
import platform

def print_header():
    print("=" * 60)
    print("Transportation Optimization - MILP")
    print("Project Setup")
    print("=" * 60)

def check_python_version():
    """Check if Python version is 3.7 or higher."""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        sys.exit(1)
    print(f"✓ Python {platform.python_version()} detected")

def create_virtualenv():
    """Create a virtual environment if it doesn't exist."""
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment already exists")
    return venv_dir

def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")
    pip_cmd = [
        os.path.join("venv", "Scripts", "pip"),
        "install",
        "-r",
        "requirements_optimizer.txt"
    ]
    subprocess.run(pip_cmd, check=True)
    print("✓ Dependencies installed")

def main():
    print_header()
    check_python_version()
    
    print("\nSetting up development environment...")
    venv_dir = create_virtualenv()
    install_dependencies()
    
    print("\nSetup complete!")
    print("\nTo activate the virtual environment, run:")
    if platform.system() == "Windows":
        print(f"  .\\{venv_dir}\\Scripts\\activate")
    else:
        print(f"  source {venv_dir}/bin/activate")
    print("\nTo run the application:")
    print("  streamlit run distribution_optimizer.py")

if __name__ == "__main__":
    main()
