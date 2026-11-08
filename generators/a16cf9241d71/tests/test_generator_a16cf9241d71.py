from __future__ import annotations

import random
from copy import deepcopy

import pytest

from puzzle_generators.per_puzzle.a16cf9241d71 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


def _pair(grid):
    return {"input": grid, "output": gen._true_rule(grid)}


def test_rule_hash_is_pinned_to_selected_canonical_source():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "13927b48170d"


def test_all_canonical_inputs_are_owned_by_structural_and_strict_contracts():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []


def test_unknown_override_key_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override key"):
        gen.generate(0, 0, difficulty="easy", typo_axis="left")


def test_declared_override_axes_round_trip_at_boundaries_and_enum_values():
    cases = [
        {"grid_h": 5}, {"grid_h": 12}, {"grid_w": 7}, {"grid_w": 15},
        {"shape_idx": 0}, {"shape_idx": 4}, {"shape_color": 1}, {"shape_color": 9},
        {"axis_gap": 0}, {"axis_gap": 1},
        {"vertical_profile": "top"}, {"vertical_profile": "middle"}, {"vertical_profile": "bottom"},
        {
            "grid_h": 5, "grid_w": 7, "shape_idx": 4, "shape_color": 9,
            "axis_gap": 1, "vertical_profile": "bottom",
        },
        {
            "grid_h": 12, "grid_w": 15, "shape_idx": 0, "shape_color": 1,
            "axis_gap": 0, "vertical_profile": "top",
        },
    ]
    for i, overrides in enumerate(cases):
        grid = gen.generate(100 + i, 200 + i, difficulty=("easy", "medium", "hard")[i % 3], **overrides)
        observed = gen.observe_overrides(grid)
        for key, value in overrides.items():
            assert observed[key] == value
        assert gen.self_check(grid) == []


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(23, 5, difficulty="medium", shape_idx=0, axis_gap=0)
    facts = gen._analyze(base)
    axis = facts["axis"]
    source = list(facts["source_cells"])

    no_axis = deepcopy(base)
    for r in range(len(no_axis)):
        no_axis[r][axis] = 0

    no_shape = deepcopy(base)
    for r, c in source:
        no_shape[r][c] = 0

    right_side_prefilled = deepcopy(base)
    r, c = source[0]
    right_side_prefilled[r][2 * axis - c] = facts["source_color"]

    disconnected = deepcopy(base)
    r, c = source[-1]
    disconnected[r][c] = 0
    disconnected[0][-1] = facts["source_color"]

    extra_color = deepcopy(base)
    r, c = source[0]
    extra_color[r][c] = 9 if facts["source_color"] != 9 else 7

    off_axis_cyan = deepcopy(base)
    off_axis_cyan[0][0] = 8

    for impostor in (no_axis, no_shape, right_side_prefilled, disconnected, extra_color, off_axis_cyan):
        assert gen.self_check(impostor), impostor


def test_every_three_demo_schedule_window_is_identifiable_and_refutes_named_rivals():
    # Exhaust every cyclic residue.  The real semantic gate repeats this with
    # canonical Racket outputs; here we protect the schedule logic itself.
    for start in range(len(gen._SCHEDULE)):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(777, start + offset, difficulty="medium")
            demos.append(_pair(grid))
        query_grid = gen.generate(777, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        assert gen.lesson_identifiable(demos, _pair(query_grid)) == []

        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            witness = gen.SEMANTIC_WITNESSES[witness_name]
            rival_seen = False
            for pair in demos:
                if not witness(pair["input"]):
                    continue
                for rival_name in rival_names:
                    if gen.SEMANTIC_RIVALS[rival_name](pair["input"]) != pair["output"]:
                        rival_seen = True
                        break
                if rival_seen:
                    break
            assert rival_seen, (start, witness_name)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    state_before = random.getstate()
    a = gen.generate(991, 17, difficulty="hard")
    state_after = random.getstate()
    b = gen.generate(991, 17, difficulty="hard")
    assert a == b
    assert a is not b
    assert all(ra is not rb for ra, rb in zip(a, b))
    assert state_before == state_after


def test_schedule_and_observer_vary_all_declared_axes_on_ordinary_draws():
    seen = {name: set() for name in gen.AXES}
    for band in ("easy", "medium", "hard"):
        for i in range(48):
            grid = gen.generate(5000 + i, i, difficulty=band)
            observed = gen.observe_overrides(grid)
            for name in seen:
                seen[name].add(observed[name])
    assert all(len(values) >= 2 for values in seen.values()), seen
