"""Task-local regression tests for the f4d4fb4404c6 input curriculum."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    analyze,
    canonical_pairs,
    facts,
    intended_output,
    load_generator,
    profile_of,
    racket_outputs,
    rival_exact_span_only,
    rival_first_marker_only,
    rival_global_frame_color,
    rival_one_copy_only,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = (
    "canonical_core",
    "overlap_marker",
    "multicolor_frames",
    "combined_witness",
)


def test_public_contract_is_pinned_and_minimal():
    assert gen.RULE_HASH == "052ea839cbdd"
    assert gen.VERSION == "3.1.0"
    assert tuple(gen.SCENE_PROFILES) == PROFILES
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == pytest.approx(1 / 5, abs=0.02)
    assert set(gen.AXES) == {"scene_profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
)
def test_all_canonical_inputs_are_owned_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
def test_scene_profile_override_is_exact_observable_and_deterministic(profile, band):
    grid = gen.generate(17, 9, difficulty=band, scene_profile=profile)
    assert gen.self_check(grid) == []
    assert profile_of(grid) == profile
    assert gen.observe_overrides(grid) == {"scene_profile": profile}
    assert grid == gen.generate(17, 9, difficulty=band, scene_profile=profile)


@pytest.mark.parametrize("kwargs", [
    {"typo_axis": "canonical_core"},
    {"scene_profile": "not-a-profile"},
    {"scene_profile": 1},
    {"scene_profile": None},
])
def test_invalid_or_unknown_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_schedule_is_a_four_profile_cycle_for_every_band_and_seed():
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 7, 811):
            observed = [gen.schedule_profile(seed, index, band) for index in range(12)]
            assert observed == list(PROFILES) * 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_of_four_rotated_lesson_pairs_teach_both_canonical_shortcuts(band):
    # Production lessons contain three demonstrations and one query.  Every
    # possible query rotation must leave three demonstrations that refute both
    # canonical-fitting shortcuts, for every cyclic schedule start.
    for start in range(16):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(4100 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert len(demos) == gen.EXAMPLES_NEEDED
            assert gen.lesson_identifiable(demos, query) == []
            for rival in (rival_exact_span_only, rival_global_frame_color):
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_distribution_is_lawful_varied_and_hits_canonical_profiles(band):
    seen_profiles = set()
    seen_canonical_profile = False
    seen_dimensions = set()
    for index in range(60):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(700 + index, index, difficulty=band)
        info = facts(grid)
        seen_profiles.add(profile_of(grid))
        seen_dimensions.add((info["height"], info["width"]))
        seen_canonical_profile |= (
            info["height"], info["width"], len(info["palette"])
        ) in CANONICAL_PROFILES
        assert info["has_long_chain"]
        assert info["has_multi_marker_frame"]
        assert {"up", "down", "left", "right"} & set(info["directions"])
        assert any(direction in info["directions"] for direction in ("up", "down"))
        assert any(direction in info["directions"] for direction in ("left", "right"))
    assert seen_profiles == set(PROFILES)
    assert seen_canonical_profile
    assert len(seen_dimensions) >= 5


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    independent = {
        "exact_span_only": rival_exact_span_only,
        "global_frame_color": rival_global_frame_color,
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(independent)
    for pair in canonical_pairs():
        for name, rival in independent.items():
            assert rival(pair["input"]) == pair["output"], name
            assert gen.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"], name


@pytest.mark.parametrize("profile,rival_name,independent", [
    ("overlap_marker", "exact_span_only", rival_exact_span_only),
    ("multicolor_frames", "global_frame_color", rival_global_frame_color),
    ("combined_witness", "exact_span_only", rival_exact_span_only),
    ("combined_witness", "global_frame_color", rival_global_frame_color),
])
def test_profile_is_an_exact_counterexample_to_its_canonical_shortcut(profile, rival_name, independent):
    grid = gen.generate(918, PROFILES.index(profile), difficulty="hard", scene_profile=profile)
    intended = intended_output(grid)
    assert profile_of(grid) == profile
    assert independent(grid) != intended
    assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended
    witness_names = [name for name, rivals in gen.WITNESS_RIVALS.items() if rival_name in rivals]
    assert witness_names and any(gen.SEMANTIC_WITNESSES[name](grid) for name in witness_names)


@pytest.mark.parametrize("rival_name,independent", [
    ("one_copy_only", rival_one_copy_only),
    ("first_marker_only", rival_first_marker_only),
])
def test_every_default_profile_refutes_noncanonical_teaching_rivals(rival_name, independent):
    for profile in PROFILES:
        grid = gen.generate(119, PROFILES.index(profile), scene_profile=profile)
        intended = intended_output(grid)
        assert independent(grid) != intended
        assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 17 for _ in range(18)]])
def test_malformed_inputs_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_short_markerless_frame_and_stray_cell():
    grid = gen.generate(31, 6, scene_profile="canonical_core")
    parsed = analyze(grid)
    markerless = deepcopy(grid)
    frame_index = parsed["markers"][0]["frame_index"]
    for marker in parsed["markers"]:
        if marker["frame_index"] == frame_index:
            for r, c in marker["cells"]:
                markerless[r][c] = 0
    assert gen.self_check(markerless)
    stray = deepcopy(grid)
    target = next(
        (r, c)
        for r, row in enumerate(stray)
        for c, value in enumerate(row)
        if value == 0 and 0 < r < len(stray) - 1 and 0 < c < len(row) - 1
    )
    stray[target[0]][target[1]] = 9
    assert gen.self_check(stray)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env,
            text=True,
        ))
    assert outputs[0] == outputs[1]


def test_real_racket_matches_independent_oracle_on_canonical_and_generated_grids():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(404 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        for index in range(12)
    ]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]

@pytest.mark.parametrize("profile", PROFILES)
def test_difficulty_bands_are_not_dead(profile):
    variants = {
        json.dumps(gen.generate(2718, PROFILES.index(profile), difficulty=band, scene_profile=profile))
        for band in ("easy", "medium", "hard")
    }
    assert len(variants) >= 2


def test_duplicate_authority_sources_are_text_synchronized():
    root = HOME.parents[1]
    base = root / "shared" / "data" / "base" / "solutions"
    if not base.exists():
        base = root / "data" / "base" / "solutions"
    training = json.loads((base / "training/c62e2108__f4d4fb4404c6.json").read_text())
    augmented = json.loads((base / "augmented/c62e2108__8c4dbe42f42e.json").read_text())
    assert augmented["racket_target"]["raw_code"] == training["racket_target"]["raw_code"]
    assert augmented["racket_target"]["target_code"] == training["racket_target"]["target_code"]
