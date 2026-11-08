"""Regression coverage for the retained task-local adversarial probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent
PROBE_PATH = TASK_HOME / "workspace" / "distribution_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "distribution_probe_round2", PROBE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {PROBE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_exhausts_every_declared_rival_and_feature_breaker():
    probe = _load_probe()
    gen = probe._load_generator()
    result, passed = probe.run_probe(seed_count=1)

    assert passed, result["failures"]
    assert result["schema"] == "9758187b19ad-distribution-probe-v2"
    assert set(result["canonical_shortcuts"]) == set(gen.CANONICAL_SHORTCUTS)
    assert all(
        record["fits_all"] for record in result["canonical_shortcuts"].values()
    )

    expected_rivals = set(gen.LESSON_COMPETITORS)
    for record in result["lesson_windows"].values():
        assert set(record["survivor_starts_by_rival"]) == expected_rivals
        assert all(not starts for starts in record["survivor_starts_by_rival"].values())
        assert all(not starts for starts in record["missing_feature_starts"].values())

    assert set(result["exact_disagreement_cases"]) == expected_rivals
    assert all(
        case["first_disagreement"] is not None
        for case in result["exact_disagreement_cases"].values()
    )
