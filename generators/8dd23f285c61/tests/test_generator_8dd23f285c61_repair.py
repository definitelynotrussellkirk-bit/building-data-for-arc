from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import (  # noqa: E402
    audit,
    canonical_pairs,
    load_generator,
    observed,
    ray_output,
    racket_outputs,
    tiny_wall_witness,
    wall_components,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_pins_current_canonical_rule_and_declares_only_exact_axes():
    assert gen.RULE_HASH == "346b3beb0ce3"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_seeds", "n_wall_components"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    assert gen.strict_canonical_like(pair["input"]) == []
    assert ray_output(pair["input"]) == pair["output"]


def test_declared_shortcut_fits_every_canonical_pair_but_fails_exact_witness():
    rival = gen.CANONICAL_SHORTCUTS["ignore_tiny_walls"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = tiny_wall_witness()
    assert gen.strict_canonical_like(witness) == []
    assert gen.SEMANTIC_WITNESSES["tiny_wall_blocks"](witness)
    assert rival(witness) == ray_output(witness, ignore_tiny_walls=True)
    assert rival(witness) != ray_output(witness)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_override_matrix_is_observable_in_every_band(band):
    options = {"grid_h": 7, "grid_w": 9, "n_seeds": 5, "n_wall_components": 4}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 17),
        ("grid_w", 8),
        ("grid_w", 17),
        ("n_seeds", 1),
        ("n_seeds", 6),
        ("n_wall_components", 0),
        ("n_wall_components", 5),
        ("grid_h", True),
        ("n_seeds", 2.0),
        ("grid_w", "10"),
    ],
)
def test_rejects_unknown_out_of_range_and_non_integer_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_draw_contains_a_real_tiny_wall_counterexample(band):
    seen_shapes = set()
    seen_seeds = set()
    seen_walls = set()
    inputs = set()
    for index in range(160):
        grid = gen.generate(3100 + index, index * 13 + 5, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(3100 + index, index * 13 + 5, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["tiny_wall_blocks"](grid)
        assert ray_output(grid) != gen.SEMANTIC_RIVALS["ignore_tiny_walls"](grid)
        stats = observed(grid)
        seen_shapes.add((stats["grid_h"], stats["grid_w"]))
        seen_seeds.add(stats["n_seeds"])
        seen_walls.add(stats["n_wall_components"])
        inputs.add(repr(grid))
    assert len(seen_shapes) >= 5
    assert seen_seeds == {2, 3, 4, 5}
    assert seen_walls == {1, 2, 3, 4}
    assert len(inputs) >= 150


def test_component_count_and_tiny_component_are_real_pixels_not_metadata():
    for count in range(1, 5):
        grid = gen.generate(401, count, n_wall_components=count)
        components = wall_components(grid)
        assert len(components) == count
        assert any(len(component) <= 2 for component in components)


def test_lesson_contract_rejects_surviving_shortcut_and_accepts_generated_lesson():
    rival = gen.LESSON_COMPETITORS["ignore_tiny_walls"]
    canonical = canonical_pairs()
    query = {"input": tiny_wall_witness(), "output": ray_output(tiny_wall_witness())}
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical[:3])
    assert gen.lesson_identifiable(canonical[:3], query)

    lesson = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(900, index)
        lesson.append({"input": grid, "output": ray_output(grid)})
    qgrid = gen.generate(901, 9)
    assert gen.lesson_identifiable(lesson, {"input": qgrid, "output": ray_output(qgrid)}) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 9 for _ in range(7)],
        [[0] * 9 for _ in range(7)],
        [[0, 2, 9] + [0] * 6 for _ in range(7)],
    ],
)
def test_malformed_inputs_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


def test_generator_does_not_mutate_returned_grid_during_semantic_checks():
    grid = gen.generate(77, 4)
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES["tiny_wall_blocks"](grid)
    assert grid == original


def test_keyed_rng_is_independent_of_python_hash_seed():
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


def test_real_racket_reference_matches_independent_oracle():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [tiny_wall_witness()]
    grids += [gen.generate(1200 + index, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(24)]
    assert racket_outputs(grids) == [ray_output(grid) for grid in grids]


def test_distribution_probe_discovers_declared_rivals_and_checks_cyclic_lessons():
    report = audit(gen, 8, use_racket=False)
    assert set(report["canonical_shortcuts"]) == set(gen.CANONICAL_SHORTCUTS)
    assert set(report["lesson_competitors"]) == set(gen.LESSON_COMPETITORS)
    assert all(
        row["matches"] == report["canonical_pairs"]
        for row in report["canonical_shortcuts"].values()
    )
    assert report["lesson_policy"]["cyclic_starts_per_band"] == 8
    assert all(
        row["lesson_contract_failures"] == 0
        for row in report["by_band"].values()
    )


def test_static_geometry_templates_are_cached_for_large_override_matrices():
    gen._component_templates.cache_clear()
    component_first = gen._component_templates(16, 16)
    component_second = gen._component_templates(16, 16)
    assert component_first is component_second
    assert gen._component_templates.cache_info().misses == 1
    assert gen._component_templates.cache_info().hits == 1

    gen._teaching_candidates.cache_clear()
    teaching_first = gen._teaching_candidates(16, 16, (0, 1), 2)
    teaching_second = gen._teaching_candidates(16, 16, (0, 1), 2)
    assert teaching_first is teaching_second
    assert gen._teaching_candidates.cache_info().misses == 1
    assert gen._teaching_candidates.cache_info().hits == 1
