from __future__ import annotations

import copy
import importlib

import pytest
from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.f84f23e456ac.generator"
)


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_canonical_pairs_match_authority():
    assert gen.RULE_HASH == "54458840a785"
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "values",
    [
        (6, 6, 2, 2, 1, "sparse"),
        (20, 24, 5, 5, 2, "dense"),
        (8, 10, 3, 4, 2, "sparse"),
        (9, 12, 4, 3, 1, "dense"),
    ],
)
def test_exact_override_surface_is_observable_in_every_band(band, values):
    h, w, mh, mw, colors, density = values
    grid = gen.generate(
        8128,
        11,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        motif_h=mh,
        motif_w=mw,
        n_distinct_colors=colors,
        density=density,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": h,
        "grid_w": w,
        "motif_h": mh,
        "motif_w": mw,
        "n_distinct_colors": colors,
        "density": density,
    }



def test_default_schedule_spans_declared_canvas_bounds_while_staying_anchored():
    canonical_profiles = {
        (8, 9, 2),
        (9, 9, 1),
        (8, 10, 2),
        (10, 12, 2),
        (9, 12, 1),
    }
    observed = [
        gen.observe_overrides(gen.generate(314, index, difficulty="medium"))
        for index in range(15)
    ]
    assert {item["grid_h"] for item in observed} >= {6, 20}
    assert {item["grid_w"] for item in observed} >= {6, 24}
    assert sum(
        (item["grid_h"], item["grid_w"], item["n_distinct_colors"])
        in canonical_profiles
        for item in observed
    ) >= 10

def test_unknown_override_and_unknown_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, imaginary_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="impossible")


def test_default_generation_is_deterministic_fresh_and_nonidentity():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(9):
            first = gen.generate(901, sample_index, difficulty=band)
            second = gen.generate(901, sample_index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert gen.self_check(first) == []
            assert gen.rule_mirror(first) != first
            first[0][0] = (first[0][0] + 1) % 10
            assert gen.generate(901, sample_index, difficulty=band) == second


def test_every_three_demo_window_refutes_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            demos = [
                _pair(gen.generate(1207, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query_grid = gen.generate(
                1207, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = _pair(query_grid)
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), f"{name} survived {band=} {start=}"


def test_fixed_width_three_shortcut_matches_canonical_but_not_curriculum():
    shortcut = gen.CANONICAL_SHORTCUTS["fixed_motif_width_3"]
    for pair in _canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(55, index, difficulty=band) for index in range(3)]
        assert any(gen.observe_overrides(grid)["motif_w"] != 3 for grid in grids)
        assert any(shortcut(grid) != gen.rule_mirror(grid) for grid in grids)


def test_self_check_rejects_structural_impostors():
    good = gen.generate(
        77,
        2,
        difficulty="medium",
        grid_h=8,
        grid_w=10,
        motif_h=3,
        motif_w=4,
        n_distinct_colors=2,
        density="sparse",
    )
    assert gen.self_check(good) == []

    shifted = [[0 for _ in row] for row in good]
    for r in range(3):
        for c in range(4):
            if r + 1 < len(shifted) and c + 1 < len(shifted[0]):
                shifted[r + 1][c + 1] = good[r][c]
    assert gen.self_check(shifted)

    outside_bbox = copy.deepcopy(good)
    outside_bbox[-1][-1] = 9
    assert gen.self_check(outside_bbox)

    no_zero = copy.deepcopy(good)
    info = gen.observe_overrides(good)
    for r in range(info["motif_h"]):
        for c in range(info["motif_w"]):
            if no_zero[r][c] == 0:
                no_zero[r][c] = 1
    assert gen.self_check(no_zero)

    periodic = [[0] * 8 for _ in range(8)]
    motif = [[1, 2, 1, 2], [2, 1, 2, 1]]
    for r, row in enumerate(motif):
        periodic[r][:4] = row
    assert gen.self_check(periodic)

    invalid_color = copy.deepcopy(good)
    invalid_color[0][0] = 10
    assert gen.self_check(invalid_color)


def test_production_shaped_cohort_has_high_pair_diversity():
    """Catch finite motif support hidden by the shared >50% smoke floor."""
    for band in ("easy", "medium", "hard"):
        grids = []
        for episode in range(50):
            seed = 1 + episode * 101
            for sample_index in range(6):
                grid = gen.generate(seed, sample_index, difficulty=band)
                grids.append(tuple(tuple(row) for row in grid))
        assert len(set(grids)) >= 285, (
            f"{band} produced only {len(set(grids))}/300 distinct inputs"
        )
