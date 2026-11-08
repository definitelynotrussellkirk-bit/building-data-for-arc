"""Safety tests for the task-local manual authority synchronizer."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
TOOL = HOME / "workspace" / "manual_authority_sync.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("manual_authority_sync_83ca9df09514", TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_patch_document_changes_only_selected_target_and_preserves_archival_raw():
    tool = _load_tool()
    old = "(rule! (lambda (g) (old g)))"
    new = "(rule! (lambda (g) (new g)))"
    before = {
        "task_id": "83ca9df09514",
        "unrelated": {"keep": [1, 2, 3]},
        "racket_target": {
            "raw_code": old,
            "target_code": old,
            "target_status": "verified_racket_available",
        },
    }
    text = json.dumps(before, indent=2, sort_keys=True) + "\n"
    patched = tool.patch_document(text, expected_old=old, canonical=new)
    after = json.loads(patched)

    expected = json.loads(text)
    expected["racket_target"]["target_code"] = new
    assert after == expected
    assert after["racket_target"]["raw_code"] == old
    assert after["unrelated"] == before["unrelated"]


def test_patch_document_refuses_wrong_source_or_ambiguous_encoding():
    tool = _load_tool()
    old = "(old)"
    new = "(new)"
    text = json.dumps({"racket_target": {"raw_code": old, "target_code": old}})
    with pytest.raises(ValueError):
        tool.patch_document(text, expected_old="(different)", canonical=new)

    ambiguous = text + "\n" + text
    with pytest.raises(ValueError):
        tool.patch_document(ambiguous, expected_old=old, canonical=new)
