"""Focused native contracts for object-derived diagonal completion."""
from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
BBOX = {"completion": "bbox"}
GAPS = {"completion": "diagonal_gaps"}


@pytest.fixture(scope="module")
def family():
    path = HOME / "workspace/parametric/prototype.py"
    assert path.is_file(), "native diagonal-gap family is missing"
    spec = importlib.util.spec_from_file_location("tested_68a312813b77_family", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def example():
    grid = [[0] * 10 for _ in range(8)]
    for r, c in ((0, 4), (1, 3), (2, 2)):
        grid[r][c] = 1
    for r, c in ((3, 8), (4, 7), (5, 6), (6, 5)):
        grid[r][c] = 3
    return grid


def test_literal_interobject_fill_and_exact_default(family):
    grid = example()
    ordinary, composed = family.transform(grid, BBOX), family.transform(grid, GAPS)
    assert ordinary[3][4] == 0 and composed[3][4] == 7
    assert ordinary[0][8] == composed[0][8] == 0
    assert composed[1][4] == 7  # original per-object bbox completion remains
    assert all(composed[r][c] == grid[r][c] for r in range(8) for c in range(10) if grid[r][c])
    assert family.program(BBOX) == "(rule! (lambda (g) (fill-object-bboxes-8 g 7)))"
    assert family.program(GAPS) != family.program(BBOX)


def test_components_use_same_color_and_eight_connectivity(family):
    grid = [[1, 2], [0, 1]]
    objects = family.components(grid)
    assert [(obj["color"], obj["cells"], obj["bbox"]) for obj in objects] == [
        (1, [[0, 0], [1, 1]], [0, 0, 1, 1]), (2, [[0, 1]], [0, 1, 0, 1])]
    assert len(family.components(grid, connectivity=4)) == 3
    assert family.transform(grid, BBOX) == [[1, 2], [7, 1]]


def test_nearest_pair_length_is_conditioned_on_left_edge_capacity(family):
    # Three starts above the left edge cannot support a five-cell slash.
    episode = family.generate(0, GAPS, demos=6, queries=4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4


def _wrong_rule(family, grid, completion, mistake):
    """Three concrete hypotheses from the independently executed before audit."""
    original = family.components(grid)
    if mistake == "color_blind":
        original = family.components([[int(v != 0) for v in row] for row in grid])
    result = [row[:] for row in grid]
    for obj in original:
        r0, c0, r1, c1 = obj["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if result[r][c] == 0:
                    result[r][c] = 7
    if completion == "bbox":
        return result
    objects = family.components(result) if mistake == "resegment" else original
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                continue
            for a in objects:
                for b in objects:
                    au = [rr+cc for rr, cc in a["cells"]]
                    bu = [rr+cc for rr, cc in b["cells"]]
                    av = {rr-cc for rr, cc in a["cells"]}
                    bv = {rr-cc for rr, cc in b["cells"]}
                    vertical = (r-c in av and r-c in bv) if mistake == "raw_v" else (
                        max(min(av), min(bv)) <= r-c <= min(max(av), max(bv)))
                    if max(au) < r+c < min(bu) and vertical:
                        result[r][c] = 7
    return result


@pytest.mark.parametrize("seed", [0, 17, 22])
@pytest.mark.parametrize("completion,mistake", [("bbox", "color_blind"),
    ("diagonal_gaps", "color_blind"), ("diagonal_gaps", "raw_v"),
    ("diagonal_gaps", "resegment")])
def test_first_two_teach_original_colored_objects_and_projected_interiors(family, seed, completion, mistake):
    episode = family.generate(seed, {"completion": completion}, demos=2, queries=4)
    assert any(_wrong_rule(family, pair["input"], completion, mistake) != pair["output"]
               for pair in episode["train"])


@pytest.mark.parametrize("demos", range(2, 7))
def test_independent_counts_matched_inputs_prefix_and_novelty(family, demos):
    episode = family.generate(17, GAPS, demos=demos, queries=4)
    short = family.generate(17, GAPS, demos=demos, queries=1)
    ordinary = family.generate(17, BBOX, demos=demos, queries=4)
    assert len(episode["train"]) == demos and len(episode["test"]) == 4
    assert short["train"] == episode["train"] and short["test"] == episode["test"][:1]
    pairs = episode["train"] + episode["test"]
    assert [p["input"] for p in pairs] == [p["input"] for p in ordinary["train"] + ordinary["test"]]
    assert len({json.dumps(p["input"]) for p in pairs}) == len(pairs)
    assert episode["program_solution"] == family.program(GAPS)
    assert all(family.transform(p["input"], BBOX) != p["output"] for p in episode["train"][:2])


@pytest.mark.parametrize("seed", [0, 17, 87])
def test_teaching_roles_and_substantive_30_canvas(family, seed):
    episode = family.generate(seed, GAPS)
    for pair in episode["train"][:2]:
        objects = family.components(pair["input"])
        assert any(len({r+c for r, c in obj["cells"]}) > 1 for obj in objects)
        h, w = len(pair["input"]), len(pair["input"][0])
        assert any(0 in obj["bbox"][:2] or obj["bbox"][2] == h-1 or obj["bbox"][3] == w-1 for obj in objects)
        assert any(0 < obj["bbox"][0] <= obj["bbox"][2] < h-1 and 0 < obj["bbox"][1] <= obj["bbox"][3] < w-1 for obj in objects)
    grid = episode["test"][3]["input"]
    assert len(grid) == len(grid[0]) == 30
    count = Counter(v for row in grid for v in row)
    assert count[0] >= 5 and count[7] == 0
    assert 900 - count[0] >= 130
    assert sum(any(row) for row in grid) >= 27
    assert sum(any(grid[r][c] for r in range(30)) for c in range(30)) >= 27
    for bottom, right in ((False, False), (False, True), (True, False), (True, True)):
        assert sum(grid[r][c] != 0 for r in range(30) for c in range(30)
                   if (r >= 15) == bottom and (c >= 15) == right) >= 20


@pytest.mark.parametrize("field,value", [("seed", True), ("seed", -1), ("seed", 2**63),
    ("demos", True), ("demos", 1), ("demos", 7), ("demos", 3.0),
    ("queries", True), ("queries", 0), ("queries", 5)])
def test_request_types_and_bounds(family, field, value):
    args = {"seed": 0, "settings": GAPS, "demos": 3, "queries": 4}
    args[field] = value
    with pytest.raises(ValueError):
        family.generate(**args)


@pytest.mark.parametrize("settings", [None, {}, {"completion": True}, {"completion": "other"},
                                      {"completion": "bbox", "extra": 0}])
def test_exact_settings(family, settings):
    with pytest.raises(ValueError):
        family.program(settings)
    with pytest.raises(ValueError):
        family.generate(0, settings)
