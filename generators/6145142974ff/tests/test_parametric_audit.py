"""Regression tests for the reusable parametric self-audit."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


audit = _load("_test_6145142974ff_audit", "audit.py")


def test_structural_audit_covers_counts_settings_and_declared_rivals():
    report = audit.structural_audit(seed_count=4)
    assert report["failures"] == []
    assert report["episodes"] == 4 * 5 * 2
    assert report["matched_input_checks"] == 4 * 5
    assert report["finite_rival_certificates"] == report["episodes"]
    assert report["public_turn_checks"] == report["episodes"] * 4
    assert report["stress_30x30_checks"] == report["episodes"]


def test_public_export_writer_uses_opaque_visible_byte_ids(tmp_path):
    report = audit.write_public_exports(tmp_path, seed=0, demos=3)
    assert report["files"] == 8
    paths = sorted(tmp_path.glob("*.json"))
    assert len(paths) == 8
    assert all(len(path.stem) == 64 for path in paths)
    for path in paths:
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
