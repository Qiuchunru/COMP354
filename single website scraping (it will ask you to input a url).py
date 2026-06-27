"""Deprecated: use `python main.py scrape --output emails.txt` with a single URL in urls.txt."""
from sponsor_pipeline.cli import main
import sys

if __name__ == "__main__":
    url = input("Enter the domain URL: ").strip()
    if not url:
        raise SystemExit("URL required")

    # Appending manually entered URL into urls.txt
    from pathlib import Path
    with open("urls.txt", "a", encoding="utf-8") as urls_file:
        urls_file.write(url + "\n")

    # Passing URL directly to cli.py via --url flag
    raise SystemExit(main(["scrape", "--url", url, "--append"]))
