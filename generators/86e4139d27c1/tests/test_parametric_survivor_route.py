"""Focused tests for the midpoint-plus / survivor-route parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "86e4139d27c1"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def adapter():
    source = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("_midpoint_survivor_adapter_test", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["task_id"] == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def literal_overlap_both() -> list[list[int]]:
    grid = [[0] * 13 for _ in range(11)]
    for row, col in ((4, 4), (4, 6), (8, 10)):
        grid[row][col] = 1
    return grid


def expected_plus() -> list[list[int]]:
    grid = literal_overlap_both()
    for row, col in ((4, 5), (3, 5), (5, 5), (4, 4), (4, 6)):
        grid[row][col] = 3
    return grid


def expected_survivor_route() -> list[list[int]]:
    grid = expected_plus()
    for row, col in ((6, 5), (7, 5), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9)):
        grid[row][col] = 8
    return grid


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=10) as bridge:
        assert bridge.runtime_identity["protected"] is True

        def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
            bridge.define_grid("survivor-route-test-grid", grid)
            return bridge.eval_text(f"({wrap_rule(program)} survivor-route-test-grid)")

        yield apply


def test_default_setting_is_exact_canonical_program():
    assert adapter().program({"continuation": "plus_only"}) == canonical_program()


def test_each_declared_program_is_one_complete_rule_expression():
    from arc_repl.parser import Symbol, parse_all

    module = adapter()
    for continuation in module.CONTINUATIONS:
        forms = parse_all(module.program({"continuation": continuation}))
        assert len(forms) == 1
        assert isinstance(forms[0], list)
        assert forms[0][0] == Symbol("rule!")


def test_literal_survivor_route_uses_stage_a_survivor_and_matches_racket(racket):
    module = adapter()
    grid = literal_overlap_both()
    observed = module.observe(grid)
    assert observed["midpoint"] == (4, 5)
    assert observed["selected_overlap_count"] == 2
    assert observed["survivor_target"] == (8, 10)
    assert module.transform(grid, "plus_only") == expected_plus()
    assert module.transform(grid, "survivor_route") == expected_survivor_route()
    assert racket(module.program({"continuation": "survivor_route"}), grid) == expected_survivor_route()


def test_wrong_pre_stage_target_changes_the_final_output():
    module = adapter()
    grid = literal_overlap_both()
    correct = module.transform(grid, "survivor_route")
    wrong = module.predict(grid, "original_first")
    assert wrong != correct
    assert wrong == expected_plus()
    assert correct[8][9] == 8
    assert correct[8][10] == 1


def episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_generated_inputs_are_setting_neutral_distinct_deterministic_and_stress_30(demos):
    module = adapter()
    first = module.generate(17, {"continuation": "plus_only"}, demos, 4)
    routed = module.generate(17, {"continuation": "survivor_route"}, demos, 4)
    assert episode_inputs(first) == episode_inputs(routed)
    assert first == module.generate(17, {"continuation": "plus_only"}, demos, 4)
    assert len(first["train"]) == demos
    assert len(first["test"]) == 4
    assert len({json.dumps(value) for value in episode_inputs(first)}) == demos + 4
    assert (len(first["test"][-1]["input"]), len(first["test"][-1]["input"][0])) == (30, 30)
    assert {module.observe(pair["input"])["selected_overlap_count"] for pair in first["train"][:2]} == {0, 2}
    assert all(pair["output"] == module.transform(pair["input"], "plus_only") for pair in first["train"] + first["test"])
    assert all(pair["output"] == module.transform(pair["input"], "survivor_route") for pair in routed["train"] + routed["test"])


def test_generated_inputs_vary_across_fresh_seeds_and_do_not_touch_global_rng():
    import random

    module = adapter()
    random.seed(9157)
    before = random.getstate()
    first = module.generate(0, {"continuation": "plus_only"}, 3, 4)
    second = module.generate(17, {"continuation": "plus_only"}, 3, 4)
    assert random.getstate() == before
    assert episode_inputs(first) != episode_inputs(second)


@pytest.mark.parametrize("continuation", ["plus_only", "survivor_route"])
def test_generated_demonstrations_identify_one_setting_against_declared_rivals(continuation):
    module = adapter()
    episode = module.generate(17, {"continuation": continuation}, 2, 4)
    certificate = module.certificate(episode["train"], [pair["input"] for pair in episode["test"]])
    assert certificate["survivors"] == [continuation]
    assert certificate["demos"] == 2
    assert certificate["queries"] == 4
    assert certificate["causal_witness"]["selected_overlap_count"] == 2
    assert certificate["causal_witness"]["correct_output_sha256"] != certificate["causal_witness"]["wrong_intermediate_output_sha256"]


@pytest.mark.parametrize("continuation", ["plus_only", "survivor_route"])
def test_every_generated_label_matches_protected_racket(racket, continuation):
    module = adapter()
    episode = module.generate(23, {"continuation": continuation}, 3, 4)
    program = module.program({"continuation": continuation})
    for pair in episode["train"] + episode["test"]:
        assert racket(program, pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"continuation": "plus_only"}, 3, 4),
        (0, {"continuation": "wrong"}, 3, 4),
        (0, {"continuation": "plus_only", "unknown": 1}, 3, 4),
        (0, {"continuation": "plus_only"}, 1, 4),
        (0, {"continuation": "plus_only"}, 7, 4),
        (0, {"continuation": "plus_only"}, 3, 3),
        (0, {"continuation": "plus_only"}, 3, 5),
        (0, {"continuation": "plus_only"}, 3, True),
    ],
)
def test_bad_generation_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_boolean_grid_cells_are_rejected():
    grid = literal_overlap_both()
    grid[0][0] = False
    with pytest.raises(ValueError):
        adapter().transform(grid, "plus_only")
