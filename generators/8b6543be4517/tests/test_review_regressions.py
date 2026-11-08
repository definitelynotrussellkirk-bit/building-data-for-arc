"""Regression frontier from review-ad7b511c587e061a; no Racket needed here."""
from __future__ import annotations

import copy
import importlib

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.8b6543be4517.generator")


def features(grid):
    """Compute features from pixels, without relying on generator witnesses."""
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(v == 8 for v in grid[r])]
    cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    assert len(rows) + len(cols) == 1
    axis, mid = ("row", rows[0]) if rows else ("col", cols[0])
    sevens = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    targets, oob, paired, collisions = set(), set(), set(), set()
    for r, c in sevens:
        q = (2 * mid - r, c) if rows else (r, 2 * mid - c)
        if not (0 <= q[0] < h and 0 <= q[1] < w):
            oob.add((r, c))
        elif q in sevens:
            paired.add((r, c))
        else:
            targets.add(q)
            if grid[q[0]][q[1]] not in (0, 7, 8):
                collisions.add(q)
    return {"axis": axis, "centered": 2 * mid == (h if rows else w) - 1,
            "sevens": sevens, "targets": targets, "paired": paired,
            "oob": oob, "collisions": collisions}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_count_distribution_is_not_the_old_six_to_nine_template(band):
    fs = [features(gen.generate(91000 + 1009 * i, i, difficulty=band)) for i in range(144)]
    assert len({len(f["sevens"]) for f in fs}) >= 5
    assert 2 in {len(f["targets"]) for f in fs}
    assert max(len(f["targets"]) for f in fs) >= 5
    assert {bool(f["paired"]) for f in fs} == {False, True}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_centered_and_clipped_support_in_both_orientations(band):
    fs = [features(gen.generate(92000 + 1009 * i, i, difficulty=band)) for i in range(72)]
    assert {f["axis"] for f in fs if f["centered"]} == {"row", "col"}
    assert {bool(f["oob"]) for f in fs} == {False, True}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_occupied_and_clean_target_cases_are_both_generated(band):
    fs = [features(gen.generate(93000 + 1009 * i, i, difficulty=band)) for i in range(72)]
    assert {bool(f["collisions"]) for f in fs} == {False, True}


def test_zero_only_rival_fits_canonical_examples_but_not_collision_witness():
    from scripts.canonical_profile_gate import canonical_pairs
    assert "paint_background_only" in gen.SEMANTIC_RIVALS
    rival = gen.SEMANTIC_RIVALS["paint_background_only"]
    for pair in canonical_pairs(gen.TASK_ID):
        assert rival(pair["input"]) == pair["output"]
    grid = [[0] * 11 for _ in range(8)]
    for row in grid:
        row[4] = 8
    grid[1][2], grid[1][6], grid[5][7], grid[6][1] = 7, 5, 7, 5
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid)[1][6] == 7
    assert rival(grid)[1][6] == 5


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_demo_window_covers_decisive_new_branches(band):
    assert gen.EXAMPLES_NEEDED == 4
    for seed in (0, 17, 987654321):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(28)]
        for start in range(24):
            fs = [features(g) for g in grids[start:start + 4]]
            assert {f["axis"] for f in fs} == {"row", "col"}
            assert any(f["centered"] for f in fs)
            assert any(f["oob"] for f in fs)
            assert {bool(f["collisions"]) for f in fs} == {False, True}
            assert any(len(f["targets"]) > 3 for f in fs)
            assert any(len(f["targets"]) == 2 for f in fs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_generated_collision_obeys_target_priority_and_preservation(band):
    for i in range(72):
        grid = gen.generate(94000 + i, i, difficulty=band)
        before = copy.deepcopy(grid)
        f = features(grid)
        out = gen.rule_mirror(grid)
        for r, row in enumerate(grid):
            for c, v in enumerate(row):
                assert out[r][c] == (7 if (r, c) in f["targets"] else v)
        assert grid == before
        assert any(v not in (0, 7, 8) and out[r][c] == v
                   for r, row in enumerate(grid) for c, v in enumerate(row))


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], "bad", [[True]], {}])
def test_malformed_lesson_input_returns_reasons_not_exceptions(bad):
    grid = gen.generate(0, 0)
    good = {"input": grid, "output": gen.rule_mirror(grid)}
    assert gen.lesson_identifiable([copy.deepcopy(good)] * 4,
                                  {"input": bad, "output": []})


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], "bad", [[True]], {}])
def test_witness_hooks_do_not_claim_or_throw_on_invalid_grid(bad):
    for name, predicate in gen.SEMANTIC_WITNESSES.items():
        assert predicate(bad) is False, name


@pytest.mark.parametrize("pair_index", [0, 4])
def test_bad_output_grid_cannot_pass_via_python_boolean_integer_equality(pair_index):
    # A clean, identifiable lesson must pass first. Repeating one demo could
    # otherwise hide a validation defect behind an unrelated rival rejection.
    pairs = []
    for i in range(5):
        grid = gen.generate(20261002, i, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
    pairs[pair_index]["output"] = [
        [False if v == 0 else v for v in row]
        for row in pairs[pair_index]["output"]
    ]
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == [
        f"pair {pair_index} has a malformed output grid"
    ]


def test_every_profile_is_in_the_shared_override_matrix_not_silently_unprobed():
    from scripts.check_generator_override_contract import _axis_values
    assert set(_axis_values(gen.AXES["scene_profile"])) == set(gen.SCENE_PROFILES)
