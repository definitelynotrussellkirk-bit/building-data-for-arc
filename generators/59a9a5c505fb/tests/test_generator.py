"""Task-local regression tests for the 59a9a5c505fb input curriculum."""
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
    intended_output,
    load_generator,
    profile_of,
    racket_outputs,
    rival_frame_fill_only,
    rival_nested_chain_only,
    rival_visible_cells_only,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = (
    "nested_frames",
    "nested_sparse",
    "crossing_sparse",
    "crossing_mixed",
)


def test_public_contract_is_pinned_and_minimal():
    assert gen.RULE_HASH == "058f695b6f59"
    assert gen.VERSION == "3.0.0"
    assert tuple(gen.SCENE_PROFILES) == PROFILES
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == pytest.approx(0.20)
    assert set(gen.AXES) == {"scene_profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
)
def test_all_canonical_inputs_are_owned_and_oracles_match(pair):
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
    {"typo_axis": "nested_frames"},
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
            assert [gen.schedule_profile(seed, i, band) for i in range(12)] == list(PROFILES) * 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_distribution_is_lawful_varied_and_canonical_profile_supported(band):
    seen_profiles = set()
    seen_shapes = set()
    seen_orientations = set()
    for index in range(60):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(700 + index, index, difficulty=band)
        info = analyze(grid)
        seen_profiles.add(profile_of(grid))
        seen_shapes.add((info["height"], info["width"], len(info["palette"])))
        seen_orientations.add(tuple(sorted((b[2] - b[0], b[3] - b[1]) for b in info["boxes"])))
        assert (info["height"], info["width"], len(info["palette"])) in CANONICAL_PROFILES
        assert info["max_depth"] == len(info["components"])
        assert 2 <= len(info["components"]) <= 3
    assert seen_profiles == set(PROFILES)
    assert len(seen_shapes) >= 2
    assert len(seen_orientations) >= 2


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    independent = {
        "frame_fill_only": rival_frame_fill_only,
        "nested_chain_only": rival_nested_chain_only,
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(independent)
    for pair in canonical_pairs():
        for name, rival in independent.items():
            assert rival(pair["input"]) == pair["output"], name
            assert gen.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"], name


@pytest.mark.parametrize("profile,rivals", [
    ("nested_sparse", ("frame_fill_only",)),
    ("crossing_sparse", ("frame_fill_only", "nested_chain_only")),
    ("crossing_mixed", ("frame_fill_only", "nested_chain_only")),
])
def test_profiles_are_exact_counterexamples_to_canonical_shortcuts(profile, rivals):
    grid = gen.generate(918, PROFILES.index(profile), difficulty="hard", scene_profile=profile)
    expected = intended_output(grid)
    independent = {
        "frame_fill_only": rival_frame_fill_only,
        "nested_chain_only": rival_nested_chain_only,
    }
    for name in rivals:
        assert independent[name](grid) != expected
        assert gen.SEMANTIC_RIVALS[name](grid) != expected
        witnesses = [w for w, names in gen.WITNESS_RIVALS.items() if name in names]
        assert witnesses and any(gen.SEMANTIC_WITNESSES[w](grid) for w in witnesses)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_of_four_query_rotation_refutes_every_declared_competitor(band):
    for start in range(12):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(4100 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_visible_cell_rival_is_refuted_by_every_profile():
    assert "visible_cells_only" in gen.LESSON_COMPETITORS
    for profile in PROFILES:
        grid = gen.generate(119, PROFILES.index(profile), scene_profile=profile)
        assert rival_visible_cells_only(grid) != intended_output(grid)
        assert gen.LESSON_COMPETITORS["visible_cells_only"](grid) != intended_output(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]])
def test_malformed_inputs_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_disconnected_same_color_and_nonoverlapping_boxes():
    disconnected = [[0] * 9 for _ in range(9)]
    disconnected[1][1] = disconnected[7][7] = 2
    disconnected[1][2] = disconnected[7][6] = 2
    assert gen.self_check(disconnected)

    separate = [[0] * 9 for _ in range(9)]
    for r, c in ((1, 1), (1, 2), (2, 1)):
        separate[r][c] = 2
    for r, c in ((6, 6), (6, 7), (7, 6)):
        separate[r][c] = 3
    assert gen.self_check(separate)


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
    grids += [gen.generate(404 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
