"""Task-local regression suite; workspace helpers are independent of production."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_FITTING_RIVALS,
    CANONICAL_GEOMETRY_RIVALS,
    bbox_center_output,
    canonical_pairs,
    load_generator,
    max_blob_size,
    observed,
    racket_outputs,
    target_corner_indices,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_bbox_center_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert bbox_center_output(pair["input"]) == pair["output"]


def test_generator_declares_exact_canonical_rule_pin_and_only_honest_axes():
    assert gen.RULE_HASH == "ef9264e6f3e7"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_blobs"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_five_draw_schedule_has_two_canonical_scale_residues_and_three_strong_witnesses():
    assert gen.SCHEDULE_PERIOD == 5
    profiles = [gen.schedule_profile(431, index) for index in range(gen.SCHEDULE_PERIOD)]
    assert profiles.count("canonical_scale") == 2
    assert set(profiles) == set(gen.SCHEDULE_PROFILES)
    for index, profile in enumerate(profiles):
        grid = gen.generate(431, index)
        intended = bbox_center_output(grid)
        if profile == "canonical_scale":
            assert (len(grid), len(grid[0])) == (6, 6)
            assert max_blob_size(grid) <= 2
        else:
            assert all(rival(grid) != intended for rival in gen.SEMANTIC_RIVALS.values())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    {"grid_h": 6, "grid_w": 6, "n_blobs": 2},
    {"grid_h": 6, "grid_w": 14, "n_blobs": 5},
    {"grid_h": 14, "grid_w": 6, "n_blobs": 5},
    {"grid_h": 14, "grid_w": 14, "n_blobs": 2},
])
def test_exact_overrides_are_constructive_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1), ("grid_h", 5), ("grid_h", 15), ("grid_w", 5), ("grid_w", 15),
    ("n_blobs", 1), ("n_blobs", 6), ("grid_h", True), ("grid_w", 7.5),
    ("n_blobs", "2"),
])
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_all_legal_axis_combinations_are_total_exact_and_deterministic():
    for height in range(6, 15):
        for width in range(6, 15):
            for n_blobs in range(2, 6):
                options = {"grid_h": height, "grid_w": width, "n_blobs": n_blobs}
                grid = gen.generate(911 + height, 17 * width + n_blobs, **options)
                assert gen.self_check(grid) == []
                assert observed(grid) == options
                assert gen.observe_overrides(grid) == options
                assert grid == gen.generate(911 + height, 17 * width + n_blobs, **options)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_has_profile_support_and_refutes_every_declared_shortcut(band):
    shapes, inputs, palette_sizes, blob_counts, target_bins = set(), set(), set(), set(), set()
    canonical_profiles = set()
    rival_refutations = {name: 0 for name in CANONICAL_GEOMETRY_RIVALS}
    for index in range(160):
        seed, sample_index = 2000 + index, index * 3 + 3
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        intended = bbox_center_output(grid)
        assert intended != grid
        for name, rival in CANONICAL_GEOMETRY_RIVALS.items():
            rival_refutations[name] += rival(grid) != intended
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        inputs.add(tuple(tuple(row) for row in grid))
        palette_sizes.add(len({cell for row in grid for cell in row}))
        blob_counts.add(stats["n_blobs"])
        target_bins.update(target_corner_indices(grid))
        if (stats["grid_h"], stats["grid_w"], len({cell for row in grid for cell in row})) in {
            (6, 6, 7), (6, 6, 8)
        }:
            canonical_profiles.add((stats["grid_h"], stats["grid_w"],
                                    len({cell for row in grid for cell in row})))
    assert len(shapes) >= 10
    assert len(inputs) >= 150
    assert palette_sizes == {7, 8, 9, 10}
    assert blob_counts == {2, 3, 4, 5}
    assert {0, 1, 2, 3} <= target_bins
    assert canonical_profiles
    assert all(count >= 80 for count in rival_refutations.values()), rival_refutations


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    pairs = canonical_pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == set(CANONICAL_FITTING_RIVALS)
    assert set(gen.SEMANTIC_RIVALS) == set(CANONICAL_GEOMETRY_RIVALS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    for name in set(gen.SEMANTIC_RIVALS) - set(gen.CANONICAL_SHORTCUTS):
        assert any(gen.SEMANTIC_RIVALS[name](pair["input"]) != pair["output"] for pair in pairs), name


def test_semantic_contract_is_live_across_each_schedule_cycle():
    for seed in range(16):
        hits = {name: 0 for name in gen.SEMANTIC_RIVALS}
        for offset in range(gen.SCHEDULE_PERIOD):
            grid = gen.generate(700 + seed, offset)
            assert gen.strict_canonical_like(grid) == []
            assert gen.SEMANTIC_WITNESSES["bbox_center_exact_tie"](grid)
            for name in gen.SEMANTIC_RIVALS:
                hits[name] += gen.SEMANTIC_WITNESSES[f"counterexample_{name}"](grid)
        assert all(count >= 3 for count in hits.values()), hits


def test_synthetic_lessons_identify_query_against_declared_competitors():
    for start in range(gen.SCHEDULE_PERIOD):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(991 + start, start + offset)
            pairs.append({"input": grid, "output": bbox_center_output(grid)})
        assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


@pytest.mark.parametrize("mutation", [
    "missing_corner", "duplicate_corner_color", "corner_color_reused",
    "one_blob", "disconnected_same_color", "bad_cell", "too_small", "too_large",
])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(4, 2, grid_h=8, grid_w=9, n_blobs=3)
    if mutation == "missing_corner":
        grid[0][0] = 0
    elif mutation == "duplicate_corner_color":
        grid[0][-1] = grid[0][0]
    elif mutation == "corner_color_reused":
        grid[1][1] = grid[0][0]
    elif mutation == "one_blob":
        corner_colors = {grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1]}
        blob_colors = sorted({v for row in grid for v in row if v and v not in corner_colors})
        for color in blob_colors[1:]:
            for row in range(len(grid)):
                for col in range(len(grid[0])):
                    if grid[row][col] == color:
                        grid[row][col] = 0
    elif mutation == "disconnected_same_color":
        corner_colors = {grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1]}
        color = next(v for row in grid for v in row if v and v not in corner_colors)
        grid[1][-2] = color
    elif mutation == "bad_cell":
        grid[1][1] = 10
    elif mutation == "too_small":
        grid = [row[:5] for row in grid[:5]]
    elif mutation == "too_large":
        grid = [row + [0] * 7 for row in grid] + [[0] * 16 for _ in range(7)]
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 6 for _ in range(6)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
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
            env=env, text=True,
        ))
    assert outputs[0] == outputs[1]


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319 + index, index, grid_h=6 + index % 9,
                           grid_w=6 + (index * 5) % 9, n_blobs=2 + index % 4)
              for index in range(24)]
    assert racket_outputs(grids) == [bbox_center_output(grid) for grid in grids]


def test_oracle_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(19, 8, n_blobs=5)
    before = deepcopy(grid)
    bbox_center_output(grid)
    for rival in gen.LESSON_COMPETITORS.values():
        rival(grid)
    assert grid == before
