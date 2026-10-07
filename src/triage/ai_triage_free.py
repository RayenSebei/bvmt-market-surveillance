"""Optional Groq-assisted triage for the BVMT statistical watchlist.

The model receives only already-computed screening evidence. Its output is a
draft prioritisation aid for human review, never a verdict. If configuration
or the service is unavailable, this module leaves the existing output intact.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        env_path = Path(".env")
        if not env_path.exists():
            return False
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))
        return True

load_dotenv()
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
OUT_DIR = Path("bvmt_data")
IN_PATH = OUT_DIR / "watchlist_refined.csv"
OUT_PATH = OUT_DIR / "watchlist_ai_assessed.csv"
PAUSE_SECONDS = 3
VALID_ASSESSMENTS = {"likely_noise", "worth_investigating", "uncertain"}
MAX_COMPLETION_TOKENS = 1500

SYSTEM_PROMPT = """You assist a student market-surveillance research tool for
the Tunis Stock Exchange. Assess only the quantitative evidence supplied.
You are not a regulator and cannot confirm wrongdoing. Return JSON with keys
assessment (likely_noise, worth_investigating, or uncertain) and reasoning
(one or two plain-language sentences citing the supplied numbers). Be
conservative, do not invent explanations, and treat repeated thin-trading
flags as possible liquidity noise."""


def build_user_prompt(row: Any, repeat_count: int) -> str:
    fields = {
        "ticker": row.get("symbole"), "company_name": row.get("ticker_name"),
        "date": str(row.get("date")), "source_detector": row.get("source"),
        "volume_zscore": row.get("volume_zscore"),
        "return_zscore": row.get("return_zscore"),
        "decline_ratio": row.get("decline_ratio"),
        "excess_return_vs_index": row.get("excess_return"),
        "co_flagged_other_tickers_same_day": row.get("co_flagged_count"),
        "tag_from_index_check": row.get("tag"),
        "times_this_ticker_appears_in_watchlist": repeat_count,
    }
    return "Assess this flagged anomaly:\n" + json.dumps(fields, default=str, indent=2)


def parse_json_response(text: str) -> dict[str, str]:
    """Extract the first valid assessment object from a possibly noisy reply."""
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(value, dict):
            continue
        assessment = value.get("assessment")
        reasoning = value.get("reasoning")
        if assessment in VALID_ASSESSMENTS and isinstance(reasoning, str) and reasoning.strip():
            return {"assessment": assessment, "reasoning": reasoning.strip()}
    raise ValueError("response did not contain a valid assessment JSON object")


def create_client(api_key: str):
    from openai import OpenAI
    return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)


def assess_row(row: Any, repeat_count: int, client: Any, max_retries: int = 3) -> tuple[str, str]:
    user_prompt = build_user_prompt(row, repeat_count)
    last_error = "unknown error"
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort="low",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or ""
            if not content.strip():
                raise ValueError("model returned empty content")
            parsed = parse_json_response(content)
            return parsed["assessment"], parsed["reasoning"]
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt + 1 < max_retries:
                wait = 20 * (attempt + 1) if "429" in str(exc) else 2 * (attempt + 1)
                print(f"  retry {attempt + 1}/{max_retries} for {row.get('symbole')} (waiting {wait}s)")
                time.sleep(wait)
    raise RuntimeError(f"AI triage failed after {max_retries} attempts: {last_error}")


def main() -> int:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("AI triage skipped: GROQ_API_KEY is not configured; existing output preserved.")
        return 0
    if not IN_PATH.exists():
        print(f"AI triage skipped: input file not found: {IN_PATH}; existing output preserved.")
        return 0
    try:
        client = create_client(api_key)
    except Exception as exc:
        print(f"AI triage skipped: client unavailable ({type(exc).__name__}); existing output preserved.")
        return 0
    frame = pd.read_csv(IN_PATH)
    repeat_counts = frame["symbole"].value_counts()
    assessments: list[str] = []
    reasonings: list[str] = []
    print(f"AI triage: {len(frame)} rows using model {MODEL}")
    try:
        for index, row in frame.iterrows():
            symbol = row.get("symbole")
            print(f"[{index + 1}/{len(frame)}] Assessing {symbol}")
            assessment, reasoning = assess_row(row, int(repeat_counts.get(symbol, 1)), client)
            assessments.append(assessment)
            reasonings.append(reasoning)
            if index + 1 < len(frame):
                time.sleep(PAUSE_SECONDS)
    except Exception as exc:
        print(f"AI triage skipped: {exc}; existing output preserved.")
        return 0
    frame["ai_assessment"] = assessments
    frame["ai_reasoning"] = reasonings
    OUT_DIR.mkdir(exist_ok=True)
    frame.to_csv(OUT_PATH, index=False)
    print(f"AI triage saved: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
