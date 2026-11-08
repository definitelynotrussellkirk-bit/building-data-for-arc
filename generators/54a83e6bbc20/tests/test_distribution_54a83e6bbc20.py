"""Task-local regressions; run through workspace/run_review.py --action tests."""
from __future__ import annotations

import importlib
import itertools

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.54a83e6bbc20.generator")


def cuts_of(grid):
    return [tuple(sum(v == 8 for v in row[:5]) for row in grid[top:top + 3])
            for top in range(1, len(grid), 4)]


def make_grid(cuts, order=None):
    n = len(cuts)
    grid = [[7] * 11 for _ in range(4 * n + 1)]
    order = list(range(n)) if order is None else order
    for i, cut in enumerate(cuts):
        for r, length in enumerate(cut):
            grid[1 + 4 * i + r][:length] = [8] * length
    for slot, i in enumerate(order):
        for r, length in enumerate(cuts[i]):
            grid[1 + 4 * slot + r][6 + length:] = [i + 1] * (5 - length)
    return grid


def test_variable_area_geometry_is_emitted_not_only_area_six():
    areas = set()
    for i in range(64):
        areas.update(sum(cut) for cut in cuts_of(gen.generate(1000 + i, i)))
    assert len(areas) >= 6, areas


@pytest.mark.parametrize("omitted_row", range(3))
def test_every_row_can_be_the_only_disambiguating_row(omitted_row):
    witnesses = []
    for i in range(80):
        grid = gen.generate(1000 + i, i, difficulty="hard")
        cuts = cuts_of(grid)
        for a, b in itertools.combinations(cuts, 2):
            if a[omitted_row] != b[omitted_row] and all(
                a[r] == b[r] for r in range(3) if r != omitted_row
            ):
                witnesses.append(i)
    assert witnesses, f"row {omitted_row} is never necessary"


def test_every_permutation_has_an_explicit_observable_profile():
    orders = {tuple(order) for _, _, order in gen._PROFILE_ROWS}
    assert orders == {p for n in (2, 3, 4) for p in itertools.permutations(range(n))}


def test_shape_axis_round_trips_and_is_validated():
    assert "shape_profile" in gen.AXES
    for scene in gen.SCENE_PROFILES:
        for shape in gen.SHAPE_PROFILES:
            g = gen.generate(992, 3, scene_profile=scene, shape_profile=shape)
            assert gen.self_check(g, meta={"scene_profile": scene, "shape_profile": shape}) == []
            assert gen.observe_overrides(g) == {"scene_profile": scene, "shape_profile": shape}
            assert gen.generate(992, 3, scene_profile=scene, shape_profile=shape) == g
    with pytest.raises(ValueError, match="shape_profile"):
        gen.generate(1, 0, shape_profile="not-a-shape")


def test_validator_rejects_a_tied_rectangle_width_mode():
    # Exhaustive 64-choose-4 search found four cutsets with a 5/4 width tie.
    g = make_grid([(3, 2, 1), (4, 2, 1), (4, 3, 1), (4, 3, 2)])
    assert any("width" in e for e in gen.self_check(g))


def test_partial_row_rivals_are_registered_and_canonical_train_compatible():
    from scripts.canonical_profile_gate import canonical_pairs
    for r in range(3):
        name = f"ignore_row_{r}"
        assert name in gen.SEMANTIC_RIVALS
        assert name in gen.LESSON_COMPETITORS
        assert name in gen.CANONICAL_SHORTCUTS
        assert all(gen.SEMANTIC_RIVALS[name](p["input"]) == p["output"]
                   for p in canonical_pairs(gen.TASK_ID)[:3])


def test_placement_matches_bruteforce_for_all_4096_cut_pairs():
    # Independent old exhaustive implementation; validates any optimized path.
    target = {(r, c) for r in range(3) for c in range(5)}
    shapes = list(itertools.product(range(1, 5), repeat=3))
    for a in shapes:
        left = {(r, c) for r, n in enumerate(a) for c in range(n)}
        for b in shapes:
            candidate = {(r, c - min(b)) for r, n in enumerate(b) for c in range(n, 5)}
            expected = []
            for dr in range(-3, 4):
                for dc in range(-5, 6):
                    shifted = {(r + dr, c + dc) for r, c in candidate}
                    if left.isdisjoint(shifted) and left | shifted == target:
                        expected.append((dr, dc))
            want = expected[0] if len(expected) == 1 else None
            assert gen._placement(left, candidate) == want, (a, b)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_three_demo_window_excludes_query_changing_rivals(band):
    seeds = (0, 1, 1000, 88795172486289, 52014595280049)
    for seed in seeds:
        outcomes = []
        for i in range(76):
            g = gen.generate(seed, i, difficulty=band)
            out = gen.rule_mirror(g)
            outcomes.append({name: fn(g) == out for name, fn in gen.LESSON_COMPETITORS.items()})
        for start in range(73):
            for name in gen.LESSON_COMPETITORS:
                assert not all(outcomes[i][name] for i in range(start, start + 3)) or outcomes[start + 3][name], (
                    band, seed, start, name)


def test_literal_axis_domains_match_runtime_enums():
    assert set(gen.AXES["scene_profile"]["valid"].split("|")) == set(gen.SCENE_PROFILES)
    assert set(gen.AXES["shape_profile"]["valid"].split("|")) == set(gen.SHAPE_PROFILES)


def test_large_scene_axis_explicitly_uses_exhaustive_manual_probe():
    # Shared automatic enum probing is capped at 16 values. Do not pretend
    # that its matrix checks this exact 32-value domain; the test above checks
    # every scene x shape combination directly in the copied runtime.
    assert gen.AXES["scene_profile"].get("probe") == "manual"
    assert len(gen.SCENE_PROFILES) == 32
    assert "test_shape_axis_round_trips" in gen.AXES["scene_profile"].get("probe_evidence", "")
