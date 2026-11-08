from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK = "0a9e3d364bb3"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def test_rule_hash_and_all_canonical_inputs_are_owned():
    assert gen.RULE_HASH == canonical_rule_hash(TASK)
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 6
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_unknown_override_rejected_and_boundaries_realized():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(7, 0, bogus_axis=1)
    for h, w, corner in [(9, 18, "tl"), (18, 9, "br"), (9, 9, "tr"), (18, 17, "bl")]:
        grid = gen.generate(31, 5, grid_h=h, grid_w=w, corner=corner, texture="plain")
        observed = gen.observe_overrides(grid)
        assert (observed["grid_h"], observed["grid_w"], observed["corner"], observed["texture"]) == (h, w, corner, "plain")
    with pytest.raises(ValueError, match="grid_h, grid_w, texture"):
        gen.generate(3, 3, grid_h=10, grid_w=12, texture="midline")


def test_each_semantic_texture_is_observable_and_non_identity():
    for sample_index, expected in enumerate(("plain", "marker_not_in_key", "second_color", "midline")):
        grid = gen.generate(101 + sample_index, sample_index, difficulty="medium")
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid)["texture"] == expected
        assert gen.rule_mirror(grid) != grid
        analysis = gen._analyze(grid)
        assert set(map(tuple, analysis["marker_quadrants"])) == {(0, 0), (0, 1), (1, 0), (1, 1)}
        if expected == "marker_not_in_key":
            assert analysis["marker"] not in analysis["key_colors"]
        if expected == "second_color":
            assert analysis["second_colors"]
        if expected == "midline":
            assert analysis["midline_positions"]


def test_negative_degenerate_fixtures_are_rejected():
    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(211, 9, texture=texture)
        assert gen.self_check(grid), texture


def test_self_check_rejects_four_targeted_impostors():
    base = gen.generate(313, 2, difficulty="medium")
    analysis = gen._analyze(base)
    kr, kc = analysis["key_row"], analysis["key_col"]
    br0, bc0, br1, bc1 = analysis["bbox"]
    impostors = []

    # 1. Break one key cell.
    bad = copy.deepcopy(base); bad[kr + 1][kc + 1] = 0; impostors.append(bad)
    # 2. Put separator colour inside the body.
    bad = copy.deepcopy(base); bad[br0][bc0] = 8; impostors.append(bad)
    # 3. Put a novel non-separator cell in the L separator.
    bad = copy.deepcopy(base)
    sep = next((r, c) for r, row in enumerate(bad) for c, v in enumerate(row) if v == 8 and (r, c) not in {(kr, kc), (kr, kc+1), (kr+1, kc), (kr+1, kc+1)})
    used = {v for row in bad for v in row}
    rogue = next(v for v in range(1, 10) if v not in used and v != 8)
    bad[sep[0]][sep[1]] = rogue; impostors.append(bad)
    # 4. Remove all body nonzero cells while retaining key/geometry.
    bad = copy.deepcopy(base)
    for r in range(br0, br1 + 1):
        for c in range(bc0, bc1 + 1):
            bad[r][c] = 0
    impostors.append(bad)

    assert len(impostors) == 4
    for grid in impostors:
        assert gen.self_check(grid)



def test_deterministic_fresh_return_and_global_python_rng_preserved():
    import random
    random.seed(123456789)
    before = random.getstate()
    a = gen.generate(777, 6, difficulty="hard")
    after = random.getstate()
    b = gen.generate(777, 6, difficulty="hard")
    assert before == after
    assert a == b
    assert a is not b
    assert all(ra is not rb for ra, rb in zip(a, b))
    a[0][0] = (a[0][0] + 1) % 10
    assert a != b

def test_declared_witnesses_really_kill_named_rivals():
    for sample_index, witness_name in [(0, "canonical_anchor"), (1, "marker_outside_key"), (2, "second_color_stays_unchanged"), (3, "exact_midline_uses_bottom_right")]:
        grid = gen.generate(401 + sample_index, sample_index, difficulty="medium")
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        truth = gen.rule_mirror(grid)
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_every_sliding_four_example_window_identifies_rule():
    # The schedule repeats every four; every possible residue start must work.
    for start in range(4):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            si = start + offset
            grid = gen.generate(900 + start, si, difficulty="hard")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[-1]
        assert gen.lesson_identifiable(demos, query) == []
