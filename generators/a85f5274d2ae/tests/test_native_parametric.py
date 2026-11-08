"""Bounded behavioral checks for the native four-setting episode adapter.

These tests exercise Python generation and independently derived labels. Native
qualification separately replays every retained label through protected Racket.
"""
from copy import deepcopy
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK = "a85f5274d2ae"
HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / "shared/runtime").is_dir())
PARAMETRIC = HOME / "workspace/parametric"
SETTINGS = (0, 1, 2, "target_panel_count")
NOISE = {1, 2, 3, 4, 8}
sys.path.insert(0, str(ROOT / "shared/runtime"))


@lru_cache(maxsize=None)
def _load(path):
    path = Path(path)
    assert path.is_file(), f"Missing native feature source: {path}"
    name = "_a85_native_test_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load(PARAMETRIC / "adapter.py")


def _native():
    return _load(PARAMETRIC / "native.py")


@lru_cache(maxsize=1)
def _canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
        programs = {row["program_solution"] for line in stream if line.strip()
                    for row in [json.loads(line)] if row.get("task_id") == TASK}
    assert len(programs) == 1
    return programs.pop()


def _facts(grid):
    """Derive panel membership without using either implementation's parser."""
    h, w = len(grid), len(grid[0])
    marker, = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    target, = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    rows = [r for r in range(h) if set(grid[r]) == {0}]
    cols = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    assert len(rows) == len(cols) == 2
    row_edges, col_edges = [-1, *rows, h], [-1, *cols, w]
    panels = {}
    for ri in range(3):
        for ci in range(3):
            cells = [(r, c) for r in range(row_edges[ri] + 1, row_edges[ri + 1])
                     for c in range(col_edges[ci] + 1, col_edges[ci + 1])]
            panels[ri, ci] = [point for point in cells if grid[point[0]][point[1]] in NOISE]
            if target in cells:
                selected = (ri, ci)
    return marker, target, rows, cols, panels, selected


def _expected(grid, setting):
    marker, target, _, _, panels, selected = _facts(grid)
    tolerance = len(panels[selected]) if setting == "target_panel_count" else setting
    dr, dc = target[0] - marker[0], target[1] - marker[1]
    step = tuple(0 if abs(d) <= tolerance else (1 if d > 0 else -1) for d in (dr, dc))
    answer = deepcopy(grid)
    answer[marker[0]][marker[1]] = 5
    answer[marker[0] + step[0]][marker[1] + step[1]] = 9
    answer[target[0]][target[1]] = 9
    return answer


def _fixed_direction_output(grid, setting, fixed_step):
    """Independent rival: retain the threshold gates but ignore target signs."""
    marker, target, _, _, panels, selected = _facts(grid)
    tolerance = len(panels[selected]) if setting == "target_panel_count" else setting
    deltas = (target[0] - marker[0], target[1] - marker[1])
    step = tuple(0 if abs(delta) <= tolerance else direction
                 for delta, direction in zip(deltas, fixed_step))
    output = deepcopy(grid)
    output[marker[0]][marker[1]] = 5
    output[marker[0] + step[0]][marker[1] + step[1]] = 9
    output[target[0]][target[1]] = 9
    return output


@pytest.mark.parametrize("seed", (0, 17))
def test_minimum_demonstrations_eliminate_query_harmful_fixed_directions(seed):
    """Catch one-quadrant teaching and never-activated-axis shortcuts."""
    adapter = _adapter()
    minimum = json.loads((PARAMETRIC / "promotion.json").read_text())["limits"]["demos"][0]
    for setting in SETTINGS:
        episode = adapter.generate(seed, {"axis_tolerance": setting}, minimum, 4)
        for row_step in (-1, 0, 1):
            for col_step in (-1, 0, 1):
                fixed = (row_step, col_step)
                if all(_fixed_direction_output(pair["input"], setting, fixed) == pair["output"]
                       for pair in episode["train"]):
                    assert all(_fixed_direction_output(pair["input"], setting, fixed) == pair["output"]
                               for pair in episode["test"]), (seed, setting, fixed, minimum)


def _freeze(grid):
    return tuple(map(tuple, grid))


def _inputs(episode):
    return {split: [pair["input"] for pair in episode[split]] for split in ("train", "test")}


def test_default_program_preserves_exact_selected_canonical_bytes():
    adapter = _adapter()
    assert adapter.program({"axis_tolerance": 1}) == _canonical()
    programs = [adapter.program({"axis_tolerance": value}) for value in SETTINGS]
    assert len(set(programs)) == 4
    episode = adapter.generate(0, {"axis_tolerance": 1}, 4, 4)
    assert episode["program_solution"] == _canonical()


def test_invalid_typed_settings_counts_and_seeds_are_rejected():
    adapter = _adapter()
    bad_settings = [None, [], {}, {"axis_tolerance": 1, "extra": 0}]
    bad_settings += [{"axis_tolerance": value}
                     for value in (True, False, -1, 3, 1.0, "1", "unknown", None)]
    for setting in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(setting)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, setting, 4, 4)
    for seed in (True, False, -1, 1.0, "0"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"axis_tolerance": 1}, 4, 4)
    for demos in (True, False, -1, 0, 1, 2, 3, 7, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"axis_tolerance": 1}, demos, 4)
    for queries in (True, False, 0, 3, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"axis_tolerance": 1}, 4, queries)


