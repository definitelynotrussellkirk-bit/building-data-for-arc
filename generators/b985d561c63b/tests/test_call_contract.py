"""Strict public call-scalar contract for b985d561c63b."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location(
    "b985d561c63b_call_contract_subject",
    REPO / "generators/b985d561c63b/generator.py",
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
@pytest.mark.parametrize("difficulty", [None, "easy", "hard"])
def test_generate_rejects_nonliteral_integer_seed(seed, difficulty):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(seed, 0, difficulty=difficulty)


@pytest.mark.parametrize("sample_index", [True, False, 0.0, "0"])
@pytest.mark.parametrize("difficulty", [None, "easy", "hard"])
def test_generate_rejects_nonliteral_integer_sample_index(sample_index, difficulty):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(991, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", [None, "easy", "hard"])
def test_generate_rejects_negative_sample_index(difficulty):
    with pytest.raises(ValueError, match="nonnegative"):
        GEN.generate(991, -1, difficulty=difficulty)


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [(0, 0, None), (-1, 0, "easy"), (17, 7, "medium"), (991, 3, "hard")],
)
def test_generate_accepts_literal_integer_calls(seed, sample_index, difficulty):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    assert GEN.self_check(grid, difficulty=difficulty) == []


def test_retained_strict_call_scalar_counterexamples():
    import json

    fixture_path = Path(__file__).resolve().parents[1] / "counterexamples" / "strict_call_scalars.json"
    assert fixture_path.is_file(), f"missing retained counterexample fixture: {fixture_path}"
    fixture = json.loads(fixture_path.read_text())
    assert fixture["schema"] == "b985d561c63b-strict-call-scalars-v1"
    assert fixture["baseline_generator_sha256"] == "c8acb6b749fa8817826507cfa27043773d462b7791fd50f5ffa7716d7107fc1d"

    exception_types = {"TypeError": TypeError, "ValueError": ValueError}
    for case in fixture["cases"]:
        error = exception_types[case["expected_exception"]]
        with pytest.raises(error, match=case["message_pattern"]):
            GEN.generate(
                case["seed"],
                case["sample_index"],
                difficulty=case["difficulty"],
                **case.get("overrides", {}),
            )
