"""Smoke tests for the reusable source-only qualification helper."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import load_generator
import qualify


gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_qualification_report_covers_population_axes_witnesses_and_rotations():
    report = qualify.qualify_generator(gen, per_band=12, starts=6, seed=20261004)
    assert report["status"] == "PASS", report["errors"]
    assert report["population"]["draws"] == 36
    assert report["population"]["self_check_failures"] == 0
    assert report["population"]["observer_mismatches"] == 0
    assert report["population"]["identity_outputs"] == 0
    assert report["population"]["unique_inputs"] >= 35
    assert set(report["population"]["witness_counts"]) == set(gen.SEMANTIC_WITNESSES)
    assert all(count > 0 for count in report["population"]["witness_counts"].values())
    assert report["overrides"]["cases"] >= 5
    assert report["overrides"]["failures"] == 0
    assert report["lessons"]["rotations"] == 3 * 6 * 4
    assert report["lessons"]["unidentifiable_rotations"] == 0


def test_cli_writes_machine_readable_report(tmp_path, monkeypatch):
    out = tmp_path / "qualification.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["qualify.py", "--per-band", "6", "--starts", "3", "--out", str(out)],
    )
    assert qualify.main() == 0
    payload = json.loads(out.read_text())
    assert payload["status"] == "PASS"
    assert payload["generator"]["task_id"] == "3a96552d8c7c"