def _hand_scene():
    """Selected panel has two color-2 cells; each other panel has four cells."""
    grid = [[7] * 13 for _ in range(13)]
    for r in (3, 10):
        grid[r] = [0] * 13
    for row in grid:
        row[3] = row[8] = 0
    for r in range(5, 8):
        for c in range(5, 8):
            grid[r][c] = 5
    grid[6][6], grid[8][9] = 9, 6
    for rlo, rhi in ((0, 3), (4, 10), (11, 13)):
        for clo, chi in ((0, 3), (4, 8), (9, 13)):
            count = 2 if (rlo, clo) == (4, 9) else 4
            cells = [(r, c) for r in range(rlo, rhi) for c in range(clo, chi) if grid[r][c] == 7]
            for index, (r, c) in enumerate(cells[:count]):
                grid[r][c] = 2 if count == 2 else (1, 2, 3, 4)[index]
    return grid


def test_dynamic_rule_counts_cells_in_target_panel_and_gates_axes_independently():
    native = _native()
    grid = _hand_scene()
    assert _load(HOME / "generator.py").strict_canonical_like(grid) == []
    facts = native.scene_facts(grid)
    assert tuple(facts["marker"]) == (6, 6)
    assert tuple(facts["target"]) == (8, 9)
    assert tuple(facts["separator_rows"]) == (3, 10)
    assert tuple(facts["separator_cols"]) == (3, 8)
    assert facts["panel_noise_count"] == 2
    assert native.selected_tolerance(grid, "target_panel_count") == 2
    expected = deepcopy(grid)
    expected[6][6], expected[6][7], expected[8][9] = 5, 9, 9
    assert native.rule_mirror(grid, "target_panel_count") == expected
    before = deepcopy(grid)
    for setting in SETTINGS:
        assert native.rule_mirror(grid, setting) == _expected(grid, setting)
    assert grid == before


@pytest.mark.parametrize("seed", (0, 17))
def test_episode_counts_grammar_matching_queries_and_labels(seed):
    adapter, native = _adapter(), _native()
    generator = _load(HOME / "generator.py")
    baseline_queries = None
    for demos in range(4, 7):
        matching = None
        for setting in SETTINGS:
            options = {"axis_tolerance": setting}
            episode = adapter.generate(seed, options, demos, 4)
            assert options == {"axis_tolerance": setting}
            assert len(episode["train"]) == demos and len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(options)
            inputs = _inputs(episode)
            if matching is None:
                matching = inputs
                all_inputs = inputs["train"] + inputs["test"]
                assert len({_freeze(grid) for grid in all_inputs}) == demos + 4
                for grid in all_inputs:
                    assert generator.strict_canonical_like(grid) == []
                    assert 8 <= len(grid) <= 30 and 8 <= len(grid[0]) <= 30
                    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
                    assert 0 <= len(_facts(grid)[4][_facts(grid)[5]]) <= 2
                sizes = {(len(grid), len(grid[0])) for grid in inputs["test"]}
                assert {(8, 8), (30, 30)} <= sizes
                large = next(grid for grid in inputs["test"] if len(grid) == len(grid[0]) == 30)
                panels = _facts(large)[4]
                assert sum(map(len, panels.values())) >= 32
                assert sum(bool(cells) for cells in panels.values()) >= 8
            assert inputs == matching
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == _expected(pair["input"], setting)
                assert native.rule_mirror(pair["input"], setting) == pair["output"]
        if baseline_queries is None:
            baseline_queries = matching["test"]
        assert matching["test"] == baseline_queries
        assert adapter.generate(seed, {"axis_tolerance": 1}, demos, 4) == adapter.generate(
            seed, {"axis_tolerance": 1}, demos, 4)


@pytest.mark.parametrize("seed", (0, 17))
def test_demonstrations_alone_eliminate_every_query_harmful_declared_rival(seed):
    adapter, native = _adapter(), _native()
    for setting in SETTINGS:
        episode = adapter.generate(seed, {"axis_tolerance": setting}, 4, 4)
        pairs = episode["train"] + episode["test"]
        predictions = []
        for pair in pairs:
            rivals = native.declared_rivals(pair["input"], setting)
            assert isinstance(rivals, dict) and rivals
            candidates = {f"setting:{value!r}": _expected(pair["input"], value) for value in SETTINGS}
            candidates.update({f"shortcut:{name}": output for name, output in rivals.items()})
            predictions.append(candidates)
        assert all(set(row) == set(predictions[0]) for row in predictions)
        survivors = {name for name in predictions[0]
                     if all(predictions[index][name] == pair["output"]
                            for index, pair in enumerate(episode["train"]))}
        assert {name for name in survivors if name.startswith("setting:")} == {f"setting:{setting!r}"}
        for name in survivors:
            assert all(predictions[index][name] == pairs[index]["output"]
                       for index in range(4, 8)), (seed, setting, name)
