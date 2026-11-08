"""Focused semantic regressions for generator 4de2bae05c7d."""
from __future__ import annotations

import importlib
import itertools
import random

from reviewer_support import canonical_pairs, find_root

import pytest


ROOT = find_root(__file__)
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.4de2bae05c7d.generator"
)




def _blank(h=7, w=7):
    return [[0 for _ in range(w)] for _ in range(h)]


def test_rule_hash_and_all_canonical_pairs_are_accepted():
    assert GEN.RULE_HASH == "12b3f52c8e05"
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_five_profile_schedule_teaches_shape_color_and_orientation():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(101, index, difficulty=band) for index in range(5)]
        observations = [GEN.semantic_observables(grid) for grid in grids]
        assert sum(bool(row["canonical_anchor"]) for row in observations) == 1
        assert set().union(*(set(row["target_orientations"]) for row in observations)) == set(
            GEN._ORIENTATIONS
        )
        kinds = set().union(*(set(row["yellow_decoy_kinds"]) for row in observations))
        assert {"straight_triomino", "square", "long_l_tetromino", "domino"} <= kinds
        assert sum(row["n_colored_l_decoys"] for row in observations) == 4
        assert all(GEN.self_check(grid) == [] for grid in grids)


def test_all_declared_axis_boundaries_are_exactly_observable():
    axis_values = {
        "grid_h": (7, 18),
        "grid_w": (7, 18),
        "n_target_l": (1, 3),
        "n_yellow_decoys": (0, 1),
        "n_colored_l_decoys": (0, 1),
        "target_position": ("interior", "edge"),
    }
    for band in ("easy", "medium", "hard"):
        for values in itertools.product(*axis_values.values()):
            overrides = dict(zip(axis_values, values))
            grid = GEN.generate(7, 3, difficulty=band, **overrides)
            assert GEN.observe_overrides(grid) == overrides


def test_unknown_or_retired_texture_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, texture="warm")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, palette_kind="varied")


def test_self_check_rejects_structure_destroying_impostors():
    blank = _blank()

    singleton = _blank()
    singleton[1][1] = 4

    square = _blank()
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2)):
        square[row][col] = 4

    straight = _blank()
    for col in (1, 2, 3):
        straight[1][col] = 4

    colored_non_l = _blank()
    for row, col in ((1, 1), (1, 2), (2, 1)):
        colored_non_l[row][col] = 4
    for row, col in ((4, 3), (4, 4), (4, 5)):
        colored_non_l[row][col] = 2

    fused_multicolor = _blank()
    for row, col in ((1, 1), (1, 2), (2, 1)):
        fused_multicolor[row][col] = 4
    for row, col in ((1, 3), (2, 3), (2, 4)):
        fused_multicolor[row][col] = 2

    for impostor in (blank, singleton, square, straight, colored_non_l, fused_multicolor):
        assert GEN.self_check(impostor), impostor


def test_generated_lessons_are_identifiable_and_named_rivals_are_refuted():
    demos = []
    for index in range(5):
        grid = GEN.generate(31337, index, difficulty="medium")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(31337, 5, difficulty="medium")
    query = {"input": query_grid}
    assert GEN.lesson_identifiable(demos, query) == []

    for name, competitor in GEN.CANONICAL_SHORTCUTS.items():
        assert any(
            competitor(demo["input"]) != demo["output"] for demo in demos
        ), name

    repeated_square_profile = []
    for index in (2, 7, 12, 17, 22):
        grid = GEN.generate(31337, index, difficulty="medium")
        repeated_square_profile.append({"input": grid, "output": GEN.rule_mirror(grid)})
    reasons = GEN.lesson_identifiable(repeated_square_profile, query)
    assert any("straight triomino" in reason or "orientations" in reason for reason in reasons)


def test_negative_recombination_is_lawful_but_not_canonical_like():
    canonical = GEN.generate(19, 0, difficulty="easy")
    assert GEN.strict_canonical_like(canonical) == []

    # Recombine canonical scale/palette with the colored-L branch from a
    # contrast profile. The general checker accepts this lawful task instance,
    # while the strict canonical-profile predicate rejects the mixed profile.
    recombined = GEN.generate(
        19,
        0,
        difficulty="easy",
        grid_h=7,
        grid_w=7,
        n_target_l=2,
        n_yellow_decoys=0,
        n_colored_l_decoys=1,
        target_position="interior",
    )
    assert GEN.self_check(recombined) == []
    assert GEN.strict_canonical_like(recombined)


def test_determinism_fresh_returns_and_global_rng_purity():
    before = random.getstate()
    first = GEN.generate(99, 4, difficulty="hard")
    assert random.getstate() == before
    second = GEN.generate(99, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(99, 4, difficulty="hard") == second


def test_known_diagonal_contact_refutes_eight_neighbor_connectivity():
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 4, 4, 0],
        [0, 0, 0, 4, 4, 0, 4, 0],
        [0, 0, 0, 4, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    truth = GEN.rule_mirror(grid)
    rival = GEN._recolor_yellow_l_8connected(grid)
    assert rival == grid
    assert rival != truth


def test_every_five_demo_window_refutes_eight_neighbor_connectivity():
    rival = GEN.LESSON_COMPETITORS["use 8-neighbor yellow components"]
    for band in ("easy", "medium", "hard"):
        for seed in range(6):
            for start in range(6):
                demos = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    grid = GEN.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
                query_grid = GEN.generate(
                    seed, start + GEN.EXAMPLES_NEEDED, difficulty=band
                )
                assert any(rival(demo["input"]) != demo["output"] for demo in demos)
                assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []
