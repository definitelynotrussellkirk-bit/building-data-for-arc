"""Regression tests for the row-compaction generator repair."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root

TASK_ID = "ba9d8eb0cd5a"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def canonical_pairs(task_id: str):
    return _canonical_pairs(task_id, root=ROOT)


def canonical_rule_hash(task_id: str) -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id and row.get("program_solution"):
                normalized = " ".join(str(row["program_solution"]).split())
                return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise KeyError(task_id)


def pack_rows(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python oracle for the unchanged Racket authority."""
    result: list[list[int]] = []
    for row in grid:
        nonzero = [value for value in row if value != 0]
        result.append(nonzero + [0] * (len(row) - len(nonzero)))
    return result


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def nonzero_colors(grid: list[list[int]]) -> set[int]:
    return {value for row in grid for value in row if value != 0}


def needs_pack(row: list[int]) -> bool:
    nonzero = [value for value in row if value != 0]
    return bool(nonzero) and row != nonzero + [0] * (len(row) - len(nonzero))


def has_order_witness(grid: list[list[int]]) -> bool:
    return any(
        len(values := [value for value in row if value != 0]) >= 2
        and values != sorted(values)
        for row in grid
    )


def test_rule_hash_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "8cd149b15ecf"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert pack_rows(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "case",
    [
        {"grid_h": 4, "grid_w": 7, "n_colors": 9},
        {"grid_h": 12, "grid_w": 16, "n_colors": 2},
    ],
)
def test_exact_override_boundaries_are_honored_in_every_band(
    band: str | None, case: dict[str, int]
) -> None:
    for seed in range(8):
        grid = gen.generate(seed, seed * 13 + 5, difficulty=band, **case)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == case
        assert len(nonzero_colors(grid)) == case["n_colors"]
        assert pack_rows(grid) != grid
        assert grid == gen.generate(seed, seed * 13 + 5, difficulty=band, **case)


@pytest.mark.parametrize(
    "case",
    [
        {"typo": 1},
        {"__override_contract_unknown_axis__": 1},
        {"grid_h": 3},
        {"grid_h": 13},
        {"grid_w": 6},
        {"grid_w": 17},
        {"n_colors": 1},
        {"n_colors": 10},
        {"n_colors": True},
        {"grid_h": 4.0},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(case: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty="easy", **case)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_broad_but_keeps_canonical_support(band: str) -> None:
    canonical_profiles = {
        profile(pair["input"]) for pair in canonical_pairs(gen.TASK_ID)
    }
    observed_profiles: set[tuple[int, int, int]] = set()
    shapes: set[tuple[int, int]] = set()
    color_counts: set[int] = set()
    for index in range(48):
        grid = gen.generate(20_000 + index, index * 17 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert any(needs_pack(row) for row in grid)
        assert any(row[0] != 0 for row in grid)
        assert has_order_witness(grid)
        assert pack_rows(grid) != grid
        observed_profiles.add(profile(grid))
        shapes.add((len(grid), len(grid[0])))
        color_counts.add(len(nonzero_colors(grid)))
    assert observed_profiles & canonical_profiles
    assert len(shapes) >= 5
    assert len(color_counts) >= 4


def test_self_check_rejects_uninformative_or_malformed_impostors() -> None:
    cases = [
        [[0] * 7 for _ in range(4)],
        [[3, 1, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0, 0]]
        + [[0] * 7 for _ in range(2)],
        [[0, 1, 0, 2, 0, 0, 0], [3, 0, 0, 0, 0, 0, 0]]
        + [[0] * 7 for _ in range(2)],
        [[False, 2, 0, 0, 0, 0, 0]] * 4,
        [[0] * 7, [0] * 6],
    ]
    for grid in cases:
        assert gen.self_check(grid), grid


def test_semantic_order_witness_refutes_sort_then_pack_rival() -> None:
    assert "order_preservation" in gen.SEMANTIC_WITNESSES
    assert "sort_then_pack" in gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS["order_preservation"] == ["sort_then_pack"]
    for index in range(40):
        grid = gen.generate(30_000 + index, index, difficulty="medium")
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_WITNESSES["order_preservation"](grid)
        assert gen.SEMANTIC_RIVALS["sort_then_pack"](grid) != pack_rows(grid)
