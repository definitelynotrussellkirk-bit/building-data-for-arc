"""Behavioral tests for the repaired target-mask closure family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
)

TASK_ID = "ccbf7456811b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
CONTRACT = PARAMETRIC / "promotion.json"
PROBE = PARAMETRIC / "adversarial_probe.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing runnable artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load(PROTOTYPE, "ccbf7456811b_parametric_subject")


@pytest.fixture(scope="module")
def adapter():
    return _load(ADAPTER, "ccbf7456811b_adapter_subject")


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _points(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _row_close(cells):
    result = set()
    for row in {r for r, _ in cells}:
        cols = [c for r, c in cells if r == row]
        result.update((row, col) for col in range(min(cols), max(cols) + 1))
    return result


def _row_scores(grid):
    target = _points(grid, 7)
    scores = []
    for color in sorted({value for row in grid for value in row} - {0, 7}):
        closed = _row_close(_points(grid, color))
        overlap = len(closed & target)
        scores.append((color, overlap, len(closed) - overlap))
    return scores


def test_repaired_base_exercises_target_ranking_and_truthful_overrides():
    generator, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
    winners = set()
    shapes = set()
    for difficulty in (None, "medium", "hard"):
        for seed in range(8):
            grid = generator.generate(seed, 0, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            scores = _row_scores(grid)
            assert len(scores) >= 3
            assert sum(overlap > 0 for _color, overlap, _extra in scores) >= 2
            winners.add(min(scores, key=lambda item: (-item[1], item[2], item[0]))[0])
            shapes.add((len(grid), len(grid[0])))
    assert len(winners) >= 3
    assert len(shapes) >= 5

    overridden = generator.generate(99, 3, grid_h=30, grid_w=30, n=5)
    assert (len(overridden), len(overridden[0])) == (30, 30)
    assert len({value for row in overridden for value in row} - {0, 7}) == 5
    with pytest.raises(TypeError):
        generator.generate(0, 0, grid_h=True)


def test_default_program_is_byte_exact_canonical(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.program({"closure_axis": "row"}) == canonical
    assert adapter.program({"closure_axis": "row"}) == canonical
    assert prototype.program({"closure_axis": "column"}) != canonical


def test_matched_inputs_distinguish_axis_on_every_labeled_pair(prototype):
    row = prototype.generate(17, {"closure_axis": "row"}, demos=2, queries=4)
    column = prototype.generate(17, {"closure_axis": "column"}, demos=2, queries=4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in row[split]] == [pair["input"] for pair in column[split]]
        assert all(a["output"] != b["output"] for a, b in zip(row[split], column[split]))


def test_counts_are_independent_inputs_are_distinct_and_first_turn_is_prefix_stable(prototype):
    for demos in (2, 3, 6):
        episode = prototype.generate(23, {"closure_axis": "row"}, demos=demos, queries=4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        encoded = [
            json.dumps(pair["input"], separators=(",", ":"))
            for split in ("train", "test")
            for pair in episode[split]
        ]
        assert len(encoded) == len(set(encoded))

    full = prototype.generate(29, {"closure_axis": "column"}, demos=3, queries=4)
    one = prototype.generate(29, {"closure_axis": "column"}, demos=3, queries=1)
    first = {"train": full["train"], "test": [{"input": full["test"][0]["input"]}]}
    assert public_challenge_bytes(first) == public_challenge_bytes(one)


def test_minimum_lesson_has_crossed_controls_and_color_is_nuisance(prototype):
    # Demo profiles 0 and 1 keep target geometry fixed while changing candidate
    # closure geometry, so a target-only shortcut cannot fit both outputs.
    a = prototype.generate(5, {"closure_axis": "row"}, demos=2, queries=4)
    assert prototype.target_mask(a["train"][0]["input"]) == prototype.target_mask(a["train"][1]["input"])
    assert a["train"][0]["output"] != a["train"][1]["output"]

    # Changing the seed permutes role colors without changing the intended
    # intermediate geometry or answer shape for a fixed profile.
    b = prototype.generate(6, {"closure_axis": "row"}, demos=2, queries=4)
    assert a["train"][0]["input"] != b["train"][0]["input"]
    assert a["train"][0]["output"] == b["train"][0]["output"]




def test_minimum_lesson_exercises_overlap_before_extra(prototype):
    for index, axis in ((0, "row"), (1, "column")):
        table = prototype.score_candidates(prototype.sample_input(11, "train", index), axis)
        best_overlap = table[0]["overlap"]
        assert any(
            0 < row["overlap"] < best_overlap
            for row in table[1:]
        ), f"minimum {axis} lesson needs a positive-but-partial overlap rival"

def test_minimum_lesson_teaches_color_tie_break_for_both_axes(prototype):
    def reverse_tie_output(grid, axis):
        rows = sorted(
            prototype.score_candidates(grid, axis),
            key=lambda row: (-row["overlap"], row["extra"], -row["color"]),
        )
        cells = rows[0]["closed"]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        output = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
        for row, col in cells:
            output[row - r0][col - c0] = 8
        return output

    for axis in ("row", "column"):
        episode = prototype.generate(5, {"closure_axis": axis}, demos=2, queries=4)
        assert any(
            reverse_tie_output(pair["input"], axis) != pair["output"]
            for pair in episode["train"]
        ), f"the two-demo {axis} lesson leaves reverse color tie-break alive"

def test_tie_break_branch_is_observable(prototype):
    grid = prototype.sample_input(31, "train", 2)
    table = prototype.score_candidates(grid, "row")
    winner = table[0]
    tied = [row for row in table[1:] if row["overlap"] == winner["overlap"] and row["extra"] == winner["extra"]]
    assert tied, "profile 2 must exercise the canonical color tie-break"
    assert winner["color"] < min(row["color"] for row in tied)
    assert any(row["closed"] != winner["closed"] for row in tied)


def test_30_square_query_is_substantive_and_boundary_touching(prototype):
    grid = prototype.sample_input(41, "test", 3)
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    assert len(occupied) >= 100
    assert {r // 15 * 2 + c // 15 for r, c in occupied} == {0, 1, 2, 3}
    assert any(r == 0 for r, _ in occupied)
    assert any(r == 29 for r, _ in occupied)
    assert any(c == 0 for _, c in occupied)
    assert any(c == 29 for _, c in occupied)


def test_native_worker_proves_two_demo_identification_with_protected_racket():
    contract = json.loads(CONTRACT.read_text())
    jobs = [
        {"seed": seed, "settings": {"closure_axis": axis}, "demos": 2, "queries": 4}
        for seed in (0, 17)
        for axis in ("row", "column")
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert [check["survivors"] for check in result["checks"]] == [[job["settings"]] for job in jobs]
    assert result["racket_evaluations"] == 32


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"queries": True},
        {"settings": {}},
        {"settings": {"closure_axis": "diagonal"}},
        {"settings": {"closure_axis": "row", "extra": 1}},
    ],
)
def test_invalid_requests_are_rejected(prototype, patch):
    kwargs = {"seed": 0, "settings": {"closure_axis": "row"}, "demos": 3, "queries": 4}
    kwargs.update(patch)
    with pytest.raises(ValueError):
        prototype.generate(**kwargs)


def test_adversarial_probe_writes_a_verified_report(tmp_path):
    out = tmp_path / "nested" / "probe"
    completed = subprocess.run(
        [sys.executable, str(PROBE), "--out", str(out)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((out / "report.json").read_text())
    assert report["status"] == "passed"
    assert report["racket"]["protected"] is True
    assert report["minimum_demo_count"] == 2
    assert report["semantic_seed_count"] == 128
    assert report["semantic_shortcut_survivors"] == []
    assert report["sampler_audit"] == {
        "axis_differences": 3328,
        "count_cases": 4,
        "episodes": 1024,
        "failures": [],
        "matched_input_pairs": 3328,
        "seeds": 128,
    }
    assert report["first_turn_private_invariance"] is True
    assert report["thirty_square_checked"] is True
