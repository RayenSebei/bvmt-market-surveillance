"""Write and verify reproducibility metadata for generated evaluation outputs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "outputs" / "evaluation"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
INPUT_PATHS = (
    "bvmt_data/_all_tickers_full.csv",
    "bvmt_data/anomaly_flags.csv",
    "data/evaluation/events.csv",
    "src/detection/anomaly_detector.py",
    "src/evaluation/config.json",
    "src/evaluation/evaluate.py",
    "src/evaluation/baselines.py",
    "src/evaluation/sensitivity.py",
    "src/evaluation/report.py",
)
OUTPUT_PATHS = (
    "outputs/evaluation/metrics.csv",
    "outputs/evaluation/baseline_comparison.csv",
    "outputs/evaluation/sensitivity.csv",
    "outputs/evaluation/events_table.csv",
    "outputs/evaluation/summary.md",
)


TEXT_SUFFIXES = {".csv", ".json", ".md", ".py", ".txt"}


def file_sha256(path: Path) -> str | None:
    """Hash text with canonical LF endings so manifests travel across OSes."""
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    content = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    digest.update(content)
    return digest.hexdigest()


def build_manifest(root: Path = ROOT) -> dict:
    return {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "hash_mode": "sha256_text_lf_normalized",
        "detector_policy": {
            "minimum_valid_prior_observations": 60,
            "ohlc_policy": "raw",
            "current_observation_excluded_from_baseline": True,
        },
        "inputs": {relative: file_sha256(root / relative) for relative in INPUT_PATHS},
        "outputs": {relative: file_sha256(root / relative) for relative in OUTPUT_PATHS},
    }


def write_manifest(path: Path = MANIFEST_PATH, root: Path = ROOT) -> dict:
    manifest = build_manifest(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return manifest


def verify_manifest(path: Path = MANIFEST_PATH, root: Path = ROOT) -> dict:
    if not path.is_file():
        return {"fresh": False, "generated_at_utc": None, "mismatches": ["manifest_missing"]}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"fresh": False, "generated_at_utc": None, "mismatches": ["manifest_invalid"]}
    mismatches = []
    for relative, expected in manifest.get("inputs", {}).items():
        if file_sha256(root / relative) != expected:
            mismatches.append(relative)
    for relative, expected in manifest.get("outputs", {}).items():
        if file_sha256(root / relative) != expected:
            mismatches.append(relative)
    return {
        "fresh": not mismatches,
        "generated_at_utc": manifest.get("generated_at_utc"),
        "mismatches": mismatches,
    }


def main() -> int:
    manifest = write_manifest()
    print(f"Saved {MANIFEST_PATH} at {manifest['generated_at_utc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
