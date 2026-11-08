"""Behavioral checks for the separate native parametric family."""
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(name):
    path = HOME / "workspace" / "parametric" / (name + ".py")
    assert path.is_file(), f"Missing native parametric implementation: {path.name}"
    spec = importlib.util.spec_from_file_location("aspect_parameters_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_adapter_preserves_exact_canonical_source():
    from arcpuzzles import Catalog
    module = load("adapter")
    programs = {row["program_solution"] for row in Catalog(".").get("f47990415137")["variants"]}
    assert programs == {module.program({"reference": "axes"})}
    assert module.program({"reference": "largest"}) != next(iter(programs))


def test_relative_aspect_uses_cell_count_anchor_and_exact_ratios():
    module = load("prototype")
    # Dense 4x2 anchor (8 cells); 3x3 L has bigger box but only 5 cells.
    grid = [[0] * 14 for _ in range(9)]
    shapes = [
        (1, [(r, c) for r in range(4) for c in range(2)]),
        (7, [(0, c + 5) for c in range(3)] + [(r, 5) for r in range(1, 3)]),
        (1, [(r, 10) for r in range(4)]),
        (8, [(6, 0), (7, 0)]),
        (9, [(5, 5), (6, 5), (7, 5), (5, 6)]),
    ]
    for color, cells in shapes:
        for r, c in cells:
            grid[r][c] = color
    output = module.transform(grid, {"reference": "largest"})
    # Ratios 2,1,4,2,1.5 -> equal,below,above,equal,below.
    for (_, cells), expected in zip(shapes, (4, 3, 2, 4, 3)):
        assert {output[r][c] for r, c in cells} == {expected}
    assert output[6][6] == 0


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_matched_inputs_and_distinct_pairs(demos, queries):
    module = load("adapter")
    a = module.generate(17, {"reference": "axes"}, demos, queries)
    b = module.generate(17, {"reference": "largest"}, demos, queries)
    assert len(a["train"]) == demos and len(a["test"]) == queries
    inputs = [p["input"] for p in a["train"] + a["test"]]
    assert inputs == [p["input"] for p in b["train"] + b["test"]]
    assert len({json.dumps(g) for g in inputs}) == demos + queries
    assert any(x["output"] != y["output"] for x, y in zip(a["train"], b["train"]))
    assert a == module.generate(17, {"reference": "axes"}, demos, queries)


def test_query_prefix_does_not_depend_on_future_query_or_demo_count():
    module = load("adapter")
    one = module.generate(31, {"reference": "largest"}, 2, 1)
    four = module.generate(31, {"reference": "largest"}, 2, 4)
    six = module.generate(31, {"reference": "largest"}, 6, 4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1] == six["test"][:1]
    assert one["train"] == six["train"][:2]


@pytest.mark.parametrize("size", [8, 30])
def test_scene_size_boundaries_have_real_content(size):
    module = load("prototype")
    grid = module.sample_scene(91, size, size, anchor_aspect="tall")
    assert len(grid) == size and all(len(row) == size for row in grid)
    objects = module.components(grid)
    counts = sorted((len(cells) for _, cells in objects), reverse=True)
    assert counts[0] > counts[1]
    assert len(objects) >= 4
    assert {module.aspect(cells) for _, cells in objects} >= {"tall", "wide", "square"}
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    if size == 30:
        assert len(objects) >= 8
        assert sum(v != 0 for row in grid for v in row) >= 100
        occupied = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
        assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= 25
        assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 25


@pytest.mark.parametrize("demos,queries", [(1,4),(7,4),(3,0),(3,5),(True,4),(3,False),(3.0,4)])
def test_invalid_counts_fail_closed(demos, queries):
    with pytest.raises(ValueError):
        load("adapter").generate(0, {"reference": "axes"}, demos, queries)


@pytest.mark.parametrize("settings", [{}, {"reference":"unknown"}, {"reference":"axes","x":1}, {"reference":True}])
def test_invalid_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        load("adapter").program(settings)


@pytest.mark.parametrize("dimensions", [(7,8),(31,30),(8,True),(8.0,9)])
def test_invalid_scene_dimensions_fail_closed(dimensions):
    with pytest.raises(ValueError):
        load("prototype").sample_scene(0, *dimensions)


def test_minimum_square_reference_is_uniquely_largest():
    module = load("prototype")
    grid = module.sample_scene(0, 8, 8, anchor_aspect="square")
    groups = module.components(grid)
    counts = sorted((len(cells) for _, cells in groups), reverse=True)
    assert counts[0] > counts[1]
    assert module.aspect(max(groups, key=lambda x: len(x[1]))[1]) == "square"


@pytest.mark.parametrize("seed,demos", [(3, 2), (2, 6)])
def test_teaching_distractors_cannot_tie_or_replace_the_reference(seed, demos):
    module = load("prototype")
    episode = module.generate(seed, {"reference": "largest"}, demos, 4)
    for index, pair in enumerate(episode["train"]):
        groups = module.components(pair["input"])
        ordered = sorted(groups, key=lambda x: len(x[1]), reverse=True)
        assert len(ordered[0][1]) > len(ordered[1][1])
        assert module.aspect(ordered[0][1]) == ("tall" if index % 2 == 0 else "wide")


@pytest.mark.parametrize("seed", [22, 42])
def test_first_raster_reference_shortcut_is_refuted_by_demonstrations(seed):
    module = load("prototype")
    episode = module.generate(seed, {"reference": "largest"}, 2, 4)
    separated = []
    for pair in episode["train"]:
        groups = module.components(pair["input"])
        fh, fw = module.dimensions(groups[0][1])
        ah, aw = module.dimensions(max(groups, key=lambda x: len(x[1]))[1])
        separated.append(fh * aw != fw * ah)
    assert any(separated), "first-raster object must not fit every demonstration as the reference"


def test_bbox_area_reference_cannot_mimic_axes_on_all_demonstrations():
    module = load("prototype")
    episode = module.generate(3, {"reference": "axes"}, 2, 4)
    nonsquare = []
    for pair in episode["train"]:
        groups = module.components(pair["input"])
        box_max = max(groups, key=lambda x: __import__("math").prod(module.dimensions(x[1])))
        h, w = module.dimensions(box_max[1])
        nonsquare.append(h != w)
    assert any(nonsquare), "a bbox-selected reference must be distinguishable from the fixed axes rule"
