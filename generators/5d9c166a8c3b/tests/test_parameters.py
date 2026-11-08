"""Focused contract tests for the separate all/largest-bbox parameter family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

TASK = "5d9c166a8c3b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _module():
    path = HOME / "adapter.py"
    assert path.is_file(), "The native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("bbox_parameters_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _witness():
    grid = [[0] * 10 for _ in range(8)]
    for r, c in [(0, 0), (0, 4), (3, 2), (6, 6), (6, 7), (7, 6), (7, 7), (6, 9)]:
        grid[r][c] = 4
    return grid


def test_default_is_exact_canonical_and_preserves_all_historical_labels():
    adapter = _module()
    from arcpuzzles.catalog import Catalog
    variants = Catalog(ROOT)._variants()[TASK]
    assert {v["program_solution"] for v in variants} == {
        adapter.program({"fill_scope": "all"})
    }
    for pair in canonical_pairs(TASK, root=ROOT):
        assert adapter.prototype.solve(pair["input"], "all") == pair["output"]


def test_largest_selection_consumes_dynamic_closure_not_original_graph():
    adapter = _module()
    grid = _witness()
    expected = copy.deepcopy(grid)
    for r in range(4):
        for c in range(5):
            if expected[r][c] == 0:
                expected[r][c] = 2
    assert adapter.prototype.solve(grid, "largest_bbox") == expected
    wrong = adapter.prototype.solve(grid, "largest_bbox", grouping="static_graph")
    assert wrong != expected
    assert sum(v == 2 for row in expected for v in row) == 17
    assert sum(v == 2 for row in wrong for v in row) == 3


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_distinctness_matched_inputs_and_first_query_prefix(demos):
    adapter = _module()
    for seed in [0, 17]:
        episodes = [adapter.generate(seed, {"fill_scope": scope}, demos, 4)
                    for scope in ["all", "largest_bbox"]]
        for scope, episode in zip(["all", "largest_bbox"], episodes):
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            inputs = [p["input"] for p in episode["train"] + episode["test"]]
            assert len({json.dumps(g) for g in inputs}) == demos + 4
            assert episode["program_solution"] == adapter.program({"fill_scope": scope})
            one = adapter.generate(seed, {"fill_scope": scope}, demos, 1)
            assert one["train"] == episode["train"]
            assert one["test"] == episode["test"][:1]
            assert adapter.prototype.first_turn_bytes(one) == adapter.prototype.first_turn_bytes(episode)
            assert adapter.prototype.teaching_check(episode, scope)["ambiguous_queries"] == []
        assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
            p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]
        assert episodes[0]["train"][0]["output"] != episodes[1]["train"][0]["output"]


@pytest.mark.parametrize("height,width", [(7, 7), (7, 30), (30, 7), (30, 30)])
def test_substantive_size_boundaries_and_exact_integer_cells(height, width):
    adapter = _module()
    for scope in ["all", "largest_bbox"]:
        episode = adapter.prototype.generate(41, {"fill_scope": scope}, 2, 4,
                                             height=height, width=width)
        for pair in episode["train"] + episode["test"]:
            assert len(pair["input"]) == height
            assert all(len(row) == width for row in pair["input"])
            assert all(type(v) is int and 0 <= v <= 9
                       for key in ["input", "output"] for row in pair[key] for v in row)
            cells = [(r, c) for r, row in enumerate(pair["input"])
                     for c, value in enumerate(row) if value]
            assert max(r for r, _ in cells) - min(r for r, _ in cells) >= height - 3
            assert max(c for _, c in cells) - min(c for _, c in cells) >= width - 3
            assert pair["input"] != pair["output"]
            if height == width == 30:
                assert len(cells) >= 35
                assert sum(v == 2 for row in pair["output"] for v in row) >= 40
        assert adapter.prototype.teaching_check(episode, scope)["ambiguous_queries"] == []


def test_all_maximal_ties_are_filled_and_foreground_is_preserved():
    adapter = _module()
    grid = [[0] * 7 for _ in range(7)]
    for r, c in [(0, 0), (0, 2), (2, 1), (4, 4), (4, 5), (4, 6), (5, 4), (6, 4)]:
        grid[r][c] = 8
    assert adapter.prototype.solve(grid, "largest_bbox") == adapter.prototype.solve(grid, "all")
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                assert adapter.prototype.solve(grid, "largest_bbox")[r][c] == v


def test_first_turn_ignores_private_metadata_answers_and_future_queries():
    adapter = _module()
    episode = adapter.generate(8, {"fill_scope": "largest_bbox"}, 3, 4)
    before = adapter.prototype.first_turn_bytes(episode)
    changed = copy.deepcopy(episode)
    changed.update(seed="secret", settings={"fill_scope": "wrong"}, program_solution="secret")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed["test"][1:] = [{"input": [[9]], "output": [[1]]}]
    assert adapter.prototype.first_turn_bytes(changed) == before
    visible = json.loads(before)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    assert before == public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (0, True, 4),
                                                 (0, 1, 4), (0, 7, 4), (0, 3, 0),
                                                 (0, 3, 5), (0, 3, 1.0)])
def test_invalid_request_types_and_bounds_fail_visibly(seed, demos, queries):
    with pytest.raises(ValueError):
        _module().generate(seed, {"fill_scope": "all"}, demos, queries)


@pytest.mark.parametrize("settings", [{}, {"fill_scope": "bogus"},
                                     {"fill_scope": "all", "extra": 1},
                                     {"fill_scope": True}, None])
def test_invalid_settings_rejected(settings):
    with pytest.raises(ValueError):
        _module().program(settings)


def test_protected_racket_programs_and_rivals_match_on_causal_witness():
    adapter = _module()
    from arcpuzzles.parametric_worker import _real_evaluator
    evaluate, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        tie = adapter.generate(1, {"fill_scope": "largest_bbox"}, 2, 4)["train"][1]["input"]
        for scope in ["all", "largest_bbox"]:
            specs = {"selected": {"scope": scope}, **adapter.prototype.rival_specs(scope)}
            for name, spec in specs.items():
                text = adapter.prototype.rule_program(**spec)
                assert text.count("(") == text.count(")"), (scope, name)
                for grid in [_witness(), tie]:
                    assert evaluate(text, grid) == adapter.prototype.solve(grid, **spec), (scope, name)
    finally:
        bridge.close()


def test_two_demos_eliminate_single_merge_pass_with_executed_labels():
    adapter = _module()
    from arcpuzzles.parametric_worker import _real_evaluator
    evaluate, _, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        episode = adapter.generate(0, {"fill_scope": "all"}, 2, 4)
        one_pass = adapter.program({"fill_scope": "all"}).replace(
            "(define merged-groups (merge-fixed groups))",
            "(define merged-groups (do-merge groups))")
        assert any(evaluate(one_pass, pair["input"]) != pair["output"]
                   for pair in episode["train"]), "a single-pass wrong rule survives the visible demos"
    finally:
        bridge.close()
