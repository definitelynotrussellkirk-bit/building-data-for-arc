"""Regression tests for the reusable source-bound contract probe."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROBE_PATH = HERE / "probe_contract.py"
GENERATOR_PATH = HERE.parent / "generator.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("probe_contract", PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_probe_exhausts_profiles_and_verifies_declared_shortcut():
    probe = _load_probe()
    report = probe.analyze(GENERATOR_PATH)
    assert report["ok"] is True
    assert report["generator_sha256"] == hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert report["rule_hash"] == "326f0e0036c3"
    assert report["canonical_pairs"] == 8
    assert report["canonical_shortcut_fits"] == 8
    assert report["profile_count"] == 16
    assert report["profiles_lawful"] == 16
    assert report["profiles_observed_exactly"] == 16
    assert report["profiles_distinguishing"] == 16
    assert report["distinct_outputs"] == 16


def test_probe_retains_an_exact_size_lookup_counterexample():
    probe = _load_probe()
    witness = probe.analyze(GENERATOR_PATH)["counterexample"]
    assert witness["profile"] == "n11_vertical_c7"
    assert witness["self_check"] == []
    assert witness["observed"] == {"scene_profile": "n11_vertical_c7"}
    assert witness["intended_output"] != witness["rival_output"]
    assert sum(value == 5 for row in witness["input"] for value in row) == 7
    assert sum(value == 5 for row in witness["intended_output"] for value in row) == 7
    assert sum(value == 5 for row in witness["rival_output"] for value in row) == 9


def test_cli_writes_the_same_source_bound_report(tmp_path):
    destination = tmp_path / "report.json"
    completed = subprocess.run(
        [sys.executable, str(PROBE_PATH), "--out", str(destination)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(destination.read_text())
    assert report["ok"] is True
    assert report["generator_sha256"] == hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
