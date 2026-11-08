"""Regressions for a canonical-fitting palette-order shortcut.

Tests use observable color ranks, not the generator's schedule implementation.
"""
from collections import Counter
import importlib.util
from itertools import permutations
from pathlib import Path
import pytest
from reviewer_support import canonical_pairs, find_root

SOURCE = Path(__file__).resolve().parents[1] / 'generator.py'
SPEC = importlib.util.spec_from_file_location('cyclic_region_generator_under_test', SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def numeric_predecessor(grid):
    """Ignore spatial order and replace foreground-color holes by numeric predecessor."""
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    palette = sorted({v for row in grid for v in row} - {bg})
    out = [row[:] for row in grid]
    for c in range(len(grid[0])):
        foreground = {row[c] for row in grid} - {bg}
        if not foreground:
            continue
        color, = foreground
        replacement = palette[(palette.index(color) - 1) % len(palette)]
        for r, row in enumerate(grid):
            if row[c] == bg:
                out[r][c] = replacement
    return out


def rank_order(grid):
    _, _, _, colors = GEN._analyze(grid)
    ordered = sorted(colors)
    return tuple(ordered.index(color) for color in colors)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_every_three_consecutive_inputs_refute_both_numeric_directions(band):
    for seed in (11, 719, 900001):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(16)]
        for start in range(14):
            window = grids[start:start + 3]
            assert any(numeric_predecessor(g) != GEN.rule_mirror(g) for g in window), (seed, start)
            assert any(GEN._numeric_color_cycle(g) != GEN.rule_mirror(g) for g in window), (seed, start)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_ordinary_color_orders_cover_all_six_permutations(band):
    observed = {rank_order(GEN.generate(81331, i, difficulty=band)) for i in range(120)}
    assert observed == set(permutations(range(3)))


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    pairs = canonical_pairs(GEN.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 6
    assert all(numeric_predecessor(p['input']) == p['output'] for p in pairs)
    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in pairs), name


def test_malformed_lesson_returns_reasons_instead_of_raising():
    g = GEN.generate(918, 0)
    pair = {'input': g, 'output': GEN.rule_mirror(g)}
    assert GEN.lesson_identifiable([{}, pair, pair], pair)
    assert GEN.lesson_identifiable([pair, pair, pair], {'input': []})
