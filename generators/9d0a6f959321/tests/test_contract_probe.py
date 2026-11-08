"""Portable smoke test for the future-review contract probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE = Path(__file__).resolve().parents[1] / "workspace" / "contract_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("contract_probe_9d0a6f959321", PROBE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import probe from {PROBE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_probe_reports_clean_source_bound_summary():
    probe = _load_probe()
    report = probe.run_probe(samples_per_band=12, starts=6)
    assert report["status"] == "pass"
    assert report["task_id"] == "9d0a6f959321"
    assert report["rule_hash"] == "7af38e7dbf07"
    assert report["summary"]["generated"] == 36
    assert report["summary"]["override_failures"] == 0
    assert report["summary"]["self_check_failures"] == 0
    assert report["summary"]["rule_mirror_failures"] == 0
    assert report["summary"]["ambiguous_production_lessons"] == 0
    assert report["summary"]["ambiguous_query_rotations"] == 0
