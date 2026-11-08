"""Focused semantic regressions for ARC generator 6d095613d305."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest


TASK = "6d095613d305"
HERE = Path(__file__).resolve()


def _repo_root() -> Path:
    for parent in HERE.parents:
        if (parent / "shared/data/canonical/puzzles.jsonl").is_file():
            return parent
        if (parent / "data/canonical/puzzles.jsonl").is_file():
            return parent
    raise AssertionError("could not locate canonical puzzle ledger")


ROOT = _repo_root()
if (ROOT / "shared/runtime").is_dir():
    sys.path.insert(0, str(ROOT / "shared/runtime"))

try:
    GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
except ModuleNotFoundError:
    module_path = ROOT / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK}", module_path)
    assert spec and spec.loader
    GEN = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = GEN
    spec.loader.exec_module(GEN)


def _canonical_path() -> Path:
    source = ROOT / "shared/data/canonical/puzzles.jsonl"
    return source if source.is_file() else ROOT / "data/canonical/puzzles.jsonl"


def _canonical_row() -> dict:
    with _canonical_path().open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError(f"missing canonical row for {TASK}")


def _grid(value) -> list[list[int]]:
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def _pairs() -> list[dict]:
    row = _canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def _frozen(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _pair(grid) -> dict:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_authority_canonical_pairs_and_python_mirror_are_exact():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    assert GEN.RULE_HASH == "bd682e817aa3"

    for pair in _pairs():
        grid = _grid(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == _grid(pair["output"])
        assert grid == snapshot


def test_declared_axis_boundaries_and_profiles_are_exactly_observable():
    cases = [
        ("grid_h", 8),
        ("grid_h", 18),
        ("grid_w", 9),
        ("grid_w", 20),
        ("points_per_color", 3),
        ("points_per_color", 5),
        ("crossing_profile", "separated"),
        ("crossing_profile", "single"),
        ("crossing_profile", "multiple"),
    ]
    for band in ("easy", "medium", "hard"):
        for axis, value in cases:
            grid = GEN.generate(7601, 17, difficulty=band, **{axis: value})
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid)[axis] == value

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)


def test_each_three_demo_window_covers_profiles_and_refutes_every_named_rival():
    expected_profiles = set(GEN.SCHEDULE_PROFILES)
    expected_rivals = {
        "vertical_first",
        "column_major_order",
        "first_to_last_only",
        "overlap_as_later_color",
    }
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals

    for start in range(12):
        demos = [_pair(GEN.generate(911, start + i, difficulty="medium")) for i in range(3)]
        query = _pair(GEN.generate(911, start + 3, difficulty="medium"))
        profiles = {
            GEN.observe_overrides(pair["input"])["crossing_profile"]
            for pair in demos
        }
        assert profiles == expected_profiles
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_every_ordinary_draw_teaches_order_bend_and_all_waypoint_use():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for profile in GEN.SCHEDULE_PROFILES:
                grid = GEN.generate(
                    seed,
                    seed + 31,
                    difficulty=band,
                    crossing_profile=profile,
                )
                truth = GEN.rule_mirror(grid)
                obs = GEN.observe_overrides(grid)
                assert obs["crossing_profile"] == profile
                assert GEN.self_check(grid) == []
                assert GEN.LESSON_COMPETITORS["vertical_first"](grid) != truth
                assert GEN.LESSON_COMPETITORS["column_major_order"](grid) != truth
                assert GEN.LESSON_COMPETITORS["first_to_last_only"](grid) != truth
                if profile == "separated":
                    assert obs["overlap_cells"] == 0
                elif profile == "single":
                    assert obs["overlap_cells"] == 1
                    assert GEN.LESSON_COMPETITORS["overlap_as_later_color"](grid) != truth
                else:
                    assert obs["overlap_cells"] >= 2
                    assert GEN.LESSON_COMPETITORS["overlap_as_later_color"](grid) != truth


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]

    frozen = _frozen(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(20)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(20)}
    assert len(by_seed) >= 18
    assert len(by_index) >= 18


def test_self_check_rejects_structural_and_semantic_impostors_without_mutation():
    cases = {
        "empty": [],
        "ragged": [[0, 1], [0]],
        "bad_color": [[10] * 9 for _ in range(8)],
        "reserved_nine": [[9] + [0] * 8] + [[0] * 9 for _ in range(7)],
        "one_color": [[0] * 9 for _ in range(8)],
        "two_points_each": [[0] * 9 for _ in range(8)],
    }
    cases["one_color"][1][1] = cases["one_color"][3][4] = cases["one_color"][6][7] = 4
    cases["two_points_each"][1][1] = cases["two_points_each"][5][6] = 4
    cases["two_points_each"][2][7] = cases["two_points_each"][6][2] = 6

    for name, grid in cases.items():
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot


def test_rule_mirror_returns_fresh_rows_and_never_aliases_input():
    grid = GEN.generate(999, 2, difficulty="easy")
    output = GEN.rule_mirror(grid)
    snapshot = copy.deepcopy(output)
    output[0][0] = 9 if output[0][0] != 9 else 8
    assert GEN.rule_mirror(grid) == snapshot
    assert output is not grid
    assert all(out_row is not in_row for out_row, in_row in zip(output, grid))


def test_reusable_curriculum_probe_audits_declared_rivals_and_cyclic_windows():
    script = ROOT / "generators" / TASK / "workspace" / "curriculum_probe.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--seed-start",
            "0",
            "--seed-count",
            "2",
            "--bands",
            "easy",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["task_id"] == TASK
    assert report["sample_spec"]["lesson_starts"] == [0, 1, 2]
    assert report["counts"]["unique_draws"] == 12
    assert report["counts"]["lesson_windows"] == 6
    assert report["counts"]["failed_windows"] == 0
    assert set(report["rival_witness_counts"]) == set(GEN.LESSON_COMPETITORS)
    assert all(value > 0 for value in report["rival_witness_counts"].values())
