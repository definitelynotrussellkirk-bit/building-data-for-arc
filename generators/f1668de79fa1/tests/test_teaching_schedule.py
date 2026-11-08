"""Semantic regressions for the complete default demonstration curriculum."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "f1668de79fa1"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("mirror_teaching_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_declared_canonical_shortcuts_fit_every_reference_pair():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 17, 731, 1000))
def test_wide_lessons_include_interior_cells_and_keep_the_exact_anchor(seed, band):
    for index in range(9):
        if gen.schedule_profile(seed, index, band) != "wide":
            continue
        grid = gen.generate(seed, index, difficulty=band)
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
        interiors = {p for p in cells if all(q in cells for q in
                     ((p[0]-1, p[1]), (p[0]+1, p[1]), (p[0], p[1]-1), (p[0], p[1]+1)))}
        assert interiors, "boundary-only mirroring must be contradicted by a full demonstration"
        assert gen.observe_overrides(grid)["marker_mode"] == "full"
        marker = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
        assert marker != (min(r for r, _ in cells), min(c for _, c in cells))


def test_lesson_hook_reports_actual_ambiguity_and_accepts_a_refuted_rival():
    pair = canonical_pairs(TASK, root=ROOT)[0]
    # Hand-derived edge-swap witness: top bar of four and an off-center stem.
    grid = [[0] * 10 for _ in range(7)]
    for r, c in ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)):
        grid[r][c] = 2
    grid[4][4] = 1
    output = [[0] * 10 for _ in range(7)]
    for r, c in ((4, 4), (4, 5), (4, 6), (4, 7), (5, 6)):
        output[r][c] = 8
    query = {"input": grid, "output": output}
    reasons = gen.lesson_identifiable([pair], query)
    assert any("swap_edge_columns" in reason for reason in reasons)
    assert gen.lesson_identifiable([pair, query], query) == []


def test_five_cell_conditional_rotation_differs_from_the_hand_derived_mirror():
    grid = [[0] * 10 for _ in range(7)]
    for r, c in ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)):
        grid[r][c] = 2
    grid[4][4] = 1
    expected_rotation = [[0] * 10 for _ in range(7)]
    for r, c in ((5, 4), (5, 5), (5, 6), (5, 7), (4, 6)):
        expected_rotation[r][c] = 8
    assert "rotate_five_else_flip_lr" in gen.SEMANTIC_RIVALS
    assert gen.SEMANTIC_RIVALS["rotate_five_else_flip_lr"](grid) == expected_rotation
    assert gen.SEMANTIC_WITNESSES["five_cell_non_ud_symmetric"](grid)
    expected_mirror = [[0] * 10 for _ in range(7)]
    for r, c in ((4, 4), (4, 5), (4, 6), (4, 7), (5, 6)):
        expected_mirror[r][c] = 8
    assert gen.SEMANTIC_RIVALS["rotate_five_else_flip_lr"](grid) != expected_mirror
    query = {"input": grid, "output": expected_mirror}
    reasons = gen.lesson_identifiable([canonical_pairs(TASK, root=ROOT)[0]], query)
    assert any("rotate_five_else_flip_lr" in reason for reason in reasons)
    grid[4][4] = 0
    grid[6][9] = 1
    assert not gen.SEMANTIC_WITNESSES["five_cell_non_ud_symmetric"](grid)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 17, 731))
def test_every_default_rotation_retains_a_five_cell_discriminator(seed, band):
    for start in range(3):
        witnesses = []
        for index in range(start, start + 6):
            grid = gen.generate(seed, index, difficulty=band)
            cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                     if value == 2}
            top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
            reflected_ud = {(top + bottom - r, c) for r, c in cells}
            is_witness = (len(cells) == 5 and reflected_ud != cells
                          and gen.observe_overrides(grid)["marker_mode"] == "full")
            if gen.schedule_profile(seed, index, band) == "core":
                assert is_witness
            witnesses.append(is_witness)
        for held_out in range(6):
            assert any(witness for position, witness in enumerate(witnesses)
                       if position != held_out)


def test_core_discriminator_uses_the_bounded_fallback_for_symmetric_growth():
    class FirstChoice:
        def choice(self, choices):
            return choices[0]

    shape = gen._grow_shape(FirstChoice(), 5, 6, 8,
                            wide=False, interior=False, non_ud=True)
    assert shape == ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0))


@pytest.mark.parametrize("count", (4, 5, 9))
@pytest.mark.parametrize("mode", ("full", "clipped"))
def test_core_profile_preserves_explicit_template_and_clipping_controls(count, mode):
    grid = gen.generate(0, 0, grid_h=6, grid_w=8,
                        template_cells=count, marker_mode=mode)
    assert gen.observe_overrides(grid) == {
        "grid_h": 6, "grid_w": 8, "template_cells": count, "marker_mode": mode}
