"""Contracts for the opt-in reflection/visible-span echo family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


@pytest.fixture(scope="module")
def prototype():
    path = HOME / "workspace/parametric/prototype.py"
    assert path.is_file(), "The native parametric implementation is required"
    spec = importlib.util.spec_from_file_location("_test_reflection_parametric", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_files_are_present():
    assert (HOME / "workspace/parametric/adapter.py").is_file()
    assert (HOME / "workspace/parametric/promotion.json").is_file()


def test_all_declared_racket_rules_have_complete_wrappers(prototype):
    from puzzle_generators.rule_wrap import wrap_rule
    for setting in prototype.SETTINGS:
        for source in [prototype.program(setting), *prototype.rival_programs(setting).values()]:
            assert wrap_rule(source).startswith("(lambda")


def test_default_is_exact_selected_canonical_program(prototype):
    rows = [json.loads(line) for line in
            (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    canonical = next(row for row in rows if row["task_id"] == HOME.name)
    assert prototype.program({"rule": "point"}) == canonical["program_solution"]
    pairs = canonical["train"] + [canonical["test"]]
    for pair in pairs:
        assert prototype.predict(pair["input"], {"rule": "point"}) == pair["output"]


@pytest.mark.parametrize("demos", [3, 4, 6])
@pytest.mark.parametrize("seed", [0, 17, 41])
def test_episode_counts_matching_inputs_and_demo_only_teaching(prototype, demos, seed):
    episodes = [prototype.generate(seed, setting, demos, 4) for setting in prototype.SETTINGS]
    inputs = []
    for setting, episode in zip(prototype.SETTINGS, episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        all_inputs = [pair["input"] for pair in pairs]
        assert len({json.dumps(grid) for grid in all_inputs}) == demos + 4
        assert all(not prototype.validate_grid(grid) for grid in all_inputs)
        assert episode["program_solution"] == prototype.program(setting)
        for rival in prototype.rival_programs(setting):
            survivors = all(prototype.predict(pair["input"], setting, rival) == pair["output"]
                            for pair in episode["train"])
            if survivors:
                assert all(prototype.predict(pair["input"], setting, rival) == pair["output"]
                           for pair in episode["test"]), rival
        inputs.append(all_inputs)
    assert inputs[0] == inputs[1]


def test_one_query_is_identical_prefix_and_returns_are_fresh(prototype):
    setting = {"rule": "visible_span_echo"}
    first = prototype.generate(19, setting, 3, 1)
    four = prototype.generate(19, setting, 3, 4)
    assert first["train"] == four["train"]
    assert first["test"] == four["test"][:1]
    first["train"][0]["input"][0][0] = 99
    assert prototype.generate(19, setting, 3, 4) == four


def test_large_query_contains_substantive_geometry(prototype):
    episode = prototype.generate(17, {"rule": "visible_span_echo"}, 3, 4)
    grid = episode["test"][-1]["input"]
    assert len(grid) == len(grid[0]) == 30
    cells = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x not in (0, 9)]
    assert len(cells) >= 40
    assert max(r for r, c in cells) - min(r for r, c in cells) >= 7
    assert max(c for r, c in cells) - min(c for r, c in cells) >= 7
    combined = [(r, c) for r, row in enumerate(episode["test"][-1]["output"])
                for c, x in enumerate(row) if x not in (0, 9)]
    assert max(r for r, c in combined) - min(r for r, c in combined) >= 20
    assert max(c for r, c in combined) - min(c for r, c in combined) >= 20


def test_post_clipping_branch_is_observably_causal(prototype):
    episode = prototype.generate(0, {"rule": "visible_span_echo"}, 3, 4)
    cases = [pair for pair in episode["train"] if
             prototype.predict(pair["input"], {"rule": "visible_span_echo"}, "source_span") != pair["output"]]
    assert cases, "A demonstration must refute selecting the axis before clipping"
    value = prototype.intermediate(cases[0]["input"])
    assert value["visible_cells"] and value["clipped_cells"] > 0


@pytest.mark.parametrize("seed,demos,queries,settings", [
    (True, 3, 4, {"rule": "point"}), (-1, 3, 4, {"rule": "point"}),
    (0, True, 4, {"rule": "point"}), (0, 2, 4, {"rule": "point"}),
    (0, 7, 4, {"rule": "point"}), (0, 3, 0, {"rule": "point"}),
    (0, 3, 5, {"rule": "point"}), (0, 3, 4, {"rule": "unknown"}),
    (0, 3, 4, {"rule": "point", "seed": 1}), (0, 3, 4, {"rule": True}),
])
def test_invalid_requests_fail_explicitly(prototype, seed, demos, queries, settings):
    with pytest.raises(ValueError):
        prototype.generate(seed, settings, demos, queries)


def test_invalid_grids_return_diagnostics(prototype):
    for grid in (None, [], [[]], [[9, 0], [1]], [[9, False], [1, 1]], [[9, 9], [1, 1]]):
        assert prototype.validate_grid(grid)
