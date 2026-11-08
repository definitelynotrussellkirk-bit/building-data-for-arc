"""Task-local regression tests for the reviewed 92f4d4eb0dbb sampler."""
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
    RIVALS,
    canonical_pairs,
    canonical_rule_hash,
    inclusive_midpoint,
    intended_output,
    load_generator,
    observed,
    pixel_centroid,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _lesson(seed, start, band):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    return pairs


def test_pins_authority_and_declares_only_observable_axes():
    assert canonical_rule_hash() == "5e129c41777b"
    assert gen.RULE_HASH == canonical_rule_hash()
    assert gen.VERSION == "3.1.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "span", "shape_kind"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_even",
        "canonical_odd",
        "broad_even",
        "broad_odd",
    )
    assert set(gen.SHAPE_KINDS) == {
        "frame",
        "ladder",
        "diamond",
        "zigzag",
        "notched_frame",
    }
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "inclusive_midpoint",
        "pixel_centroid",
    }
    assert set(gen.LESSON_COMPETITORS) == {
        "inclusive_midpoint",
        "pixel_centroid",
    }
    assert set(gen.SEMANTIC_WITNESSES) == {
        "strict_midpoint",
        "bounding_box_midpoint",
    }


@pytest.mark.parametrize(
    "pair", canonical_pairs(),
    ids=lambda pair: f"{len(pair['input'])}x{len(pair['input'][0])}",
)
def test_accepts_canonical_and_independent_oracle_matches(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 7, "span": 5, "shape_kind": "frame"},
        {"grid_h": 14, "grid_w": 14, "span": 7, "shape_kind": "zigzag"},
        {"grid_h": 9, "grid_w": 11, "span": 6, "shape_kind": "diamond"},
        {"grid_h": 10, "grid_w": 8, "span": 5, "shape_kind": "ladder"},
        {"grid_h": 11, "grid_w": 12, "span": 7, "shape_kind": "notched_frame"},
    ],
)
def test_exact_overrides_are_constructive_and_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 15),
        ("grid_w", 6),
        ("grid_w", 15),
        ("span", 4),
        ("span", 8),
        ("shape_kind", "unknown"),
        ("grid_h", True),
        ("span", 5.0),
        ("shape_kind", 1),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_rejects_non_exact_integer_seed(seed):
    with pytest.raises(ValueError, match="seed"):
        gen.generate(seed, 0)


