"""Focused tests for the native anchor-hole relay parametric family."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_PROGRAM = """(rule! (lambda (g)
  (paint-objects-by g (objects g 0)
    (lambda (obj)
      (with-bbox obj (r1 c1 r2 c2)
        (let* ((sub (subgrid g r1 c1 r2 c2))
               (n-holes (length (objects sub 8))))
          (casev n-holes {1 1 2 2 3 3 4 7} (obj-color obj))))))))"""
CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))
COLOR_BY_COUNT = {1: 1, 2: 2, 3: 3, 4: 7}


def _load(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _components(grid, color=8):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append(cells)
    return sorted(result, key=min)


def _regions(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        region = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    region.add(nxt)
                    stack.append(nxt)
        result.append(region)
    return result


def _facts(grid):
    facts = []
    for cells in _components(grid):
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        r2 = max(r for r, _ in cells)
        c2 = max(c for _, c in cells)
        noncyan = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if grid[r][c] != 8
        }
        facts.append({
            "cells": cells,
            "bbox": (r1, c1, r2, c2),
            "hole_count": len(_regions(noncyan)),
        })
    return facts


def _oracle(grid, scope):
    facts = _facts(grid)
    assert facts
    anchor_count = facts[0]["hole_count"]
    out = [row[:] for row in grid]
    for fact in facts:
        count = fact["hole_count"]
        color = COLOR_BY_COUNT.get(count, 8)
        if scope == "anchor_hole_matches" and count != anchor_count:
            color = 8
        for r, c in fact["cells"]:
            out[r][c] = color
    return out


def test_adapter_preserves_exact_canonical_program_and_validates_settings():
    adapter = _load("fa_anchor_hole_adapter_contract", PARAMETRIC / "adapter.py")
    prototype = _load("fa_anchor_hole_prototype_contract", PARAMETRIC / "prototype.py")

    assert adapter.program({"recolor_scope": "all_objects"}) == CANONICAL_PROGRAM
    assert adapter.program({"recolor_scope": "anchor_hole_matches"}) == prototype.MATCH_PROGRAM
    assert prototype.counterfactual_program() != prototype.MATCH_PROGRAM

    for invalid in (
        None,
        {},
        {"recolor_scope": "unknown"},
        {"recolor_scope": "all_objects", "extra": 1},
    ):
        with pytest.raises(ValueError):
            adapter.program(invalid)


@pytest.mark.parametrize("seed", [0, 17, 991])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_matched_inputs_prefix_stability_and_python_labels(seed, demos, queries):
    prototype = _load(
        f"fa_anchor_hole_proto_{seed}_{demos}_{queries}",
        PARAMETRIC / "prototype.py",
    )
    canonical = prototype.generate_episode(
        seed, recolor_scope="all_objects", demos=demos, queries=queries
    )
    matched = prototype.generate_episode(
        seed, recolor_scope="anchor_hole_matches", demos=demos, queries=queries
    )

    assert len(canonical["train"]) == len(matched["train"]) == demos
    assert len(canonical["test"]) == len(matched["test"]) == queries
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in matched["train"] + matched["test"]
    ]

    maximum = prototype.generate_episode(
        seed, recolor_scope="anchor_hole_matches", demos=6, queries=4
    )
    assert matched["train"] == maximum["train"][:demos]
    assert matched["test"] == maximum["test"][:queries]

    pairs = canonical["train"] + canonical["test"]
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    assert len(serialized) == len(set(serialized))

    for scope, episode in (
        ("all_objects", canonical),
        ("anchor_hole_matches", matched),
    ):
        for pair in episode["train"] + episode["test"]:
            grid = pair["input"]
            assert {value for row in grid for value in row} <= {0, 8}
            facts = _facts(grid)
            assert 4 <= len(facts) <= 6
            assert all(0 <= fact["hole_count"] <= 6 for fact in facts)
            assert pair["output"] == _oracle(grid, scope)
            assert (len(pair["output"]), len(pair["output"][0])) == (
                len(grid), len(grid[0])
            )

    for c_pair, m_pair in zip(canonical["train"], matched["train"]):
        assert c_pair["output"] != m_pair["output"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "recolor_scope": "all_objects", "demos": 3, "queries": 4},
        {"seed": -1, "recolor_scope": "all_objects", "demos": 3, "queries": 4},
        {"seed": 0, "recolor_scope": "unknown", "demos": 3, "queries": 4},
        {"seed": 0, "recolor_scope": "all_objects", "demos": 1, "queries": 4},
        {"seed": 0, "recolor_scope": "all_objects", "demos": 7, "queries": 4},
        {"seed": 0, "recolor_scope": "all_objects", "demos": 3, "queries": 0},
        {"seed": 0, "recolor_scope": "all_objects", "demos": 3, "queries": 5},
    ],
)
def test_invalid_episode_requests_reject(kwargs):
    prototype = _load("fa_anchor_hole_bad_requests", PARAMETRIC / "prototype.py")
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)


def test_first_two_demos_teach_input_derived_anchor_count_and_refute_fixed_counts():
    prototype = _load("fa_anchor_hole_teaching", PARAMETRIC / "prototype.py")
    audit = _load("fa_anchor_hole_audit", PARAMETRIC / "audit.py")

    for seed in (0, 17):
        episode = prototype.generate_episode(
            seed, recolor_scope="anchor_hole_matches", demos=2, queries=4
        )
        assert [_facts(pair["input"])[0]["hole_count"] for pair in episode["train"]] == [1, 3]
        for pair in episode["train"]:
            counts = [fact["hole_count"] for fact in _facts(pair["input"])]
            assert counts.count(counts[0]) >= 2
            assert any(count in COLOR_BY_COUNT and count != counts[0] for count in counts)

    report = audit.python_audit(seeds=(0, 17), demo_counts=range(2, 7))
    assert report["ambiguities"] == []
    assert report["episodes"] == 10
    assert report["stress_30x30"] == 10
    assert {
        "all_objects",
        "anchor_only",
        "first_match_only",
        "fixed_count_1",
        "fixed_count_2",
        "fixed_count_3",
        "fixed_count_4",
        "second_object_anchor",
    } <= set(report["rivals"])


def test_fourth_query_is_substantive_30x30_with_boundary_spread():
    prototype = _load("fa_anchor_hole_stress", PARAMETRIC / "prototype.py")
    episode = prototype.generate_episode(
        17, recolor_scope="anchor_hole_matches", demos=3, queries=4
    )
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    assert len(cyan) >= 80
    assert {0, 29} <= {r for r, _ in cyan}
    assert {0, 29} <= {c for _, c in cyan}
    facts = _facts(grid)
    assert len(facts) == 6
    assert len({fact["bbox"] for fact in facts}) == 6


def test_public_turn_hides_private_fields_and_matches_one_query_request():
    prototype = _load("fa_anchor_hole_public", PARAMETRIC / "prototype.py")
    full = prototype.generate_episode(
        23, recolor_scope="anchor_hole_matches", demos=3, queries=4
    )
    single = prototype.generate_episode(
        23, recolor_scope="anchor_hole_matches", demos=3, queries=1
    )
    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("recolor_scope", "program", "seed", "answer"):
        assert forbidden not in text


def test_racket_programs_match_python_on_constructive_cases():
    prototype = _load("fa_anchor_hole_racket", PARAMETRIC / "prototype.py")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate_episode(
        0, recolor_scope="anchor_hole_matches", demos=2, queries=1
    )
    programs = {
        scope: prototype.rule_text(scope)
        for scope in ("all_objects", "anchor_hole_matches")
    }
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for scope, program in programs.items():
            wrapped = wrap_rule(program)
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(f"({wrapped} {literal})")
                assert actual == _oracle(pair["input"], scope)


def test_causal_case_wrong_intermediate_changes_final_output():
    prototype = _load("fa_anchor_hole_causal", PARAMETRIC / "prototype.py")
    case = prototype.causal_case(seed=0)
    assert case["settings"] == {"recolor_scope": "anchor_hole_matches"}
    assert case["intermediate_value"]["anchor_hole_count"] != case["intermediate_value"]["wrong_second_object_hole_count"]
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
