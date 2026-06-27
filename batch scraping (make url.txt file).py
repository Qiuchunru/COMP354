"""Deprecated: use `python main.py scrape urls.txt` instead."""
from sponsor_pipeline.cli import main
import sys

if __name__ == "__main__":
    raise SystemExit(main(["scrape"] + sys.argv[1:]))
