"""Task-local regressions for 71fd3c801ee1.

These tests independently reconstruct the feature triple used by the canonical
rule so generator helpers are not allowed to certify themselves.
"""
from __future__ import annotations

import copy
import importlib
import random
from collections import Counter

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "71fd3c801ee1"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.71fd3c801ee1.generator"
)
BANDS = ("easy", "medium", "hard")


def _norm(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            found.append(tuple(cells))
    return found


def _triple(cells):
    shape = set(_norm(cells))
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    seen = set()
    holes = 0
    for row0 in range(height):
        for col0 in range(width):
            if (row0, col0) in shape or (row0, col0) in seen:
                continue
            region = []
            stack = [(row0, col0)]
            seen.add((row0, col0))
            while stack:
                row, col = stack.pop()
                region.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in shape
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            if all(
                0 < row < height - 1 and 0 < col < width - 1
                for row, col in region
            ):
                holes += 1
    row_sym = all((height - 1 - row, col) in shape for row, col in shape)
    col_sym = all((row, width - 1 - col) in shape for row, col in shape)
    symmetry = 3 if row_sym and col_sym else 1 if row_sym else 2 if col_sym else 0
    return (len(shape), holes, symmetry)


def _independent_rule(grid):
    objects = _components(grid)
    triples = [_triple(cells) for cells in objects]
    counts = Counter(triples)
    output = [row[:] for row in grid]
    for cells, feature in zip(objects, triples):
        if counts[feature] > 1:
            for row, col in cells:
                output[row][col] = 8
    return output


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": _independent_rule(grid)}


def test_rule_pin_and_all_canonical_pairs_are_exact():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "12f0cca6ed07"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert _independent_rule(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", BANDS)
def test_every_family_override_is_exact_observable_and_band_safe(band):
    for index, family in enumerate(GEN.TARGET_FAMILIES):
        grid = GEN.generate(
            10_000 + index,
            20 + index,
            difficulty=band,
            target_family=family,
        )
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.observe_overrides(grid) == {"target_family": family}
        assert _independent_rule(grid) == GEN.rule_mirror(grid)


def test_unknown_override_and_invalid_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="small_asym")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        GEN.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_is_strict_canonical_profile_and_kills_core_rivals(band):
    seen = set()
    family_counts = Counter()
    for index in range(60):
        grid = GEN.generate(20_000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert (len(grid), len(grid[0]), len({v for row in grid for v in row})) == (12, 18, 6)
        truth = _independent_rule(grid)
        assert truth == GEN.rule_mirror(grid)
        assert truth != grid
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert rival(grid) != truth, (band, index, name)
        family_counts[GEN.observe_overrides(grid)["target_family"]] += 1
        seen.add(str(grid))
    assert len(seen) == 60
    assert len(family_counts) >= 4


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID)
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "same_area",
        "same_area_and_holes",
        "same_area_and_symmetry",
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", BANDS)
def test_every_sliding_lesson_window_is_identifiable(band):
    for start in range(12):
        seed = 30_000 + start
        grids = [
            GEN.generate(seed, start + offset, difficulty=band)
            for offset in range(GEN.EXAMPLES_NEEDED + 1)
        ]
        demos = [_pair(grid) for grid in grids[: GEN.EXAMPLES_NEEDED]]
        query = _pair(grids[GEN.EXAMPLES_NEEDED])
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), (
                band,
                start,
                name,
            )


def test_named_witnesses_fire_and_refute_every_claimed_rival():
    grids = [GEN.generate(40_000, index, difficulty="hard") for index in range(20)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        fired = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert fired, witness_name
        for grid in fired:
            truth = _independent_rule(grid)
            for rival_name in rival_names:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_determinism_fresh_returns_input_purity_and_global_rng_isolation():
    random.seed(20261004)
    state = random.getstate()
    first = GEN.generate(555, 17, difficulty="hard")
    pristine = copy.deepcopy(first)
    assert GEN.rule_mirror(first) == _independent_rule(first)
    assert first == pristine
    second = GEN.generate(555, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == state
    first[0][0] = 9
    assert GEN.generate(555, 17, difficulty="hard") == second


def test_targeted_mutations_and_malformed_grids_are_rejected():
    for malformed in (None, [], [[]], [[0], [0, 1]], [[True]], [[10]]):
        assert GEN.self_check(malformed)
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
