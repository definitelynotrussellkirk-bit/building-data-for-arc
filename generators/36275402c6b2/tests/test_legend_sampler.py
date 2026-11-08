"""Exact selection order, RNG compatibility, and bounded sampler memory."""
from __future__ import annotations

import importlib
from itertools import combinations
import random
import tracemalloc

import pytest


GEN = importlib.import_module("puzzle_generators.per_puzzle.36275402c6b2.generator")


def _lawful(slots, count):
    return [
        chosen
        for chosen in combinations(slots, count)
        if all(
            row_a != row_b or abs(col_a - col_b) >= 3
            for (row_a, col_a), (row_b, col_b) in combinations(chosen, 2)
        )
    ]


class _RankRng:
    """Supply each rank once, accepting the old and proposed RNG interfaces."""

    def __init__(self, rank, total):
        self.rank = rank
        self.total = total
        self.calls = 0

    def randrange(self, stop):
        assert stop == self.total
        self.calls += 1
        return self.rank

    def choice(self, values):
        return values[self.randrange(len(values))]


def test_all_legal_ranks_on_exhaustive_small_gapped_slot_sets(monkeypatch):
    # Include touching starts, exact three-column separation, gaps, and row jumps.
    universe = [(0, 0), (0, 1), (0, 3), (0, 7), (2, 0), (2, 2), (2, 3)]
    for size in range(len(universe) + 1):
        for subset in combinations(universe, size):
            slots = list(subset)
            monkeypatch.setattr(GEN, "_legend_slots", lambda *args: slots)
            for count in range(size + 2):
                lawful = _lawful(slots, count)
                if not lawful:
                    rng = _RankRng(0, 0)
                    with pytest.raises(ValueError, match="no lawful isolated legend placement"):
                        GEN._choose_legend_slots(0, 0, (), count, rng)
                    assert rng.calls == 0
                for rank, chosen in enumerate(lawful):
                    rng = _RankRng(rank, len(lawful))
                    actual = GEN._choose_legend_slots(0, 0, (), count, rng)
                    assert actual == list(chosen), (slots, count, rank)
                    assert rng.calls == 1


def test_all_required_side_ranks_on_exhaustive_small_gapped_slot_sets(monkeypatch):
    universe = [(0, 0), (0, 1), (0, 3), (0, 7), (2, 0), (2, 2), (2, 3)]
    bbox = (0, 10, 0, 12)  # Row 0 is a side row; row 2 is below the crop.
    for size in range(len(universe) + 1):
        for subset in combinations(universe, size):
            slots = list(subset)
            monkeypatch.setattr(GEN, "_legend_slots", lambda *args: slots)
            for count in range(size + 2):
                lawful = [
                    chosen for chosen in _lawful(slots, count)
                    if any(bbox[0] <= row <= bbox[2] for row, _ in chosen)
                ]
                if not lawful:
                    rng = _RankRng(0, 0)
                    with pytest.raises(ValueError, match="no lawful isolated legend placement"):
                        GEN._choose_legend_slots(0, 0, bbox, count, rng, require_side=True)
                    assert rng.calls == 0
                for rank, chosen in enumerate(lawful):
                    rng = _RankRng(rank, len(lawful))
                    actual = GEN._choose_legend_slots(0, 0, bbox, count, rng, require_side=True)
                    assert actual == list(chosen), (slots, count, rank)
                    assert rng.calls == 1


def test_required_side_seeded_selection_and_rng_state_match_filtered_enumeration(monkeypatch):
    slots = [(0, 0), (0, 3), (2, 0), (2, 1), (2, 3), (2, 8), (5, 0)]
    bbox = (2, 10, 3, 12)
    monkeypatch.setattr(GEN, "_legend_slots", lambda *args: slots)
    lawful = [
        chosen for chosen in _lawful(slots, 3)
        if any(bbox[0] <= row <= bbox[2] for row, _ in chosen)
    ]
    for seed in (0, 1, 7, 42, 987654321):
        old_rng, new_rng = random.Random(seed), random.Random(seed)
        expected = list(old_rng.choice(lawful))
        assert GEN._choose_legend_slots(0, 0, bbox, 3, new_rng, require_side=True) == expected
        assert new_rng.getstate() == old_rng.getstate()
        assert new_rng.random() == old_rng.random()


@pytest.mark.parametrize("height,width,bbox,count", [
    (11, 11, (2, 1, 8, 7), 3),
    (13, 12, (3, 2, 8, 7), 2),
    (15, 15, (2, 5, 5, 8), 3),
    (15, 15, (2, 5, 5, 8), 0),
])
def test_seeded_selection_and_rng_state_match_old_enumeration(height, width, bbox, count, monkeypatch):
    # Fix the original supported slot set even when placement coverage expands.
    r1, _, r2, _ = bbox
    old_slots = [
        (row, col)
        for row in range(height)
        if row <= r1 - 2 or row >= r2 + 2
        for col in range(width - 1)
    ]
    monkeypatch.setattr(GEN, "_legend_slots", lambda *args: old_slots)
    lawful = _lawful(old_slots, count)
    for seed in (0, 1, 7, 42, 987654321):
        old_rng, new_rng = random.Random(seed), random.Random(seed)
        expected = list(old_rng.choice(lawful))
        assert GEN._choose_legend_slots(height, width, bbox, count, new_rng) == expected
        assert new_rng.getstate() == old_rng.getstate()
        assert new_rng.random() == old_rng.random()


def test_negative_count_preserves_error_and_rng_state():
    rng = random.Random(4)
    state = rng.getstate()
    with pytest.raises(ValueError):
        GEN._choose_legend_slots(11, 11, (2, 1, 8, 7), -1, rng)
    assert rng.getstate() == state


def test_maximum_supported_layout_has_bounded_peak_memory():
    # 15x15 with the smallest crop maximizes candidate slots. The old lawful
    # list alone needs tens of MB; a suffix table and rank need well below 1 MB.
    tracemalloc.start()
    try:
        chosen = GEN._choose_legend_slots(15, 15, (2, 5, 5, 8), 3, random.Random(42))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert len(chosen) == 3
    assert peak < 1_000_000, f"sampler peak allocation was {peak:,} bytes"


def test_required_side_on_large_expanded_slot_set_has_bounded_memory(monkeypatch):
    height, width, bbox = 15, 15, (2, 5, 5, 8)
    r1, c1, r2, c2 = bbox
    slots = [
        (row, col)
        for row in range(height)
        for col in range(width - 1)
        if row <= r1 - 2 or row >= r2 + 2
        or (r1 <= row <= r2 and (col <= c1 - 3 or col >= c2 + 2))
    ]
    assert len(slots) == 154
    monkeypatch.setattr(GEN, "_legend_slots", lambda *args: slots)
    tracemalloc.start()
    try:
        chosen = GEN._choose_legend_slots(height, width, bbox, 3, random.Random(42), require_side=True)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert len(chosen) == 3
    assert any(r1 <= row <= r2 for row, _ in chosen)
    assert tuple(chosen) in _lawful(chosen, 3)
    assert peak < 1_000_000, f"required-side sampler peak allocation was {peak:,} bytes"


def test_oversized_count_fails_without_unbounded_table(monkeypatch):
    monkeypatch.setattr(GEN, "_legend_slots", lambda *args: [(0, 0), (0, 3)])
    rng = random.Random(4)
    state = rng.getstate()
    with pytest.raises(ValueError, match="no lawful isolated legend placement"):
        GEN._choose_legend_slots(0, 0, (), 1_000_000, rng)
    assert rng.getstate() == state
