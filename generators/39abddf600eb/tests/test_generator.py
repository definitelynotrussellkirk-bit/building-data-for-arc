"""Task-local regression suite for 39abddf600eb.

All expected outputs come from the independent pixel parser/oracle in workspace,
not from production generator helpers.
"""
from copy import deepcopy
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
    canonical_pairs,
    diagonal_only_output,
    load_generator,
    manhattan_output,
    observed,
    seed_geometry,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {
    "grid_h", "grid_w", "frame_color", "seed_geometry", "seed_color_relation"
}
CANONICAL_PROFILES = {
    (11, 13, 4), (10, 12, 4), (12, 14, 4), (11, 11, 4), (12, 13, 4)
}


def palette_size(grid):
    return len({value for row in grid for value in row})


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "38c495fef5e9"
    assert gen.ALLOW_IDENTITY_OUTPUT is True
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert manhattan_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("geometry", ["identity", "axis", "diagonal"])
@pytest.mark.parametrize("relation", ["same", "different"])
def test_every_exact_axis_combination_is_constructive_and_observable(band, geometry, relation):
    options = {
        "grid_h": 8,
        "grid_w": 8,
        "frame_color": 8,
        "seed_geometry": geometry,
        "seed_color_relation": relation,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert seed_geometry(grid) == geometry
    assert (manhattan_output(grid) == grid) is (geometry == "identity")


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 7), ("grid_h", 17), ("grid_w", 7), ("grid_w", 19),
    ("frame_color", 1), ("frame_color", 9),
    ("grid_h", True), ("grid_w", 9.5), ("frame_color", "5"),
    ("seed_geometry", "adjacent"), ("seed_geometry", 1),
    ("seed_color_relation", "varied"), ("seed_color_relation", False),
    ("palette_kind", "default"), ("density", "sparse"), ("texture", "default"),
])
def test_rejects_unknown_obsolete_or_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_diverse_and_anchors_canonical_profiles(band):
    shapes, geometries, relations, colors, inputs = set(), set(), set(), set(), set()
    exact_hits = 0
    identity_count = 0
    for index in range(120):
        grid = gen.generate(8000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(8000 + index, index, difficulty=band)
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        geometries.add(stats["seed_geometry"])
        relations.add(stats["seed_color_relation"])
        colors.add(stats["frame_color"])
        inputs.add(json.dumps(grid, separators=(",", ":")))
        exact_hits += (stats["grid_h"], stats["grid_w"], palette_size(grid)) in CANONICAL_PROFILES
        identity_count += manhattan_output(grid) == grid
    assert geometries == {"identity", "axis", "diagonal"}
    assert relations == {"same", "different"}
    assert len(shapes) >= 5
    assert len(colors) >= 6
    assert len(inputs) >= 116
    assert exact_hits >= 72
    # Identity is a real canonical branch, but should not dominate teaching.
    assert 8 <= identity_count <= 24


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_first_twenty_draws_meet_profile_floor_in_every_band(band):
    hits = 0
    for index in range(20):
        grid = gen.generate(12000 + index, index * 5 + 1, difficulty=band)
        hits += (len(grid), len(grid[0]), palette_size(grid)) in CANONICAL_PROFILES
    assert hits >= 1


def test_identity_is_lawful_canonical_behavior_not_a_rejection():
    identity_pairs = [pair for pair in canonical_pairs() if pair["input"] == pair["output"]]
    assert len(identity_pairs) == 2
    assert all(gen.self_check(pair["input"]) == [] for pair in identity_pairs)
    for index in range(12):
        grid = gen.generate(91, index, seed_geometry="identity")
        assert gen.self_check(grid) == []
        assert manhattan_output(grid) == grid


def test_declared_shortcut_fits_all_canonical_pairs_and_witness_refutes_it():
    assert all(diagonal_only_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = witness_input()
    intended = manhattan_output(witness)
    rival = diagonal_only_output(witness)
    assert gen.self_check(witness) == []
    assert gen.SEMANTIC_WITNESSES["aligned_seed_pair"](witness)
    assert gen.SEMANTIC_RIVALS["diagonal_only"](witness) == rival
    assert rival != intended
    differing = [
        (r, c)
        for r in range(len(witness))
        for c in range(len(witness[0]))
        if intended[r][c] != rival[r][c]
    ]
    assert differing == [(r, 5) for r in range(2, 8)]


@pytest.mark.parametrize("start", range(12))
def test_every_three_consecutive_default_examples_refute_diagonal_only(start):
    demos = []
    for sample_index in range(start, start + 3):
        grid = gen.generate(777, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": manhattan_output(grid)})
    assert "axis" in {seed_geometry(demo["input"]) for demo in demos}
    assert gen.lesson_identifiable(demos, {"input": demos[0]["input"]}) == []
    assert any(diagonal_only_output(demo["input"]) != demo["output"] for demo in demos)


@pytest.mark.parametrize("start", range(12))
def test_four_example_windows_survive_every_cyclic_query_rotation(start):
    pairs = []
    for sample_index in range(start, start + 4):
        grid = gen.generate(778, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": manhattan_output(grid)})
    for query_index in range(4):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []
        assert any(diagonal_only_output(demo["input"]) != demo["output"] for demo in demos)


@pytest.mark.parametrize("mutation", [
    "open_frame", "extra_nonzero", "third_seed", "seed_on_frame", "marker_9", "bad_dimension"
])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        55, 4, grid_h=10, grid_w=12, frame_color=5,
        seed_geometry="diagonal", seed_color_relation="different",
    )
    scene = observed(grid)
    assert scene["frame_color"] == 5
    if mutation == "open_frame":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 5:
                    grid[r][c] = 0
                    break
            else:
                continue
            break
    elif mutation == "extra_nonzero":
        grid[0][0] = 1
    elif mutation == "third_seed":
        # Put a third seed into a zero strict-interior cell.
        for r in range(1, len(grid) - 1):
            for c in range(1, len(grid[0]) - 1):
                if grid[r][c] == 0:
                    grid[r][c] = 1
                    break
            else:
                continue
            break
    elif mutation == "seed_on_frame":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value not in (0, 5):
                    grid[r][c] = 0
                    grid[1][2] = value
                    break
            else:
                continue
            break
    elif mutation == "marker_9":
        grid[0][0] = 9
    elif mutation == "bad_dimension":
        grid = grid[:7]
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generation_returns_fresh_grids_and_preserves_global_random_state():
    random.seed(12345)
    before = random.getstate()
    a = gen.generate(44, 7)
    after = random.getstate()
    b = gen.generate(44, 7)
    assert before == after
    assert a == b and a is not b and a[0] is not b[0]
    a[0][0] = 9
    assert b[0][0] == 0


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env,
            text=True,
        ))
    assert results[0] == results[1]


def test_independent_audit_schedule_exercises_both_seed_color_relations():
    from reference_probe import audit

    report, _ = audit(gen, 42)
    for row in report["by_band"].values():
        assert set(row["relations"]) == {"same", "different"}


def test_independent_audit_reports_all_cyclic_query_rotations():
    from reference_probe import audit

    report, _ = audit(gen, 12)
    rotations = report["cyclic_query_rotation"]
    assert rotations["windows"] == 48
    assert rotations["rotations"] == 192
    assert rotations["unrefuted_rotations"] == 0
    assert rotations["hook_failures"] == 0
    assert rotations["failure_examples"] == []


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    grids += [gen.generate(319, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(18)]
    assert racket_outputs(grids) == [manhattan_output(grid) for grid in grids]
