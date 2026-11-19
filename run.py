"""Create the virtual environment if needed, install slider and start it.

Usage: python run.py examples/preso [-f video] [-t terminal]
"""

import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / os.getenv("VENV_DIR", ".venv")


def main() -> int:
    if not VENV_DIR.is_dir():
        print(f"Creating virtual environment in {VENV_DIR}")
        venv.create(VENV_DIR, with_pip=True)

    scripts = "Scripts" if os.name == "nt" else "bin"
    python = str(VENV_DIR / scripts / ("python.exe" if os.name == "nt" else "python"))

    subprocess.run(
        [python, "-m", "pip", "install", "-q", "-e", str(ROOT)],
        check=True,
    )
    # Run from the caller's folder so relative deck paths keep working.
    return subprocess.call([python, "-m", "slider", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())
