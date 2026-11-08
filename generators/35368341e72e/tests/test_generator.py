"""Regression tests for the prototype-dictionary gallery generator.

The oracle in this file is deliberately independent of the production helper:
it translates the canonical Racket rule directly from the visible grid layout.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "35368341e72e"
RULE_HASH = "dfe1312c69fd"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
BANDS = (None, "easy", "medium", "hard")
EXPECTED_AXES = {"grid_h", "grid_w", "n_keys", "query_len"}


def _prototypes(grid: list[list[int]]) -> dict[int, list[list[int]]]:
    return {
        value: [row[col - 1 : col + 2] for row in grid[1:4]]
        for col, value in enumerate(grid[0])
        if value != 0
    }


def _pack(parts: list[list[list[int]]]) -> list[list[int]]:
    if not parts:
        return [[0]]
    width = 4 * len(parts) - 1
    out = [[0] * width for _ in range(3)]
    for index, part in enumerate(parts):
        left = 4 * index
        for row in range(3):
            for col in range(3):
                if part[row][col] != 0:
                    out[row][left + col] = part[row][col]
    return out


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    prototypes = _prototypes(grid)
    query = [value for value in grid[-1] if value != 0]
    return _pack([prototypes[value] for value in query])


def deduplicate_query_output(grid: list[list[int]]) -> list[list[int]]:
    prototypes = _prototypes(grid)
    seen: set[int] = set()
    query = []
    for value in grid[-1]:
        if value != 0 and value not in seen:
            seen.add(value)
            query.append(value)
    return _pack([prototypes[value] for value in query])


def observed(grid: list[list[int]]) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_keys": sum(value != 0 for value in grid[0]),
        "query_len": sum(value != 0 for value in grid[-1]),
    }


def _query(grid: list[list[int]]) -> list[int]:
    return [value for value in grid[-1] if value != 0]


def test_metadata_and_semantic_contract_are_explicit() -> None:
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.RULE_HASH == RULE_HASH
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.EXAMPLES_NEEDED == 2
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.SEMANTIC_WITNESSES) == {"repeated_query"}
    assert set(GEN.SEMANTIC_RIVALS) == {"deduplicate_query"}
    assert GEN.WITNESS_RIVALS == {"repeated_query": ["deduplicate_query"]}
    assert set(GEN.CANONICAL_SHORTCUTS) == {"deduplicate_query"}


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"{pair.get('split', 'pair')}{pair.get('pair_index', '')}",
)
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair) -> None:
    before = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 5, "grid_w": 11, "n_keys": 3, "query_len": 3},
        {"grid_h": 12, "grid_w": 20, "n_keys": 1, "query_len": 2},
    ],
)
def test_exact_override_boundaries_are_honored_in_every_band(band, options) -> None:
    grid = GEN.generate(17, 9, difficulty=band, **options)
    assert GEN.self_check(grid, difficulty=band) == []
    assert observed(grid) == options
    assert GEN.observe_overrides(grid) == options
    assert GEN.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 4},
        {"grid_h": 13},
        {"grid_w": 10},
        {"grid_w": 21},
        {"n_keys": 0},
        {"n_keys": 4},
        {"query_len": 1},
        {"query_len": 4},
        {"grid_h": True},
        {"grid_w": 11.5},
        {"n_keys": "3"},
        {"query_len": False},
    ],
)
def test_invalid_overrides_are_rejected(overrides) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", BANDS)
def test_generated_queries_repeat_and_refute_the_canonical_shortcut(band) -> None:
    for index in range(48):
        grid = GEN.generate(700 + index, index * 11, difficulty=band)
        query = _query(grid)
        assert GEN.self_check(grid, difficulty=band) == []
        assert grid == GEN.generate(700 + index, index * 11, difficulty=band)
        assert len(query) > len(set(query))
        assert GEN.SEMANTIC_WITNESSES["repeated_query"](grid) is True
        assert GEN.SEMANTIC_RIVALS["deduplicate_query"](grid) == deduplicate_query_output(grid)
        assert GEN.SEMANTIC_RIVALS["deduplicate_query"](grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_pinned_profile_census_has_an_exact_canonical_anchor_in_every_band(band) -> None:
    hits = 0
    for index in range(20):
        digest = hashlib.sha256(
            f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
        ).hexdigest()
        seed = int(digest[:12], 16)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        hits += profile in {(6, 11, 5), (6, 11, 6)}
    assert hits >= 1


def test_pinned_profile_census_meets_the_pooled_canonical_envelope_floor() -> None:
    hits = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += profile in {(6, 11, 5), (6, 11, 6)}
            total += 1
    assert hits / total >= 0.25


@pytest.mark.parametrize("band", BANDS)
def test_generated_outputs_preserve_the_canonical_shrink_relation(band) -> None:
    for index in range(64):
        grid = GEN.generate(1200 + index, index * 13, difficulty=band)
        output = GEN.rule_mirror(grid)
        assert len(output) <= len(grid)
        assert len(output[0]) <= len(grid[0])


def test_deduplication_shortcut_fits_every_canonical_label() -> None:
    assert all(
        deduplicate_query_output(pair["input"]) == pair["output"]
        for pair in PAIRS
    )
    assert all(
        GEN.CANONICAL_SHORTCUTS["deduplicate_query"](pair["input"])
        == pair["output"]
        for pair in PAIRS
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_key",
        "adjacent_key_band",
        "outside_prototype",
        "stray_middle_cell",
        "unknown_query_key",
        "empty_query",
    ],
)
def test_structural_self_check_rejects_minimal_impostors(mutation) -> None:
    grid = GEN.generate(91, 4, grid_h=7, grid_w=11, n_keys=3, query_len=3)
    key_cols = [col for col, value in enumerate(grid[0]) if value]
    if mutation == "duplicate_key":
        grid[0][key_cols[1]] = grid[0][key_cols[0]]
    elif mutation == "adjacent_key_band":
        grid[0][key_cols[0] + 1] = grid[0][key_cols[0]]
    elif mutation == "outside_prototype":
        outside = next(
            col
            for col in range(len(grid[0]))
            if all(abs(col - key_col) > 1 for key_col in key_cols)
        )
        grid[2][outside] = 9
    elif mutation == "stray_middle_cell":
        grid[4][0] = 9
    elif mutation == "unknown_query_key":
        grid[-1] = [0] * len(grid[-1])
        grid[-1][0] = next(value for value in range(1, 10) if value not in grid[0])
    elif mutation == "empty_query":
        grid[-1] = [0] * len(grid[-1])
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(5)]],
)
def test_malformed_grids_are_diagnostic_not_exception(grid) -> None:
    assert GEN.self_check(grid)
