"""Behavioral tests for the reusable source-bound review probe."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_HOME / "workspace" / "probe_generator.py"
SPEC = importlib.util.spec_from_file_location("left_pack_workspace_probe", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


def test_probe_covers_the_full_schedule_and_reports_no_failures():
    module, source = probe.load_generator()
    report = probe.audit(module, source, seeds_per_band=1)

    assert report["failures"] == []
    assert report["generator_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["schedule_period"] == 4
    assert report["counts"]["generated_grids"] == 16
    assert report["counts"]["query_rotations"] == 16
    assert report["counts"]["canonical_pairs"] == 4
    assert report["canonical_shortcut_fit"] == {
        "first_four_active_rows_only": 4,
        "fixed_five_rows": 4,
    }


def test_probe_rejects_a_stale_expected_source_hash():
    module, source = probe.load_generator()
    with pytest.raises(ValueError, match="source hash mismatch"):
        probe.audit(
            module,
            source,
            seeds_per_band=1,
            expected_generator_sha256="0" * 64,
        )


def test_probe_reports_schedule_profile_drift(monkeypatch):
    module, source = probe.load_generator()
    monkeypatch.setattr(
        module,
        "schedule_profile",
        lambda seed, sample_index, difficulty=None: "undeclared_profile",
    )

    report = probe.audit(module, source, seeds_per_band=1)

    assert any(item["kind"] == "schedule_profile_mismatch" for item in report["failures"])


def test_probe_reports_missing_semantic_declarations():
    module, source = probe.load_generator()
    module.SEMANTIC_WITNESSES = dict(module.SEMANTIC_WITNESSES)
    module.SEMANTIC_WITNESSES.pop("internal_gap_collapse")
    module.CANONICAL_SHORTCUTS = dict(module.CANONICAL_SHORTCUTS)
    module.CANONICAL_SHORTCUTS.pop("fixed_five_rows")
    module.LESSON_COMPETITORS = dict(module.LESSON_COMPETITORS)
    module.LESSON_COMPETITORS.pop("identity")

    report = probe.audit(module, source, seeds_per_band=1)
    failure_kinds = {item["kind"] for item in report["failures"]}

    assert "missing_witness_declaration" in failure_kinds
    assert "missing_shortcut_declaration" in failure_kinds
    assert "missing_competitor_declaration" in failure_kinds
