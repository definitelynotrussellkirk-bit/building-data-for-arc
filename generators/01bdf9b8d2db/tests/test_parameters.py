"""Native parametric contract tests for 01bdf9b8d2db."""
from __future__ import annotations

import json
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def test_native_parametric_entrypoints_exist():
    assert (PARAM / "adapter.py").is_file()
    contract_path = PARAM / "promotion.json"
    assert contract_path.is_file()
    contract = json.loads(contract_path.read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["adapter"] == (
        "generators/01bdf9b8d2db/workspace/parametric/adapter.py"
    )
    assert contract["parameters"] == {
        "finish": ["fill_all", "mark_smallest_total"]
    }
    assert contract["default"] == {"finish": "fill_all"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2

import importlib.util
import hashlib
import pytest
from arcpuzzles import Catalog


def _load_adapter():
    path = PARAM / "adapter.py"
    spec = importlib.util.spec_from_file_location("review_parametric_adapter_01bdf9b8d2db", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selected_canonical_program():
    record = Catalog(HOME.parents[1]).get("01bdf9b8d2db")
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_exact_selected_canonical_bytes():
    adapter = _load_adapter()
    canonical = _selected_canonical_program()
    assert adapter.program({"finish": "fill_all"}) == canonical
    assert (PARAM / "canonical.rkt").read_bytes() == canonical.encode("utf-8")
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "e829e66a9c1a766749a02f8fec6de78f84cb5c13db3d8ad9e5e0647d7c2550ab"
    )


def test_alternative_program_is_nonempty_distinct_racket_source():
    adapter = _load_adapter()
    canonical = adapter.program({"finish": "fill_all"})
    alternate = adapter.program({"finish": "mark_smallest_total"})
    assert isinstance(alternate, str) and alternate.strip().startswith("(rule!")
    assert alternate != canonical
    assert alternate == (PARAM / "mark_smallest_total.rkt").read_text()


@pytest.mark.parametrize("settings", [
    None,
    {},
    {"finish": "unknown"},
    {"finish": "fill_all", "extra": 1},
    {"finish": 1},
])
def test_program_rejects_undeclared_settings(settings):
    with pytest.raises(ValueError):
        _load_adapter().program(settings)


def _regions(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and grid[point[0]][point[1]] != 5
                        and point not in seen
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(sorted(cells))
    return result


def _canonical_output(grid):
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for cells in _regions(grid):
        markers = [grid[r][c] for r, c in cells if grid[r][c] not in (0, 5)]
        assert len(markers) == 1
        for r, c in cells:
            out[r][c] = markers[0]
    return out


def _color_totals(filled):
    return {
        color: sum(value == color for row in filled for value in row)
        for color in sorted({value for row in filled for value in row} - {0, 5})
    }


def _alternate_output(grid):
    filled = _canonical_output(grid)
    totals = _color_totals(filled)
    selected = min(totals, key=lambda color: (totals[color], color))
    return [
        [9 if value == selected else value for value in row]
        for row in filled
    ]


def _assert_input_grammar(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    assert all(value == 5 for value in grid[0] + grid[-1])
    assert all(row[0] == row[-1] == 5 for row in grid)
    assert 9 not in {value for row in grid for value in row}
    for cells in _regions(grid):
        markers = [grid[r][c] for r, c in cells if grid[r][c] not in (0, 5)]
        assert len(markers) == 1


@pytest.mark.parametrize("seed", [0, 17, 97])
@pytest.mark.parametrize("demos,queries", [(2, 1), (3, 4), (6, 4)])
def test_generation_is_deterministic_count_independent_and_matched(seed, demos, queries):
    adapter = _load_adapter()
    canonical_settings = {"finish": "fill_all"}
    alternate_settings = {"finish": "mark_smallest_total"}
    canonical = adapter.generate(seed, canonical_settings, demos, queries)
    repeated = adapter.generate(seed, canonical_settings, demos, queries)
    alternate = adapter.generate(seed, alternate_settings, demos, queries)
    assert canonical == repeated
    assert canonical["program_solution"] == adapter.program(canonical_settings)
    assert alternate["program_solution"] == adapter.program(alternate_settings)
    assert len(canonical["train"]) == len(alternate["train"]) == demos
    assert len(canonical["test"]) == len(alternate["test"]) == queries
    assert [pair["input"] for pair in canonical["train"]] == [
        pair["input"] for pair in alternate["train"]
    ]
    assert [pair["input"] for pair in canonical["test"]] == [
        pair["input"] for pair in alternate["test"]
    ]
    long = adapter.generate(seed, canonical_settings, 6, 4)
    assert canonical["train"] == long["train"][:demos]
    assert canonical["test"] == long["test"][:queries]
    serialized = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in canonical["train"] + canonical["test"]
    ]
    assert len(serialized) == len(set(serialized))


@pytest.mark.parametrize("seed", [0, 17, 97])
def test_generated_labels_match_independent_oracle_and_settings_are_visible(seed):
    adapter = _load_adapter()
    canonical = adapter.generate(seed, {"finish": "fill_all"}, 6, 4)
    alternate = adapter.generate(seed, {"finish": "mark_smallest_total"}, 6, 4)
    for index, pair in enumerate(canonical["train"] + canonical["test"]):
        _assert_input_grammar(pair["input"])
        assert pair["output"] == _canonical_output(pair["input"])
        alt_pair = (alternate["train"] + alternate["test"])[index]
        assert alt_pair["output"] == _alternate_output(pair["input"])
        assert alt_pair["output"] != pair["output"]
        totals = _color_totals(pair["output"])
        assert len(totals) >= 3
        assert len(set(totals.values())) == len(totals)
    assert all(
        canonical["train"][index]["output"] != alternate["train"][index]["output"]
        for index in range(2)
    )


def _paint_selected(filled, selected):
    return [[9 if value == selected else value for value in row] for row in filled]


def _rival_outputs(grid):
    filled = _canonical_output(grid)
    totals = _color_totals(filled)
    seed_counts = {
        color: sum(value == color for row in grid for value in row)
        for color in totals
    }
    regions = _regions(grid)
    smallest = min(regions, key=lambda cells: (len(cells), cells[0]))
    smallest_color = next(grid[r][c] for r, c in smallest if grid[r][c] not in (0, 5))
    smallest_only = [row[:] for row in filled]
    for r, c in smallest:
        smallest_only[r][c] = 9
    return {
        "numeric_lowest": _paint_selected(filled, min(totals)),
        "seed_frequency": _paint_selected(
            filled, min(seed_counts, key=lambda color: (seed_counts[color], color))
        ),
        "largest_total": _paint_selected(
            filled, max(totals, key=lambda color: (totals[color], -color))
        ),
        "smallest_chamber_only": smallest_only,
        "smallest_chamber_color": _paint_selected(filled, smallest_color),
    }


def test_two_demonstrations_refute_declared_selector_shortcuts():
    adapter = _load_adapter()
    episode = adapter.generate(0, {"finish": "mark_smallest_total"}, 2, 4)
    for name in _rival_outputs(episode["train"][0]["input"]):
        assert any(
            _rival_outputs(pair["input"])[name] != pair["output"]
            for pair in episode["train"]
        ), name


def test_queries_include_substantive_exact_30_by_30_stress():
    adapter = _load_adapter()
    episode = adapter.generate(17, {"finish": "mark_smallest_total"}, 3, 4)
    stress = episode["test"][3]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    nonzero = sum(value != 0 for row in stress["input"] for value in row)
    colors = {value for row in stress["input"] for value in row} - {0, 5}
    assert nonzero >= 130
    assert len(colors) >= 4
    assert len(_regions(stress["input"])) >= 6
    assert stress["output"] == _alternate_output(stress["input"])


@pytest.mark.parametrize("args", [
    (-1, {"finish": "fill_all"}, 2, 1),
    (True, {"finish": "fill_all"}, 2, 1),
    (0, {"finish": "fill_all"}, 1, 1),
    (0, {"finish": "fill_all"}, 7, 1),
    (0, {"finish": "fill_all"}, 2, 0),
    (0, {"finish": "fill_all"}, 2, 5),
    (0, {"finish": "unknown"}, 2, 1),
])
def test_generate_rejects_invalid_requests(args):
    with pytest.raises(ValueError):
        _load_adapter().generate(*args)


def _load_prototype():
    path = PARAM / "prototype.py"
    spec = importlib.util.spec_from_file_location("review_parametric_prototype_01bdf9b8d2db", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_frequency_output(grid):
    filled = _canonical_output(grid)
    colors = sorted(_color_totals(filled))
    counts = {
        color: sum(value == color for row in grid for value in row)
        for color in colors
    }
    selected = min(colors, key=lambda color: (counts[color], color))
    return _paint_selected(filled, selected), selected


def test_seed_frequency_counterfactual_is_total_and_changes_the_witness():
    prototype = _load_prototype()
    source = prototype.counterfactual_program("seed_frequency")
    assert source.strip().startswith("(rule!")
    witness = prototype.generate(
        0, {"finish": "mark_smallest_total"}, 2, 4
    )["train"][0]
    wrong, wrong_selected = _seed_frequency_output(witness["input"])
    assert prototype.O.intermediate(witness["input"])["selected_color"] == 8
    assert wrong_selected == 1
    assert wrong != witness["output"]
