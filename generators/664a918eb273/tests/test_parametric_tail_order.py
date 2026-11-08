"""Native parametric contract tests for tail-order path concatenation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / "shared/runtime").exists())
PARAMETRIC = HOME / "workspace/parametric"


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing parametric implementation: {path}"
    spec = importlib.util.spec_from_file_location(f"test_664_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    location = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in location.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == "664a918eb273":
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_variants_are_distinct():
    adapter = _load("adapter")
    programs = {
        order: adapter.program({"tail_order": order})
        for order in ("left_to_right", "shortest_first", "longest_first")
    }
    assert programs["left_to_right"] == _canonical_program()
    assert len(set(programs.values())) == 3
    assert all(program.strip().startswith("(rule!") for program in programs.values())


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_counts_inputs_and_setting_identification(seed, demos):
    prototype = _load("prototype")
    episodes = {
        order: prototype.generate_episode(seed, order, demos, 4)
        for order in prototype.TAIL_ORDERS
    }
    common_inputs = _inputs(episodes["left_to_right"])
    assert len(common_inputs) == demos + 4
    assert len({json.dumps(grid, separators=(",", ":")) for grid in common_inputs}) == demos + 4
    assert all(_inputs(episode) == common_inputs for episode in episodes.values())
    assert all(len(episode["train"]) == demos and len(episode["test"]) == 4
               for episode in episodes.values())
    for selected, episode in episodes.items():
        assert episode["program_solution"] == prototype.program_for(selected)
        survivors = []
        for candidate in prototype.TAIL_ORDERS:
            if all(prototype.output_for(pair["input"], candidate) == pair["output"]
                   for pair in episode["train"]):
                survivors.append(candidate)
        assert survivors == [selected]


def test_first_two_demos_refute_declared_shortcuts_for_every_setting():
    prototype = _load("prototype")
    for seed in (0, 17):
        for selected in prototype.TAIL_ORDERS:
            episode = prototype.generate_episode(seed, selected, 2, 4)
            result = prototype.audit_episode(episode, selected)
            assert result["survivors"] == [f"setting:{selected}"]
            assert result["ambiguous_query_rivals"] == []


def test_query_profiles_include_substantive_exact_30x30_boundary():
    prototype = _load("prototype")
    episode = prototype.generate_episode(23, "shortest_first", 3, 4)
    queries = episode["test"]
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in queries]
    assert shapes[-1] == (30, 30)
    boundary = queries[-1]["input"]
    colored_rows = [r for r, row in enumerate(boundary) if any(row)]
    colored_cols = [c for c in range(30) if any(boundary[r][c] for r in range(30))]
    assert min(colored_rows) == 0 and max(colored_rows) == 29
    assert max(colored_cols) >= 24
    assert sum(bool(value) for row in boundary for value in row) >= 18
    assert len(set(shapes)) == 4


def test_dependency_intermediate_changes_selected_tail_order():
    prototype = _load("prototype")
    grid = prototype.generate_episode(0, "left_to_right", 2, 4)["train"][0]["input"]
    records = {order: prototype.dependency_intermediate(grid, order)
               for order in prototype.TAIL_ORDERS}
    assert len({tuple(value["selected_tail_indices"]) for value in records.values()}) == 3
    assert records["shortest_first"]["selected_tail_lengths"] == sorted(
        records["shortest_first"]["selected_tail_lengths"]
    )
    assert records["longest_first"]["selected_tail_lengths"] == sorted(
        records["longest_first"]["selected_tail_lengths"], reverse=True
    )
    outputs = {order: prototype.output_for(grid, order) for order in prototype.TAIL_ORDERS}
    assert len({json.dumps(value) for value in outputs.values()}) == 3


def test_equal_length_tail_paths_keep_original_left_to_right_tie_order():
    prototype = _load("prototype")
    grid = prototype.generate_episode(0, "left_to_right", 2, 4)["train"][0]["input"]
    infos = prototype._infos(grid)
    assert [len(info["cells"]) for info in infos] == [11, 3, 6, 4, 6]
    assert prototype._ordered_indices(infos, "shortest_first") == [0, 1, 3, 2, 4]
    assert prototype._ordered_indices(infos, "longest_first") == [0, 2, 4, 3, 1]


@pytest.mark.parametrize(
    "call",
    [
        lambda adapter: adapter.program({}),
        lambda adapter: adapter.program({"tail_order": "unknown"}),
        lambda adapter: adapter.generate(True, {"tail_order": "left_to_right"}, 3, 4),
        lambda adapter: adapter.generate(0, {"tail_order": "left_to_right"}, 1, 4),
        lambda adapter: adapter.generate(0, {"tail_order": "left_to_right"}, 7, 4),
        lambda adapter: adapter.generate(0, {"tail_order": "left_to_right"}, 3, 3),
    ],
)
def test_invalid_contract_values_fail_closed(call):
    adapter = _load("adapter")
    with pytest.raises((TypeError, ValueError)):
        call(adapter)
