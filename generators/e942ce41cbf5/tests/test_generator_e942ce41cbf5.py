"""Focused semantic and distribution regressions for e942ce41cbf5."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "e942ce41cbf5"
REPO = find_root(__file__)
_SPEC = importlib.util.spec_from_file_location(
    f"generator_{TASK_ID}", REPO / "generators" / TASK_ID / "generator.py"
)
assert _SPEC and _SPEC.loader
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)
CANONICAL_SHAPES = {(10, 11), (10, 13), (11, 11), (11, 12)}


def _canonical_task() -> dict:
    pairs = canonical_pairs(TASK_ID, root=REPO, variant=0)
    train = [
        {"input": pair["input"], "output": pair["output"]}
        for pair in pairs
        if pair["split"] == "train"
    ]
    test = [
        {"input": pair["input"], "output": pair["output"]}
        for pair in pairs
        if pair["split"] == "test"
    ]
    assert len(test) == 1
    return {"train": train, "test": test[0]}


def _control(grid, colors: tuple[int, ...]) -> int:
    hits = [value for row in grid for value in row if value in colors]
    assert len(hits) == 1
    return hits[0]


def _replace_corner_control(grid, *, op: int | None = None, transform: int | None = None):
    out = copy.deepcopy(grid)
    if op is not None:
        out[-1][0] = op
    if transform is not None:
        out[-1][-1] = transform
    return out


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for nxt in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def test_rule_hash_and_python_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == "7aa66cd7d9ab"
    task = _canonical_task()
    pairs = list(task["train"]) + [task["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_public_override_contract_is_exact_recoverable_and_rejects_typos():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "op_control", "transform_control"}
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()

    for band in ("easy", "medium", "hard"):
        for h in (10, 11):
            for w in (11, 12, 13):
                for op in (3, 4, 6):
                    for transform in (7, 8, 9):
                        requested = {
                            "grid_h": h,
                            "grid_w": w,
                            "op_control": op,
                            "transform_control": transform,
                        }
                        grid = GEN.generate(1200 + h + w, op * 10 + transform, difficulty=band, **requested)
                        assert GEN.self_check(grid, meta={"overrides": requested}) == []
                        assert GEN.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=1)


def test_every_three_demo_window_covers_all_operation_and_transform_controls():
    assert GEN.EXAMPLES_NEEDED == 3
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(9):
                grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(3)]
                assert {_control(grid, (3, 4, 6)) for grid in grids} == {3, 4, 6}
                assert {_control(grid, (7, 8, 9)) for grid in grids} == {7, 8, 9}


def test_generated_inputs_are_sparse_connected_canonical_scale_and_controls_matter():
    seen_profiles: set[tuple[int, int, int]] = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(10):
            for sample_index in range(9):
                grid = GEN.generate(10000 + seed, sample_index, difficulty=band)
                h, w = len(grid), len(grid[0])
                assert (h, w) in CANONICAL_SHAPES
                assert GEN.self_check(grid) == []
                assert set(value for row in grid for value in row) == {
                    0,
                    1,
                    2,
                    _control(grid, (3, 4, 6)),
                    _control(grid, (7, 8, 9)),
                }
                blue = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
                red = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
                assert 4 <= len(blue) <= 8
                assert 4 <= len(red) <= 8
                assert _connected(blue)
                assert _connected(red)

                op_outputs = {
                    tuple(map(tuple, GEN.rule_mirror(_replace_corner_control(grid, op=op))))
                    for op in (3, 4, 6)
                }
                transform_outputs = {
                    tuple(map(tuple, GEN.rule_mirror(_replace_corner_control(grid, transform=tr))))
                    for tr in (7, 8, 9)
                }
                assert len(op_outputs) == 3
                assert len(transform_outputs) == 3
                seen_profiles.add((h, w, len(blue) + len(red)))
    assert len(seen_profiles) >= 8


def test_exact_corner_controls_are_required_and_structural_impostors_are_rejected():
    grid = GEN.generate(404, 5, difficulty="medium")
    assert GEN.self_check(grid) == []

    missing_transform = copy.deepcopy(grid)
    missing_transform[-1][-1] = 0
    assert GEN.self_check(missing_transform)

    moved_op = copy.deepcopy(grid)
    moved_op[-2][0], moved_op[-1][0] = moved_op[-1][0], 0
    assert GEN.self_check(moved_op)

    duplicate_transform = copy.deepcopy(grid)
    duplicate_transform[0][-1] = duplicate_transform[-1][-1]
    assert GEN.self_check(duplicate_transform)

    unknown_color = copy.deepcopy(grid)
    unknown_color[0][0] = 5
    assert GEN.self_check(unknown_color)


def test_three_demos_identify_all_named_rivals_for_every_schedule_residue():
    assert len(GEN.LESSON_COMPETITORS) >= 6
    for band in ("easy", "medium", "hard"):
        for seed in range(9):
            for start in range(6):
                pairs = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                    grid = GEN.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
                demos, query = pairs[:-1], pairs[-1]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_missing_identity_branch_shortcut_fits_canonical_train_but_generated_cases_kill_it():
    task = _canonical_task()
    shortcut = GEN.CANONICAL_SHORTCUTS["control_7_as_rotate_cw"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in task["train"])
    assert shortcut(task["test"]["input"]) != task["test"]["output"]

    witnesses = [
        GEN.generate(seed, sample_index, difficulty="medium")
        for seed in range(8)
        for sample_index in range(6)
        if _control(GEN.generate(seed, sample_index, difficulty="medium"), (7, 8, 9)) == 7
    ]
    assert witnesses
    assert all(shortcut(grid) != GEN.rule_mirror(grid) for grid in witnesses)


def test_shortcut_probe_reports_canonical_ambiguity_and_generated_refutation():
    probe = REPO / "generators" / TASK_ID / "workspace" / "shortcut_probe.py"
    completed = subprocess.run(
        [sys.executable, str(probe), "--json", "--seeds", "3", "--windows", "2"],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["rule_hash"] == GEN.RULE_HASH
    shortcut = report["canonical_shortcuts"]["control_7_as_rotate_cw"]
    assert shortcut["fits_all_demonstrations"] is True
    assert shortcut["disagrees_on_query"] is True
    assert report["generated_lessons"]["lessons_checked"] == 18
    assert report["generated_lessons"]["unidentifiable_lessons"] == []
    assert report["generated_lessons"]["surviving_rivals"] == {}
