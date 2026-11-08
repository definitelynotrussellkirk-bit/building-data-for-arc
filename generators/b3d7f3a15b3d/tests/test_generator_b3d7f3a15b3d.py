"""Focused regressions for the framed-cell propagation curriculum."""
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
from reference_probe import (  # noqa: E402
    SCENE_PROFILES,
    canonical_pairs,
    first_special_only,
    horizontal_only,
    independent_output,
    inspect_grid,
    load_generator,
    observed,
    vertical_only,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_contract_surface_is_small_exact_and_rule_pinned():
    assert GEN.VERSION == "3.1.0"
    assert GEN.RULE_HASH == "032c15e97118"
    assert set(GEN.AXES) == {"scene_profile"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.SCENE_PROFILES) == set(SCENE_PROFILES)


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_all_canonical_pairs_are_owned_and_match_independent_rule(pair):
    source = deepcopy(pair["input"])
    assert GEN.self_check(source) == []
    assert GEN.strict_canonical_like(source) == []
    assert independent_output(source) == pair["output"]
    assert GEN.rule_mirror(source) == pair["output"]
    assert source == pair["input"], "validation and rule mirrors must be pure"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", sorted(SCENE_PROFILES))
def test_every_profile_override_is_exact_observable_and_lawful(band, profile):
    grid = GEN.generate(1701, 19, difficulty=band, scene_profile=profile)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert observed(grid) == {"scene_profile": profile}
    assert GEN.observe_overrides(grid) == {"scene_profile": profile}
    assert GEN.rule_mirror(grid) == independent_output(grid)
    assert GEN.rule_mirror(grid) != grid
    assert GEN.generate(1701, 19, difficulty=band, scene_profile=profile) == grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"scene_profile": "unknown"},
        {"scene_profile": 3},
        {"scene_profile": True},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_has_exact_profile_support_and_all_semantic_branches(band):
    seen_profiles = set()
    for index in range(80):
        grid = GEN.generate(9000 + index, index * 17 + 3, difficulty=band)
        facts = inspect_grid(grid)
        assert GEN.self_check(grid) == []
        assert facts["scene_profile"] in SCENE_PROFILES
        assert facts["horizontal_changes"]
        assert facts["vertical_changes"]
        assert len(facts["changed_colors"]) >= 2
        assert 5 <= facts["palette_size"] <= 7
        seen_profiles.add(facts["scene_profile"])
    assert seen_profiles == set(SCENE_PROFILES)


def test_declared_witnesses_have_real_rival_counterexamples():
    expected = {
        "horizontal_propagation": "vertical_only",
        "vertical_propagation": "horizontal_only",
        "multiple_special_colors": "first_special_only",
    }
    assert set(expected) <= set(GEN.SEMANTIC_WITNESSES)
    assert {
        "horizontal_only", "vertical_only", "first_special_only"
    } <= set(GEN.SEMANTIC_RIVALS)
    for index in range(32):
        grid = GEN.generate(712, index, difficulty="medium")
        official = independent_output(grid)
        for witness_name, rival_name in expected.items():
            assert GEN.SEMANTIC_WITNESSES[witness_name](grid)
            assert rival_name in GEN.WITNESS_RIVALS[witness_name]
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != official


def test_rival_helpers_match_independent_definitions_and_fail_canonical_somewhere():
    pairs = canonical_pairs()
    independent_rivals = {
        "horizontal_only": horizontal_only,
        "vertical_only": vertical_only,
        "first_special_only": first_special_only,
    }
    for name, rival in independent_rivals.items():
        assert all(
            GEN.SEMANTIC_RIVALS[name](pair["input"]) == rival(pair["input"])
            for pair in pairs
        )
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs)


@pytest.mark.parametrize("start", range(12))
def test_every_consecutive_lesson_is_identifiable(start):
    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(4401, start + offset, difficulty="medium")
        pairs.append({"input": grid, "output": independent_output(grid)})
    assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:-1]), name


@pytest.mark.parametrize(
    "mutation",
    ["separator", "frame", "erase_special_color", "non_integer", "ragged"],
)
def test_validator_rejects_targeted_structural_impostors(mutation):
    grid = GEN.generate(41, 7, scene_profile="canonical_4x4_p5")
    if mutation == "separator":
        grid[0][1] = 9
    elif mutation == "frame":
        grid[1][1] = 9
    elif mutation == "erase_special_color":
        facts = inspect_grid(grid)
        color = max(facts["specials"])
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == color:
                    grid[row][col] = facts["common"]
    elif mutation == "non_integer":
        grid[2][2] = True
    elif mutation == "ragged":
        grid[-1].pop()
    assert GEN.self_check(grid)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(91231)
    state = random.getstate()
    first = GEN.generate(902, 11, difficulty="hard")
    assert random.getstate() == state
    first[1][1] = 0
    second = GEN.generate(902, 11, difficulty="hard")
    third = GEN.generate(902, 11, difficulty="hard")
    assert second == third
    assert second is not third
    assert all(a is not b for a, b in zip(second, third))


def test_python_hash_seed_does_not_change_pixels():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(221,17,difficulty='hard')))"
    )
    source = str(Path(GEN.__file__).resolve())
    outputs = []
    for hash_seed in ("1", "991"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, source], env=env, text=True
            )
        )
    assert outputs[0] == outputs[1]


def test_difficulty_bands_change_pixels_without_changing_owned_profile():
    outputs = []
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(
            1701,
            19,
            difficulty=band,
            scene_profile="canonical_5x5_p7",
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {"scene_profile": "canonical_5x5_p7"}
        outputs.append(tuple(tuple(row) for row in grid))
    assert len(set(outputs)) == 3
