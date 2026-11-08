"""Regression tests for the scan-order 3x3-growth intersection sampler."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Iterable

import pytest

TASK_ID = "3ef5f8be2639"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs() -> list[dict]:
    try:
        from reviewer_support import canonical_pairs, find_root
    except ImportError:
        # Direct repo execution fallback; the public task-test stage supplies
        # reviewer_support in its portable runtime.
        import json

        root = HOME.parents[1]
        rows = []
        with (root / "shared/data/canonical/puzzles.jsonl").open() as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
        assert len(rows) == 1
        row = rows[0]
        return [*row["train"], row["test"]]
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _first(grid: list[list[int]], color: int) -> tuple[int, int]:
    return next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    )


def _grown(point: tuple[int, int], h: int, w: int) -> set[tuple[int, int]]:
    r, c = point
    return {
        (rr, cc)
        for rr in range(r - 1, r + 2)
        for cc in range(c - 1, c + 2)
        if 0 <= rr < h and 0 <= cc < w
    }


def _oracle(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    cells = _grown(_first(grid, 2), h, w) & _grown(_first(grid, 3), h, w)
    return [[8 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]


def _all_pair_oracle(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    twos = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    threes = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    cells: set[tuple[int, int]] = set()
    for two in twos:
        for three in threes:
            cells |= _grown(two, h, w) & _grown(three, h, w)
    return [[8 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]


def _nonzero_count(grid: Iterable[Iterable[int]]) -> int:
    return sum(value != 0 for row in grid for value in row)


def test_metadata_pins_authority_and_declares_only_observable_axes():
    assert gen.RULE_HASH == "020757caefaf"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "offset_id",
        "num_2_seeds",
        "num_3_seeds",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert tuple(gen.HELPFUL_TEXTURES) == ()
    assert tuple(gen.DEGENERATE_TEXTURES) == ()


@pytest.mark.parametrize("pair", _canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]
    assert gen._first_pair_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("offset_id", [0, 7, 8, 15, 23])
@pytest.mark.parametrize("num_2,num_3", [(1, 1), (2, 1), (1, 2), (2, 2)])
def test_exact_overrides_are_realized_in_every_band(band, offset_id, num_2, num_3):
    expected = {
        "grid_h": 7,
        "grid_w": 8,
        "offset_id": offset_id,
        "num_2_seeds": num_2,
        "num_3_seeds": num_3,
    }
    grid = gen.generate(913, 37, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    assert _oracle(grid) == gen._first_pair_output(grid)
    assert _nonzero_count(_oracle(grid)) > 0


@pytest.mark.parametrize("offset_id", range(24))
def test_every_relative_offset_is_constructive_and_observable(offset_id):
    grid = gen.generate(
        44,
        offset_id,
        grid_h=7,
        grid_w=7,
        offset_id=offset_id,
        num_2_seeds=2,
        num_3_seeds=2,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["offset_id"] == offset_id
    assert _nonzero_count(_oracle(grid)) > 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 6},
        {"grid_w": 15},
        {"offset_id": -1},
        {"offset_id": 24},
        {"num_2_seeds": 0},
        {"num_3_seeds": 3},
        {"num_2_seeds": True},
        {"grid_h": 7.0},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


def test_default_schedule_covers_canonical_profiles_both_distances_and_counterexamples():
    profiles = set()
    distances = set()
    effective_distractors = 0
    for index in range(48):
        grid = gen.generate(700 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert gen.self_check(grid) == []
        assert grid == gen.generate(700 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        obs = gen.observe_overrides(grid)
        profiles.add((obs["grid_h"], obs["grid_w"], len({v for row in grid for v in row})))
        two, three = _first(grid, 2), _first(grid, 3)
        distances.add(max(abs(two[0] - three[0]), abs(two[1] - three[1])))
        if _all_pair_oracle(grid) != _oracle(grid):
            effective_distractors += 1
    assert (7, 7, 3) in profiles
    assert (8, 8, 3) in profiles
    assert distances == {1, 2}
    assert effective_distractors >= 24


def test_declared_rivals_fit_canonical_and_generated_witnesses_refute_them():
    pairs = _canonical_pairs()
    for pair in pairs:
        assert gen.SEMANTIC_RIVALS["all_pairs"](pair["input"]) == pair["output"]
        assert gen.SEMANTIC_RIVALS["distance_two_only"](pair["input"]) == pair["output"]

    seen = {"scan_order_distractor": False, "distance_one": False}
    for index in range(48):
        grid = gen.generate(1500 + index, index)
        authoritative = _oracle(grid)
        for witness, rival_names in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                seen[witness] = True
                assert any(gen.SEMANTIC_RIVALS[name](grid) != authoritative for name in rival_names)
    assert all(seen.values())


@pytest.mark.parametrize("mutation", ["erase_two", "erase_three", "bad_color", "far_pair", "extra_seed"])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(91, 5, grid_h=8, grid_w=8, offset_id=0, num_2_seeds=1, num_3_seeds=1)
    if mutation == "erase_two":
        r, c = _first(grid, 2)
        grid[r][c] = 0
    elif mutation == "erase_three":
        r, c = _first(grid, 3)
        grid[r][c] = 0
    elif mutation == "bad_color":
        grid[0][0] = 9
    elif mutation == "far_pair":
        grid = [[0] * 8 for _ in range(8)]
        grid[1][1] = 2
        grid[6][6] = 3
    else:
        # Three color-2 seeds exceed the declared lawful count.
        for r in range(7, -1, -1):
            for c in range(7, -1, -1):
                if grid[r][c] == 0:
                    grid[r][c] = 2
                    break
            else:
                continue
            break
        for r in range(7, -1, -1):
            for c in range(7, -1, -1):
                if grid[r][c] == 0:
                    grid[r][c] = 2
                    break
            else:
                continue
            break
    assert gen.self_check(grid)


@pytest.mark.parametrize("malformed", [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(7)]])
def test_self_check_reports_malformed_grids_without_raising(malformed):
    assert gen.self_check(malformed)
