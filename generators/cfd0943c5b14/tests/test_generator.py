"""Task-local regression suite for the diagonal-X generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    boundary_kind,
    canonical_pairs,
    canonical_shortcut_fits,
    ignored_boundary_output,
    ignored_cyan_output,
    load_generator,
    observed,
    only_color_three_output,
    overlapping_pair_count,
    seeds,
    x_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs()
SCENES = ("canonical", "edge_seed", "mixed_overlap", "corner_seed", "cyan_interior")


def labeled(grid):
    return {"input": deepcopy(grid), "output": x_output(grid)}


def test_rule_hash_and_independent_oracle_bind_all_canonical_pairs():
    assert gen.RULE_HASH == "6e86df413712"
    assert len(PAIRS) == 3
    for pair in PAIRS:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
        assert x_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("scene", SCENES)
def test_every_advertised_joint_override_is_exact_and_recoverable(band, scene):
    options = {"grid_h": 6, "grid_w": 7, "seed_count": 5, "scene": scene}
    grid = gen.generate(91, 13, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(91, 13, difficulty=band, **options)


@pytest.mark.parametrize(
    "options",
    [
        {"typo": 1},
        {"grid_h": 5},
        {"grid_h": 13},
        {"grid_w": True},
        {"grid_w": 7.0},
        {"seed_count": 1},
        {"seed_count": 6},
        {"seed_count": "3"},
        {"scene": "not-a-scene"},
        {"scene": 8},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("scene", SCENES)
def test_each_scene_has_an_unmistakable_pixel_signature(scene):
    grid = gen.generate(313, 7, grid_h=8, grid_w=9, seed_count=4, scene=scene)
    pts = seeds(grid)
    kinds = [boundary_kind(grid, r, c) for r, c, _value in pts]
    colors = {value for _r, _c, value in pts}
    assert observed(grid)["scene"] == scene
    if scene == "canonical":
        assert colors == {3}
        assert set(kinds) == {"interior"}
    elif scene == "edge_seed":
        assert 8 not in colors
        assert kinds.count("edge") == 1 and kinds.count("corner") == 0
    elif scene == "corner_seed":
        assert 8 not in colors
        assert kinds.count("corner") == 1 and kinds.count("edge") == 0
    elif scene == "cyan_interior":
        assert colors == {8}
        assert set(kinds) == {"interior"}
    else:
        assert 8 in colors and len(colors) >= 2
        assert set(kinds) == {"interior"}
        assert overlapping_pair_count(grid) >= 1


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_five_scene_schedule_is_rotation_safe(band):
    for start in range(12):
        grids = [gen.generate(20261005, start + offset, difficulty=band) for offset in range(5)]
        assert [observed(grid)["scene"] for grid in grids] == [
            SCENES[(start + offset) % len(SCENES)] for offset in range(5)
        ]
        for held_out in range(5):
            demos = [labeled(grid) for index, grid in enumerate(grids) if index != held_out]
            query = labeled(grids[held_out])
            assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name



def test_default_distribution_introduces_cyan_on_a_canonical_majority():
    grids = [gen.generate(20261005, index) for index in range(25)]
    assert sum(8 not in {value for row in grid for value in row} for grid in grids) == 15

def test_declared_canonical_shortcuts_really_fit_canonical_and_are_refuted():
    assert canonical_shortcut_fits() == {
        "ignore_cyan_seed": True,
        "ignore_boundary_seeds": True,
        "only_color_three": True,
    }
    expected = {
        "ignore_cyan_seed": ignored_cyan_output,
        "ignore_boundary_seeds": ignored_boundary_output,
        "only_color_three": only_color_three_output,
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(expected)
    grids = [gen.generate(77, index) for index in range(5)]
    intended = [x_output(grid) for grid in grids]
    for name, independent in expected.items():
        rival = gen.CANONICAL_SHORTCUTS[name]
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in PAIRS)
        assert any(rival(deepcopy(grid)) != out for grid, out in zip(grids, intended))
        assert all(rival(deepcopy(grid)) == independent(grid) for grid in grids)


def test_semantic_witness_claims_have_real_counterexamples():
    grids = [gen.generate(404, index) for index in range(5)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        matching = [grid for grid in grids if witness(deepcopy(grid))]
        assert matching, witness_name
        if witness_name in gen.WITNESS_RIVALS:
            rival_names = gen.WITNESS_RIVALS[witness_name]
            if isinstance(rival_names, str):
                rival_names = [rival_names]
            for grid in matching:
                assert any(
                    gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != x_output(grid)
                    for name in rival_names
                )


def test_self_check_rejects_malformed_and_semantically_destructive_inputs():
    malformed = (None, [], [[]], [[0], [0, 1]], [[True] * 6 for _ in range(6)])
    for grid in malformed:
        assert gen.self_check(grid)

    blank = [[0] * 6 for _ in range(6)]
    singleton = deepcopy(blank)
    singleton[2][2] = 3
    orthogonal = deepcopy(blank)
    orthogonal[2][2] = 3
    orthogonal[2][3] = 3
    two_boundaries = deepcopy(blank)
    two_boundaries[0][2] = 8
    two_boundaries[5][3] = 8
    unclassified_palette = deepcopy(blank)
    unclassified_palette[2][1] = 3
    unclassified_palette[3][4] = 4
    for grid in (blank, singleton, orthogonal, two_boundaries, unclassified_palette):
        assert gen.self_check(grid)


def test_generated_inputs_are_deterministic_and_do_not_touch_global_random_state():
    random.seed(418)
    before = random.getstate()
    first = [gen.generate(808, index, difficulty="hard") for index in range(16)]
    assert random.getstate() == before
    assert first == [gen.generate(808, index, difficulty="hard") for index in range(16)]
    assert len({repr(grid) for grid in first}) == len(first)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_workspace_contract_probe_covers_distribution_and_cyclic_lessons():
    import importlib.util

    probe_path = HOME / "workspace" / "contract_probe.py"
    assert probe_path.exists(), "workspace contract probe has not been implemented"
    spec = importlib.util.spec_from_file_location("cfd0943c5b14_contract_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_probe(gen, draws_per_band=10, schedule_starts=10, seed=20261005)
    assert report["passed"] is True
    assert report["canonical_oracle_matches"] == len(PAIRS)
    assert report["draws"] == 30
    assert report["cyclic_rotations_checked"] == 150
    assert report["errors"] == []


@pytest.mark.parametrize("index", range(100))
def test_mixed_scene_cyan_seed_always_has_a_causal_output_pixel(index):
    grid = gen.generate(20261005 + index, index, difficulty="hard", scene="mixed_overlap")
    assert ignored_cyan_output(grid) != x_output(grid)
