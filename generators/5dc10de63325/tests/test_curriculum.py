"""Meaningful regressions for canonical shortcuts and missing glyph evidence."""
from __future__ import annotations

import importlib.util
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "5dc10de63325"
ROOT = find_root(__file__)
PATH = next(path for path in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("cyan_count_curriculum_generator", PATH)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)
GLYPHS = {
    q: [[int(v) for v in row] for row in rows]
    for q, rows in {
        1: ("00000", "08008", "00000", "00000", "08008"),
        2: ("00000", "88088", "00000", "00000", "88088"),
        3: ("08008", "88088", "00000", "08008", "88088"),
        4: ("88088", "88088", "00000", "88088", "88088"),
    }.items()
}


def count8(grid):
    return sum(v == 8 for row in grid for v in row)


def test_literal_glyphs_and_claimed_shortcuts_match_every_canonical_variant():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs
    for pair in pairs:
        assert GLYPHS[count8(pair["input"]) // 4] == pair["output"]
        assert GENERATOR.strict_canonical_like(pair["input"]) == []
        for name, rival in GENERATOR.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("seed", (0, 7, 997))
@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_cycle_window_retains_actual_rival_counterexamples_after_any_holdout(seed, difficulty):
    period = len(GENERATOR._schedule(seed)[0])
    width = GENERATOR.EXAMPLES_NEEDED + 1
    rivals = {**GENERATOR.SEMANTIC_RIVALS, **GENERATOR.CANONICAL_SHORTCUTS,
              **GENERATOR.LESSON_COMPETITORS}
    samples = []
    for index in range(period + width - 1):
        grid = GENERATOR.generate(seed, index, difficulty=difficulty)
        n = count8(grid)
        expected = GLYPHS[n // 4]
        samples.append((n, {name: rival(grid) != expected for name, rival in rivals.items()}))
    for start in range(period):
        window = samples[start:start + width]
        frequencies = Counter(n // 4 for n, _ in window)
        # A single occurrence can become the query and hide a tile-order branch.
        assert all(frequencies[q] >= 2 for q in (1, 2, 3)), (seed, start, frequencies)
        assert sum(n < 16 and n % 4 >= 2 for n, _ in window) >= 2
        for name in rivals:
            # Two actual disagreements are exactly what protects every one-pair holdout.
            assert sum(disagrees[name] for _, disagrees in window) >= 2, (seed, start, name)


def test_witnesses_refute_each_named_rival_on_every_supported_count():
    for n in range(4, 20):
        grid = [[8 if r * 6 + c < n else 0 for c in range(6)] for r in range(6)]
        expected = GLYPHS[n // 4]
        for name, predicate in GENERATOR.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                claimed = GENERATOR.WITNESS_RIVALS[name]
                claimed = [claimed] if isinstance(claimed, str) else claimed
                assert claimed
                # Stronger than the shared contract's existential multi-rival claim.
                assert all(GENERATOR.SEMANTIC_RIVALS[rival](grid) != expected for rival in claimed), (n, name)
