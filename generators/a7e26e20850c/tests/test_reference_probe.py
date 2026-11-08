"""Regression tests for the portable future-review probe."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HOME = Path(__file__).resolve().parents[1]
PROBE = HOME / "workspace" / "reference_probe.py"


def _load_probe():
    assert PROBE.exists(), "workspace/reference_probe.py must be retained for future agents"
    spec = importlib.util.spec_from_file_location("a7_reference_probe", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_oracle_matches_every_canonical_label():
    probe = _load_probe()
    pairs = probe.canonical_pairs()
    assert len(pairs) == 3
    assert all(probe.intended_output(pair["input"]) == pair["output"] for pair in pairs)
    assert all(probe.first_three_rival(pair["input"]) == pair["output"] for pair in pairs)


def test_probe_audit_exercises_counterexample_and_exact_axes():
    probe = _load_probe()
    report = probe.audit(probe.load_generator(), count=12)
    assert report["canonical_matches"] == 3
    assert report["counts"]["samples"] == 48
    assert report["counts"]["self_check_errors"] == 0
    assert report["counts"]["nondeterministic"] == 0
    assert report["counts"]["rival_disagreements"] >= 20
    assert report["counts"]["object_count_mismatches"] == 0
    assert set(report["observed"]["n_sizes"]) == {2, 3, 4}


def test_probe_cli_writes_reproducible_json(tmp_path):
    out = tmp_path / "probe.json"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    subprocess.run(
        [sys.executable, "-B", str(PROBE), "--count", "4", "--out", str(out)],
        check=True,
        env=env,
        text=True,
    )
    report = json.loads(out.read_text())
    assert report["schema"] == "a7e26e20850c-reference-probe-v1"
    assert report["counts"]["samples"] == 16
    assert report["generator_sha256"]
    assert report["probe_sha256"]
