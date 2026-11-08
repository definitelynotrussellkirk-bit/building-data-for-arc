from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root


ROOT = find_root(__file__)
HERE = ROOT / "generators" / "49754d8fa42e" / "workspace" / "parametric"
CANONICAL = {"orientation": "canonical"}
COMPOSED = {"orientation": "modal_components"}


def _load():
    path = HERE / "composition.py"
    assert path.is_file(), "native modal-component composition is not implemented"
    name = "native_composition_49754d8fa42e_tests"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


# Same color totals; only the selected color's geometry changes.
TWO = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [3, 0, 0, 0, 0, 0, 0, 0, 0],
    [3, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 2, 2],
    [0, 0, 0, 0, 0, 0, 2, 2, 2],
    [0, 0, 0, 0, 0, 0, 0, 0, 3],
]
THREE = [
    [2, 2, 0, 1, 1, 1, 1, 1, 1],
    [2, 2, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 2, 2, 0, 0, 0, 0, 1],
    [0, 0, 2, 2, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 2, 0],
    [3, 0, 0, 0, 0, 0, 2, 2, 0],
    [3, 0, 0, 0, 0, 0, 0, 0, 3],
]


def _hist(grid):
    return Counter(value for row in grid for value in row)


def _component_count(module, grid):
    color = module.mode_color(grid)
    return sum(obj["color"] == color for obj in module.components(grid))


def test_selected_topology_changes_output_and_canonical_bytes_are_preserved():
    module = _load()
    assert module.transform(TWO, COMPOSED) == [[0, 0, 5], [5, 5, 5], [0, 0, 5]]
    assert module.transform(THREE, COMPOSED) == [[0, 5, 0], [0, 5, 0], [5, 5, 5]]
    assert module.transform(TWO, CANONICAL) == [[5, 5, 5], [0, 5, 0], [0, 5, 0]]
    records = (json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
    canonical = next(row["program_solution"] for row in records if row.get("task_id") == "49754d8fa42e")
    assert module.program(CANONICAL) == canonical


def test_component_connectivity_does_not_merge_diagonal_contact():
    module = _load()
    four = [obj["size"] for obj in module.components(TWO) if obj["color"] == 2]
    eight = [obj["size"] for obj in module.components(TWO, diagonal=True) if obj["color"] == 2]
    assert four == [6, 6]
    assert eight == [12]


def test_smallest_query_canvas_has_feasible_counts_and_keeps_distractors():
    module = _load()
    episode = module.generate(87, COMPOSED, demos=2, queries=1)
    grid = episode["test"][0]["input"]
    assert sorted((len(grid), len(grid[0]))) == [8, 9]
    counts = _hist(grid)
    assert counts[0] >= 5
    assert 12 <= counts[module.mode_color(grid)] <= 28
    assert len(counts) in (5, 6)
    assert _component_count(module, grid) == 1


@pytest.mark.parametrize("seed", [0, 17, 22, 99])
def test_teaching_pair_keeps_histogram_but_changes_modal_connectivity(seed):
    module = _load()
    episode = module.generate(seed, COMPOSED, demos=3, queries=4)
    first, second = episode["train"][:2]
    assert _hist(first["input"]) == _hist(second["input"])
    assert [_component_count(module, pair["input"]) for pair in (first, second)] == [2, 3]
    assert module.mode_color(first["input"]) == module.mode_color(second["input"])
    assert max(_hist(first["input"])) > 3
    assert first["output"] != second["output"]


@pytest.mark.parametrize("seed", [0, 17])
def test_each_taught_rotation_sensitive_class_has_an_active_rotation_demo(seed):
    module = _load()
    episode = module.generate(seed, COMPOSED, demos=3, queries=4)
    base_glyphs = {2: [[5, 5, 5], [0, 5, 0], [0, 5, 0]],
                   3: [[0, 0, 5], [0, 0, 5], [5, 5, 5]]}
    for color, canonical in base_glyphs.items():
        assert any(module.mode_color(pair["input"]) == color and pair["output"] != canonical
                   for pair in episode["train"]), f"mode {color} never demonstrates active rotation"


@pytest.mark.parametrize("demos", range(2, 7))
def test_queries_are_independent_novel_taught_and_include_substantial_size_30(demos):
    module = _load()
    episode = module.generate(17, COMPOSED, demos=demos, queries=4)
    shorter = module.generate(17, COMPOSED, demos=demos, queries=1)
    canonical = module.generate(17, CANONICAL, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert shorter["train"] == episode["train"]
    assert shorter["test"] == episode["test"][:1]
    assert [pair["input"] for pair in canonical["train"] + canonical["test"]] == [
        pair["input"] for pair in episode["train"] + episode["test"]
    ]
    serialized = [json.dumps(pair["input"]) for pair in episode["train"] + episode["test"]]
    assert len(set(serialized)) == demos + 4
    seen = {module.mode_color(pair["input"]) for pair in episode["train"]}
    assert all(module.mode_color(pair["input"]) in seen for pair in episode["test"])
    assert len(seen) == (1 if demos == 2 else 2 if demos == 3 else 3)
    assert [_component_count(module, pair["input"]) for pair in episode["test"][:3]] == [1, 4, 5]
    large = episode["test"][3]["input"]
    assert len(large) == len(large[0]) == 30
    assert _component_count(module, large) in (7, 8)
    histogram = _hist(large)
    assert 200 <= histogram[module.mode_color(large)] <= 250
    assert 900 - histogram[0] >= 400
    assert sum(any(row) for row in large) >= 28
    assert sum(any(large[r][c] for r in range(30)) for c in range(30)) >= 28


@pytest.mark.parametrize("field,value", [
    ("seed", True), ("seed", -1), ("seed", 1.5),
    ("demos", True), ("demos", 1), ("demos", 7), ("demos", 3.0),
    ("queries", True), ("queries", 0), ("queries", 5), ("queries", 1.0),
])
def test_count_and_seed_types_are_strict(field, value):
    module = _load()
    args = dict(seed=0, settings=COMPOSED, demos=3, queries=4)
    args[field] = value
    with pytest.raises((TypeError, ValueError)):
        module.generate(**args)


@pytest.mark.parametrize("settings", [None, {}, {"orientation": True}, {"orientation": "other"},
                                     {"orientation": "canonical", "extra": 0}])
def test_rule_settings_are_exact_and_typed(settings):
    module = _load()
    with pytest.raises((TypeError, ValueError)):
        module.program(settings)
    with pytest.raises((TypeError, ValueError)):
        module.generate(0, settings)