@pytest.mark.parametrize(
    "difficulty",
    [True, False, 0, 1.0, "__invalid_difficulty__"],
)
def test_rejects_invalid_difficulty_scalars(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_has_canonical_scale_and_odd_midpoint_witnesses_in_each_band(band):
    canonical_dims = {(8, 9), (7, 7), (9, 9), (9, 11)}
    profiles = []
    exact = 0
    odd_witnesses = 0
    for sample_index in range(16):
        grid = gen.generate(2718, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        profile = gen.schedule_profile(2718, sample_index, band)
        profiles.append(profile)
        stats = observed(grid)
        exact += int((stats["grid_h"], stats["grid_w"]) in canonical_dims)
        if stats["span"] % 2:
            odd_witnesses += 1
            assert inclusive_midpoint(grid) != intended_output(grid)
            assert gen.SEMANTIC_WITNESSES["strict_midpoint"](grid)
        else:
            assert inclusive_midpoint(grid) == intended_output(grid)
    assert set(profiles) == set(gen.SCHEDULE_PROFILES)
    assert exact >= 8
    assert odd_witnesses >= 8


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_cyclic_three_demo_lesson_refutes_declared_shortcut(band):
    for start in range(len(gen.SCHEDULE_PROFILES)):
        lesson = _lesson(314159, start, band)
        demos, query = lesson[: gen.EXAMPLES_NEEDED], lesson[-1]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_declared_shortcut_fits_all_canonical_pairs_but_generated_odd_case_refutes_it():
    for pair in canonical_pairs():
        assert inclusive_midpoint(pair["input"]) == pair["output"]
        assert gen.CANONICAL_SHORTCUTS["inclusive_midpoint"](pair["input"]) == pair["output"]
        assert pixel_centroid(pair["input"]) == pair["output"]
        assert gen.CANONICAL_SHORTCUTS["pixel_centroid"](pair["input"]) == pixel_centroid(pair["input"])
    grid = gen.generate(99, 1, difficulty="medium")
    assert observed(grid)["span"] % 2 == 1
    assert inclusive_midpoint(grid) != intended_output(grid)


def _centroid_counterexample():
    grid = [[0] * 7 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 6):
            if r in {1, 5} or c in {1, 5}:
                grid[r][c] = 1
    grid[5][3] = 0
    return grid


def test_notched_shape_refutes_pixel_centroid_shortcut():
    witness = _centroid_counterexample()
    assert gen.self_check(witness) == []
    assert gen.strict_canonical_like(witness) == []
    intended = intended_output(witness)
    rival = pixel_centroid(witness)
    assert gen.CANONICAL_SHORTCUTS["pixel_centroid"](witness) == rival
    assert rival != intended
    assert gen.SEMANTIC_WITNESSES["bounding_box_midpoint"](witness)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_each_three_demo_schedule_window_contains_a_centroid_witness(band):
    for start in range(len(gen.SCHEDULE_PROFILES)):
        lesson = _lesson(8675309, start, band)
        demos = lesson[: gen.EXAMPLES_NEEDED]
        assert any(
            gen.CANONICAL_SHORTCUTS["pixel_centroid"](pair["input"])
            != pair["output"]
            for pair in demos
        )


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(7)],
        [[1] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(3)] + [[0, 0, 0, 1, 0, 0, 0]] + [[0] * 7 for _ in range(3)],
        [[0] * 7 for _ in range(2)] + [[0, 0, 1, 1, 1, 1, 0]] + [[0] * 7 for _ in range(4)],
        [[0] * 7 for _ in range(2)] + [[0, 0, 1, 1, 0, 0, 0], [0, 0, 1, 1, 0, 0, 0]] + [[0] * 7 for _ in range(3)],
        [[0] * 7 for _ in range(2)] + [[0, 0, 0, 2, 0, 0, 0]] * 5,
    ],
)
def test_malformed_and_degenerate_grids_return_diagnostics(grid):
    assert gen.self_check(grid)


def test_validator_rejects_disconnected_and_missing_row_mutations():
    grid = gen.generate(44, 0, grid_h=10, grid_w=10, span=6, shape_kind="frame")
    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    r0, r1 = min(r for r, _ in ones), max(r for r, _ in ones)
    c0, c1 = min(c for _, c in ones), max(c for _, c in ones)

    disconnected = deepcopy(grid)
    disconnected[r0][c0] = 0
    disconnected[0 if r0 > 0 else len(grid) - 1][0 if c0 > 0 else len(grid[0]) - 1] = 1
    assert gen.self_check(disconnected)

    missing_row = deepcopy(grid)
    middle = (r0 + r1) // 2
    missing_row[middle] = [0] * len(missing_row[middle])
    assert gen.self_check(missing_row)


def test_sampler_has_material_diversity_without_losing_contract():
    grids = [gen.generate(123456 + i, i, difficulty=("easy", "medium", "hard")[i % 3])
             for i in range(96)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert len({str(grid) for grid in grids}) >= 80
    assert {observed(grid)["shape_kind"] for grid in grids} == set(gen.SHAPE_KINDS)


def test_keyed_rng_is_independent_of_python_hash_seed():
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


def test_real_racket_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(
        gen.generate(808, i, difficulty=("easy", "medium", "hard")[i % 3])
        for i in range(12)
    )
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_lesson_probe_uses_stable_source_bound_sampler_contract():
    import lesson_probe

    assert lesson_probe.TASK_ID == gen.TASK_ID
    assert lesson_probe.BANDS == ("easy", "medium", "hard")
    assert lesson_probe.N_DEMOS == gen.EXAMPLES_NEEDED
    assert lesson_probe.N_QUERIES == 1
    assert lesson_probe.STRIDE % len(gen.SCHEDULE_PROFILES) in {1, 3}
    assert lesson_probe.pinned_seed("easy", 7) == lesson_probe.pinned_seed("easy", 7)
    assert lesson_probe.pinned_seed("easy", 7) != lesson_probe.pinned_seed("hard", 7)
