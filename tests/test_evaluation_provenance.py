import json
from pathlib import Path
import shutil
import uuid

import pytest

from src.evaluation import provenance


def prepare_tree(root: Path) -> None:
    for relative in (*provenance.INPUT_PATHS, *provenance.OUTPUT_PATHS):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture:{relative}\n", encoding="utf-8")


@pytest.fixture
def writable_tree():
    root = Path.cwd() / f".test-provenance-{uuid.uuid4().hex}"
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root)


def test_manifest_verification_detects_fresh_and_stale_outputs(writable_tree):
    prepare_tree(writable_tree)
    manifest_path = writable_tree / "outputs/evaluation/manifest.json"
    provenance.write_manifest(manifest_path, writable_tree)
    assert provenance.verify_manifest(manifest_path, writable_tree)["fresh"] is True

    changed = writable_tree / provenance.INPUT_PATHS[0]
    changed.write_text("changed\n", encoding="utf-8")
    result = provenance.verify_manifest(manifest_path, writable_tree)
    assert result["fresh"] is False
    assert provenance.INPUT_PATHS[0] in result["mismatches"]


def test_invalid_manifest_is_reported_without_exception(writable_tree):
    path = writable_tree / "manifest.json"
    path.write_text("not json", encoding="utf-8")
    assert provenance.verify_manifest(path, writable_tree)["mismatches"] == ["manifest_invalid"]
