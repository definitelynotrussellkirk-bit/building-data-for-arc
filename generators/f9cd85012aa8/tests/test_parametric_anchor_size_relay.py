"""Focused tests for the native anchor-size relay parametric family."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_PROGRAM = '(rule! (let ((dummy 0)) (define (object-color-cells grid color) (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0))) (let* ((obj (first (object-color-cells g 6))) (bb (obj-bbox obj))) (grid-from-fn (rows g) (cols g) (lambda (r c) (if (and (>= r (first bb)) (<= r (third bb)) (>= c (second bb)) (<= c (fourth bb))) 6 0))))))'
CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _load(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _objects(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining and grid[nxt[0]][nxt[1]] == color:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append({
            "color": color,
            "cells": cells,
            "bbox": (
                min(r for r, _ in cells),
                min(c for _, c in cells),
                max(r for r, _ in cells),
                max(c for _, c in cells),
            ),
        })
    return sorted(result, key=lambda obj: min(obj["cells"]))


def _fill_bbox(grid, obj):
    out = [[0 for _ in row] for row in grid]
    r0, c0, r1, c1 = obj["bbox"]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = obj["color"]
    return out


def _oracle(grid, mode):
    objects = _objects(grid)
    anchors = [obj for obj in objects if obj["color"] == 6]
    candidates = [obj for obj in objects if obj["color"] != 6]
    assert len(anchors) == 1 and candidates
    if mode == "canonical_target":
        target = anchors[0]
    else:
        target = candidates[(len(anchors[0]["cells"]) - 3) % len(candidates)]
    return _fill_bbox(grid, target)


def test_adapter_preserves_exact_canonical_program_and_validates_settings():
    adapter = _load("f9_anchor_size_adapter_contract", PARAMETRIC / "adapter.py")
    prototype = _load("f9_anchor_size_prototype_contract", PARAMETRIC / "prototype.py")

    assert adapter.program({"target_mode": "canonical_target"}) == CANONICAL_PROGRAM
    assert adapter.program({"target_mode": "anchor_size_relay"}) == prototype.RELAY_PROGRAM
    assert prototype.counterfactual_program() != prototype.RELAY_PROGRAM

    for invalid in (
        None,
        {},
        {"target_mode": "unknown"},
        {"target_mode": "canonical_target", "extra": 1},
    ):
        with pytest.raises(ValueError):
            adapter.program(invalid)


@pytest.mark.parametrize("seed", [0, 17, 991])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_matched_inputs_prefix_stability_and_python_labels(seed, demos, queries):
    prototype = _load(
        f"f9_anchor_size_proto_{seed}_{demos}_{queries}",
        PARAMETRIC / "prototype.py",
    )
    canonical = prototype.generate_episode(
        seed, target_mode="canonical_target", demos=demos, queries=queries
    )
    relay = prototype.generate_episode(
        seed, target_mode="anchor_size_relay", demos=demos, queries=queries
    )

    assert len(canonical["train"]) == len(relay["train"]) == demos
    assert len(canonical["test"]) == len(relay["test"]) == queries
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in relay["train"] + relay["test"]
    ]

    maximum = prototype.generate_episode(
        seed, target_mode="anchor_size_relay", demos=6, queries=4
    )
    assert relay["train"] == maximum["train"][:demos]
    assert relay["test"] == maximum["test"][:queries]

    pairs = canonical["train"] + canonical["test"]
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    assert len(serialized) == len(set(serialized))

    for mode, episode in (
        ("canonical_target", canonical),
        ("anchor_size_relay", relay),
    ):
        for pair in episode["train"] + episode["test"]:
            grid = pair["input"]
            assert 1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30
            assert {value for row in grid for value in row} <= set(range(10))
            objects = _objects(grid)
            anchors = [obj for obj in objects if obj["color"] == 6]
            candidates = [obj for obj in objects if obj["color"] != 6]
            assert len(anchors) == 1
            assert 4 <= len(candidates) <= 6
            assert 3 <= len(anchors[0]["cells"]) <= 10
            assert len({obj["color"] for obj in objects}) == len(objects)
            assert all(
                len(obj["cells"])
                < (obj["bbox"][2] - obj["bbox"][0] + 1)
                * (obj["bbox"][3] - obj["bbox"][1] + 1)
                for obj in objects
            )
            assert pair["output"] == _oracle(grid, mode)
            assert (len(pair["output"]), len(pair["output"][0])) == (
                len(grid), len(grid[0])
            )

    for c_pair, r_pair in zip(canonical["train"], relay["train"]):
        assert c_pair["output"] != r_pair["output"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "target_mode": "canonical_target", "demos": 3, "queries": 4},
        {"seed": -1, "target_mode": "canonical_target", "demos": 3, "queries": 4},
        {"seed": 0, "target_mode": "unknown", "demos": 3, "queries": 4},
        {"seed": 0, "target_mode": "canonical_target", "demos": 1, "queries": 4},
        {"seed": 0, "target_mode": "canonical_target", "demos": 7, "queries": 4},
        {"seed": 0, "target_mode": "canonical_target", "demos": 3, "queries": 0},
        {"seed": 0, "target_mode": "canonical_target", "demos": 3, "queries": 5},
    ],
)
def test_invalid_episode_requests_reject(kwargs):
    prototype = _load("f9_anchor_size_bad_requests", PARAMETRIC / "prototype.py")
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)


def test_first_two_demos_teach_input_derived_selector_and_refute_rivals():
    prototype = _load("f9_anchor_size_teaching", PARAMETRIC / "prototype.py")
    audit = _load("f9_anchor_size_audit", PARAMETRIC / "audit.py")

    for seed in (0, 17):
        episode = prototype.generate_episode(
            seed, target_mode="anchor_size_relay", demos=2, queries=4
        )
        anchor_sizes = []
        target_indices = []
        for pair in episode["train"]:
            objects = _objects(pair["input"])
            anchor = next(obj for obj in objects if obj["color"] == 6)
            candidates = [obj for obj in objects if obj["color"] != 6]
            anchor_sizes.append(len(anchor["cells"]))
            target_indices.append((len(anchor["cells"]) - 3) % len(candidates))
        assert anchor_sizes == [3, 5]
        assert target_indices == [0, 2]

    report = audit.python_audit(seeds=(0, 17), demo_counts=range(2, 7))
    assert report["ambiguities"] == []
    assert report["episodes"] == 10
    assert report["stress_30x30"] == 10
    assert {
        "canonical_target",
        "all_candidate_boxes",
        "fixed_candidate_0",
        "fixed_candidate_1",
        "fixed_candidate_2",
        "fixed_candidate_3",
        "largest_candidate",
        "smallest_candidate",
        "wrong_plus_one_selector",
        "reverse_selector",
    } <= set(report["rivals"])


def test_fourth_query_is_substantive_30x30_with_boundary_spread():
    prototype = _load("f9_anchor_size_stress", PARAMETRIC / "prototype.py")
    episode = prototype.generate_episode(
        17, target_mode="anchor_size_relay", demos=3, queries=4
    )
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 35
    assert {0, 29} <= {r for r, _ in nonzero}
    assert {0, 29} <= {c for _, c in nonzero}
    objects = _objects(grid)
    assert len(objects) == 7
    assert len({obj["bbox"] for obj in objects}) == 7


def test_public_turn_hides_private_fields_and_matches_one_query_request():
    prototype = _load("f9_anchor_size_public", PARAMETRIC / "prototype.py")
    full = prototype.generate_episode(
        23, target_mode="anchor_size_relay", demos=3, queries=4
    )
    single = prototype.generate_episode(
        23, target_mode="anchor_size_relay", demos=3, queries=1
    )
    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("target_mode", "program", "seed", "answer"):
        assert forbidden not in text


def test_racket_programs_match_python_on_constructive_cases():
    prototype = _load("f9_anchor_size_racket", PARAMETRIC / "prototype.py")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate_episode(
        0, target_mode="anchor_size_relay", demos=2, queries=1
    )
    programs = {
        mode: prototype.rule_text(mode)
        for mode in ("canonical_target", "anchor_size_relay")
    }
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for mode, program in programs.items():
            wrapped = wrap_rule(program)
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(f"({wrapped} {literal})")
                assert actual == _oracle(pair["input"], mode)


def test_causal_case_wrong_intermediate_changes_final_output():
    prototype = _load("f9_anchor_size_causal", PARAMETRIC / "prototype.py")
    case = prototype.causal_case(seed=0)
    assert case["settings"] == {"target_mode": "anchor_size_relay"}
    assert case["intermediate_value"]["anchor_size"] == 3
    assert case["intermediate_value"]["target_index"] == 0
    assert case["intermediate_value"]["wrong_target_index"] == 1
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
