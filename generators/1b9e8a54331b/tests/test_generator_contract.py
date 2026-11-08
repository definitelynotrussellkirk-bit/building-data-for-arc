from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


TASK_ID = "1b9e8a54331b"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_row() -> dict:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _transform(grid, *, honor_walls: bool = True, crossing_color: int = 6):
    """Independent ray oracle used only for the two reported shortcut classes."""
    h, w = len(grid), len(grid[0])
    horizontal: set[tuple[int, int]] = set()
    vertical: set[tuple[int, int]] = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 2:
                horizontal.add((r, c))
                for dc in (-1, 1):
                    cc = c + dc
                    while 0 <= cc < w and (not honor_walls or grid[r][cc] != 5):
                        horizontal.add((r, cc))
                        cc += dc
            elif grid[r][c] == 1:
                vertical.add((r, c))
                for dr in (-1, 1):
                    rr = r + dr
                    while 0 <= rr < h and (not honor_walls or grid[rr][c] != 5):
                        vertical.add((rr, c))
                        rr += dr
    result = []
    for r in range(h):
        row = []
        for c in range(w):
            point = (r, c)
            if grid[r][c] == 5:
                value = 5
            elif point in horizontal and point in vertical:
                value = crossing_color
            elif point in horizontal:
                value = 7
            elif point in vertical:
                value = 8
            else:
                value = 0
            row.append(value)
        result.append(row)
    return result


def _pairs(seed: int, start: int, difficulty: str, count: int = 4):
    grids = [GEN.generate(seed, start + offset, difficulty=difficulty) for offset in range(count)]
    return [{"input": grid, "output": _transform(grid)} for grid in grids]


def test_rule_pin_and_python_mirror_match_every_canonical_pair() -> None:
    row = _canonical_row()
    normalized_rule = " ".join(row["program_solution"].split())
    assert GEN.RULE_HASH == "db20de981b4f"
    assert hashlib.sha256(normalized_rule.encode()).hexdigest()[:12] == GEN.RULE_HASH
    assert GEN.EXAMPLES_NEEDED == 3

    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_axes_accept_documented_boundaries_and_are_observable() -> None:
    requested = {
        "grid_h": 14,
        "grid_w": 14,
        "horizontal_seed_count": 2,
        "vertical_seed_count": 2,
        "block_axis": "vertical",
    }
    grid = GEN.generate(123, 4, difficulty="medium", **requested)
    assert len(grid) == 14
    assert len(grid[0]) == 14
    assert GEN.observe_overrides(grid) == requested
    assert GEN.self_check(grid) == []

    with pytest.raises((TypeError, ValueError), match="unknown|override"):
        GEN.generate(123, 4, __override_contract_unknown_axis__=1)


def test_reported_crossing_and_blocker_windows_are_no_longer_ambiguous() -> None:
    windows = [
        (7, 187, "easy"),  # prior no-crossing demonstrations
        (1, 2, "easy"),    # prior no-blocker demonstrations
    ]
    for seed, start, difficulty in windows:
        demos = _pairs(seed, start, difficulty)[:3]
        assert any(6 in row for pair in demos for row in pair["output"])
        assert any(
            _transform(pair["input"], honor_walls=False) != pair["output"]
            for pair in demos
        )
        assert any(
            _transform(pair["input"], crossing_color=7) != pair["output"]
            for pair in demos
        )


def test_sliding_three_demo_lessons_refute_declared_competitors() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = _pairs(17_071, start, difficulty)
            demos, query = pairs[:3], pairs[3]
            assert GEN.lesson_identifiable(demos, query) == [], (difficulty, start)
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    difficulty,
                    start,
                    name,
                )


def test_no_crossings_degenerate_really_has_no_crossing() -> None:
    grid = GEN.generate(99, 0, difficulty="medium", texture="no_crossings")
    assert GEN.self_check(grid, meta={"texture": "no_crossings"}) == []
    assert all(6 not in row for row in _transform(grid))


def test_five_consecutive_samples_do_not_collapse_to_duplicate_pairs() -> None:
    grids = [GEN.generate(0, index, difficulty="medium") for index in range(5)]
    fingerprints = {
        json.dumps({"input": grid, "output": GEN.rule_mirror(grid)}, separators=(",", ":"))
        for grid in grids
    }
    assert len(fingerprints) == 5


def test_semantic_contract_probe_emits_replayable_racket_batch(tmp_path) -> None:
    import subprocess
    import sys

    script = ROOT / "generators" / TASK_ID / "workspace" / "semantic_contract_probe.py"
    report = tmp_path / "report.json"
    inputs = tmp_path / "inputs.json"
    expected = tmp_path / "expected.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--report",
            str(report),
            "--inputs",
            str(inputs),
            "--expected",
            str(expected),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(report.read_text())
    replay_inputs = json.loads(inputs.read_text())["inputs"]
    replay_outputs = json.loads(expected.read_text())["outputs"]
    assert payload["status"] == "pass"
    assert payload["summary"]["ordinary_cases"] >= 30
    assert payload["summary"]["boundary_cases"] == 8
    assert len(replay_inputs) == len(replay_outputs) == 5
    assert replay_outputs == [GEN.rule_mirror(grid) for grid in replay_inputs]
