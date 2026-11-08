"""Source-bound regressions for the b2387c876b95 generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_examples,
    changed_cells,
    divider,
    intended_output,
    load_generator,
    observed,
    red_cells,
    reflected,
    source_side,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "orientation",
    "source_side",
    "shape_variant",
    "distractor_color",
    "distractor_shape",
}


def _objects(grid):
    """Match the review gate's row-major, same-color 4-connected objects."""
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    }
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        cells = {start}
        todo = [start]
        remaining.remove(start)
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append((color, sorted(cells)))
    return result


def _first_object_only(grid):
    """Independent reproduction of the review gate's measured spatial rival."""
    output = gen.rule_mirror(grid)
    components = _objects(grid)
    for r, row in enumerate(output):
        for c, value in enumerate(row):
            if value == grid[r][c]:
                continue
            distances = [
                min(abs(r - rr) + abs(c - cc) for rr, cc in cells)
                for _color, cells in components
            ]
            if distances.index(min(distances)) != 0:
                output[r][c] = grid[r][c]
    return output


def test_contract_surface_pins_authority_and_observable_axes():
    assert getattr(gen, "RULE_HASH", None) == "d6356bd3481a"
    assert getattr(gen, "VERSION", None) == "3.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.AXES["grid_h"]["valid"] == "9..12"
    assert gen.AXES["grid_w"]["valid"] == "10..13"
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(gen.observe_overrides)
    assert callable(gen.rule_mirror)


def test_every_canonical_input_is_accepted_and_oracle_matches_labels():
    pairs = canonical_examples(include_unlabeled=True)
    assert len(pairs) == 5
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert gen.self_check(source) == [], (pair["split"], pair["pair_index"])
        assert gen.strict_canonical_like(source) == []
        if "output" in pair:
            assert intended_output(source) == pair["output"]
            assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_observable_in_every_band(band):
    requested = {
        "grid_h": 9,
        "grid_w": 10,
        "orientation": "horizontal",
        "source_side": "positive",
        "shape_variant": 11,
        "distractor_color": 9,
        "distractor_shape": 8,
    }
    grid = gen.generate(8128, 17, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid, gen.SOURCE_SHAPES, gen.DISTRACTOR_SHAPES) == requested
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "override",
    [
        {"typo": 1},
        {"grid_h": 8},
        {"grid_w": 9},
        {"grid_h": 13},
        {"grid_w": 14},
        {"orientation": "diagonal"},
        {"source_side": "left"},
        {"shape_variant": -1},
        {"shape_variant": 12},
        {"distractor_color": 5},
        {"distractor_shape": 9},
        {"grid_h": True},
        {"shape_variant": 2.5},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(override):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize(
    ("seed", "sample_index"),
    [
        (True, 0),
        (False, 0),
        (0, True),
        (0, False),
        (0, -1),
        (1.5, 0),
        (0, 1.5),
    ],
)
def test_seed_and_sample_index_are_strict_scalars(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_covers_both_directions_shapes_and_canonical_profiles(band):
    grids = [gen.generate(1701, index, difficulty=band) for index in range(8)]
    stats = [gen.observe_overrides(grid) for grid in grids]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.rule_mirror(grid) == intended_output(grid) for grid in grids)
    assert {item["orientation"] for item in stats} == {"vertical", "horizontal"}
    assert {item["source_side"] for item in stats} == {"negative", "positive"}
    assert {len(red_cells(grid)) for grid in grids} == {3, 4}
    assert len({item["shape_variant"] for item in stats}) >= 4
    assert len({item["distractor_color"] for item in stats}) >= 4
    assert len({item["distractor_shape"] for item in stats}) >= 4
    canonical_sizes = {(10, 11), (12, 10), (9, 13), (11, 12)}
    assert canonical_sizes <= {(item["grid_h"], item["grid_w"]) for item in stats}
    assert grids == [gen.generate(1701, index, difficulty=band) for index in range(8)]


def test_validator_rejects_both_sides_destination_collision_and_missing_distractor():
    base = gen.generate(31, 2, orientation="vertical", source_side="negative")
    orientation, d = divider(base)
    assert orientation == "vertical"

    both_sides = deepcopy(base)
    rr, cc = reflected(next(iter(red_cells(base))), orientation, d)
    both_sides[rr][cc] = 2
    assert gen.self_check(both_sides)

    collision = deepcopy(base)
    rr, cc = reflected(next(iter(red_cells(base))), orientation, d)
    collision[rr][cc] = 9
    assert gen.self_check(collision)

    no_distractor = [[0 if value not in (0, 2, 5) else value for value in row] for row in base]
    assert gen.self_check(no_distractor)


@pytest.mark.parametrize("mutation", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]])
def test_malformed_grids_return_diagnostics_not_exceptions(mutation):
    assert gen.self_check(mutation)


def test_semantic_witnesses_refute_declared_rivals_and_rotations_are_identifiable():
    assert set(gen.SEMANTIC_WITNESSES) == {
        "positive_source",
        "horizontal_divider",
        "triomino_source",
        "nonred_distractor",
        "first_object_refuter",
    }
    assert set(gen.SEMANTIC_RIVALS) == {
        "negative_side_only",
        "vertical_only",
        "tetromino_only",
        "reflect_all_colored",
        "first_object_only",
    }
    for index in range(8):
        grid = gen.generate(9000, index)
        expected = gen.rule_mirror(grid)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            if witness(grid):
                rivals = gen.WITNESS_RIVALS[witness_name]
                assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in rivals)

    for start in range(8):
        grids = [gen.generate(12000 + start, start + offset) for offset in range(4)]
        pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []
            for rival in gen.LESSON_COMPETITORS.values():
                fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                ambiguous = fits and rival(pairs[query_index]["input"]) != pairs[query_index]["output"]
                assert not ambiguous


def test_reported_first_object_shortcut_is_refuted_in_every_query_rotation():
    """Regression for the exact warning emitted by the strict semantic gate."""
    seed = 253315711988339
    start = 22
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, sample_index, difficulty="easy")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        fits = all(_first_object_only(pair["input"]) == pair["output"] for pair in demos)
        changes_query = _first_object_only(query["input"]) != query["output"]
        assert not (fits and changes_query), query_index


def test_reflection_uses_color_three_and_preserves_source_and_distractor():
    grid = gen.generate(77, 3, orientation="horizontal", source_side="positive")
    output = gen.rule_mirror(grid)
    assert output == intended_output(grid)
    changes = changed_cells(grid, output)
    assert changes
    assert {before for _, _, before, _ in changes} == {0}
    assert {after for _, _, _, after in changes} == {3}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                assert output[r][c] == value

@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
@pytest.mark.parametrize("side", ["negative", "positive"])
@pytest.mark.parametrize("shape_variant", range(12))
@pytest.mark.parametrize("distractor_shape", range(9))
def test_every_smallest_declared_geometry_override_cross_is_constructive(
    orientation, side, shape_variant, distractor_shape
):
    requested = {
        "grid_h": 9,
        "grid_w": 10,
        "orientation": orientation,
        "source_side": side,
        "shape_variant": shape_variant,
        "distractor_color": 4,
        "distractor_shape": distractor_shape,
    }
    grid = gen.generate(4400, shape_variant * 10 + distractor_shape, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
