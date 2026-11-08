"""Behavioral contract for the native 20b53e0c4957 parametric family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
TASK = ROOT / "generators" / "20b53e0c4957"
FAMILY_PATH = TASK / "workspace" / "parametric" / "family.py"
CANONICAL_PATH = TASK / "workspace" / "parametric" / "canonical.rkt"


def load_family():
    spec = importlib.util.spec_from_file_location("parametric_20b53e0c4957_test", FAMILY_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(FAMILY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def split(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    width = (len(grid[0]) - 2) // 3
    return (
        [row[:width] for row in grid],
        [row[width + 1 : 2 * width + 1] for row in grid],
        [row[2 * width + 2 :] for row in grid],
    )


def cells(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value}


def bbox(points: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return min(r for r, _ in points), min(c for _, c in points), max(r for r, _ in points), max(c for _, c in points)


def independent_transform(grid: list[list[int]], policy: str) -> list[list[int]]:
    a, b, c = split(grid)
    ca, cb, cc = cells(a), cells(b), cells(c)
    ar0, ac0, _, _ = bbox(ca)
    cr0, cc0, cr1, cc1 = bbox(cc)
    removed = {(r - ar0, col - ac0) for r, col in ca - cb}
    out = copy.deepcopy(c)
    if policy == "repair_then_transfer":
        colors = {value for row in c for value in row if value}
        assert len(colors) == 1
        color = next(iter(colors))
        for r in range(cr0, cr1 + 1):
            for col in range(cc0, cc1 + 1):
                out[r][col] = color
    for rr, col in removed:
        out[cr0 + rr][cc0 + col] = 0
    return out


def test_default_program_is_exact_canonical_source() -> None:
    family = load_family()
    exact = CANONICAL_PATH.read_text()
    assert family.program({"hole_policy": "preserve"}) == exact
    assert family.program(None) == exact
    assert family.program({"hole_policy": "repair_then_transfer"}) != exact


def test_independent_counts_matched_inputs_and_distinct_pairs() -> None:
    family = load_family()
    for seed in (0, 17, 2026):
        for demos in range(2, 7):
            preserve = family.generate(seed, {"hole_policy": "preserve"}, demos, 4)
            repair = family.generate(seed, {"hole_policy": "repair_then_transfer"}, demos, 4)
            assert len(preserve["train"]) == len(repair["train"]) == demos
            assert len(preserve["test"]) == len(repair["test"]) == 4
            p_inputs = [pair["input"] for pair in preserve["train"] + preserve["test"]]
            r_inputs = [pair["input"] for pair in repair["train"] + repair["test"]]
            assert p_inputs == r_inputs
            assert len({repr(grid) for grid in p_inputs}) == demos + 4
            for ppair, rpair in zip(preserve["train"] + preserve["test"], repair["train"] + repair["test"]):
                assert ppair["output"] == independent_transform(ppair["input"], "preserve")
                assert rpair["output"] == independent_transform(rpair["input"], "repair_then_transfer")
                assert ppair["output"] != rpair["output"]


def test_minimum_two_demos_identify_the_setting() -> None:
    family = load_family()
    for seed in range(12):
        preserve = family.generate(seed, {"hole_policy": "preserve"}, 2, 4)
        repair = family.generate(seed, {"hole_policy": "repair_then_transfer"}, 2, 4)
        assert any(a["output"] != b["output"] for a, b in zip(preserve["train"], repair["train"]))


def test_scene_contract_refutes_shortcuts_and_preserves_bbox_semantics() -> None:
    family = load_family()
    for seed in range(16):
        episode = family.generate(seed, {"hole_policy": "preserve"}, 3, 4)
        for pair in episode["train"] + episode["test"]:
            grid = pair["input"]
            a, b, c = split(grid)
            ca, cb, cc = cells(a), cells(b), cells(c)
            assert ca and cb and cc and cb < ca
            ar0, ac0, ar1, ac1 = bbox(ca)
            cr0, cc0, cr1, cc1 = bbox(cc)
            assert (ar1 - ar0, ac1 - ac0) == (cr1 - cr0, cc1 - cc0)
            assert (ar0, ac0) != (cr0, cc0)
            removed = {(r - ar0, col - ac0) for r, col in ca - cb}
            existing_holes = {
                (r - cr0, col - cc0)
                for r in range(cr0, cr1 + 1)
                for col in range(cc0, cc1 + 1)
                if c[r][col] == 0
            }
            assert removed
            assert existing_holes
            assert removed.isdisjoint(existing_holes)
            assert pair["output"] != c  # skip-A cannot solve preserve
            assert pair["output"] != [[next(v for row in c for v in row if v) if v else 0 for v in row] for row in b]


def test_lawful_stress_case_reaches_30_by_29_with_substantive_content() -> None:
    family = load_family()
    episode = family.generate(31, {"hole_policy": "repair_then_transfer"}, 6, 4)
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 29)
    assert sum(value != 0 for row in stress for value in row) > 300
    assert independent_transform(stress, "repair_then_transfer") == episode["test"][-1]["output"]


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.program({"hole_policy": "unknown"}),
        lambda f: f.program({}),
        lambda f: f.generate(True, {"hole_policy": "preserve"}, 2, 4),
        lambda f: f.generate(0, {"hole_policy": "preserve"}, 1, 4),
        lambda f: f.generate(0, {"hole_policy": "preserve"}, 7, 4),
        lambda f: f.generate(0, {"hole_policy": "preserve"}, 2, 0),
        lambda f: f.generate(0, {"hole_policy": "preserve"}, 2, 5),
    ],
)
def test_invalid_requests_fail_loudly(call) -> None:
    family = load_family()
    with pytest.raises(ValueError):
        call(family)

@pytest.mark.parametrize("seed", [177, 934])
def test_removal_mask_never_exhausts_the_independent_c_hole(seed: int) -> None:
    """Catch samplers that consume every interior cell as an A-minus-B removal."""
    family = load_family()
    preserved = family.generate(seed, {"hole_policy": "preserve"}, 6, 4)
    repaired = family.generate(seed, {"hole_policy": "repair_then_transfer"}, 6, 4)
    assert all(
        left["output"] != right["output"]
        for left, right in zip(
            preserved["train"] + preserved["test"],
            repaired["train"] + repaired["test"],
        )
    )
