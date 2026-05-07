#!/usr/bin/env python3
"""
Crypto RPA Dashboard Runner.
Run the Flask dashboard for data visualization.
"""

import os
import subprocess

BASE_DIR = os.path.dirname(__file__)


def resolve_python_executable():
    """Resolve python executable from .venv/venv with system fallback."""
    for env_dir in (".venv", "venv"):
        candidate = os.path.join(BASE_DIR, env_dir, "bin", "python")
        if os.path.exists(candidate):
            return candidate
        candidate = os.path.join(BASE_DIR, env_dir, "Scripts", "python.exe")
        if os.path.exists(candidate):
            return candidate
    return "python3"


def run_dashboard():
    """Run the Flask dashboard."""
    dashboard_path = os.path.join(BASE_DIR, "dashboard", "app_new.py")
    python_exe = resolve_python_executable()

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = BASE_DIR
        if python_exe == "python":
            print("Virtual environment not found, using system Python...")
        subprocess.run([python_exe, dashboard_path], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running dashboard: {e}")
    except KeyboardInterrupt:
        print("Dashboard stopped")


if __name__ == "__main__":
    print("Starting Crypto RPA Dashboard...")
    print("Open your browser to http://localhost:5000")
    run_dashboard()
