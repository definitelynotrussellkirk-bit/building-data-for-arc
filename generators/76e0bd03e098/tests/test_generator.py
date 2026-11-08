"""Task-local regression suite for the repaired clear-elbow generator."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    blocked_fallback_witness,
    branch_summary,
    canonical_pairs,
    load_generator,
    observed,
    oracle_output,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_canonical_inputs_are_lawful_and_oracle_matches_labels(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]


def test_explicit_blocked_fallback_is_lawful_and_changes_output():
    grid = blocked_fallback_witness()
    summary, overlaps = branch_summary(grid)
    assert summary["both_clear"] >= 1
    assert summary["h_blocked_v_clear"] >= 1
    assert summary["both_blocked"] >= 1
    assert summary["overlap_pairs"] >= 1
    assert summary["numeric_order_diff"]
    assert summary["first_wins_diff"]
    assert oracle_output(grid) != oracle_output(grid, policy="clear_required")
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["8x10", "8x11", "8x12", "9x10", "9x11"])
@pytest.mark.parametrize("n_walls", [4, 5])
def test_exact_observable_overrides_in_every_band(band, profile, n_walls):
    grid = gen.generate(17, 9, difficulty=band, scene_profile=profile, n_walls=n_walls)
    expected = {"scene_profile": profile, "n_walls": n_walls}
    assert gen.self_check(grid) == []
    assert observed(grid) == expected
    assert gen.observe_overrides(grid) == expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"scene_profile": "9x12"},
        {"scene_profile": 810},
        {"n_walls": 3},
        {"n_walls": 6},
        {"n_walls": True},
        {"n_walls": 4.0},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_ordinary_draw_teaches_authoritative_branch_and_order_semantics(band):
    seen = set()
    for index in range(80):
        grid = gen.generate(8000 + index, index * 7 + 3, difficulty=band)
        before = deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == before
        summary, _overlaps = branch_summary(grid)
        assert summary["pairs"] == 3
        assert summary["both_clear"] >= 1
        assert summary["h_blocked_v_clear"] >= 1
        assert summary["both_blocked"] >= 1
        assert summary["overlap_pairs"] >= 1
        assert summary["numeric_order_diff"]
        assert summary["first_wins_diff"]
        assert gen.rule_mirror(grid) == oracle_output(grid)
        assert grid == gen.generate(8000 + index, index * 7 + 3, difficulty=band)
        seen.add(tuple(map(tuple, grid)))
    assert len(seen) >= 60


def test_semantic_contract_has_real_counterexamples():
    grid = blocked_fallback_witness()
    intended = oracle_output(grid)
    expected_witnesses = {
        "horizontal_preference",
        "vertical_detour",
        "blocked_vertical_fallback",
        "late_color_wins_overlap",
        "reading_order_precedence",
    }
    assert expected_witnesses <= set(gen.SEMANTIC_WITNESSES)
    assert gen.SEMANTIC_WITNESSES["horizontal_preference"](grid)
    assert gen.SEMANTIC_WITNESSES["vertical_detour"](grid)
    assert gen.SEMANTIC_WITNESSES["blocked_vertical_fallback"](grid)
    assert gen.SEMANTIC_WITNESSES["late_color_wins_overlap"](grid)
    assert gen.SEMANTIC_WITNESSES["reading_order_precedence"](grid)
    for rival_name, rival in gen.SEMANTIC_RIVALS.items():
        candidate = rival(grid)
        assert candidate != intended, rival_name
        assert grid == blocked_fallback_witness(), f"{rival_name} mutated its input"


def test_rule_mirror_matches_all_canonical_labels_and_racket_witness():
    pairs = canonical_pairs()
    grids = [pair["input"] for pair in pairs] + [blocked_fallback_witness()]
    expected = [pair["output"] for pair in pairs] + [oracle_output(grids[-1])]
    assert [gen.rule_mirror(grid) for grid in grids] == expected
    try:
        actual = racket_outputs(grids)
    except Exception as exc:
        pytest.skip(f"canonical Racket runtime unavailable: {exc}")
    assert actual == expected


@pytest.mark.parametrize(
    "mutation",
    ["unknown_color", "one_endpoint", "aligned_pair", "wrong_wall_count", "wrong_pair_count", "ragged"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = blocked_fallback_witness()
    if mutation == "unknown_color":
        grid[7][9] = 10
    elif mutation == "one_endpoint":
        grid[5][8] = 0
    elif mutation == "aligned_pair":
        grid[5][8] = 0
        grid[0][8] = 7
    elif mutation == "wrong_wall_count":
        grid[7][0] = 0
    elif mutation == "wrong_pair_count":
        grid[7][9] = 4
        grid[6][9] = 4
    elif mutation == "ragged":
        grid[-1].pop()
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


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
