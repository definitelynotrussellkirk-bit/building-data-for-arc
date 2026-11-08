"""Regression tests for the strict public replay-call contract."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root

TASK_ID = "0832c700ffb9"
ROOT = find_root(__file__)
_RUNTIME_GENERATOR = ROOT / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py"
_LIBRARY_GENERATOR = ROOT / f"generators/{TASK_ID}/generator.py"
GENERATOR_PATH = (
    _RUNTIME_GENERATOR if _RUNTIME_GENERATOR.is_file() else _LIBRARY_GENERATOR
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "strict_scalar_generator_0832c700ffb9", GENERATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_coercible_seed_scalars(gen, bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_coercible_sample_index_scalars(gen, bad_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.generate(991, bad_index, difficulty="easy")


def test_generate_rejects_negative_sample_index(gen):
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.generate(991, -1, difficulty="easy")


@pytest.mark.parametrize(
    "bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_generate_rejects_invalid_difficulty_scalars(gen, bad_difficulty):
    with pytest.raises(ValueError, match="difficulty must be one of"):
        gen.generate(991, 0, difficulty=bad_difficulty)


def test_schedule_profile_uses_the_same_strict_public_contract(gen):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.schedule_profile(True, 0, "easy")
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.schedule_profile(1, 0.0, "easy")
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.schedule_profile(1, -1, "easy")
    with pytest.raises(ValueError, match="difficulty must be one of"):
        gen.schedule_profile(1, 0, "expert")


def _grid_sha256(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize(
    "seed,sample_index,difficulty,overrides,expected",
    [
        (0, 0, None, {}, "5967e5bf5dbbb07b107b4083c0683ccca0351e25de2381d5fc109b8172802cd5"),
        (991, 0, "easy", {}, "bd3de80b8312f35d85f79baef4b98edc63381437ccee9eb68477123eae6ebcf2"),
        (-7, 5, "medium", {}, "c57a73c6133b95674f0799a3df1469a01b32b33f3687dec055849ac4b084e0db"),
        (123456, 11, "hard", {}, "98c06e29564cbb94c603055632602fd1ae0f25257cb3a23a153263673189160e"),
        (
            17,
            3,
            "easy",
            {"grid_h": 15, "grid_w": 17, "texture": "same_rows"},
            "c0ce136852611430dcc830fbfa0d013c3045f4407dd0fb28d6343ba4fab049a6",
        ),
        (
            17,
            5,
            "hard",
            {"grid_h": 18, "grid_w": 14, "texture": "two_rects_border"},
            "a71286005b0feb2ede3464ad6fb846eb8a975fb842c5979c926d3a9ba9b93a36",
        ),
    ],
)
def test_valid_calls_remain_byte_identical(
    gen, seed, sample_index, difficulty, overrides, expected
):
    assert (
        _grid_sha256(
            gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
        )
        == expected
    )
