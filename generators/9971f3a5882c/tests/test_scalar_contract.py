"""Replay arguments must not silently coerce into a different sample identity."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


gen, _, _ = load_selected_generator("9971f3a5882c", root=find_root(__file__))


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_noninteger_seed(bad_seed, difficulty):
    with pytest.raises(ValueError, match="seed must be a Python int"):
        gen.generate(bad_seed, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", None, -1])
def test_generate_rejects_invalid_sample_index(bad_index, difficulty):
    with pytest.raises(ValueError, match="sample_index must be a nonnegative Python int"):
        gen.generate(991, bad_index, difficulty=difficulty)


@pytest.mark.parametrize("seed,sample_index", [(-17, 0), (0, 0), (991, 17), (2**65, 2**65)])
def test_signed_and_large_integer_replay_arguments_remain_valid(seed, sample_index):
    first = gen.generate(seed, sample_index)
    assert gen.self_check(first) == []
    assert first == gen.generate(seed, sample_index)


def test_valid_calls_reproduce_retained_baseline_grids():
    """Guard the valid API distribution, independent of the new rejection code."""
    import hashlib

    fixture = Path(__file__).resolve().parent / "fixtures" / "valid_call_baseline.json"
    records = json.loads(fixture.read_text())
    assert records["source_sha256"] == "5235171e7b63356bd8b76162c2fd4aa63c61a73c83e4cb59bc6a8b63768a1c00"
    for row in records["cases"]:
        grid = gen.generate(row["seed"], row["sample_index"], difficulty=row["difficulty"])
        digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
        assert digest == row["input_sha256"], row
