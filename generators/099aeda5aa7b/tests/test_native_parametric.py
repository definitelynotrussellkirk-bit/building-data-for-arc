"""Focused source-review and native-parametric tests for 099aeda5aa7b."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "099aeda5aa7b"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"
PROMOTION = HOME / "workspace/parametric/promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing runnable source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return _load(HOME / "generator.py", "generator_099aeda5aa7b_test")


@pytest.fixture(scope="module")
def p():
    return _load(PROTOTYPE, "parametric_099aeda5aa7b_test")


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row["task_id"] == TASK_ID}
    assert len(programs) == 1
    return next(iter(programs))


def _nonzero(grid):
    return sum(value != 0 for row in grid for value in row)


def _occupied_bbox_overlay(grid, axis):
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    cells = [(r, c, grid[r][c]) for r in range(height) for c in range(width) if grid[r][c] != 0]
    rows = [r for r, _, _ in cells]
    columns = [c for _, c, _ in cells]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(columns), max(columns)
    for r, c, value in cells:
        if axis == "horizontal":
            output[r][min_c + max_c - c] = value
        else:
            output[min_r + max_r - r][c] = value
    return output


def test_base_pins_rule_and_rejects_unknown_or_coercive_overrides(base):
    assert base.RULE_HASH == "f48a460c6519"
    with pytest.raises(ValueError, match="unknown override"):
        base.generate(0, 0, __unknown_axis__=1)
    with pytest.raises((TypeError, ValueError)):
        base.generate(0, 0, marks=True)


def test_base_exact_axes_and_swap_conflict(base):
    grid = base.generate(0, 0, difficulty="easy", grid_h=4, grid_w=18,
                         marks=20, texture="swap_pair")
    assert len(grid) == 4 and all(len(row) == 18 for row in grid)
    assert _nonzero(grid) == 20
    assert base.self_check(grid) == []
    assert any(row[c] and row[-1 - c] and row[c] != row[-1 - c]
               for row in grid for c in range(9))
    axis = base.generate(3, 1, grid_h=16, grid_w=17, marks=3, texture="on_axis")
    assert _nonzero(axis) == 3
    assert any(row[8] != 0 for row in axis)
    with pytest.raises(ValueError):
        base.generate(0, 0, grid_w=12, texture="on_axis")


def test_base_python_mirror_exercises_both_halves_and_swaps(base):
    grid = [[0, 0, 0, 0, 0], [2, 0, 0, 0, 7], [0, 0, 4, 0, 0]]
    assert base._mirror(grid) == [[0, 0, 0, 0, 0], [7, 0, 0, 0, 2], [0, 0, 4, 0, 0]]


def test_default_program_is_byte_exact_and_settings_are_strict(p):
    assert p.program({"axis": "horizontal"}) == _canonical_program()
    assert p.program({"axis": "vertical"}) != _canonical_program()
    for bad in ({}, {"axis": "wrong"}, {"axis": "horizontal", "extra": 1}, {"axis": True}):
        with pytest.raises(ValueError):
            p.program(bad)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_prefix_stability_and_two_demo_identification(p, demos):
    horizontal = p.generate(23, {"axis": "horizontal"}, demos, 4)
    vertical = p.generate(23, {"axis": "vertical"}, demos, 4)
    one = p.generate(23, {"axis": "horizontal"}, demos, 1)
    assert len(horizontal["train"]) == demos and len(horizontal["test"]) == 4
    assert len(vertical["train"]) == demos and len(vertical["test"]) == 4
    for split in ("train", "test"):
        assert [pair["input"] for pair in horizontal[split]] == [pair["input"] for pair in vertical[split]]
    assert any(a["output"] != b["output"] for a, b in zip(horizontal["train"], vertical["train"]))
    visible = {"train": horizontal["train"], "test": [{"input": horizontal["test"][0]["input"]}]}
    assert public_challenge_bytes(visible) == public_challenge_bytes(one)
    inputs = [json.dumps(pair["input"]) for split in ("train", "test") for pair in horizontal[split]]
    assert len(inputs) == len(set(inputs))
    assert any(p.transform(pair["input"], {"axis": "vertical"}) != pair["output"]
               for pair in horizontal["train"])
    assert any(p.transform(pair["input"], {"axis": "horizontal"}) != pair["output"]
               for pair in vertical["train"])


def test_fourth_query_is_substantive_30_square_and_claims_match_transform(p):
    for axis in ("horizontal", "vertical"):
        settings = {"axis": axis}
        episode = p.generate(5, settings, 2, 4)
        grid = episode["test"][3]["input"]
        assert len(grid) == 30 and all(len(row) == 30 for row in grid)
        for r0 in (0, 15):
            for c0 in (0, 15):
                assert sum(cell != 0 for row in grid[r0:r0 + 15] for cell in row[c0:c0 + 15]) >= 20
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == p.transform(pair["input"], settings)


@pytest.mark.parametrize("axis", ["horizontal", "vertical"])
def test_lessons_refute_reflection_inside_occupied_bbox(p, axis):
    """Catch a shortcut that uses object extent instead of the full canvas axis."""
    episode = p.generate(0, {"axis": axis}, 2, 4)
    candidate_train = [_occupied_bbox_overlay(pair["input"], axis) for pair in episode["train"]]
    candidate_test = [_occupied_bbox_overlay(pair["input"], axis) for pair in episode["test"]]
    assert any(got != pair["output"] for got, pair in zip(candidate_train, episode["train"]))
    assert any(got != pair["output"] for got, pair in zip(candidate_test, episode["test"]))


def test_reflection_stage_is_input_dependent_and_consumed_by_overlay(p):
    episode = p.generate(17, {"axis": "vertical"}, 2, 4)
    pair = next(pair for pair in [*episode["train"], *episode["test"]]
                if p.transform(pair["input"], {"axis": "horizontal"}) != pair["output"])
    reflected = p.intermediate(pair["input"], {"axis": "vertical"})
    assert reflected != pair["input"]
    assert p.overlay(pair["input"], reflected) == pair["output"]


@pytest.mark.parametrize("case", [
    {"seed": True}, {"demos": 1}, {"demos": 7}, {"demos": 2.0},
    {"queries": 0}, {"queries": 5}, {"queries": True},
])
def test_invalid_generation_requests_are_rejected(p, case):
    args = {"seed": 0, "settings": {"axis": "horizontal"}, "demos": 2, "queries": 4}
    args.update(case)
    with pytest.raises(ValueError):
        p.generate(**args)


def test_native_worker_contract_identifies_both_settings(p):
    contract = json.loads(PROMOTION.read_text())
    programs = {
        p.program({"axis": "horizontal"}): {"axis": "horizontal"},
        p.program({"axis": "vertical"}): {"axis": "vertical"},
    }

    def apply(program, grid):
        return p.transform(grid, programs[program])

    jobs = [{"seed": seed, "settings": {"axis": axis}, "demos": 2, "queries": 4}
            for seed in (0, 17) for axis in ("horizontal", "vertical")]
    report = evaluate_contract(REPO, TASK_ID, contract, jobs, apply_program=apply)
    assert len(report["episodes"]) == 4
    assert all(check["survivors"] == [check["settings"]] for check in report["checks"])


def test_plain_two_mark_witness_cannot_collapse_to_horizontal_symmetry(base):
    """Catch same-row, same-colour mirrored witnesses that abort ordinary generation."""
    grid = base.generate(10, 0, grid_h=4, grid_w=5, marks=2, texture="plain")
    assert sum(value != 0 for row in grid for value in row) == 2
    assert base._mirror(grid) != grid
    assert base.self_check(grid) == []


def test_on_axis_three_mark_witness_cannot_be_completed_into_symmetry(base):
    """Catch generic fill recreating the off-axis source beside an axis mark."""
    grid = base.generate(11, 0, grid_h=4, grid_w=5, marks=3, texture="on_axis")
    assert sum(value != 0 for row in grid for value in row) == 3
    assert any(row[2] != 0 for row in grid)
    assert base._mirror(grid) != grid
    assert base.self_check(grid) == []
