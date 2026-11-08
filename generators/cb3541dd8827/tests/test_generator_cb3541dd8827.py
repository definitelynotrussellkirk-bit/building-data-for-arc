"""Task-local regression contract for arbitrary-colour seeded frames."""
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
    canonical_pairs,
    color_two_only_output,
    first_frame_only_output,
    frame_color_output,
    frames,
    global_seed_output,
    intended_output,
    load_generator,
    observed,
    root,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(7, 9, 3), (11, 9, 5)}
EXPECTED_AXES = {"grid_h", "grid_w"}
EXPECTED_PROFILES = {
    "canonical_single",
    "canonical_double",
    "broad_double",
    "broad_multi",
}


def _pair(grid):
    return {"input": grid, "output": intended_output(grid)}


def _profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def test_authority_pin_and_honest_public_contract():
    assert gen.RULE_HASH == "6f461f08806c"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert set(gen.SCHEDULE_PROFILES) == EXPECTED_PROFILES
    assert gen.MIN_STRICT_FRAC == 1.0


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_match_both_oracles(pair):
    source = deepcopy(pair["input"])
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert intended_output(source) == pair["output"]
    assert gen.rule_mirror(source) == pair["output"]
    assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 9},
        {"grid_h": 20, "grid_w": 22},
        {"grid_h": 8, "grid_w": 21},
        {"grid_h": 19, "grid_w": 10},
    ],
)
def test_exact_dimension_overrides_are_constructive_and_observable(band, options):
    for sample_index in range(4):
        grid = gen.generate(1729, sample_index, difficulty=band, **options)
        assert gen.self_check(grid, meta={"overrides": options}) == []
        assert {key: observed(grid)[key] for key in EXPECTED_AXES} == options
        assert gen.observe_overrides(grid) == options
        assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "args,overrides",
    [
        ((0, 0), {"grid_heigth": 9}),
        ((0, 0), {"grid_h": 6}),
        ((0, 0), {"grid_h": 21}),
        ((0, 0), {"grid_w": 8}),
        ((0, 0), {"grid_w": 23}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"grid_h": 7.0}),
        ((0, 0), {"grid_w": "9"}),
        ((0, True), {}),
        ((0, -1), {}),
        ((True, 0), {}),
    ],
)
def test_invalid_scalars_unknown_axes_and_out_of_range_values_fail_closed(args, overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(*args, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_sliding_lesson_and_every_query_rotation_refutes_declared_rivals(band):
    for start in range(8):
        grids = [gen.generate(9000 + start, start + offset, difficulty=band) for offset in range(5)]
        assert {
            gen.schedule_profile(9000 + start, start + offset, band)
            for offset in range(4)
        } == EXPECTED_PROFILES
        pairs = [_pair(grid) for grid in grids]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_diverse_and_canonically_anchored(band):
    shapes = set()
    frame_counts = set()
    frame_colors = set()
    seed_colors = set()
    exact_profiles = 0
    for index in range(120):
        grid = gen.generate(8100 + index, index * 11, difficulty=band)
        assert grid == gen.generate(8100 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        frame_counts.add(stats["n_frames"])
        frame_colors.update(stats["frame_colors"])
        seed_colors.update(stats["seed_colors"])
        exact_profiles += _profile(grid) in CANONICAL_PROFILES
        assert intended_output(grid) != grid
    assert len(shapes) >= 12
    assert frame_counts == {1, 2, 3}
    assert len(frame_colors) >= 8
    assert len(seed_colors) >= 8
    assert exact_profiles >= 40


def test_declared_witnesses_really_refute_their_named_rivals():
    grids = [gen.generate(41, index, difficulty="hard") for index in range(4)]
    assert any(gen.SEMANTIC_WITNESSES["non_two_frame"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["multiple_seed_colors"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["multiple_frames"](grid) for grid in grids)
    for grid in grids:
        expected = intended_output(grid)
        for witness, rival_names in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in rival_names)
    multi = next(grid for grid in grids if observed(grid)["n_frames"] >= 2)
    assert color_two_only_output(multi) == gen.SEMANTIC_RIVALS["color_two_frames_only"](multi)
    assert global_seed_output(multi) == gen.SEMANTIC_RIVALS["single_global_seed"](multi)
    assert first_frame_only_output(multi) == gen.SEMANTIC_RIVALS["first_frame_only"](multi)
    assert frame_color_output(multi) == gen.SEMANTIC_RIVALS["fill_with_frame_color"](multi)


@pytest.mark.parametrize(
    "mutation",
    ["break_frame", "remove_seed", "second_seed_color", "second_same_seed", "stray_color"],
)
def test_self_check_rejects_structural_mutations(mutation):
    grid = gen.generate(313, 3, difficulty="hard", grid_h=15, grid_w=17)
    parsed = frames(grid)
    frame = parsed[0]
    if mutation == "break_frame":
        grid[frame["r1"]][frame["c1"]] = 0
    elif mutation == "remove_seed":
        row, col = frame["seed_cells"][0]
        grid[row][col] = 0
    elif mutation in ("second_seed_color", "second_same_seed"):
        seed_color = frame["seed_colors"][0]
        replacement = seed_color if mutation == "second_same_seed" else next(
            color for color in range(1, 10)
            if color not in (frame["frame_color"], seed_color)
        )
        for row in range(frame["r1"] + 1, frame["r2"]):
            for col in range(frame["c1"] + 1, frame["c2"]):
                if grid[row][col] == 0:
                    grid[row][col] = replacement
                    break
            else:
                continue
            break
    else:
        owners = [
            (row, col)
            for row, line in enumerate(grid)
            for col, value in enumerate(line)
            if value == 0
            and not any(
                item["r1"] < row < item["r2"] and item["c1"] < col < item["c2"]
                for item in parsed
            )
        ]
        row, col = owners[0]
        grid[row][col] = 9
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "bad",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)], [[10] * 9 for _ in range(7)]],
)
def test_malformed_grid_is_diagnostic_not_exception(bad):
    assert gen.self_check(bad)


def test_generated_inputs_match_real_racket_authority():
    from arcpuzzles import Catalog

    grids = [
        gen.generate(601, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(4)
    ]
    receipt = Catalog(root()).apply(gen.TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        intended_output(grid) for grid in grids
    ]


def test_generation_is_independent_of_python_hash_seed():
    source = str(Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")))
    script = (
        "import importlib.util,json,sys;"
        "s=importlib.util.spec_from_file_location('g',sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31337,19,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "777"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output([sys.executable, "-B", "-c", script, source], env=env, text=True)
        )
    assert outputs[0] == outputs[1]
