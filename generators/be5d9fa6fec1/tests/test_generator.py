"""Task-local regressions for the be5d9fa6fec1 row-group curriculum."""
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
    PROFILE_SPECS,
    RIVALS,
    analyze,
    canonical_pairs,
    canonical_rule_hash,
    intended_output,
    load_generator,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
KINDS = ("mix", "eight")


def test_public_contract_is_pinned_and_minimal():
    assert gen.RULE_HASH == canonical_rule_hash() == "0ff6975f3e81"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == pytest.approx(1.0)
    assert set(gen.AXES) == {"profile_id", "start_kind"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    info = analyze(pair["input"])
    expected = PROFILE_SPECS[info["profile_id"]]
    assert (info["height"], info["width"], info["group_count"]) == expected
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile_id", sorted(PROFILE_SPECS))
@pytest.mark.parametrize("start_kind", KINDS)
def test_exact_overrides_are_observable_in_every_band(band, profile_id, start_kind):
    options = {"profile_id": profile_id, "start_kind": start_kind}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize("kwargs", [
    {"typo_axis": 1},
    {"profile_id": -1},
    {"profile_id": 5},
    {"profile_id": True},
    {"profile_id": 2.0},
    {"profile_id": "2"},
    {"profile_id": None},
    {"start_kind": "other"},
    {"start_kind": 1},
    {"start_kind": None},
])
def test_invalid_or_unknown_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("bad", ["unknown", "DEFAULT", 0, True])
def test_unknown_difficulty_fails_loudly(bad):
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(0, 0, difficulty=bad)


@pytest.mark.parametrize("band", BANDS)
def test_generated_distribution_is_constructive_lawful_and_varied(band):
    seen_profiles = set()
    seen_starts = set()
    serialized = set()
    for index in range(180):
        grid = gen.generate(2000 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == gen.generate(2000 + index, index * 11, difficulty=band)
        info = analyze(grid)
        profile = PROFILE_SPECS[info["profile_id"]]
        assert (info["height"], info["width"], info["group_count"]) == profile
        assert set(info["palette"]) == {0, 1, 8}
        assert all(1 <= height <= 3 for height in info["heights"])
        assert info["heights"][0] >= 2
        assert all(kind in KINDS for kind in info["kinds"])
        assert all(a != b for a, b in zip(info["kinds"], info["kinds"][1:]))
        assert info["two_step_repeats"] == ()
        assert all(not ({1, 8} <= set(group["row"])) for group in info["groups"])
        seen_profiles.add(info["profile_id"])
        seen_starts.add(info["start_kind"])
        serialized.add(json.dumps(grid, separators=(",", ":")))
    assert seen_profiles == set(PROFILE_SPECS)
    assert seen_starts == set(KINDS)
    assert len(serialized) >= 170


def test_sampled_distribution_never_replays_a_canonical_input():
    canonical = {json.dumps(pair["input"], separators=(",", ":")) for pair in canonical_pairs()}
    generated = {
        json.dumps(gen.generate(5000 + index, index), separators=(",", ":"))
        for index in range(500)
    }
    assert not (canonical & generated)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_generated_grid_refutes_declared_rivals(band):
    assert set(gen.SEMANTIC_RIVALS) == set(RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(RIVALS)
    for index in range(80):
        grid = gen.generate(6100 + index, index, difficulty=band)
        expected = intended_output(grid)
        assert gen.rule_mirror(grid) == expected
        for name, independent_rival in RIVALS.items():
            assert independent_rival(grid) != expected, name
            assert gen.SEMANTIC_RIVALS[name](grid) == independent_rival(grid)
            assert gen.SEMANTIC_RIVALS[name](grid) != expected
            witness_names = [w for w, names in gen.WITNESS_RIVALS.items() if name in names]
            assert witness_names, name
            assert any(gen.SEMANTIC_WITNESSES[witness](grid) for witness in witness_names)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_query_rotation_is_identifiable_against_declared_rivals(band):
    for start in range(40):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(7200 + start, start * 11 + offset, difficulty=band)
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("bad", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[True] * 4 for _ in range(20)],
    [[0] * 4 for _ in range(20)],
    [[1] * 4 for _ in range(20)],
    [[1, 8, 0, 0] for _ in range(20)],
    [[1, 0], [0, 8]],
])
def test_malformed_and_minimal_impostors_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize("mutation", [
    "mixed_foreground_row",
    "all_zero_group",
    "too_tall_group",
    "split_group",
    "missing_palette",
    "wrong_group_count",
])
def test_self_check_rejects_structure_destroying_mutations(mutation):
    grid = gen.generate(91, 7, profile_id=0, start_kind="mix")
    groups = analyze(grid)["groups"]
    if mutation == "mixed_foreground_row":
        r = groups[0]["start"]
        grid[r][0], grid[r][1] = 1, 8
    elif mutation == "all_zero_group":
        for r in range(groups[0]["start"], groups[0]["stop"]):
            grid[r] = [0] * len(grid[0])
    elif mutation == "too_tall_group":
        grid.insert(groups[0]["stop"], list(grid[0]))
        grid.pop()
    elif mutation == "split_group":
        r = groups[0]["start"] + 1
        grid[r] = list(groups[2]["row"])
    elif mutation == "missing_palette":
        grid = [[1 if value == 8 else value for value in row] for row in grid]
    elif mutation == "wrong_group_count":
        r = groups[-1]["start"]
        grid[r:] = [list(groups[-2]["row"]) for _ in grid[r:]]
    assert gen.self_check(grid)


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
        for index in range(18)
    ]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
