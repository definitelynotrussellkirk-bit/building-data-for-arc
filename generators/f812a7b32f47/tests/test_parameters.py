"""Behavior tests for completion followed by connected-component selection."""
from pathlib import Path
import importlib.util
import json
from copy import deepcopy

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(name):
    path = HOME / "workspace" / "parametric" / f"{name}.py"
    assert path.is_file(), f"missing native parametric module: {name}"
    spec = importlib.util.spec_from_file_location(f"test_f812_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bridge_scene(tie=False):
    grid = [[0] * 11 for _ in range(11)]
    for i in range(11):
        grid[0][i] = grid[10][i] = grid[i][0] = grid[i][10] = 5
    for i in (2, 4, 7):
        grid[i][0] = 2
        grid[0][i] = 3
    grid[10][6] = 2
    grid[6][10] = 3
    for r, c in ((2, 3), (3, 2), (3, 4), (4, 3)):
        grid[r][c] = 7
    for c in range(1, 9 if tie else 6):
        grid[9][c] = 7
    return grid


def test_largest_selection_uses_components_created_by_completion():
    module = load("prototype")
    grid = bridge_scene()
    original = deepcopy(grid)
    expected = deepcopy(grid)
    for c in range(1, 6):
        expected[9][c] = 0
    for r, c in ((2, 2), (2, 4), (4, 2), (4, 4)):
        expected[r][c] = 7
    assert module.solve(grid, "largest") == expected
    assert grid == original
    assert module.rival_solutions(grid)["select_before_fill"] != expected


def test_largest_keeps_every_tied_winner_and_drops_smaller_components():
    module = load("prototype")
    grid = bridge_scene(tie=True)
    expected = deepcopy(grid)
    for r, c in ((2, 2), (2, 4), (4, 2), (4, 4)):
        expected[r][c] = 7
    assert module.solve(grid, "largest") == expected
    assert sum(v == 7 for row in expected for v in row) == 16
    assert module.rival_solutions(grid)["first_largest"] != expected


def test_default_preserves_anchors_and_paints_all_edge_selected_crossings():
    module = load("prototype")
    grid = bridge_scene()
    expected = deepcopy(grid)
    for r in (2, 4, 7):
        for c in (2, 4, 7):
            expected[r][c] = 7
    assert module.solve(grid, "all") == expected
    root = HOME.parents[1]
    rows = [json.loads(line) for line in
            (root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    authority = next(row["program_solution"] for row in rows
                     if row["task_id"] == "f812a7b32f47")
    assert module.program({"selection": "all"}) == authority


def test_every_finite_rival_executes_and_matches_its_claim():
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    module = load("prototype")
    runtime = HOME.parents[1] / "shared/runtime"
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for tie in (False, True):
                grid = bridge_scene(tie=tie)
                claims = module.rival_solutions(grid)
                for name in module.RIVALS:
                    assert _grid(apply(module.rival_program(name), grid)) == claims[name], name
        finally:
            bridge.close()


@pytest.mark.parametrize("settings", [{}, {"selection": "bad"},
    {"selection": True}, {"selection": "all", "extra": 1}, None])
def test_unknown_or_mistyped_settings_reject(settings):
    with pytest.raises(ValueError):
        load("prototype").program(settings)


@pytest.mark.parametrize("demos,queries", [(2, 4), (3, 1), (6, 4)])
def test_independent_counts_matched_inputs_and_unique_queries(demos, queries):
    adapter = load("adapter")
    episodes = [adapter.generate(23, {"selection": mode}, demos, queries)
                for mode in ("all", "largest")]
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        keys = [json.dumps(p["input"]) for p in episode["train"] + episode["test"]]
        assert len(keys) == len(set(keys))
    assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]
    assert any(a["output"] != b["output"] for a, b in
               zip(episodes[0]["train"], episodes[1]["train"]))


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5),
    (True, 4), (3, True), (3.0, 4)])
def test_out_of_contract_counts_fail_loudly(demos, queries):
    with pytest.raises(ValueError):
        load("adapter").generate(0, {"selection": "all"}, demos, queries)


def test_first_query_is_independent_of_requested_query_count():
    adapter = load("adapter")
    for mode in ("all", "largest"):
        single = adapter.generate(81, {"selection": mode}, 3, 1)
        multi = adapter.generate(81, {"selection": mode}, 3, 4)
        assert single["train"] == multi["train"]
        assert single["test"] == multi["test"][:1]


def test_two_demo_lesson_refutes_absolute_size_cutoff():
    adapter, module = load("adapter"), load("prototype")
    for seed in (0, 17, 23):
        episode = adapter.generate(seed, {"selection": "largest"}, 2, 4)
        def cutoff(grid):
            completed = module.solve(grid, "all")
            kept = {tuple(cell) for group in module.describe_components(completed)
                    if group["size"] >= 8 for cell in group["cells"]}
            return [[0 if value == 7 and (r, c) not in kept else value
                     for c, value in enumerate(row)] for r, row in enumerate(completed)]
        assert any(cutoff(pair["input"]) != pair["output"]
                   for pair in episode["train"]), f"absolute cutoff survives seed {seed}"
