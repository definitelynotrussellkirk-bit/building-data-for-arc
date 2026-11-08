"""Focused contract and real-Racket checks for the MAIN component-policy prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK = "fb7f02aa9ab0"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
POLICIES = ("all", "largest")


def _load(name):
    path = HOME / "workspace" / "parametric" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_main_test_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def api():
    return _load("adapter"), _load("prototype")


@pytest.fixture(scope="module")
def apply_program():
    bridge = RacketBridge()
    try:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        wrapped = {}

        def apply(source, grid):
            if source not in wrapped:
                wrapped[source] = wrap_rule(source)
            literal = "'(" + " ".join(
                "(" + " ".join(map(str, row)) + ")" for row in grid
            ) + ")"
            return bridge.eval_text(f"({wrapped[source]} {literal})")

        yield apply
    finally:
        bridge.close()


def _input(a, b, control):
    """Place already-normalized supports at deliberately different offsets."""
    grid = [[0] * 16 for _ in range(10)]
    grid[0][15] = control
    for cells, color, dr, dc in ((a, 1, 1, 1), (b, 2, 3, 9)):
        for r, c in cells:
            grid[r + dr][c + dc] = color
    return grid


def _assert_labels(api, apply_program, grid, all_output, largest_output):
    adapter, prototype = api
    for policy, expected in zip(POLICIES, (all_output, largest_output)):
        settings = {"component_policy": policy}
        source = adapter.program(settings)
        assert prototype.program(settings) == source
        assert prototype.reference(grid, policy=policy) == expected
        assert apply_program(source, grid) == expected


@pytest.mark.parametrize("control,all_output,largest_output", [
    (3, [[8, 8, 0], [8, 8, 8], [0, 8, 0]],
        [[8, 8, 0], [8, 8, 8], [0, 8, 0]]),
    (4, [[8], [8]], [[8], [8]]),
    (6, [[8, 0, 0], [8, 0, 8], [0, 8, 0]], [[8], [8]]),
])
def test_controls_normalize_independently_before_selection(
    api, apply_program, control, all_output, largest_output
):
    # The XOR singles touch the winning vertical pair only diagonally.
    a = {(0, 1), (1, 0), (1, 1), (2, 1)}
    b = {(0, 0), (0, 1), (1, 1), (1, 2)}
    _assert_labels(api, apply_program, _input(a, b, control), all_output, largest_output)


def test_largest_crops_only_selected_cells_not_every_cell_inside_its_box(api, apply_program):
    ring = {(r, c) for r in range(5) for c in range(5) if r in (0, 4) or c in (0, 4)}
    # Both source shapes are connected, but their intersection is a ring and
    # an isolated center. A raw bounding-box crop would wrongly retain it.
    grid = _input(ring | {(1, 2), (2, 2)}, ring | {(2, 2), (3, 2)}, 4)
    all_output = [
        [8, 8, 8, 8, 8],
        [8, 0, 0, 0, 8],
        [8, 0, 8, 0, 8],
        [8, 0, 0, 0, 8],
        [8, 8, 8, 8, 8],
    ]
    largest_output = [
        [8, 8, 8, 8, 8],
        [8, 0, 0, 0, 8],
        [8, 0, 0, 0, 8],
        [8, 0, 0, 0, 8],
        [8, 8, 8, 8, 8],
    ]
    _assert_labels(api, apply_program, grid, all_output, largest_output)


@pytest.mark.parametrize("a,b,expected", [
    # Same top row: the left horizontal pair beats the right vertical pair.
    ({(0, c) for c in range(5)} | {(1, 4)},
     {(0, 0), (0, 1), (0, 4), (1, 0), (1, 4)} | {(2, c) for c in range(5)},
     [[8, 8]]),
    # Earlier top row wins even when its component starts farther right.
    ({(0, 4), (1, 4)} | {(2, c) for c in range(5)},
     {(0, c) for c in range(5)} | {(1, 0), (1, 4), (2, 0), (2, 1)},
     [[8], [8]]),
    # Five cells in a narrow box beat four cells in a larger-area box.
    ({(0, c) for c in range(6)} | {(1, 0)} | {(r, 5) for r in range(5)},
     {(0, 0), (0, 1), (0, 2)} | {(r, 0) for r in range(5)}
     | {(r, 5) for r in range(5)} | {(4, c) for c in range(6)},
     [[8], [8], [8], [8], [8]]),
])
def test_largest_uses_cell_count_then_bbox_row_then_column(api, apply_program, a, b, expected):
    adapter, prototype = api
    grid = _input(a, b, 4)
    assert prototype.reference(grid, policy="largest") == expected
    assert apply_program(adapter.program({"component_policy": "largest"}), grid) == expected


@pytest.mark.parametrize("a,b,control", [
    ({(0, 1), (1, 0), (1, 1)}, {(0, 0)}, 4),
    ({(0, 0), (0, 1)}, {(0, 0), (0, 1)}, 6),
])
def test_empty_result_is_one_black_cell(api, apply_program, a, b, control):
    _assert_labels(api, apply_program, _input(a, b, control), [[0]], [[0]])


def test_all_program_preserves_canonical_bytes_and_labels(api, apply_program):
    adapter, prototype = api
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        sources = {row["program_solution"] for line in handle
                   if (row := json.loads(line)).get("task_id") == TASK}
    assert sources == {adapter.program({"component_policy": "all"})}
    source = sources.pop()
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert prototype.reference(pair["input"]) == pair["output"]
        assert apply_program(source, pair["input"]) == pair["output"]


@pytest.mark.parametrize("settings", [
    None, [], "all", {}, {"component_policy": "unknown"},
    {"component_policy": True}, {"component_policy": 1},
    {"component_policy": None}, {"component_policy": []},
    {"component_policy": "all", "extra": 0}, {"other": "largest"},
])
def test_settings_are_exact_and_typed(api, settings):
    adapter, prototype = api
    for call in (
        lambda: prototype.validate_settings(settings),
        lambda: adapter.program(settings),
        lambda: adapter.generate(17, settings, 3, 1),
    ):
        with pytest.raises(ValueError):
            call()


@pytest.mark.parametrize("name,value", [
    ("demos", 2), ("demos", 7), ("demos", True), ("demos", False),
    ("demos", 3.0), ("demos", "3"), ("demos", None),
    ("queries", 0), ("queries", 5), ("queries", True), ("queries", False),
    ("queries", 1.0), ("queries", "1"), ("queries", None),
])
def test_count_bounds_and_types_are_strict(api, name, value):
    adapter, _ = api
    counts = {"demos": 3, "queries": 1, name: value}
    with pytest.raises(ValueError):
        adapter.generate(17, {"component_policy": "all"}, **counts)


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


@pytest.mark.parametrize("seed,demos", [(0, 3), (1, 4), (17, 5), (91, 6)])
def test_supported_demo_counts_have_unique_matched_inputs_and_executable_labels(
    api, apply_program, seed, demos
):
    adapter, prototype = api
    episodes = []
    for policy in POLICIES:
        settings = {"component_policy": policy}
        episode = adapter.generate(seed, settings, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(settings)
        again = adapter.generate(seed, settings, demos, 4)
        assert (again["train"], again["test"], again["program_solution"]) == (
            episode["train"], episode["test"], episode["program_solution"]
        )
        inputs = _inputs(episode)
        assert len({tuple(map(tuple, grid)) for grid in inputs}) == demos + 4
        controls = [{v for row in pair["input"] for v in row} & {3, 4, 6}
                    for pair in episode["train"]]
        assert all(len(colors) == 1 for colors in controls)
        assert set.union(*controls) == {3, 4, 6}
        for pair in episode["train"] + episode["test"]:
            grid, output = pair["input"], pair["output"]
            assert 8 <= len(grid) <= 30 and 11 <= len(grid[0]) <= 30
            assert all(len(row) == len(grid[0]) for row in grid)
            assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
            assert 1 <= len(output) <= 30 and 1 <= len(output[0]) <= 30
            assert all(len(row) == len(output[0]) for row in output)
            assert all(type(v) is int and v in (0, 8) for row in output for v in row)
            assert prototype.reference(grid, policy=policy) == output
            assert apply_program(episode["program_solution"], grid) == output
        episodes.append(episode)
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    assert any(a["output"] != b["output"]
               for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


@pytest.mark.parametrize("policy", POLICIES)
def test_query_prefix_is_stable_and_seed_changes_inputs(api, policy):
    adapter, _ = api
    settings = {"component_policy": policy}
    full = adapter.generate(812, settings, 3, 4)
    for queries in (1, 2, 3):
        prefix = adapter.generate(812, settings, 3, queries)
        assert prefix["train"] == full["train"]
        assert prefix["test"] == full["test"][:queries]
    assert _inputs(adapter.generate(813, settings, 3, 4)) != _inputs(full)
# A control can be taught only if the full legend is distinguished, not merely
# each constant-operation shortcut. Keep tie orientation explicit as well.
def test_teaching_rivals_include_legend_permutations_and_reverse_ties():
    import importlib.util
    source = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("fb7_teaching_rivals", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rivals = module.rival_specs("largest")
    assert len([name for name in rivals if name.startswith("legend_")]) == 5
    assert "last_tie" in rivals
    for policy in module.POLICIES:
        episode = module.generate(17, {"component_policy": policy}, 3, 4)
        assert not module._survivors([p["input"] for p in episode["train"]], policy)
