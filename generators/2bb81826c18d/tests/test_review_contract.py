"""Behavioral regressions for the canonical generator's review contracts."""
from __future__ import annotations

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator("2bb81826c18d", root=ROOT)
PAIRS = canonical_pairs("2bb81826c18d", root=ROOT)


def profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def reference(grid):
    """Color bounding boxes: independent of the generator's component walker."""
    out = [row[:] for row in grid]
    for color in {v for row in grid for v in row} - {0}:
        cells = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color]
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        for r in range(top + 1, bottom):
            for c in range(left + 1, right):
                if (r - top + c - left) % 2 == 0:
                    out[r][c] = 0
    return out


@pytest.mark.parametrize("name", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1"])
def test_call_identity_rejects_coerced_scalars(name, value):
    args = {"seed": 991, "sample_index": 0}
    args[name] = value
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(**args)


def test_sample_index_rejects_negative_value():
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(991, -1)


def test_profile_support_in_each_difficulty():
    canonical = {profile(pair["input"]) for pair in PAIRS}
    lo = tuple(min(p[j] for p in canonical) for j in range(3))
    hi = tuple(max(p[j] for p in canonical) for j in range(3))
    exact_total = envelope_total = 0
    for band in ("easy", "medium", "hard"):
        grids = [GENERATOR.generate(2026, i, difficulty=band) for i in range(20)]
        exact = sum(profile(grid) in canonical for grid in grids)
        assert exact >= 1, (band, exact)
        exact_total += exact
        envelope_total += sum(
            all(lo[j] <= profile(grid)[j] <= hi[j] for j in range(3))
            for grid in grids
        )
    assert exact_total >= 3
    assert envelope_total >= 15


def test_keyed_default_draws_match_returned_geometry():
    from puzzle_generators.base import set_ctx_observer

    contexts = []
    set_ctx_observer(contexts.append)
    try:
        for band in ("easy", "medium", "hard"):
            for seed in (0, 1, 7):
                for index in range(4):
                    grid = GENERATOR.generate(seed, index, difficulty=band)
                    drawn = contexts[-1].recorded_draws()
                    for name, observed in GENERATOR.observe_overrides(grid).items():
                        assert drawn[name] == observed, (band, seed, index, name, drawn[name], observed)
    finally:
        set_ctx_observer(None)


def test_independent_reference_matches_all_canonical_labels():
    for pair in PAIRS:
        assert reference(pair["input"]) == pair["output"]


def test_declared_shortcuts_really_fit_all_canonical_pairs():
    shortcuts = getattr(GENERATOR, "CANONICAL_SHORTCUTS", {})
    assert "skip_thin_rectangles" in shortcuts
    for rival in shortcuts.values():
        for pair in PAIRS:
            assert rival(pair["input"]) == pair["output"]


def test_every_cyclic_lesson_and_query_rotation_refutes_declared_rivals():
    rivals = getattr(GENERATOR, "LESSON_COMPETITORS", {})
    assert len(rivals) >= 2, "Executable lesson rivals are required"
    for seed in (0, 2, 11, 73):
        for band in ("easy", "medium", "hard"):
            for start in range(8):
                pairs = []
                for i in range(start, start + 4):
                    grid = GENERATOR.generate(seed, i, difficulty=band)
                    pairs.append({"input": grid, "output": reference(grid)})
                for held_out in range(4):
                    demos = [p for i, p in enumerate(pairs) if i != held_out]
                    for name, rival in rivals.items():
                        assert any(rival(p["input"]) != p["output"] for p in demos), (
                            seed, band, start, held_out, name
                        )
                    assert GENERATOR.lesson_identifiable(demos, pairs[held_out]) == []
