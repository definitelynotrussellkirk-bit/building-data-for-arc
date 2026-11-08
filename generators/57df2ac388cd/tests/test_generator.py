"""Focused regression suite for the repaired 57df2ac388cd generator."""
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
    TEXTURE_PALETTES,
    branch_support,
    canonical_pairs,
    load_generator,
    observed,
    overlay_output,
    subset_counterexample,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "a668b763669f"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_owned_and_python_geometry_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert overlay_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_controls_are_observable_in_every_band(band):
    requested = {
        "grid_h": 10,
        "grid_w": 14,
        "motif_a_cells": 4,
        "motif_b_cells": 6,
        "texture": "warm",
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 8),
        ("grid_h", 17),
        ("grid_w", 8),
        ("grid_w", 19),
        ("motif_a_cells", 2),
        ("motif_a_cells", 7),
        ("motif_b_cells", 2),
        ("motif_b_cells", 7),
        ("texture", "no_such_texture"),
        ("grid_h", True),
        ("grid_w", 10.5),
        ("motif_a_cells", "4"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_distribution_always_exercises_all_three_overlay_branches(band):
    inputs = set()
    sizes = set()
    cell_pairs = set()
    textures = set()
    for index in range(128):
        grid = gen.generate(1000 + index, index * 13 + 5, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(1000 + index, index * 13 + 5, difficulty=band)
        assert all(value > 0 for value in branch_support(grid).values())
        obs = observed(grid)
        inputs.add(repr(grid))
        sizes.add((obs["grid_h"], obs["grid_w"]))
        cell_pairs.add((obs["motif_a_cells"], obs["motif_b_cells"]))
        textures.add(obs["texture"])
        before = deepcopy(grid)
        assert overlay_output(grid) != grid
        assert grid == before
    assert len(inputs) >= 110
    assert len(sizes) >= 8
    assert len(cell_pairs) >= 10
    assert textures == set(TEXTURE_PALETTES)


@pytest.mark.parametrize("texture", sorted(TEXTURE_PALETTES))
def test_helpful_textures_are_active_and_lawful(texture):
    grid = gen.generate(91, 4, texture=texture)
    assert gen.self_check(grid) == []
    assert observed(grid)["texture"] == texture


@pytest.mark.parametrize("texture", ["no_motifs", "single_motif", "all_same_color"])
def test_negative_texture_fixtures_are_rejected_by_the_contract(texture):
    grid = gen.generate(91, 4, texture=texture)
    assert gen.self_check(grid)


def test_normalized_subset_counterexample_is_rejected():
    grid = subset_counterexample()
    assert branch_support(grid) == {"overlap": 3, "first_only": 0, "second_only": 1}
    assert any("first-only" in reason for reason in gen.self_check(grid))


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]])
def test_malformed_grids_return_diagnostics_instead_of_crashing(bad):
    assert gen.self_check(bad)


def test_declared_witnesses_really_refute_their_named_rivals():
    for index in range(32):
        grid = gen.generate(700, index)
        intended = overlay_output(grid)
        assert gen.strict_canonical_like(grid) == []
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), witness_name
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended


def test_lesson_hook_rejects_no_lawful_generated_lesson():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(880, index)
        demos.append({"input": grid, "output": overlay_output(grid)})
    query_grid = gen.generate(881, 17)
    query = {"input": query_grid, "output": overlay_output(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def test_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31,8,difficulty='hard')))"
    )
    outputs = []
    runtime = Path(gen.__file__).resolve().parents[2] / "shared/runtime"
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        prior_path = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(runtime) + (os.pathsep + prior_path if prior_path else "")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(Path(gen.__file__).resolve())],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]
