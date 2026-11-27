"""One-click launcher for LexiCount (used by START_LexiCount_Windows.bat and START_LexiCount_Mac.command).

What it does, in order:
  1. Checks the Python version (3.10 or newer).
  2. First run only: creates a private virtual environment in lexicount/.venv and installs
     lexicount/requirements.txt (needs internet, about 1-2 minutes). Nothing outside this folder changes.
  3. Creates the test datasets (1, 10 and 100 MB) if they are missing.
  4. Starts the web dashboard and opens it in the browser.

If the packages cannot be installed (for example, no internet), it falls back to the command-line
version (main.py), which needs only the Python standard library.

Options:  --cli    run the command-line demo instead of the dashboard
Uses only the standard library, so it runs with any Python 3.10+ installation.
"""

import hashlib
import os
import socket
import subprocess
import sys
import time
import urllib.request
import venv
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.join(HERE, "lexicount")
VENV = os.path.join(PROJECT, ".venv")
REQUIREMENTS = os.path.join(PROJECT, "requirements.txt")
MARKER = os.path.join(VENV, ".lexicount-installed")
DATASETS = ["1", "10", "100"]  # MB; generated the same way on every computer


def say(text: str = "") -> None:
    print(text, flush=True)


def venv_python() -> str:
    folder = "Scripts" if os.name == "nt" else "bin"
    name = "python.exe" if os.name == "nt" else "python"
    return os.path.join(VENV, folder, name)


def requirements_hash() -> str:
    with open(REQUIREMENTS, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


def install_packages() -> bool:
    """Create lexicount/.venv and install the requirements once. Returns True when ready."""
    if os.path.isfile(MARKER) and os.path.isfile(venv_python()):
        with open(MARKER, encoding="utf-8") as file:
            if file.read().strip() == requirements_hash():
                return True
    say("First run: setting up LexiCount (about 1-2 minutes, needs internet)...")
    try:
        if not os.path.isfile(venv_python()):
            venv.EnvBuilder(with_pip=True).create(VENV)
        subprocess.run([venv_python(), "-m", "pip", "install", "--disable-pip-version-check", "-q",
                        "-r", REQUIREMENTS], check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        say(f"Could not install the dashboard packages ({error}).")
        return False
    with open(MARKER, "w", encoding="utf-8") as file:
        file.write(requirements_hash())
    say("Setup complete.")
    return True


def make_datasets(python: str) -> None:
    """Create the test files in lexicount/data (skips files that already exist)."""
    missing = [size for size in DATASETS
               if not os.path.isfile(os.path.join(PROJECT, "data", f"dataset_{size}MB.txt"))]
    if missing:
        say(f"Creating test datasets ({', '.join(m + ' MB' for m in missing)})...")
        subprocess.run([python, "dataset_generator.py", *missing], cwd=PROJECT, check=True,
                       stdout=subprocess.DEVNULL)


def free_port(start: int = 8501) -> int:
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def run_dashboard() -> int:
    make_datasets(venv_python())
    port = free_port()
    url = f"http://localhost:{port}"
    say(f"Starting the LexiCount dashboard at {url} ...")
    server = subprocess.Popen(
        [venv_python(), "-m", "streamlit", "run", "dashboard.py", "--server.headless", "true",
         "--server.port", str(port), "--browser.gatherUsageStats", "false"], cwd=PROJECT)
    for _ in range(120):  # wait up to 60 s for the server to answer
        if server.poll() is not None:
            say("The dashboard stopped unexpectedly; see the messages above.")
            return server.returncode or 1
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except OSError:
            time.sleep(0.5)
    if not os.environ.get("LEXICOUNT_NO_BROWSER"):
        webbrowser.open(url)
    say()
    say(f"LexiCount is running at {url}  (opened in your browser).")
    say("Keep this window open while you use it. Close the window or press Ctrl+C to stop.")
    try:
        return server.wait()
    except KeyboardInterrupt:
        server.terminate()
        return 0


def run_cli() -> int:
    """Command-line demo: standard library only, works without the dashboard packages."""
    python = sys.executable
    make_datasets(python)
    workers = str(min(4, os.cpu_count() or 1))
    say(f"Running the command-line demo on the 100 MB file with {workers} workers...")
    say()
    return subprocess.run([python, "main.py", "--file", os.path.join("data", "dataset_100MB.txt"),
                           "--workers", workers], cwd=PROJECT).returncode


def main() -> int:
    say("=" * 60)
    say("  LexiCount: Parallel Word Frequency Analyzer")
    say("=" * 60)
    if sys.version_info < (3, 10):
        say(f"Python 3.10 or newer is required (this is {sys.version.split()[0]}).")
        say("Download it from https://www.python.org/downloads/ and run this file again.")
        return 1
    if "--cli" in sys.argv:
        return run_cli()
    if install_packages():
        return run_dashboard()
    say("Falling back to the command-line version, which needs no extra packages.")
    say()
    return run_cli()


if __name__ == "__main__":
    sys.exit(main())
