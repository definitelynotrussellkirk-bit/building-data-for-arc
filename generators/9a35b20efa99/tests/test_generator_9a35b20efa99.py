"""Source-bound regressions for the orbit-stamp generator repair."""
from __future__ import annotations

from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    BASE_SHAPES,
    above_only_output,
    analyze,
    canonical_pairs,
    corner_l_only_output,
    load_generator,
    observed,
    racket_outputs,
    rule_output,
    shortcut_witness,
    source_is_above,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {"grid_h", "grid_w", "motif_color", "motif_rotation"}
BANDS = (None, "easy", "medium", "hard")


def pair(grid):
    return {"input": deepcopy(grid), "output": rule_output(grid)}


def test_public_contract_is_rule_pinned_and_exact():
    assert gen.RULE_HASH == "019ee1056dff"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "corner_l3_above",
        "branch5_below",
        "corner_l4_left",
        "blob6_right",
    )


@pytest.mark.parametrize(
    "canonical",
    canonical_pairs(),
    ids=lambda item: f"v{item['variant']}-{item['split']}-{item['pair_index']}",
)
def test_all_canonical_pairs_are_accepted_and_match_independent_oracle(canonical):
    original = deepcopy(canonical["input"])
    assert gen.self_check(canonical["input"]) == []
    assert gen.strict_canonical_like(canonical["input"]) == []
    assert rule_output(canonical["input"]) == canonical["output"]
    assert gen.rule_mirror(canonical["input"]) == canonical["output"]
    assert canonical["input"] == original


@pytest.mark.parametrize("band", BANDS)
def test_every_joint_boundary_override_is_constructive_exact_and_observable(band):
    cases = itertools.product((13, 15), (13, 15, 17), (1, 8), range(4))
    for index, (height, width, color, rotation) in enumerate(cases):
        requested = {
            "grid_h": height,
            "grid_w": width,
            "motif_color": color,
            "motif_rotation": rotation,
        }
        grid = gen.generate(10_000 + index, index, difficulty=band, **requested)
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize("overrides", [
    {"typo_axis": 1},
    {"grid_h": 12}, {"grid_h": 17}, {"grid_h": 13.0}, {"grid_h": True},
    {"grid_w": 12}, {"grid_w": 19}, {"grid_w": "13"},
    {"motif_color": 0}, {"motif_color": 9}, {"motif_color": 2.0},
    {"motif_rotation": -1}, {"motif_rotation": 4}, {"motif_rotation": False},
])
def test_invalid_and_unknown_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_fails_closed():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


def test_schedule_covers_all_roles_and_every_query_rotation_refutes_both_rivals():
    for band in BANDS:
        for start in range(20):
            grids = [gen.generate(80_000 + start, start + offset, difficulty=band) for offset in range(4)]
            assert {analyze(grid)["shape_kind"] for grid in grids} == set(BASE_SHAPES)
            assert any(source_is_above(grid) for grid in grids)
            assert sum(not source_is_above(grid) for grid in grids) == 3
            for query_index in range(4):
                demos = [pair(grid) for index, grid in enumerate(grids) if index != query_index]
                query = {"input": deepcopy(grids[query_index])}
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_exact_shortcut_counterexample_and_canonical_rival_fit():
    fixture = json.loads((HOME / "counterexamples" / "above-only-and-corner-l-only.json").read_text())
    grid = fixture["input"]
    intended = rule_output(grid)
    assert intended == fixture["intended_output"]
    assert above_only_output(grid) == fixture["above_only_output"]
    assert corner_l_only_output(grid) == fixture["corner_l_only_output"]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == intended
    assert gen.SEMANTIC_RIVALS["above_only"](grid) == fixture["above_only_output"]
    assert gen.SEMANTIC_RIVALS["corner_l_only"](grid) == fixture["corner_l_only_output"]
    assert intended != fixture["above_only_output"]
    assert intended != fixture["corner_l_only_output"]
    for canonical in canonical_pairs():
        assert above_only_output(canonical["input"]) == canonical["output"]
        assert corner_l_only_output(canonical["input"]) == canonical["output"]
        assert gen.CANONICAL_SHORTCUTS["above_only"](canonical["input"]) == canonical["output"]
        assert gen.CANONICAL_SHORTCUTS["corner_l_only"](canonical["input"]) == canonical["output"]


def test_production_sampler_emits_both_counterexample_classes_in_each_period():
    for band in BANDS:
        grids = [gen.generate(90_000, index, difficulty=band) for index in range(4)]
        assert any(not source_is_above(grid) for grid in grids)
        assert any(analyze(grid)["shape_kind"] not in {"corner_l3", "corner_l4"} for grid in grids)
        assert any(
            not source_is_above(grid)
            and analyze(grid)["shape_kind"] not in {"corner_l3", "corner_l4"}
            for grid in grids
        )


@pytest.mark.parametrize("band", BANDS)
def test_generated_distribution_is_lawful_varied_deterministic_and_nonidentity(band):
    shapes, colors, rotations, dimensions, inputs = set(), set(), set(), set(), set()
    for index in range(160):
        seed = 300_000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == rule_output(grid)
        assert gen.rule_mirror(grid) != grid
        info = analyze(grid)
        values = observed(grid)
        shapes.add(info["shape_kind"])
        colors.add(values["motif_color"])
        rotations.add(values["motif_rotation"])
        dimensions.add((values["grid_h"], values["grid_w"]))
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert shapes == set(BASE_SHAPES)
    assert colors == set(range(1, 9))
    assert rotations == {0, 1, 2, 3}
    assert dimensions == {(13, 13), (15, 15), (13, 15), (15, 17)}
    assert len(inputs) >= 150


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[True, 0], [0, 0]],
    [[9, 9], [0, 1]],
    [[9, 0], [1, 2]],
    [[9, 0, 0], [1, 0, 1], [0, 0, 0]],
])
def test_validator_rejects_malformed_grids_without_throwing(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("mutation", [
    "extra_anchor",
    "second_color",
    "disconnect_motif",
    "unknown_shape",
    "remove_anchor",
])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(31, 1, grid_h=13, grid_w=13, motif_color=2, motif_rotation=0)
    info = analyze(grid)
    if mutation == "extra_anchor":
        grid[0][0] = 9
    elif mutation == "second_color":
        r, c = next(iter(info["motif_cells"]))
        grid[r][c] = 3
    elif mutation == "disconnect_motif":
        grid[0][0] = 2
    elif mutation == "unknown_shape":
        for r, c in info["motif_cells"]:
            grid[r][c] = 0
        grid[0][0] = grid[0][1] = grid[0][2] = grid[0][3] = 2
    elif mutation == "remove_anchor":
        r, c = info["anchor"]
        grid[r][c] = 0
    assert gen.self_check(grid)


def test_replay_is_fresh_and_does_not_touch_global_random_state():
    random.seed(20261008)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert first != second


def test_python_hashseed_does_not_change_generation():
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


def test_real_racket_authority_matches_oracle_on_canonical_witness_and_generated_cases():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [item["input"] for item in canonical_pairs()] + [shortcut_witness()]
    grids += [gen.generate(500_000 + index, index) for index in range(32)]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
