from __future__ import annotations

import copy
import hashlib
import importlib
import json
import math
import random
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b3b409a9afe5"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.b3b409a9afe5.generator"
)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _normalized_hash(code: str) -> str:
    return hashlib.sha256(" ".join(code.split()).encode()).hexdigest()[:12]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def test_metadata_rule_hash_and_honest_axes():
    row = _canonical_row()
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"])
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_comps", "texture"}
    assert GEN.HELPFUL_TEXTURES == ("mixed", "irregular")
    assert GEN.DEGENERATE_TEXTURES == ()


def test_all_canonical_inputs_are_accepted_and_python_mirror_is_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_racket_canonical_exactness_input_purity_and_a_b_a():
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in _canonical_pairs():
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        grid_a = GEN.generate(901, 11, difficulty="easy", texture="mixed")
        grid_b = GEN.generate(902, 12, difficulty="hard", texture="irregular")
        a1 = _apply_rule(bridge, fn_name, grid_a)
        b = _apply_rule(bridge, fn_name, grid_b)
        a2 = _apply_rule(bridge, fn_name, grid_a)
        assert a1 == GEN.rule_mirror(grid_a)
        assert b == GEN.rule_mirror(grid_b)
        assert a2 == a1
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("texture", ["mixed", "irregular"])
def test_full_small_boundary_combination_is_exact(difficulty, texture):
    grid = GEN.generate(
        1701,
        29,
        difficulty=difficulty,
        grid_h=8,
        grid_w=10,
        n_comps=7,
        texture=texture,
    )
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 8,
        "grid_w": 10,
        "n_comps": 7,
        "texture": texture,
    }
    assert GEN.rule_mirror(grid) == [[6, 1, 0, 0]]


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8},
        {"grid_h": 18},
        {"grid_w": 10},
        {"grid_w": 30},
        {"n_comps": 2},
        {"n_comps": 7},
        {"texture": "mixed"},
        {"texture": "irregular"},
    ],
)
def test_each_axis_boundary_is_observable(overrides):
    grid = GEN.generate(313, 419, difficulty="hard", **overrides)
    observed = GEN.observe_overrides(grid)
    assert all(observed[key] == value for key, value in overrides.items())
    assert GEN.self_check(grid) == []


def test_default_keyed_values_equal_returned_observations_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(seed, seed * 17 + 3, difficulty=difficulty)
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            ctx = captured[0]
            observed = GEN.observe_overrides(grid)
            for axis in GEN.AXES:
                assert ctx.axis_value(axis) == observed[axis]


def test_canonical_profile_schedule_and_shortcut_rebuttals():
    profile = GEN.generate(77, 10, difficulty="medium")
    facts = GEN.semantic_observables(profile)
    assert (facts["grid_h"], facts["grid_w"], facts["n_comps"]) == (13, 30, 4)
    assert facts["depth_counts"] == [1, 1, 1, 1]
    assert facts["irregular_components"] >= 2

    seen_repeated_color = False
    seen_depth_three = False
    seen_depth_four = False
    seen_bbox_shortcut_failure = False
    inputs = set()
    outputs = set()
    for seed in range(80):
        grid = GEN.generate(seed, seed + 1, difficulty="hard")
        facts = GEN.semantic_observables(grid)
        seen_repeated_color |= facts["repeated_color"]
        seen_depth_three |= 3 in facts["depths"]
        seen_depth_four |= 4 in facts["depths"]
        for comp in GEN._components(grid):
            r0, c0, r1, c1 = GEN._bbox(comp["cells"])
            bbox_guess = math.ceil(min(r1 - r0 + 1, c1 - c0 + 1) / 2)
            seen_bbox_shortcut_failure |= bbox_guess != GEN._onion_depth(comp["cells"])
        assert facts["irregular_components"] >= 1
        inputs.add(_grid_key(grid))
        outputs.add(_grid_key(GEN.rule_mirror(grid)))
    assert seen_repeated_color
    assert seen_depth_three
    assert seen_depth_four
    assert seen_bbox_shortcut_failure
    assert len(inputs) >= 75
    assert len(outputs) >= 12


def test_replay_is_deterministic_fresh_and_global_rng_safe():
    random.seed(8821)
    state = random.getstate()
    kwargs = dict(
        difficulty="hard",
        grid_h=8,
        grid_w=10,
        n_comps=7,
        texture="mixed",
    )
    first = GEN.generate(991, 4, **kwargs)
    assert random.getstate() == state
    second = GEN.generate(991, 4, **kwargs)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second == GEN.generate(991, 4, **kwargs)


def test_invalid_controls_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 1, palette_kind="warm")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        GEN.generate(1, 1, grid_w=31)
    with pytest.raises(ValueError):
        GEN.generate(1, 1, texture="solid")


def test_self_check_rejects_targeted_structural_impostors():
    impostors = {
        "all_background": [[0] * 10 for _ in range(8)],
        "single_component": [
            [0] * 10,
            [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 2, 2, 0, 0, 0, 0, 0, 0, 0],
            *([[0] * 10] * 5),
        ],
        "solid_only": [
            [0, 2, 0, 0, 0, 0, 3, 3, 3, 0],
            [0, 0, 0, 0, 0, 0, 3, 3, 3, 0],
            [0, 0, 0, 0, 0, 0, 3, 3, 3, 0],
            *([[0] * 10] * 5),
        ],
        "one_depth_class": [
            [0, 2, 0, 0, 0, 0, 3, 0, 0, 0],
            [0, 2, 2, 0, 0, 0, 3, 3, 0, 0],
            *([[0] * 10] * 6),
        ],
        "ignored_color_9": [
            [0, 2, 0, 0, 0, 0, 3, 3, 3, 0],
            [0, 2, 2, 0, 9, 0, 3, 3, 3, 0],
            [0, 0, 0, 0, 0, 0, 3, 3, 3, 0],
            *([[0] * 10] * 5),
        ],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_is_rejected_but_oracle_mirror_executes():
    grid = GEN.generate(
        55,
        17,
        difficulty="medium",
        grid_h=10,
        grid_w=14,
        n_comps=4,
        texture="mixed",
    )
    existing = {value for row in grid for value in row}
    replacement = next(color for color in range(1, 9) if color not in existing)
    impostor = [
        [replacement if value == 0 else value for value in row]
        for row in grid
    ]
    assert replacement not in {
        value for row in grid for value in row if value != 0
    }
    assert GEN.self_check(impostor)
    before = copy.deepcopy(impostor)
    output = GEN.rule_mirror(impostor)
    assert output and len(output[0]) == 4
    assert impostor == before
