from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

TASK_ID = "eefadafb2b7b"
gen = importlib.import_module(f"generators.{TASK_ID}.generator")
BASELINE = (
    Path(__file__).resolve().parents[1]
    / "counterexamples"
    / "request-contract-baseline.json"
)


def _grid_sha256(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_every_recorded_valid_request_is_byte_for_byte_stable():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert baseline["schema"] == "eefadafb2b7b-valid-request-baseline-v1"
    assert baseline["case_count"] == len(baseline["cases"]) == 224
    observed_hashes = []
    for case in baseline["cases"]:
        grid = gen.generate(
            case["seed"],
            case["sample_index"],
            difficulty=case["difficulty"],
            **case["overrides"],
        )
        assert grid == case["grid"]
        digest = _grid_sha256(grid)
        assert digest == case["grid_sha256"]
        observed_hashes.append(digest)
    aggregate = hashlib.sha256("\n".join(observed_hashes).encode("utf-8")).hexdigest()
    assert aggregate == baseline["aggregate_sha256"] == (
        "6c05b9cc04484978cea6323215375934130cca4ab406c3927ac745152a83a2f0"
    )


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_must_be_a_plain_python_integer(seed):
    with pytest.raises(ValueError, match="seed"):
        gen.generate(seed, 0)


@pytest.mark.parametrize(
    "sample_index", [True, False, 1.0, 1.75, "1", -1]
)
def test_sample_index_must_be_a_nonnegative_plain_python_integer(sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid__"])
def test_difficulty_is_none_or_one_of_the_three_named_bands(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w"])
@pytest.mark.parametrize("value", [True, False, "5", 5.0, 5.5])
def test_integer_overrides_reject_coercible_nonintegers(axis, value):
    with pytest.raises(ValueError, match=axis):
        gen.generate(0, 0, **{axis: value})


@pytest.mark.parametrize("lesson_profile", [True, False, 0, 1.0, ["small_bridge"]])
def test_lesson_profile_must_be_an_exact_declared_string(lesson_profile):
    with pytest.raises(ValueError, match="lesson_profile"):
        gen.generate(0, 0, lesson_profile=lesson_profile)
