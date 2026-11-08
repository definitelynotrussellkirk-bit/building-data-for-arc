"""Task-local contract tests for the efdd2b265cc8 transpose curriculum."""
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


TASK_ID = "efdd2b265cc8"
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
    assert set(gen.AXES) == {"grid_size", "n_colors"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=[f"{pair['split']}{pair['pair_index']}" for pair in PAIRS],
)
def test_canonical_pairs_are_accepted_and_python_mirror_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_size", [4, 5, 6])
@pytest.mark.parametrize("n_colors", [2, 3, 4])
def test_all_exact_overrides_are_composable(band, grid_size, n_colors):
    options = {"grid_size": grid_size, "n_colors": n_colors}
    grid = gen.generate(1701, 29, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert len(grid) == grid_size
    assert all(len(row) == grid_size for row in grid)
    assert len(_palette_without_background(grid)) == n_colors


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_curriculum_covers_all_canonical_profiles(band):
    grids = [gen.generate(3307, index, difficulty=band) for index in range(4)]
    observed = {
        (
            len(grid),
            len(_palette_without_background(grid)),
            gen.semantic_observables(grid)["morphology"],
        )
        for grid in grids
    }
    assert observed == {
        (4, 3, "three_points"),
        (5, 2, "blob_plus_point"),
        (5, 4, "four_points"),
        (6, 2, "two_triads"),
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_size": 3},
        {"grid_size": 7},
        {"n_colors": 1},
        {"n_colors": 5},
        {"grid_size": True},
        {"grid_size": 5.0},
        {"n_colors": "2"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


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


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[0, 0, 0, 0] for _ in range(4)],
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        [[1, 1, 1, 1] for _ in range(4)],
    ],
)
def test_validator_rejects_malformed_or_uninformative_inputs_without_crashing(grid):
    assert gen.self_check(grid)


def test_every_declared_witness_is_a_real_counterexample():
    grids = [gen.generate(404, index, difficulty="medium") for index in range(4)]
    for witness, rival_names in gen.WITNESS_RIVALS.items():
        matching = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness](grid)]
        assert matching, witness
        for grid in matching:
            for rival_name in rival_names:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)
    for witness in gen.BRANCH_WITNESSES:
        assert any(gen.SEMANTIC_WITNESSES[witness](grid) for grid in grids), witness


def test_three_demo_lessons_refute_all_declared_d4_competitors_under_rotations():
    pairs = [_label(gen.generate(6001, index, difficulty="hard")) for index in range(4)]
    for query_index in range(4):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


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
    assert payload["task_id"] == TASK_ID
    assert payload["status"] == "pass"
    assert payload["summary"] == {
        "canonical_pairs": 4,
        "competitors": 7,
        "lesson_queries": 64,
        "override_cases": 36,
    }
    assert payload["failures"] == []
    assert payload["limitations"]

