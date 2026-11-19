"""Entry point: `python -m slider`."""

import sys

from dotenv import load_dotenv

from slider.cli import main

if __name__ == "__main__":
    load_dotenv()
    sys.exit(main())
