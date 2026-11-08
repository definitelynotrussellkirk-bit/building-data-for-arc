"""Behavioral contract for the native ba9d8eb0cd5a parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "ba9d8eb0cd5a"
ROOT = find_root(__file__)
TASK = ROOT / "generators" / TASK_ID
HOME = TASK / "workspace" / "parametric"
CANONICAL_PATH = TASK / "workspace" / "canonical-current.rkt"


def load_family():
    path = HOME / "family.py"
    spec = importlib.util.spec_from_file_location("parametric_ba9d8eb0cd5a_test", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pack_rows(grid: list[list[int]]) -> list[list[int]]:
    return [
        [value for value in row if value != 0]
        + [0] * sum(value == 0 for value in row)
        for row in grid
    ]


def mark_vertical_contacts(grid: list[list[int]]) -> list[list[int]]:
    packed = pack_rows(grid)
    height, width = len(packed), len(packed[0])
    return [
        [
            2
            if packed[r][c] != 0
            and (
                (r > 0 and packed[r - 1][c] != 0)
                or (r + 1 < height and packed[r + 1][c] != 0)
            )
            else packed[r][c]
            for c in range(width)
        ]
        for r in range(height)
    ]


def mark_before_pack(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    marked = [
        [
            2
            if grid[r][c] != 0
            and (
                (r > 0 and grid[r - 1][c] != 0)
                or (r + 1 < height and grid[r + 1][c] != 0)
            )
            else grid[r][c]
            for c in range(width)
        ]
        for r in range(height)
    ]
    return pack_rows(marked)


def nonzero_sequence(row: list[int]) -> list[int]:
    return [value for value in row if value]


def test_default_program_is_exact_canonical_bytes() -> None:
    family = load_family()
    exact = CANONICAL_PATH.read_text()
    assert family.program(None) == exact
    assert family.program({"finish_rule": "pack_only"}) == exact
    assert family.program({"finish_rule": "mark_vertical_contacts"}) != exact


@pytest.mark.parametrize("seed", [0, 17, 2026])
@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_distinct_pairs_and_independent_labels(seed: int, demos: int) -> None:
    family = load_family()
    plain = family.generate(seed, {"finish_rule": "pack_only"}, demos, 4)
    marked = family.generate(seed, {"finish_rule": "mark_vertical_contacts"}, demos, 4)
    assert len(plain["train"]) == len(marked["train"]) == demos
    assert len(plain["test"]) == len(marked["test"]) == 4
    plain_inputs = [pair["input"] for pair in plain["train"] + plain["test"]]
    marked_inputs = [pair["input"] for pair in marked["train"] + marked["test"]]
    assert plain_inputs == marked_inputs
    assert len({repr(grid) for grid in plain_inputs}) == demos + 4
    for ppair, mpair in zip(plain["train"] + plain["test"], marked["train"] + marked["test"]):
        assert ppair["output"] == pack_rows(ppair["input"])
        assert mpair["output"] == mark_vertical_contacts(mpair["input"])


def test_minimum_demonstrations_identify_the_declared_setting() -> None:
    family = load_family()
    for seed in (0, 17, 99):
        plain = family.generate(seed, {"finish_rule": "pack_only"}, 2, 4)
        marked = family.generate(seed, {"finish_rule": "mark_vertical_contacts"}, 2, 4)
        assert all(
            p["output"] != m["output"]
            for p, m in zip(plain["train"], marked["train"])
        )


def test_post_pack_contacts_are_real_and_wrong_order_is_refuted() -> None:
    family = load_family()
    episode = family.generate(17, {"finish_rule": "mark_vertical_contacts"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        packed = pack_rows(grid)
        # The construction makes neighboring active rows disjoint before packing.
        assert all(
            not (grid[r][c] and grid[r + 1][c])
            for r in range(len(grid) - 1)
            for c in range(len(grid[0]))
        )
        assert any(
            packed[r][c] and packed[r + 1][c]
            for r in range(len(grid) - 1)
            for c in range(len(grid[0]))
        )
        assert pair["output"] != mark_before_pack(grid)


def test_rows_preserve_nonmonotone_order_and_marker_color_is_reserved() -> None:
    family = load_family()
    episode = family.generate(0, {"finish_rule": "pack_only"}, 2, 4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        assert 2 not in {value for row in grid for value in row}
        assert any(
            len(values := nonzero_sequence(row)) >= 2 and values != sorted(values)
            for row in grid
        )


def test_query_pool_contains_a_dense_30_by_30_stress_case() -> None:
    family = load_family()
    episode = family.generate(0, {"finish_rule": "mark_vertical_contacts"}, 2, 4)
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(value != 0 for row in stress for value in row) >= 330
    assert sum(value == 2 for row in episode["test"][-1]["output"] for value in row) >= 300


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.generate(-1, {"finish_rule": "pack_only"}, 2, 4),
        lambda f: f.generate(0, {"finish_rule": "pack_only"}, 1, 4),
        lambda f: f.generate(0, {"finish_rule": "pack_only"}, 7, 4),
        lambda f: f.generate(0, {"finish_rule": "pack_only"}, 2, 0),
        lambda f: f.generate(0, {"finish_rule": "pack_only"}, 2, 5),
        lambda f: f.generate(0, {}, 2, 4),
        lambda f: f.generate(0, {"finish_rule": "unknown"}, 2, 4),
        lambda f: f.generate(0, {"finish_rule": "pack_only", "extra": 1}, 2, 4),
    ],
)
def test_invalid_requests_fail_loudly(call) -> None:
    with pytest.raises(ValueError):
        call(load_family())
