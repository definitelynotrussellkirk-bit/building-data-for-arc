"""Regressions for numeric palette order leaking the absent-header role.

Run with the packet wrapper or with shared/runtime on PYTHONPATH.  Generated
labels below are the documented Python mirror; canonical labels are loaded
independently through the portable public data helper.
"""
from __future__ import annotations

import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "40e85135fbf8"
ROOT = find_root(__file__)
SOURCE = next(
    path for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ) if path.is_file()
)
SPEC = importlib.util.spec_from_file_location("palette_roles_generator", SOURCE)
assert SPEC and SPEC.loader
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def ordinal_rank_prediction(grid):
    """Independent baseline shortcut: equality of separate ordinal ranks."""
    rows = [line[0] for line in grid[1:]]
    cols = grid[0][1:]
    row_rank = {color: rank for rank, color in enumerate(sorted(set(rows)))}
    col_rank = {color: rank for rank, color in enumerate(sorted(set(cols)))}
    return [[row if row_rank[row] == col_rank[col] else 0 for col in cols]
            for row in rows]


def header_roles(grid):
    """Observe roles from cells, independently of generator scheduling code."""
    row_colors = {line[0] for line in grid[1:]}
    col_colors = set(grid[0][1:])
    colors = sorted(row_colors | col_colors)
    private = row_colors ^ col_colors
    if not private:
        return "canonical", None, colors
    assert len(private) == 1
    color = next(iter(private))
    scene = "row_gap" if color in row_colors else "col_gap"
    return scene, colors.index(color), colors


def test_independent_rank_shortcut_fits_all_five_canonical_labels():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert ordinal_rank_prediction(pair["input"]) == pair["output"], (
            pair["variant"], pair["split"], pair["pair_index"]
        )


def test_declared_rank_rival_matches_independent_prediction():
    # These two noncanonical inputs distinguish rank alignment from equality.
    grids = [
        [[0, 2, 3, 2, 3, 2], [1, 0, 0, 0, 0, 0],
         [2, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0]],
        [[0, 1, 2, 3, 2, 1], [1, 0, 0, 0, 0, 0],
         [3, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0]],
    ]
    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        declarations = getattr(gen, namespace)
        assert "ordinal_header_rank" in declarations, namespace
        rival = declarations["ordinal_header_rank"]
        for grid in grids:
            assert rival(grid) == ordinal_rank_prediction(grid)
            assert rival(grid) != gen.rule_mirror(grid)
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            assert rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_advertised_lesson_has_nonmax_gaps_on_both_axes(band):
    failures = []
    for seed in (-7, 0, 1, 2, 19, 911):
        # Eighteen starts exercise every role-schedule residue twice, including
        # lessons spanning block boundaries.  This is an ordered lesson test.
        grids = [gen.generate(seed, index, difficulty=band)
                 for index in range(18 + gen.EXAMPLES_NEEDED - 1)]
        for start in range(18):
            lesson = grids[start:start + gen.EXAMPLES_NEEDED]
            roles = [header_roles(grid) for grid in lesson]
            nonmax_axes = {scene for scene, rank, colors in roles
                           if rank is not None and rank < len(colors) - 1}
            if nonmax_axes != {"row_gap", "col_gap"}:
                failures.append((seed, start, "missing nonmax gap", sorted(nonmax_axes)))
            if not any(ordinal_rank_prediction(grid) != gen.rule_mirror(grid)
                       for grid in lesson):
                failures.append((seed, start, "ordinal rival survived"))
            palettes = {tuple(colors) for _, _, colors in roles}
            if len(palettes) < 2:
                failures.append((seed, start, "constant palette"))
    assert not failures, f"{len(failures)} failures; first six: {failures[:6]}"


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_each_gap_axis_can_omit_every_palette_rank(band):
    for seed in (-7, 0, 19):
        ranks = {"row_gap": set(), "col_gap": set()}
        for index in range(18):
            grid = gen.generate(seed, index, difficulty=band)
            scene, rank, _ = header_roles(grid)
            if rank is not None:
                ranks[scene].add(rank)
        assert ranks == {"row_gap": {0, 1, 2}, "col_gap": {0, 1, 2}}, (seed, ranks)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_mixed_palette_is_observable_and_reaches_middle_colors(band):
    reached = set()
    for shape in gen.SHAPE_PROFILES:
        for scene in gen.SCENE_PROFILES:
            for index in range(9):
                requested = {"shape_profile": shape, "scene_profile": scene,
                             "palette_kind": "mixed"}
                grid = gen.generate(37, index, difficulty=band, **requested)
                assert gen.observe_overrides(grid) == requested
                assert gen.strict_canonical_like(grid) == []
                _, _, palette = header_roles(grid)
                assert len(palette) == 3
                assert tuple(palette) not in ((1, 2, 3), (7, 8, 9))
                reached.update(palette)
    assert {4, 5, 6} <= reached


def test_exact_low_and_high_palettes_keep_their_observable_meaning():
    for kind, palette in (("low", [1, 2, 3]), ("high", [7, 8, 9])):
        for scene in gen.SCENE_PROFILES:
            grid = gen.generate(37, 53, palette_kind=kind, scene_profile=scene)
            assert header_roles(grid)[2] == palette
            assert gen.observe_overrides(grid)["palette_kind"] == kind
