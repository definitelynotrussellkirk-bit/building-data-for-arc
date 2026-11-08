"""Behavioral checks for the opt-in ordered-symbol path adapter."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes


ROOT = find_root(__file__)
HOME = ROOT / "generators/f0f2806877da/workspace/parametric"


@pytest.fixture(scope="module")
def adapter():
    path = HOME / "adapter.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("tested_path_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_selected_reference(adapter):
    assert adapter is not None, "the native read-order adapter is not implemented"
    with canonical_path(ROOT).open() as handle:
        canonical = {r["program_solution"] for r in map(json.loads, handle)
                     if r.get("task_id") == "f0f2806877da"}
    assert canonical == {adapter.program({"read_order": "forward"})}
    assert adapter.program({"read_order": "reverse"}) not in canonical


@pytest.mark.parametrize("order", ["forward", "reverse"])
def test_literal_trace_executes_in_protected_racket(adapter, order):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = [[0, 0, 0, 0, 0, 2, 2, 0, 2, 2, 0, 2],
            [2, 2, 0, 2, 0, 2, 2, 0, 2, 2, 0, 2]]
    expected = {
        "forward": [[0, 0, 0, 3, 0, 0, 0], [0, 0, 2, 2, 0, 0, 0],
                    [0, 0, 2, 0, 0, 0, 0], [0, 0, 2, 0, 0, 0, 0],
                    [0, 0, 2, 2, 0, 0, 0], [0, 0, 0, 2, 2, 0, 0],
                    [0, 0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 2, 0, 0]],
        "reverse": [[0, 0, 0, 3, 0, 0, 0], [0, 0, 0, 2, 0, 0, 0],
                    [0, 0, 0, 2, 0, 0, 0], [0, 0, 0, 2, 2, 0, 0],
                    [0, 0, 0, 0, 2, 2, 0], [0, 0, 0, 0, 0, 2, 0],
                    [0, 0, 0, 0, 0, 2, 0], [0, 0, 0, 0, 2, 2, 0]],
    }[order]
    settings = {"read_order": order}
    assert adapter.predict(grid, settings) == expected
    bridge = RacketBridge()
    try:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        literal = "'(" + " ".join("(" + " ".join(map(str, r)) + ")" for r in grid) + ")"
        assert bridge.eval_text(f"({wrap_rule(adapter.program(settings))} {literal})") == expected
    finally:
        bridge.close()


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_independent_counts_matched_inputs_and_novel_queries(adapter, seed, demos, queries):
    forward = adapter.generate(seed, {"read_order": "forward"}, demos, queries)
    reverse = adapter.generate(seed, {"read_order": "reverse"}, demos, queries)
    assert (len(forward["train"]), len(forward["test"])) == (demos, queries)
    all_inputs = [p["input"] for split in ("train", "test") for p in forward[split]]
    assert len({json.dumps(g) for g in all_inputs}) == demos + queries
    assert all(len(g) == 2 and all(len(row) == 12 for row in g) for g in all_inputs)
    for split in ("train", "test"):
        assert [p["input"] for p in forward[split]] == [p["input"] for p in reverse[split]]
    assert any(a["output"] != b["output"] for a, b in zip(forward["train"], reverse["train"]))
    # The first two examples carry different paths despite identical command counts.
    assert forward["train"][0]["output"] != forward["train"][1]["output"]


def test_first_turn_does_not_reveal_future_count_or_inputs(adapter):
    settings = {"read_order": "reverse"}
    many = adapter.generate(17, settings, 3, 4)
    one = adapter.generate(17, settings, 3, 1)
    assert adapter.public_turn(many, 0) == adapter.public_turn(one, 0)
    assert adapter.public_turn(many, 0) == public_challenge_bytes(one)
    public = json.loads(adapter.public_turn(many, 2))
    assert set(public) == {"train", "test"}
    assert public["train"] == many["train"]
    assert public["test"] == [{"input": many["test"][2]["input"]}]
    changed = copy.deepcopy(many)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "private text"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[8]]
    assert adapter.public_turn(changed, 0) == adapter.public_turn(many, 0)


def test_boundary_queries_reach_both_sides_and_bottom(adapter):
    for order in ("forward", "reverse"):
        episode = adapter.generate(0, {"read_order": order}, 2, 4)
        left, right = [pair["output"] for pair in episode["test"][:2]]
        assert any(row[0] == 2 for row in left)
        assert any(row[6] == 2 for row in right)
        assert all(2 in pair["output"][-1] for pair in episode["test"])


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"demos": 1}, {"demos": 7}, {"demos": 2.0}, {"demos": True},
    {"queries": 0}, {"queries": 5}, {"queries": 4.0}, {"queries": False},
    {"settings": {}}, {"settings": {"read_order": "sideways"}},
    {"settings": {"read_order": True}},
    {"settings": {"read_order": "forward", "hidden": 1}},
])
def test_invalid_requests_fail_closed(adapter, kwargs):
    request = dict(seed=0, settings={"read_order": "forward"}, demos=3, queries=4)
    request.update(kwargs)
    with pytest.raises(ValueError):
        adapter.generate(**request)


@pytest.mark.parametrize("index", [-1, True, 1.0, 4])
def test_public_turn_rejects_invalid_index(adapter, index):
    episode = adapter.generate(0, {"read_order": "forward"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.public_turn(episode, index)


def test_generation_returns_independent_mutable_grids(adapter):
    first = adapter.generate(17, {"read_order": "forward"}, 3, 4)
    expected = copy.deepcopy(first)
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert adapter.generate(17, {"read_order": "forward"}, 3, 4) == expected


@pytest.mark.parametrize("seed,decoder", [
    (1, "(if (zero? (at g 0 e)) 1 2)"),
    (2, "(if (or (zero? (at g 0 s)) (zero? (at g 0 e))) 1 2)"),
])
@pytest.mark.parametrize("order", ["forward", "reverse"])
def test_two_demos_reject_offdiagonal_decoder_rivals(adapter, seed, decoder, order):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    settings = {"read_order": order}
    episode = adapter.generate(seed, settings, 2, 4)
    rival = adapter.program(settings).replace("(if (zero? (at g 0 s)) 1 2)", decoder)
    bridge = RacketBridge()
    try:
        assert bridge.runtime_identity["protected"] is True
        outputs = []
        for pair in episode["train"]:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")"
                                      for row in pair["input"]) + ")"
            outputs.append(bridge.eval_text(f"({wrap_rule(rival)} {literal})"))
        assert any(output != pair["output"] for output, pair in zip(outputs, episode["train"])), \
            "a wrong upper-row decoder still fits every demonstration"
    finally:
        bridge.close()


def test_two_demo_teaching_covers_all_upper_row_bend_patterns(adapter):
    for seed in range(24):
        episode = adapter.generate(seed, {"read_order": "forward"}, 2, 4)
        patterns = set()
        for pair in episode["train"]:
            grid = pair["input"]
            pieces, _ = adapter._source()._parse(grid)
            patterns.update((grid[0][start], grid[0][end])
                            for start, end, _ in pieces if start != end)
        assert patterns == {(0, 0), (0, 2), (2, 0), (2, 2)}
