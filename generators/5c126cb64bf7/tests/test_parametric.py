"""Native whole-pattern / largest-component family for 5c126cb64bf7."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/5c126cb64bf7/workspace/parametric"
STARTS = (0, 6, 12)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _load(name, filename):
    path = HOME / filename
    assert path.exists(), f"missing {filename}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load("parametric_5c126cb64bf7", "adapter.py")


def _norm(cells):
    cells = tuple(cells)
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate(cells, turns=1):
    cells = _norm(cells)
    for _ in range(turns % 4):
        cells = _norm((c, -r) for r, c in cells)
    return cells


def _orbit(cells):
    return min(_rotate(cells, turns) for turns in range(4))


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, component = [start], []
        while stack:
            row, column = stack.pop()
            component.append((row, column))
            for dr, dc in CARDINAL:
                neighbor = (row + dr, column + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(component)))
    return tuple(sorted(result, key=lambda part: (-len(part), part)))


def _panels(grid):
    return tuple(tuple((row, column) for row, line in enumerate(grid)
                       for column, value in enumerate(line[start:start + 5]) if value)
                 for start in STARTS)


def _relation(keys):
    return [[8 if i == j else 2 if keys[i] == keys[j] else 0 for j in range(3)]
            for i in range(3)]


def _whole(grid):
    return _relation([_orbit(panel) for panel in _panels(grid)])


def _largest(grid):
    return _relation([_orbit(_components(panel)[0]) for panel in _panels(grid)])


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_programs_and_settings_are_exact_and_strict():
    adapter = _adapter()
    assert adapter.program({"pattern_scope": "whole"}) == (HOME / "canonical.rkt").read_text()
    assert adapter.program({"pattern_scope": "largest_component"}) == (
        HOME / "largest_component.rkt").read_text()
    for bad in ({}, None, {"pattern_scope": "bad"}, {"pattern_scope": 1},
                {"pattern_scope": "whole", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_inputs_are_setting_matched_and_count_prefixes_are_independent():
    adapter = _adapter()
    whole = adapter.generate(17, {"pattern_scope": "whole"}, 3, 4)
    largest = adapter.generate(17, {"pattern_scope": "largest_component"}, 3, 4)
    assert _inputs(whole, "train") == _inputs(largest, "train")
    assert _inputs(whole, "test") == _inputs(largest, "test")
    two = adapter.generate(17, {"pattern_scope": "whole"}, 2, 4)
    six = adapter.generate(17, {"pattern_scope": "whole"}, 6, 4)
    one = adapter.generate(17, {"pattern_scope": "whole"}, 3, 1)
    assert _inputs(two, "train") == _inputs(six, "train")[:2]
    assert _inputs(two, "test") == _inputs(six, "test")
    assert _inputs(one, "test") == _inputs(whole, "test")[:1]
    all_inputs = _inputs(six, "train") + _inputs(six, "test")
    assert len({repr(grid) for grid in all_inputs}) == len(all_inputs)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_python_claims_match_both_rules_and_two_demos_identify_scope(seed):
    adapter = _adapter()
    whole = adapter.generate(seed, {"pattern_scope": "whole"}, 2, 4)
    largest = adapter.generate(seed, {"pattern_scope": "largest_component"}, 2, 4)
    for left, right in zip(whole["train"] + whole["test"], largest["train"] + largest["test"]):
        assert left["input"] == right["input"]
        assert left["output"] == _whole(left["input"])
        assert right["output"] == _largest(right["input"])
    assert whole["train"][0]["output"] == largest["train"][0]["output"]
    assert whole["train"][1]["output"] != largest["train"][1]["output"]


@pytest.mark.parametrize("scope", ["whole", "largest_component"])
def test_four_queries_include_boundary_spanning_30x17_stress(scope):
    adapter = _adapter()
    episode = adapter.generate(42, {"pattern_scope": scope}, 3, 4)
    pair = episode["test"][-1]
    grid = pair["input"]
    assert len(grid) == 30 and all(len(row) == 17 for row in grid)
    assert sum(value != 0 for row in grid for value in row) >= 27
    assert any(grid[0][column] != 0 for column in range(17))
    assert any(grid[-1][column] != 0 for column in range(17))
    assert all(row[5] == row[11] == 0 for row in grid)
    assert len(pair["output"]) == 3 and all(len(row) == 3 for row in pair["output"])


def test_every_panel_has_a_unique_largest_component_and_monochrome_content():
    adapter = _adapter()
    episode = adapter.generate(123, {"pattern_scope": "largest_component"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        for start, cells in zip(STARTS, _panels(grid)):
            parts = _components(cells)
            assert parts and (len(parts) == 1 or len(parts[0]) > len(parts[1]))
            colors = {grid[row][start + column] for row, column in cells}
            assert len(colors) == 1


def test_public_turn_reveals_only_one_query_input():
    adapter = _adapter()
    episode = adapter.generate(7, {"pattern_scope": "largest_component"}, 3, 4)
    view = adapter.public_turn(episode, 2)
    assert view["train"] == episode["train"]
    assert view["test"] == [{"input": episode["test"][2]["input"]}]
    assert "program_solution" not in view


def test_invalid_counts_and_seed_types_are_rejected():
    adapter = _adapter()
    settings = {"pattern_scope": "whole"}
    for args in ((True, settings, 3, 4), (-1, settings, 3, 4),
                 (0, settings, 1, 4), (0, settings, 7, 4),
                 (0, settings, 3, 0), (0, settings, 3, 5),
                 (0, settings, 3.0, 4)):
        with pytest.raises(ValueError):
            adapter.generate(*args)


def test_bounded_self_audit_refutes_named_shortcuts():
    audit = _load("audit_5c126cb64bf7", "audit.py")
    report = audit.run(seeds=(0, 17, 991))
    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["episodes_checked"] == 6
    assert report["has_30x17"] is True


def test_canonical_file_is_byte_exact_selected_source():
    from arcpuzzles import Catalog

    selected = Catalog(REPO).get("5c126cb64bf7")["variants"]
    programs = {row["program_solution"] for row in selected}
    assert len(programs) == 1
    assert (HOME / "canonical.rkt").read_text() == next(iter(programs))
