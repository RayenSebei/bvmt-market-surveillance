"""Run the BVMT analysis pipeline from the repository root."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRAPE_STEPS = ["src/scraping/scrape_ilboursa.py", "src/scraping/scrape_news.py"]
BUILD_STEPS = ["src/evaluation/build_full_universe.py"]
ANALYSIS_STEPS = [
    "src/detection/anomaly_detector.py",
    "src/detection/decay_detector.py",
    "src/detection/crossref_legal_events.py",
    "src/validation/classify_anomalies.py",
    "src/validation/refine_watchlist.py",
    "src/triage/ai_triage_free.py",
    "src/validation/validate_distress_cases.py",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BVMT statistical screening from existing local data."
    )
    parser.add_argument(
        "--with-scrape", action="store_true",
        help="refresh market/news data before analysis (requires network access)",
    )
    parser.add_argument(
        "--skip-ai", action="store_true",
        help="skip the optional Groq-assisted triage step",
    )
    return parser


def selected_steps(with_scrape: bool = False, skip_ai: bool = False) -> list[str]:
    steps = (
        [*SCRAPE_STEPS, *BUILD_STEPS, *ANALYSIS_STEPS]
        if with_scrape else [*BUILD_STEPS, *ANALYSIS_STEPS]
    )
    if skip_ai:
        steps.remove("src/triage/ai_triage_free.py")
    return steps


def run_script(script: str, position: int, total: int) -> None:
    path = ROOT / script
    print(f"\n[{position}/{total}] Running {script}", flush=True)
    environment = os.environ.copy()
    existing_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(ROOT) + (os.pathsep + existing_path if existing_path else "")
    result = subprocess.run(
        [sys.executable, str(path)], cwd=ROOT, env=environment, check=False
    )
    if result.returncode:
        raise RuntimeError(f"{script} failed with exit code {result.returncode}")
    print(f"[{position}/{total}] Completed {script}", flush=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    steps = selected_steps(with_scrape=args.with_scrape, skip_ai=args.skip_ai)
    mode = "scrape + analysis" if args.with_scrape else "analysis only (existing data)"
    print("BVMT Market Surveillance Pipeline")
    print(f"Mode: {mode}")
    print(f"AI triage: {'disabled' if args.skip_ai else 'enabled when configured'}")
    try:
        for position, script in enumerate(steps, start=1):
            run_script(script, position, len(steps))
    except (RuntimeError, OSError) as exc:
        print(f"\nPIPELINE STOPPED: {exc}", file=sys.stderr)
        return 1
    print("\nPipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
