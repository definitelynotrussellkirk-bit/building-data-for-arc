from __future__ import annotations

import copy
import importlib
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "75837d4fa905"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _blank(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _put_square(grid: list[list[int]], r: int, c: int, color: int) -> None:
    for rr in (r, r + 1):
        for cc in (c, c + 1):
            grid[rr][cc] = color


def _edge_square_present(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    for cells in by_color.values():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        if min(rows) == 0 or min(cols) == 0 or max(rows) == h - 1 or max(cols) == w - 1:
            return True
    return False


def test_rule_hash_canonical_domain_and_python_mirror() -> None:
    assert GEN.RULE_HASH == "e56cca9b3b6c"
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7, "grid_w": 8, "n_squares": 2},
        {"grid_h": 8, "grid_w": 10, "n_squares": 2},
        {"grid_h": 9, "grid_w": 9, "n_squares": 3},
        {"grid_h": 16, "grid_w": 18, "n_squares": 4},
    ],
)
def test_exact_overrides_round_trip_in_every_band(difficulty: str, overrides: dict[str, int]) -> None:
    grid = GEN.generate(711, 5, difficulty=difficulty, **overrides)
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid) == overrides


def test_unknown_invalid_and_out_of_range_overrides_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis=3)
    for key, value in (
        ("grid_h", 6),
        ("grid_w", 7),
        ("n_squares", 0),
        ("n_squares", 1),
        ("n_squares", 5),
        ("grid_h", True),
        ("grid_w", "10"),
        ("n_squares", 2.0),
    ):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 2, **{key: value})
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="extreme")


def test_validator_rejects_3x3_composites_and_preserves_first_writer_overlap() -> None:
    solid_3x3 = _blank(7, 8)
    for r in range(2, 5):
        for c in range(2, 5):
            solid_3x3[r][c] = 4
    assert GEN.self_check(solid_3x3)

    shared_bloom = _blank(7, 8)
    _put_square(shared_bloom, 2, 0, 3)
    _put_square(shared_bloom, 2, 3, 7)
    assert GEN.self_check(shared_bloom) == []
    output = GEN.rule_mirror(shared_bloom)
    assert output[1][2] == 3
    assert output[4][2] == 3


def test_single_square_is_outside_teaching_grammar_and_boundary_pair_refutes_shortcut() -> None:
    lone = _blank(7, 8)
    _put_square(lone, 0, 0, 4)
    assert GEN.self_check(lone)

    grid = _blank(7, 8)
    _put_square(grid, 0, 0, 4)
    _put_square(grid, 4, 5, 7)
    assert GEN.self_check(grid) == []
    expected = GEN.rule_mirror(grid)
    assert expected[2][2] == 4
    assert GEN.SEMANTIC_RIVALS["interior_only"](grid) != expected
    assert GEN.SEMANTIC_WITNESSES["clipped_boundary_bloom"](grid)


def test_canonical_demonstrations_fit_declared_shortcut() -> None:
    rival = GEN.CANONICAL_SHORTCUTS["interior_only"]
    for pair in _pairs():
        assert rival(pair["input"]) == pair["output"]


def test_every_three_default_examples_refute_declared_shortcut() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            demos = []
            for offset in range(3):
                grid = GEN.generate(20_000 + band_index, start + offset, difficulty=band)
                assert GEN.self_check(grid) == []
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(20_000 + band_index, start + 3, difficulty=band)
            assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []
            assert any(_edge_square_present(pair["input"]) for pair in demos)


def test_each_band_retains_exact_canonical_profile_support() -> None:
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in _pairs()
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        observed = set()
        for index in range(18):
            grid = GEN.generate(30_000 + band_index, index, difficulty=band)
            observed.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert canonical_profiles <= observed


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    before = random.getstate()
    first = GEN.generate(909, 17, difficulty="hard")
    assert random.getstate() == before
    second = GEN.generate(909, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(909, 17, difficulty="hard") == second


def test_four_pair_lesson_is_identifiable_under_every_query_rotation() -> None:
    # This exact production-census start formerly had only one clipped-boundary
    # witness, so holding it out left the canonical-fitting interior-only rival alive.
    seed = 3_999_318_746
    start = 28
    pairs = []
    for offset in range(4):
        grid = GEN.generate(seed, start + offset, difficulty="easy")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, pairs[query_index]) == []
