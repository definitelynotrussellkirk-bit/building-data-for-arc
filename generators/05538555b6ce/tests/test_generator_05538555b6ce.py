from __future__ import annotations

import copy
import importlib
import random

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.05538555b6ce.generator"
)


def _pairs():
    return canonical_pairs(gen.TASK_ID)


def _pair(grid):
    return {"input": grid, "output": gen.oracle_output(grid)}


def test_rule_hash_and_all_canonical_pairs_match_python_mirror():
    pairs = _pairs()
    assert len(pairs) == 3
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_regression_canonical_right_edge_target_is_lawful_clipped_stamp():
    pair = _pairs()[1]
    info = gen._analysis(pair["input"])
    assert info["targets"] == [(2, 9)]
    assert info["target_records"][0]["clipped"] is True
    assert info["target_records"][0]["visible_non_anchor"] == 3
    assert gen.self_check(pair["input"]) == []
    assert gen.oracle_output(pair["input"]) == pair["output"]


def test_exact_axes_round_trip_in_every_band_and_unknown_controls_reject():
    for band in ("easy", "medium", "hard"):
        for h in (5, 6):
            for w in (9, 10, 12):
                grid = gen.generate(71 + h + w, h * 100 + w, difficulty=band, grid_h=h, grid_w=w)
                assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}
                assert gen.self_check(grid) == []
    try:
        gen.generate(1, 1, bogus_axis=3)
    except ValueError as exc:
        assert "unknown override axis" in str(exc)
    else:
        raise AssertionError("unknown override axis was silently accepted")
    try:
        gen.generate(1, 1, difficulty="expert")
    except ValueError as exc:
        assert "unknown difficulty" in str(exc)
    else:
        raise AssertionError("unknown difficulty was silently accepted")


def test_every_three_demo_window_is_identifiable_against_named_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            grids = [
                gen.generate(10_000 + start, start + offset, difficulty=band)
                for offset in range(4)
            ]
            demos = [_pair(grid) for grid in grids[:3]]
            query = _pair(grids[3])
            assert gen.lesson_identifiable(demos, query) == []

            witness_sets = [
                {name for name, fn in gen.SEMANTIC_WITNESSES.items() if fn(grid)}
                for grid in grids[:3]
            ]
            union = set().union(*witness_sets)
            assert "clipped_stamp_visible" in union
            assert "anchor_not_bbox_top_left" in union
            assert "multiple_targets" in union
            assert "multicolor_prototype" in union


def test_public_monochrome_shortcut_is_killed_by_generated_multicolor_witness():
    for pair in _pairs():
        assert gen._rival_monochrome_stamp(pair["input"]) == pair["output"]
    for sample_index in range(1, 20, 2):
        grid = gen.generate(99, sample_index, difficulty="medium")
        if gen._witness_multicolor(grid):
            assert gen._rival_monochrome_stamp(grid) != gen.oracle_output(grid)
            break
    else:
        raise AssertionError("no generated multicolor counterexample found")


def test_self_check_rejects_structural_impostors_and_foreign_recombination():
    base = gen.generate(123, 1, difficulty="medium", grid_h=6, grid_w=12)
    assert gen.self_check(base) == []
    info = gen._analysis(base)

    blank = [[0] * len(base[0]) for _ in base]
    assert gen.self_check(blank)

    missing_anchor = copy.deepcopy(base)
    ar, ac = info["anchor"]
    missing_anchor[ar][ac] = next(iter(info["proto_colors"]))
    assert gen.self_check(missing_anchor)

    two_anchors = copy.deepcopy(base)
    non_anchor = next(cell for cell in info["proto"] if cell != info["anchor"])
    two_anchors[non_anchor[0]][non_anchor[1]] = 8
    assert gen.self_check(two_anchors)

    foreign = copy.deepcopy(base)
    target = info["targets"][0]
    absent = next(color for color in range(1, 10) if color not in {v for row in base for v in row})
    foreign[target[0]][target[1]] = absent
    errors = gen.self_check(foreign)
    assert errors
    assert any("singleton 8 target" in error for error in errors)

    rogue = copy.deepcopy(base)
    placed = False
    for r, row in enumerate(rogue):
        for c, value in enumerate(row):
            if value != 0:
                continue
            trial = copy.deepcopy(rogue)
            trial[r][c] = absent
            if gen.self_check(trial):
                rogue = trial
                placed = True
                break
        if placed:
            break
    assert placed
    assert gen.self_check(rogue)


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(31415, 8, difficulty="hard", grid_h=6, grid_w=12)
    assert random.getstate() == state
    second = gen.generate(31415, 8, difficulty="hard", grid_h=6, grid_w=12)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(31415, 8, difficulty="hard", grid_h=6, grid_w=12)
