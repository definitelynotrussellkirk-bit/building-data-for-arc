"""Contracts for the opt-in periodic-row / rigid-reflection prototype.

These tests do not replace canonical generator qualification or protected
Racket execution.  All imports are bound to this test's repository/runtime.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from functools import lru_cache
from pathlib import Path

import pytest


TASK_ID = "3031e2ee53d1"
EDGES = ("linear", "bounce")
MAX_SEED = 2**63 - 1


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _support_from_this_tree():
    for ancestor in Path(__file__).resolve().parents:
        for relative in ("shared/runtime/reviewer_support.py", "reviewer_support.py"):
            candidate = ancestor / relative
            if candidate.is_file():
                return _load_module("_parametric_3031e2ee53d1_support", candidate)
    raise AssertionError("No reviewer_support.py in this test's source tree")


SUPPORT = _support_from_this_tree()
ROOT = SUPPORT.find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace/parametric/prototype.py"


@lru_cache(maxsize=1)
def _prototype():
    # Keep the missing-feature red run an assertion failure, not an import error.
    assert PROTOTYPE_PATH.is_file(), f"Parametric prototype is not implemented: {PROTOTYPE_PATH}"
    return _load_module("_parametric_3031e2ee53d1_under_test", PROTOTYPE_PATH)


@lru_cache(maxsize=1)
def _canonical_row():
    with SUPPORT.canonical_path(ROOT).open(encoding="utf-8") as handle:
        matches = [row for line in handle if line.strip()
                   if (row := json.loads(line)).get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]


def _grid(*rows):
    return [[int(cell) for cell in row] for row in rows]


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _assert_arc_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def test_linear_program_preserves_exact_canonical_rule_bytes():
    prototype = _prototype()
    canonical = _canonical_row()["program_solution"]
    assert prototype.program({"edge": "linear"}).encode("utf-8") == canonical.encode("utf-8")
    assert prototype.program({"edge": "bounce"}) != canonical


def test_linear_solver_matches_every_canonical_answer():
    prototype = _prototype()
    pairs = SUPPORT.canonical_pairs(TASK_ID, root=ROOT, variant=0)
    assert len(pairs) == 5
    for pair in pairs:
        assert prototype.solve(pair["input"]) == pair["output"]
        assert prototype.solve(pair["input"], "linear") == pair["output"]


def test_reflection_continues_translation_and_preserves_color_order():
    prototype = _prototype()
    grid = _grid("0002700000", "0000270000", "0000027000", "0000002700")
    assert prototype.detect(grid) == (1, 1)
    description = prototype.describe(grid)
    assert {key: description[key] for key in ("period", "shift", "height", "width")} == {
        "period": 1, "shift": 1, "height": 4, "width": 10,
    }
    bounce = prototype.solve(grid, "bounce")
    assert bounce == _grid(
        "0002700000", "0000270000", "0000027000", "0000002700", "0000000270",
        "0000000027", "0000000270", "0000002700", "0000027000", "0000270000",
    )
    assert [next(c for c, value in enumerate(row) if value) for row in bounce] == [
        3, 4, 5, 6, 7, 8, 7, 6, 5, 4,
    ]
    assert prototype.solve(grid, "linear") == _grid(
        "0002700000", "0000270000", "0000027000", "0000002700", "0000000270",
        "0000000027", "0000000002", "0000000000", "0000000000", "0000000000",
    )


def test_reflection_uses_the_entire_period_union_not_each_row_extent():
    prototype = _prototype()
    grid = _grid("0002700000", "0006089000", "0000270000", "0000608900")
    assert prototype.detect(grid) == (2, 1)
    assert prototype.solve(grid, "bounce") == _grid(
        "0002700000", "0006089000", "0000270000", "0000608900", "0000027000",
        "0000060890", "0000002700", "0000006089", "0000027000", "0000060890",
    )


def test_reflection_keeps_overshoot_instead_of_clamping_at_an_edge():
    prototype = _prototype()
    grid = _grid("0270000000", "0002700000", "0000027000", "0000000270")
    assert prototype.detect(grid) == (1, 2)
    assert prototype.solve(grid, "bounce") == _grid(
        "0270000000", "0002700000", "0000027000", "0000000270", "0000000270",
        "0000027000", "0002700000", "0270000000", "0270000000", "0002700000",
    )


def test_leftward_reflection_keeps_the_motif_orientation():
    prototype = _prototype()
    grid = _grid("0000027000", "0000270000", "0002700000", "0027000000")
    assert prototype.detect(grid) == (1, -1)
    assert prototype.solve(grid, "bounce") == _grid(
        "0000027000", "0000270000", "0002700000", "0027000000", "0270000000",
        "2700000000", "0270000000", "0027000000", "0002700000", "0000270000",
    )


def test_stationary_full_width_motif_has_no_reflection_division_by_zero():
    prototype = _prototype()
    grid = _grid(*(["2727272727"] * 4))
    expected = _grid(*(["2727272727"] * 10))
    assert prototype.detect(grid) == (1, 0)
    assert prototype.solve(grid, "linear") == expected
    assert prototype.solve(grid, "bounce") == expected


@pytest.mark.parametrize("edge", EDGES)
@pytest.mark.parametrize("demos", (2, 6))
@pytest.mark.parametrize("queries", (1, 4))
def test_count_boundaries_have_unique_lawful_labeled_grids(edge, demos, queries):
    prototype = _prototype()
    episode = prototype.generate(2026, {"edge": edge}, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    pairs = episode["train"] + episode["test"]
    assert len({_grid_key(pair["input"]) for pair in pairs}) == demos + queries
    for pair in pairs:
        inp, output = pair["input"], pair["output"]
        _assert_arc_grid(inp)
        _assert_arc_grid(output)
        assert len(inp) < len(inp[0])
        assert len(output) == len(output[0]) == len(inp[0])
        assert output[:len(inp)] == inp
        assert output == prototype.solve(inp, edge)


@pytest.mark.parametrize("edge", EDGES)
def test_default_episode_has_three_demos_and_four_novel_queries(edge):
    episode = _prototype().generate(17, {"edge": edge})
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    train_keys = {_grid_key(grid) for grid in _inputs(episode, "train")}
    test_keys = {_grid_key(grid) for grid in _inputs(episode, "test")}
    assert len(train_keys) == 3 and len(test_keys) == 4
    assert train_keys.isdisjoint(test_keys)


@pytest.mark.parametrize("seed", (0, 37, MAX_SEED))
def test_settings_change_labels_without_changing_episode_inputs(seed):
    prototype = _prototype()
    episodes = [prototype.generate(seed, {"edge": edge}, demos=2, queries=4) for edge in EDGES]
    for split in ("train", "test"):
        assert _inputs(episodes[0], split) == _inputs(episodes[1], split)


@pytest.mark.parametrize("edge", EDGES)
def test_demo_and_query_streams_are_independent_and_first_turn_is_stable(edge):
    prototype = _prototype()
    short = prototype.generate(31, {"edge": edge}, demos=2, queries=1)
    four = prototype.generate(31, {"edge": edge}, demos=2, queries=4)
    six = prototype.generate(31, {"edge": edge}, demos=6, queries=4)
    assert short["train"] == four["train"] == six["train"][:2]
    assert short["test"][0] == four["test"][0]
    assert four["test"] == six["test"]
    assert prototype.public_challenge(short) == prototype.public_challenge(four)


@pytest.mark.parametrize("edge", EDGES)
def test_generation_is_deterministic_without_consuming_global_randomness(edge):
    prototype = _prototype()
    settings = {"edge": edge}
    saved_state = random.getstate()
    try:
        random.seed(2468013579)
        state = random.getstate()
        first = prototype.generate(81, settings)
        assert random.getstate() == state
        random.seed(9753108642)
        state = random.getstate()
        second = prototype.generate(81, settings)
        assert random.getstate() == state
        assert first == second
        assert settings == {"edge": edge}
    finally:
        random.setstate(saved_state)


def test_returned_episodes_and_pair_grids_do_not_share_mutable_state():
    prototype = _prototype()
    settings = {"edge": "bounce"}
    first = prototype.generate(81, settings)
    second = prototype.generate(81, settings)
    expected = copy.deepcopy(second)
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert second == expected
    assert first["train"][0]["output"] == expected["train"][0]["output"]
    assert first["train"][1:] == expected["train"][1:]
    assert first["test"] == expected["test"]
    settings["edge"] = "linear"
    assert second == expected
    assert prototype.generate(81, {"edge": "bounce"}) == expected


@pytest.mark.parametrize("edge", EDGES)
def test_solver_and_observers_leave_the_caller_grid_unchanged(edge):
    prototype = _prototype()
    grid = _grid("0002700000", "0000270000", "0000027000", "0000002700")
    original = copy.deepcopy(grid)
    output = prototype.solve(grid, edge)
    prototype.detect(grid)
    prototype.describe(grid)
    assert grid == original
    output[0][0] = (output[0][0] + 1) % 10
    assert grid == original


@pytest.mark.parametrize("seed", (0, 29, MAX_SEED))
@pytest.mark.parametrize("edge", EDGES)
def test_two_demos_distinguish_the_finite_setting_family(seed, edge):
    prototype = _prototype()
    episode = prototype.generate(seed, {"edge": edge}, demos=2, queries=4)
    fitting = {
        candidate for candidate in EDGES
        if all(prototype.solve(pair["input"], candidate) == pair["output"]
               for pair in episode["train"])
    }
    assert fitting == {edge}
    other = "bounce" if edge == "linear" else "linear"
    assert any(prototype.solve(pair["input"], other) != pair["output"]
               for pair in episode["test"])


@pytest.mark.parametrize("edge", EDGES)
def test_both_rules_preserve_every_observed_row_on_the_produced_grammar(edge):
    prototype = _prototype()
    episode = prototype.generate(54, {"edge": edge}, demos=6, queries=4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        for rule in EDGES:
            assert prototype.solve(grid, rule)[:len(grid)] == grid


@pytest.mark.parametrize("edge", EDGES)
def test_two_demos_reject_restarting_the_motif_phase_after_a_partial_input(edge):
    """Seed12 formerly taught only complete periods, then queried a partial one."""
    prototype = _prototype()
    episode = prototype.generate(12, {"edge": edge}, demos=2, queries=4)

    def reset_phase(grid):
        facts = prototype.describe(grid)
        output = copy.deepcopy(grid)
        for r in range(len(grid), facts["width"]):
            offset = (r // facts["period"]) * facts["shift"]
            if edge == "bounce":
                span = facts["span"]
                phase = (facts["left"] + offset) % (2 * span) if span else 0
                offset = min(phase, 2 * span - phase) - facts["left"]
            row = grid[(r - len(grid)) % facts["period"]]
            output.append([row[c - offset] if 0 <= c - offset < facts["width"] else 0
                           for c in range(facts["width"])])
        return output

    assert any(reset_phase(pair["input"]) != pair["output"] for pair in episode["test"])
    assert any(reset_phase(pair["input"]) != pair["output"] for pair in episode["train"]), (
        "A prefix-preserving phase-reset rival fits all demos but fails a novel query"
    )


@pytest.mark.parametrize("edge", EDGES)
def test_thirty_square_query_has_substantive_foreground_across_the_canvas(edge):
    prototype = _prototype()
    episode = prototype.generate(0, {"edge": edge}, queries=4)
    largest = [pair for pair in episode["test"] if len(pair["input"][0]) == 30]
    assert largest, "The four-query schedule must exercise the lawful 30-column boundary"
    for pair in largest:
        output = pair["output"]
        _assert_arc_grid(output)
        assert len(output) == len(output[0]) == 30
        assert output == prototype.solve(pair["input"], edge)
        occupied = [(r, c) for r, row in enumerate(output) for c, cell in enumerate(row) if cell]
        rows = {r for r, _ in occupied}
        columns = {c for _, c in occupied}
        assert len(occupied) >= 50
        assert len(rows) >= 20 and len(columns) >= 15
        assert max(rows) - min(rows) + 1 >= 25
        assert max(columns) - min(columns) + 1 >= 25


def test_public_projection_has_only_demos_and_the_selected_query_input():
    prototype = _prototype()
    episode = prototype.generate(99, {"edge": "bounce"}, demos=2, queries=4)
    expected_train = [{"input": pair["input"], "output": pair["output"]}
                      for pair in episode["train"]]
    for index in range(4):
        public = prototype.public_challenge(episode, query_index=index)
        assert public == {"train": expected_train, "test": [{"input": episode["test"][index]["input"]}]}
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert set(public["test"][0]) == {"input"}
        expected_id = hashlib.sha256(SUPPORT.public_challenge_bytes(public)).hexdigest()
        assert prototype.public_id(public) == expected_id


def test_hidden_labels_settings_and_metadata_cannot_change_public_identity():
    prototype = _prototype()
    episode = prototype.generate(99, {"edge": "bounce"}, demos=2, queries=4)
    public = prototype.public_challenge(episode)
    expected_id = hashlib.sha256(SUPPORT.public_challenge_bytes(public)).hexdigest()
    altered = copy.deepcopy(episode)
    altered.update({"settings": {"edge": "linear"}, "program": "private changed program",
                    "query_count": 876, "private": {"seed": -999}})
    for pair in altered["train"]:
        pair["private"] = {"setting": "different", "future_queries": 1000}
    for pair in altered["test"]:
        pair["output"] = [[0 for _ in row] for row in pair["output"]]
        pair["private"] = "changed query label metadata"
    assert prototype.public_challenge(altered) == public
    assert prototype.public_id(prototype.public_challenge(altered)) == expected_id

    decorated_public = copy.deepcopy(public)
    decorated_public.update({"settings": {"edge": "linear"}, "program": "secret", "query_count": 4})
    decorated_public["train"][0]["private"] = "secret"
    decorated_public["test"][0].update({"output": [[9]], "private": "secret"})
    assert prototype.public_id(decorated_public) == expected_id


@pytest.mark.parametrize("split,field", (("train", "input"), ("train", "output"), ("test", "input")))
def test_visible_grid_changes_change_the_public_identity(split, field):
    prototype = _prototype()
    public = prototype.public_challenge(prototype.generate(99, {"edge": "linear"}))
    changed = copy.deepcopy(public)
    changed[split][0][field][0][0] = (changed[split][0][field][0][0] + 1) % 10
    assert prototype.public_id(changed) != prototype.public_id(public)


def test_public_projection_is_a_fresh_deep_copy():
    prototype = _prototype()
    episode = prototype.generate(99, {"edge": "bounce"})
    snapshot = copy.deepcopy(episode)
    public = prototype.public_challenge(episode)
    public["train"][0]["input"][0][0] = (public["train"][0]["input"][0][0] + 1) % 10
    public["train"][0]["output"][0][0] = (public["train"][0]["output"][0][0] + 1) % 10
    public["test"][0]["input"][0][0] = (public["test"][0]["input"][0][0] + 1) % 10
    assert episode == snapshot
    assert prototype.public_challenge(episode) != public


class _IntegerSubclass(int):
    pass


@pytest.mark.parametrize(
    "argument,value",
    [("seed", value) for value in (True, False, 1.0, "1", None, -1, 2**63, _IntegerSubclass(1))]
    + [("demos", value) for value in (True, 2.0, "3", None, 1, 7, _IntegerSubclass(3))]
    + [("queries", value) for value in (True, 1.0, "1", None, 0, 5, _IntegerSubclass(1))],
)
def test_generate_rejects_nonexact_or_out_of_range_public_scalars(argument, value):
    prototype = _prototype()
    arguments = {"seed": 1, "settings": {"edge": "linear"}, "demos": 3, "queries": 4}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(**arguments)


@pytest.mark.parametrize(
    "settings",
    (None, [], "linear", {}, {"Edge": "linear"}, {"edge": "LINEAR"}, {"edge": "reflect"},
     {"edge": None}, {"edge": True}, {"edge": 1}, {"edge": []}, {"edge": {}},
     {"edge": "linear", "extra": 1}),
)
def test_program_and_generate_reject_malformed_settings(settings):
    prototype = _prototype()
    with pytest.raises((TypeError, ValueError)):
        prototype.program(settings)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(1, settings)


@pytest.mark.parametrize("index", (True, 0.0, "0", None, -1, 4))
def test_public_projection_rejects_invalid_query_indexes(index):
    prototype = _prototype()
    episode = prototype.generate(5, {"edge": "linear"}, queries=4)
    with pytest.raises((TypeError, ValueError, IndexError)):
        prototype.public_challenge(episode, query_index=index)
