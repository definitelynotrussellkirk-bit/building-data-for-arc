from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

TASK_ID = "9ea9f1e62275"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"test_generator_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record():
    path = ROOT / "shared/data/base/solutions/banks/3c7b85b8eeb1/H42__9ea9f1e62275.json"
    return json.loads(path.read_text())


def _grid(value):
    return [[int(cell) for cell in row] for row in value] if value and isinstance(value[0], str) else value


def _pairs(record):
    samples = json.loads(record["visible_context"]["samples_text"])
    pairs = [
        {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
        for pair in samples["train"]
    ]
    expected = record["verification"]["expected_test_outputs"]
    pairs.extend(
        {"input": _grid(pair["input"]), "output": _grid(output)}
        for pair, output in zip(samples["test"], expected)
    )
    return pairs


def test_rule_hash_and_all_canonical_inputs_are_accepted_by_self_check():
    gen = _load_generator()
    assert gen.RULE_HASH == "caf596654388"
    for pair in _pairs(_canonical_record()):
        assert gen.self_check(pair["input"]) == []


def test_python_mirror_matches_all_canonical_labels_without_mutation():
    gen = _load_generator()
    for pair in _pairs(_canonical_record()):
        before = [row[:] for row in pair["input"]]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_axes_round_trip_at_boundaries_and_unknown_keys_reject():
    gen = _load_generator()
    cases = (
        {"grid_h": 8, "grid_w": 10, "n_seeds": 2},
        {"grid_h": 30, "grid_w": 30, "n_seeds": 8},
        {"grid_h": 13, "grid_w": 21, "n_seeds": 5},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(800 + index, 17 + index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, made_up_axis=1)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError):
        gen.generate(0, 0, n_seeds=9)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    gen = _load_generator()
    state = random.getstate()
    first = gen.generate(123, 7, difficulty="medium")
    assert random.getstate() == state
    frozen = tuple(tuple(row) for row in first)
    first[0][0] = 9
    second = gen.generate(123, 7, difficulty="medium")
    assert tuple(tuple(row) for row in second) == frozen
    assert second is not first
    assert all(a is not b for a, b in zip(first, second))


def test_self_check_rejects_broken_or_ambiguous_frames_and_seed_errors():
    gen = _load_generator()
    good = gen.generate(919, 3, grid_h=14, grid_w=17, n_seeds=4)
    assert gen.self_check(good) == []

    broken = [row[:] for row in good]
    frame = gen.analyze_grid(broken)["frame_bbox"]
    r1, c1, _, _ = frame
    broken[r1][c1 + 1] = 0
    assert gen.self_check(broken)

    duplicate_color = [row[:] for row in good]
    seeds = gen.analyze_grid(duplicate_color)["seeds"]
    duplicate_color[seeds[1][0]][seeds[1][1]] = seeds[0][2]
    assert any("distinct" in message for message in gen.self_check(duplicate_color))

    extra_one = [row[:] for row in good]
    extra_one[0][0] = 1
    assert gen.self_check(extra_one)
