"""Regression coverage for the reusable c5a69e7cd8c8 curriculum probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def test_probe_exhausts_schedule_rotations_and_geometric_contract():
    path = Path(__file__).resolve().parents[1] / "workspace" / "probe_curriculum.py"
    spec = importlib.util.spec_from_file_location("c5a69e7cd8c8_curriculum_probe", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.audit(seeds=(901,), starts=8)
    assert report["status"] == "PASS", report
    assert report["windows_checked"] == 3 * 8
    assert report["rotations_checked"] == 3 * 8 * 4
    assert report["geometric_contract_cases"] == 7 * 4 * 2 * 3
    assert report["canonical_pairs"] == 4
    assert report["canonical_shortcut_failures"] == []
    assert report["ambiguities"] == []
    assert report["geometric_failures"] == []
    assert report["witness_claim_failures"] == []
