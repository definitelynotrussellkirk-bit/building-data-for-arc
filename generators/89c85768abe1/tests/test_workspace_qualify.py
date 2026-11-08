from __future__ import annotations

import importlib.util
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_ROOT / "workspace" / "qualify.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("qualify_89c85768abe1", PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_workspace_qualification_probe_covers_contract_and_passes():
    probe = load_probe()
    report = probe.qualify(draws_per_band=12)
    assert report["status"] == "pass"
    assert report["errors"] == []
    assert report["bands"] == ["easy", "medium", "hard"]
    assert report["draws"] == 36
    assert report["lawful_draws"] == 36
    assert report["unique_inputs"] >= 34
    assert report["identifiable_windows"] == 36
    assert report["override_cases"] >= 36
    assert report["mutation_fixtures_rejected"] >= 5
    assert report["witness_hits"]["anti_diagonal_pair"] > 0
