from __future__ import annotations

import copy
import importlib
import random

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "cbe60e2c4b18"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.cbe60e2c4b18.generator"
)
def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _split(grid):
    divider = next(
        col
        for col in range(len(grid[0]))
        if all(row[col] == 9 for row in grid)
    )
    left = [row[:divider] for row in grid]
    right = [row[divider + 1 :] for row in grid]
    return left, right


def _join(left, right):
    return [a + [9] + b for a, b in zip(left, right)]


def _supports(panel):
    return {
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value != 0
    }


def test_canonical_inputs_are_accepted_and_mirrored_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_unknown_and_exact_overrides_are_loud_and_observable():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, difficulty="easy", typo_axis=1)

    requested = {
        "grid_h": 9,
        "panel_w": 5,
        "palette_kind": "same_gray",
        "shared_count": 8,
        "left_only_count": 6,
        "right_only_count": 6,
        "overlap_layout": "disconnected",
    }
    grid = GEN.generate(17, 23, difficulty="easy", **requested)
    assert GEN.observe_overrides(grid) == requested
    assert GEN.self_check(grid, meta={"overrides": requested}) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(90210)
    before = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_semantic_schedule_identifies_every_residue_window():
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(700 + start, sample_index, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(
                700 + start, start + GEN.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            analyses = [GEN._analysis(demo["input"]) for demo in demos]
            assert any(a["left_color"] == a["right_color"] for a in analyses)
            assert any(a["left_color"] != a["right_color"] for a in analyses)
            assert {a["overlap_layout"] for a in analyses} == {
                "connected",
                "disconnected",
            }


def test_every_lawful_draw_refutes_copy_union_and_xor_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grid = GEN.generate(seed, seed * 7 + 3, difficulty=band)
            official = GEN.rule_mirror(grid)
            for name in ("copy_left_panel", "copy_right_panel", "union", "xor"):
                assert GEN.SEMANTIC_RIVALS[name](grid) != official


def test_self_check_rejects_targeted_rule_hiding_mutations():
    grid = GEN.generate(41, 9, difficulty="medium")
    left, right = _split(grid)
    height, width = len(left), len(left[0])
    left_support = _supports(left)
    right_support = _supports(right)
    shared = sorted(left_support & right_support)
    unused = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in left_support and (row, col) not in right_support
    ]

    no_shared_right = [[0 for _ in range(width)] for _ in range(height)]
    right_color = next(value for row in right for value in row if value)
    replacement = unused[: len(right_support)]
    assert len(replacement) == len(right_support)
    for row, col in replacement:
        no_shared_right[row][col] = right_color
    no_shared = _join(left, no_shared_right)
    assert any("shared" in error for error in GEN.self_check(no_shared))
    with pytest.raises(ValueError):
        GEN.rule_mirror(no_shared)

    identical = _join(left, [row[:] for row in left])
    identical_errors = GEN.self_check(identical)
    assert any("private" in error for error in identical_errors)
    with pytest.raises(ValueError):
        GEN.rule_mirror(identical)

    empty_right = _join(left, [[0] * width for _ in range(height)])
    assert GEN.self_check(empty_right)
    with pytest.raises(ValueError):
        GEN.rule_mirror(empty_right)

    multicolor_left = [row[:] for row in left]
    row, col = next(iter(left_support))
    original_color = multicolor_left[row][col]
    multicolor_left[row][col] = 1 if original_color != 1 else 2
    multicolor = _join(multicolor_left, right)
    assert any("exactly one" in error for error in GEN.self_check(multicolor))

    extra_divider = [row[:] for row in grid]
    candidate_col = 0
    for row in range(height):
        extra_divider[row][candidate_col] = 9
    assert any("exactly one" in error for error in GEN.self_check(extra_divider))

    # The no-shared replacement coordinates are absent from every remaining
    # left/right scene part, so this is a true negative recombination rather
    # than a recoloring of a feature already present elsewhere.
    assert set(replacement).isdisjoint(left_support | right_support)
    assert shared


def _normalized_support_pair(grid):
    left, right = _split(grid)
    left_support = _supports(left)
    right_support = _supports(right)
    all_cells = left_support | right_support
    row0 = min(row for row, _ in all_cells)
    col0 = min(col for _, col in all_cells)

    def normalize(cells):
        return frozenset((row - row0, col - col0) for row, col in cells)

    return normalize(left_support), normalize(right_support)


def test_ordinary_sampling_uses_every_lawful_panel_color():
    observed = set()
    bands = ("easy", "medium", "hard")
    for sample_index in range(256):
        grid = GEN.generate(
            10_000 + sample_index // 7,
            sample_index,
            difficulty=bands[sample_index % len(bands)],
        )
        left, right = _split(grid)
        observed.update(value for panel in (left, right) for row in panel for value in row if value)

    assert observed == set(range(1, 9))


def test_minimal_disconnected_bridge_covers_reflections_and_panel_handedness():
    signatures = {
        _normalized_support_pair(
            GEN.generate(
                20_000 + sample_index // 5,
                sample_index,
                difficulty="medium",
                overlap_layout="disconnected",
                shared_count=2,
                left_only_count=1,
                right_only_count=1,
            )
        )
        for sample_index in range(256)
    }
    expected = {
        (
            frozenset({(0, 0), (0, 1), (1, 1)}),
            frozenset({(0, 0), (1, 0), (1, 1)}),
        ),
        (
            frozenset({(0, 0), (1, 0), (1, 1)}),
            frozenset({(0, 0), (0, 1), (1, 1)}),
        ),
        (
            frozenset({(0, 0), (0, 1), (1, 0)}),
            frozenset({(0, 1), (1, 0), (1, 1)}),
        ),
        (
            frozenset({(0, 1), (1, 0), (1, 1)}),
            frozenset({(0, 0), (0, 1), (1, 0)}),
        ),
    }
    assert signatures == expected
