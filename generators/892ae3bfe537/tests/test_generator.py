"""Regression tests for the color-pair rectangle curriculum."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

TASK = "892ae3bfe537"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK}", TASK_ROOT / "generator.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return [*row["train"], *row["test"]]
    raise AssertionError(f"canonical task {TASK} missing")


def _shape(grid):
    return len(grid), len(grid[0])


def _nonzero_colors(grid):
    return {value for row in grid for value in row if value != 0}


@pytest.mark.parametrize("pair", _canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_in_domain_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen._fill_pairs(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "band,expected",
    [("easy", (6, 9, 2)), ("medium", (8, 8, 2)), ("hard", (10, 10, 3))],
)
def test_default_curriculum_anchors_a_canonical_profile_in_every_band(band, expected):
    seen = set()
    for seed in range(32):
        grid = gen.generate(seed, seed * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert (_shape(grid)[0], _shape(grid)[1], observed["n_pairs"]) == expected
        seen.add(tuple(tuple(row) for row in grid))
    assert len(seen) >= 24


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [6, 7, 10])
@pytest.mark.parametrize("grid_w", [8, 9, 10])
@pytest.mark.parametrize("n_pairs", [2, 3])
def test_every_advertised_override_is_exact_observable_and_constructive(
    band, grid_h, grid_w, n_pairs
):
    requested = {"grid_h": grid_h, "grid_w": grid_w, "n_pairs": n_pairs}
    grid = gen.generate(193, 17, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen._fill_pairs(grid) != grid


@pytest.mark.parametrize(
    "override",
    [
        {"typo": 1},
        {"grid_h": 5},
        {"grid_h": 11},
        {"grid_w": 7},
        {"grid_w": 11},
        {"n_pairs": 1},
        {"n_pairs": 4},
        {"grid_h": 6.0},
        {"grid_w": True},
        {"n_pairs": "2"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(override):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **override)


def test_unbanded_schedule_covers_all_canonical_profiles():
    profiles = set()
    for index in range(90):
        grid = gen.generate(911, index, difficulty=None)
        observed = gen.observe_overrides(grid)
        profiles.add((len(grid), len(grid[0]), observed["n_pairs"]))
    assert profiles == {(6, 9, 2), (8, 8, 2), (10, 10, 3)}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_exercise_all_rule_critical_branches(band):
    for index in range(40):
        grid = gen.generate(800 + index, index, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["collinear_pair"](grid)
        assert gen.SEMANTIC_WITNESSES["area_pair"](grid)
        assert gen.SEMANTIC_WITNESSES["solid_interior"](grid)
        authority = gen._fill_pairs(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != authority, name


def test_two_demo_lesson_refutes_every_declared_competitor():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(77, index, difficulty="medium")
        demos.append({"input": grid, "output": gen._fill_pairs(grid)})
    query = gen.generate(78, 99, difficulty="medium")
    assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_count_and_bbox_overlap_impostors():
    wrong_count = [[0] * 8 for _ in range(6)]
    wrong_count[0][0] = 2
    assert gen.self_check(wrong_count)

    overlap = [[0] * 8 for _ in range(6)]
    overlap[0][0] = overlap[4][4] = 2
    overlap[0][4] = overlap[4][0] = 3
    assert any("overlap" in reason for reason in gen.self_check(overlap))


def test_deterministic_bytes_and_color_count_contract():
    first = gen.generate(412, 31, difficulty="hard")
    assert first == gen.generate(412, 31, difficulty="hard")
    for color in _nonzero_colors(first):
        assert sum(value == color for row in first for value in row) == 2
    assert len(_nonzero_colors(first)) == 3
