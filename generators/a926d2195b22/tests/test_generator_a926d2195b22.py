"""Contract and semantic-regression tests for a926d2195b22."""
from __future__ import annotations

from collections import Counter
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


TASK_ID = "a926d2195b22"
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


def _label(grid):
    return {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}


def _components(grid):
    return gen._components(grid)


def _palette_size(grid):
    return len({value for row in grid for value in row})


def test_rule_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "eb3b09c1bddc"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "num_objects",
        "smallest_size",
        "minimum_count",
    }
    assert not gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0


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


def test_strongest_canonical_shortcut_really_fits_all_official_pairs():
    rival = gen.CANONICAL_SHORTCUTS["rarest_color"]
    assert len(PAIRS) == 5
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [8, 13])
@pytest.mark.parametrize("grid_w", [8, 14])
@pytest.mark.parametrize("num_objects", [3, 5])
@pytest.mark.parametrize("smallest_size", [1, 3])
@pytest.mark.parametrize("minimum_count", [1, 2])
def test_all_boundary_overrides_are_exact_and_composable(
    band, grid_h, grid_w, num_objects, smallest_size, minimum_count
):
    options = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "num_objects": num_objects,
        "smallest_size": smallest_size,
        "minimum_count": minimum_count,
    }
    grid = gen.generate(1701, 29, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": options}) == []
    assert gen.observe_overrides(grid) == options
    assert gen.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 7},
        {"grid_h": 14},
        {"grid_w": 7},
        {"grid_w": 15},
        {"num_objects": 2},
        {"num_objects": 6},
        {"smallest_size": 0},
        {"smallest_size": 4},
        {"minimum_count": 0},
        {"minimum_count": 3},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"num_objects": "3"},
        {"smallest_size": False},
        {"minimum_count": 1.0},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("seed,sample_index", [(True, 0), (1.0, 0), ("1", 0), (0, True), (0, 1.0), (0, "1"), (0, -1)])
def test_seed_and_sample_index_are_strict(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


def test_negative_fixtures_are_explicit_invalid_examples_only():
    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(0, 0, texture=texture)
        assert gen.self_check(grid), texture
    with pytest.raises(ValueError):
        gen.generate(0, 0, texture="warm")
    with pytest.raises(ValueError):
        gen.generate(0, 0, texture=gen.DEGENERATE_TEXTURES[0], grid_h=8)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_curriculum_covers_every_canonical_profile_and_both_palette_modes(band):
    grids = [gen.generate(3307, index, difficulty=band) for index in range(20)]
    profiles = {
        (len(grid), len(grid[0]), len(_components(grid)))
        for grid in grids
    }
    assert profiles == {(9, 10, 4), (10, 10, 3), (8, 12, 4), (9, 11, 3), (10, 12, 4)}
    palette_gaps = {
        len(_components(grid)) + 1 - _palette_size(grid)
        for grid in grids
    }
    assert palette_gaps == {0, 1}
    assert {min(len(obj["cells"]) for obj in _components(grid)) for grid in grids} >= {1, 2, 3}


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


def test_generation_is_independent_of_python_hash_seed(tmp_path):
    script = (
        "import json; import generator as g; "
        "print(json.dumps(g.generate(717, 9, difficulty='hard')))"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(HOME), str(find_root(__file__) / "shared" / "runtime")]
    )
    outputs = []
    for hash_seed in ("1", "999"):
        run_env = dict(env, PYTHONHASHSEED=hash_seed)
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=HOME,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        outputs.append(completed.stdout)
    assert outputs[0] == outputs[1]


def test_every_declared_witness_is_a_real_counterexample():
    grids = [gen.generate(404, index, difficulty="medium") for index in range(4)]
    for witness, rival_names in gen.WITNESS_RIVALS.items():
        matching = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness](grid)]
        assert matching, witness
        for grid in matching:
            for rival_name in rival_names:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)


def test_three_demo_lessons_refute_all_declared_competitors_under_rotations():
    pairs = [_label(gen.generate(6001, index, difficulty="hard")) for index in range(4)]
    for query_index in range(4):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


def test_tie_policy_recolors_only_the_row_major_first_minimum():
    grid = gen.generate(
        90,
        2,
        grid_h=8,
        grid_w=8,
        num_objects=3,
        smallest_size=1,
        minimum_count=2,
    )
    objects = sorted(_components(grid), key=lambda obj: (obj["size"], obj["first"]))
    assert objects[0]["size"] == objects[1]["size"] == 1
    expected = deepcopy(grid)
    for row, col in objects[0]["cells"]:
        expected[row][col] = 9
    assert gen.rule_mirror(grid) == expected
    assert gen.SEMANTIC_RIVALS["all_minima"](grid) != expected


def test_repeated_color_witness_kills_global_color_frequency_shortcut():
    grids = [gen.generate(91, index, difficulty="medium") for index in (0, 1)]
    for grid in grids:
        counts = Counter(value for row in grid for value in row if value)
        assert len(counts) < len(_components(grid))
        assert gen.SEMANTIC_RIVALS["rarest_color"](grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_four_example_cycle_has_two_nonfirst_target_witnesses(band):
    for seed in (0, 1, 404, 6001):
        grids = [gen.generate(seed, index, difficulty=band) for index in range(4)]
        disagreements = [
            gen.SEMANTIC_RIVALS["first_component"](grid) != gen.rule_mirror(grid)
            for grid in grids
        ]
        assert sum(disagreements) >= 2, (band, seed, disagreements)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[0, 0, 0] for _ in range(3)],
        [[9, 0, 0], [0, 1, 0], [0, 0, 2]],
        [[1, 1], [1, 1]],
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
        "canonical_pairs": 5,
        "competitors": 3,
        "lesson_queries": 64,
        "override_cases": 128,
    }
    assert payload["failures"] == []
    assert payload["limitations"]
    assert any(
        "3 declared executable rivals" in limitation
        for limitation in payload["limitations"]
    )


def test_retained_rarest_color_counterexample_is_executable_and_source_bound():
    path = HOME / "counterexamples" / "rarest_color_shortcut.json"
    payload = json.loads(path.read_text())
    assert payload["task_id"] == TASK_ID
    assert payload["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(payload["input"]) == []
    assert gen.rule_mirror(payload["input"]) == payload["intended_output"]
    assert gen.CANONICAL_SHORTCUTS["rarest_color"](payload["input"]) == payload["rival_output"]
    assert payload["intended_output"] != payload["rival_output"]
