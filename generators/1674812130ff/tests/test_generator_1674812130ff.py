"""Focused regression tests for generator 1674812130ff."""
from __future__ import annotations

import copy
import importlib
import random

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.1674812130ff.generator")
ROOT = find_root(__file__)


def _must_reject(grid, label):
    errors = gen.self_check(grid)
    assert errors, f"self_check accepted targeted impostor: {label}"


def _canonical_inputs():
    for pair in canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True):
        yield pair["input"]


def test_generator_contract():
    # All official inputs remain lawful under the stronger structural checker.
    official = list(_canonical_inputs())
    assert len(official) == 4
    assert all(not gen.self_check(grid) for grid in official)

    # Exact override boundaries, including combinations across difficulty bands.
    for band in ("easy", "medium", "hard"):
        for size, width, palette_size, layout in (
            (13, 3, 2, "terraced"),
            (21, 7, 7, "hourglass"),
            (19, 6, 4, "wedge"),
            (17, 5, 3, "mosaic"),
        ):
            grid = gen.generate(
                101,
                size * 100 + width,
                difficulty=band,
                grid_size=size,
                shape_width=width,
                fg_palette_size=palette_size,
                layout=layout,
            )
            assert not gen.self_check(grid)
            assert len(grid) == len(grid[0]) == size
            assert gen.observe_overrides(grid) == {
                "fg_palette_size": palette_size,
                "shape_width": width,
            }

    # Incompatible exact axes reject loudly rather than silently clamping.
    try:
        gen.generate(1, 1, grid_size=13, shape_width=7)
    except ValueError as exc:
        assert "supports shape_width" in str(exc)
    else:
        raise AssertionError("incompatible grid_size/shape_width was accepted")

    # Deterministic replay, fresh return objects, and process-global RNG purity.
    state = random.getstate()
    first = gen.generate(23, 7, difficulty="medium")
    second = gen.generate(23, 7, difficulty="medium")
    assert first == second and first is not second
    first[0][0] = 9 if first[0][0] != 9 else 6
    assert gen.generate(23, 7, difficulty="medium") == second
    assert random.getstate() == state

    base = gen.generate(
        17,
        5,
        difficulty="hard",
        grid_size=19,
        shape_width=7,
        fg_palette_size=7,
        layout="mosaic",
    )
    centre = len(base) // 2

    # Four targeted structural impostors must be rejected.
    broken_axis = copy.deepcopy(base)
    broken_axis[1][centre] = 7
    _must_reject(broken_axis, "broken central divider")

    missing_anchor = copy.deepcopy(base)
    missing_anchor[centre][-1] = 7
    _must_reject(missing_anchor, "missing right endpoint anchor")

    target_intrusion = copy.deepcopy(base)
    target_intrusion[1][centre + 2] = 2
    _must_reject(target_intrusion, "pre-painted target half")

    singleton = [[7] * 13 for _ in range(13)]
    singleton[6][6] = 8
    singleton[6][0] = singleton[6][-1] = 8
    for r in range(13):
        if r != 6:
            singleton[r][6] = 4
    singleton[5][5] = 1
    _must_reject(singleton, "single-cell source")

    # Every normal draw is an actual lesson and distinguishes the main rival.
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(80):
            grid = gen.generate(50_000 + band_index * 1_000 + offset, offset * 19 + 5, difficulty=band)
            facts, errors = gen._analyze(grid)
            assert not errors
            assert facts["changed_cells"] >= 12
            assert facts["horizontal_rival_delta"] >= 4
            assert gen.rule_mirror(grid) != grid
