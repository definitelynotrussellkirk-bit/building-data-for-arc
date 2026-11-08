"""Focused regression contract for the divider-reflection sampler."""
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
    blue_cells,
    canonical_pairs,
    connected4,
    load_generator,
    observed,
    oracle,
    profile,
    run_audit,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_oracle_matches(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=8, grid_w=11, blue_size=3, source_side="left",
             mirror_visibility="full", n_distractors=0),
        dict(grid_h=10, grid_w=14, blue_size=8, source_side="right",
             mirror_visibility="partial", n_distractors=3),
        dict(grid_h=9, grid_w=12, blue_size=6, source_side="left",
             mirror_visibility="partial", n_distractors=2),
    ],
)
def test_every_advertised_override_is_exact_and_observable(band, options):
    grid = gen.generate(317, 29, difficulty=band, **options)
    assert gen.self_check(deepcopy(grid)) == []
    assert observed(grid) == options
    assert gen.observe_overrides(deepcopy(grid)) == options
    assert connected4(blue_cells(grid))
    assert oracle(grid) != grid
    visible = sum(value == 8 for row in oracle(grid) for value in row)
    if options["mirror_visibility"] == "partial":
        assert 0 < visible < options["blue_size"]
    else:
        assert visible == options["blue_size"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7), ("grid_h", 11), ("grid_h", True), ("grid_h", 8.0),
        ("grid_w", 10), ("grid_w", 15), ("grid_w", "12"),
        ("blue_size", 2), ("blue_size", 9), ("blue_size", False),
        ("source_side", "both"), ("source_side", 1),
        ("mirror_visibility", "none"), ("mirror_visibility", 0),
        ("n_distractors", -1), ("n_distractors", 4), ("n_distractors", 1.5),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_default_distribution_is_deterministic_lawful_and_canonical_anchored():
    canonical_profiles = {profile(pair["input"]) for pair in canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        profiles = set()
        sides = set()
        visibility = set()
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        rival_disagreements = {name: 0 for name in gen.SEMANTIC_RIVALS}
        for index in range(100):
            seed = 20_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            assert grid == gen.generate(seed, index, difficulty=band)
            assert gen.self_check(deepcopy(grid)) == []
            assert gen.strict_canonical_like(deepcopy(grid)) == []
            assert connected4(blue_cells(grid))
            obs = observed(grid)
            assert obs == gen.observe_overrides(deepcopy(grid))
            assert obs["n_distractors"] >= 1
            profiles.add(profile(grid))
            sides.add(obs["source_side"])
            visibility.add(obs["mirror_visibility"])
            intended = oracle(grid)
            assert intended != grid
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(deepcopy(grid)):
                    witness_hits[name] += 1
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if rival(deepcopy(grid)) != intended:
                    rival_disagreements[name] += 1
        assert profiles & canonical_profiles
        assert sides == {"left", "right"}
        assert visibility == {"full", "partial"}
        assert all(count > 0 for count in witness_hits.values())
        assert all(count > 0 for count in rival_disagreements.values())


def test_every_four_pair_window_survives_all_query_rotations():
    # Production lessons use 3 demos plus one query.  Each four-pair window must
    # retain both source directions, clipping evidence, and distractor evidence
    # no matter which member is held out as the query.
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for index in range(start, start + 4):
                grid = gen.generate(71_000 + start, index, difficulty=band)
                pairs.append({"input": grid, "output": oracle(grid)})
            for query_index in range(4):
                demos = [deepcopy(pair) for i, pair in enumerate(pairs) if i != query_index]
                query = deepcopy(pairs[query_index])
                assert gen.lesson_identifiable(demos, query) == []


def test_declared_witness_claims_are_true_counterexamples():
    for index in range(32):
        grid = gen.generate(51_000 + index, index, difficulty="medium")
        intended = oracle(grid)
        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            if not gen.SEMANTIC_WITNESSES[witness_name](deepcopy(grid)):
                continue
            assert any(
                gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != intended
                for name in rival_names
            ), witness_name


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(8)], [[0, 10]]],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_disconnected_or_two_sided_blue():
    grid = gen.generate(7, 3, source_side="left", mirror_visibility="full")
    bad = deepcopy(grid)
    for r, row in enumerate(bad):
        for c, value in enumerate(row):
            if value == 1:
                bad[r][c] = 0
    bad[0][0] = bad[-1][0] = 1
    assert gen.self_check(bad)

    bad = deepcopy(grid)
    divider = next(c for c in range(len(bad[0])) if all(row[c] == 5 for row in bad))
    bad[0][divider + 1] = 1
    assert gen.self_check(bad)


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
            env=env, text=True,
        ))
    assert outputs[0] == outputs[1]


def test_authority_pin_and_probe_contract():
    assert gen.RULE_HASH == "549dba88300b"
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    report = run_audit(count=8)
    assert report["status"] == "pass"
    assert report["canonical_accepted"] == 5
    assert report["canonical_oracle_matches"] == 5
