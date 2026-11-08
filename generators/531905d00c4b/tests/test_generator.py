"""Task-local regression tests for 531905d00c4b."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    absolute_row_rival,
    canonical,
    canonical_pairs,
    fixed_3x3_rival,
    intended_output,
    load_generator,
    parse,
    racket_outputs,
    uncropped_index_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: hashlib.sha1(json.dumps(p["input"]).encode()).hexdigest()[:8])
def test_canonical_inputs_are_owned_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_selected_authority():
    normalized = " ".join(canonical()["program_solution"].split())
    expected = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected == "2ace815dad55"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_observable_in_every_band(band):
    requested = {
        "library_h": 5,
        "prototype_count": 5,
        "prototype_w": 4,
        "index_h": 2,
        "index_w": 2,
        "index_top_padding": 2,
        "index_left_padding": 2,
        "vertical_layout": "mixed",
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert grid == gen.generate(17, 9, difficulty=band, **requested)


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("library_h", 2), ("library_h", 6),
    ("prototype_count", 2), ("prototype_count", 6),
    ("prototype_w", 1), ("prototype_w", 5),
    ("index_h", 1), ("index_h", 6),
    ("index_w", 1), ("index_w", 6),
    ("index_top_padding", -1), ("index_top_padding", 3),
    ("index_left_padding", -1), ("index_left_padding", 3),
    ("vertical_layout", "diagonal"),
    ("index_h", 2.5), ("prototype_count", True),
])
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_declared_schedule_has_all_four_semantic_profiles():
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_core", "shifted_prototype", "padded_index", "broad_tiles"
    )
    assert [gen.schedule_profile(3, i, "hard") for i in range(8)] == list(gen.SCHEDULE_PROFILES) * 2


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_covers_canonical_profile_and_all_shortcut_witnesses(band):
    seen_profiles = set()
    seen_exact_profile = False
    witnessed = {name: False for name in gen.SEMANTIC_WITNESSES}
    rival_disagreement = {name: False for name in gen.SEMANTIC_RIVALS}
    for index in range(32):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert intended_output(grid) == intended_output(deepcopy(grid))
        assert grid == gen.generate(700 + index, index, difficulty=band)
        seen_profiles.add(gen.schedule_profile(700 + index, index, band))
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        seen_exact_profile |= profile in {(6, 11, 4), (7, 11, 4)}
        authoritative = intended_output(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            witnessed[name] |= bool(predicate(grid))
        for name, rival in gen.SEMANTIC_RIVALS.items():
            rival_disagreement[name] |= rival(grid) != authoritative
    assert seen_profiles == set(gen.SCHEDULE_PROFILES)
    assert seen_exact_profile
    assert all(witnessed.values()), witnessed
    assert all(rival_disagreement.values()), rival_disagreement


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    independent = {
        "absolute_row_padding": absolute_row_rival,
        "uncropped_index": uncropped_index_rival,
        "fixed_3x3": fixed_3x3_rival,
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(independent)
    assert set(gen.LESSON_COMPETITORS) == set(independent)
    for pair in canonical_pairs():
        for name, rival in independent.items():
            assert rival(pair["input"]) == pair["output"], name
            assert gen.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"], name


@pytest.mark.parametrize("profile,rival_name", [
    ("shifted_prototype", "absolute_row_padding"),
    ("padded_index", "uncropped_index"),
    ("broad_tiles", "fixed_3x3"),
])
def test_each_noncanonical_profile_is_an_exact_rival_counterexample(profile, rival_name):
    index = list(gen.SCHEDULE_PROFILES).index(profile)
    grid = gen.generate(918, index, difficulty="hard")
    assert gen.schedule_profile(918, index, "hard") == profile
    intended = intended_output(grid)
    assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended
    witness_names = [name for name, rivals in gen.WITNESS_RIVALS.items() if rival_name in rivals]
    assert witness_names and any(gen.SEMANTIC_WITNESSES[name](grid) for name in witness_names)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(6)]])
def test_malformed_inputs_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_unknown_index_color_and_zero_hole():
    grid = gen.generate(31, 6, index_top_padding=0, index_left_padding=0)
    parts = parse(grid)
    r0, c0, _, _ = parts["index_bbox"]
    unknown = deepcopy(grid)
    colors = {v for row in parts["library"] for v in row if v}
    replacement = next(c for c in range(1, 10) if c not in colors)
    unknown[r0][c0] = replacement
    assert any("without prototypes" in item for item in gen.self_check(unknown))
    hole = deepcopy(grid)
    hole[r0][c0] = 0
    assert any("zero hole" in item for item in gen.self_check(hole))


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


def test_real_racket_matches_independent_oracle():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(404 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
