"""
scraper/run_pipeline.py
=======================
This file is called by the dashboard backend whenever a user opens the page.
It runs in the background (non-blocking) and updates the CSV files in ./data/

EDIT THIS FILE to point to your actual pipeline entry point.
"""

import os
import argparse
import subprocess
import sys

# ── OPTION A: Call your existing main scraper script ────────────────────────
# Change this path to wherever your pipeline entry point is
PIPELINE_SCRIPT = os.environ.get(
    "PIPELINE_SCRIPT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run_all.py")),
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local BVMT pipeline wrapper.")
    parser.add_argument(
        "--with-scrape", action="store_true",
        help="explicitly enable the network scraping stages",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    print(f"[Scraper] Starting pipeline: {PIPELINE_SCRIPT}")
    command = [sys.executable, PIPELINE_SCRIPT]
    if args.with_scrape:
        command.append("--with-scrape")
    result = subprocess.run(
        command,
        capture_output=False,
        text=True
    )
    if result.returncode == 0:
        print("[Scraper] Pipeline completed successfully.")
    else:
        print(f"[Scraper] Pipeline exited with code {result.returncode}")
        sys.exit(result.returncode)
