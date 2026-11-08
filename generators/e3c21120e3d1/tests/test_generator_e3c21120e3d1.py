"""Task-local contract tests for the e3c21120e3d1 transpose curriculum."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "e3c21120e3d1"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _palette_without_background(grid):
    return {value for row in grid for value in row if value != 0}


def _label(grid):
    return {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_rule_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "f5d00e3992ee"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_colors"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=[f"{pair['split']}{pair['pair_index']}" for pair in PAIRS],
)
def test_canonical_pairs_are_owned_and_python_mirror_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(3, 3), (3, 8), (8, 3), (8, 8)])
@pytest.mark.parametrize("n_colors", [1, 2])
def test_all_boundary_overrides_are_exact_and_composable(band, grid_h, grid_w, n_colors):
    options = {"grid_h": grid_h, "grid_w": grid_w, "n_colors": n_colors}
    grid = gen.generate(1701, 29, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert len(_palette_without_background(grid)) == n_colors
    assert gen.rule_mirror(grid) != grid
    for rival in gen.SEMANTIC_RIVALS.values():
        assert rival(grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 2},
        {"grid_w": 9},
        {"n_colors": 0},
        {"n_colors": 3},
        {"grid_h": True},
        {"grid_w": 4.0},
        {"n_colors": "2"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_curriculum_covers_all_canonical_profiles_and_morphologies(band):
    grids = [gen.generate(3307, index, difficulty=band) for index in range(4)]
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids
    }
    assert profiles == {(3, 8, 2), (4, 7, 3), (5, 6, 3), (6, 4, 3)}
    assert {gen.semantic_observables(grid)["morphology"] for grid in grids} == {
        "mono_points",
        "two_blobs",
        "blob_plus_points",
    }


def test_difficulty_is_live_but_replay_is_deterministic_and_fresh():
    outputs = [gen.generate(812, 5, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in outputs}) == 3
    first = gen.generate(812, 5, difficulty="hard")
    second = gen.generate(812, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(812, 5, difficulty="hard")


def test_generation_does_not_touch_module_global_random_state():
    random.seed(9917)
    before = random.getstate()
    gen.generate(12, 7, difficulty="medium")
    assert random.getstate() == before


def test_every_declared_witness_is_a_real_counterexample():
    grids = [gen.generate(404, index, difficulty="medium") for index in range(4)]
    for witness, rival_names in gen.WITNESS_RIVALS.items():
        matching = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness](grid)]
        assert matching, witness
        for grid in matching:
            for rival_name in rival_names:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)


def test_three_demo_lessons_refute_all_declared_d4_competitors_under_rotations():
    pairs = [_label(gen.generate(6001, index, difficulty="hard")) for index in range(4)]
    for query_index in range(4):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[0, 0, 0] for _ in range(3)],
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
    ],
)
def test_validator_rejects_malformed_or_uninformative_inputs_without_crashing(grid):
    assert gen.self_check(grid)


def test_reusable_review_probe_covers_exact_axes_and_rotated_lessons(tmp_path):
    probe = HOME / "workspace" / "review_probe.py"
    assert probe.exists(), "workspace/review_probe.py is missing"
    out = tmp_path / "probe.json"
    env = os.environ.copy()
    repo_root = find_root(__file__)
    env["PYTHONPATH"] = str(repo_root / "shared" / "runtime")
    completed = subprocess.run(
        [
            sys.executable,
            str(probe),
            "--seeds-per-case",
            "1",
            "--lesson-starts",
            "4",
            "--out",
            str(out),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(out.read_text())
    assert payload["status"] == "pass"
    assert payload["summary"] == {
        "canonical_pairs": 4,
        "competitors": 7,
        "lesson_queries": 64,
        "override_cases": 288,
    }
    assert payload["failures"] == []
    assert payload["limitations"]
