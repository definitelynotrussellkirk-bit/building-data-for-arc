"""Exercise the final-panel typed-cursor authority with real Racket.

Run from a prepared ARCpuzzles checkout with:
  python -m pytest -q generators/generic_waypoint_route_gen2/tests/test_reference_rule.py
The fixture explicitly stages both waypoint generators because gen2 imports
gen1's route sampler. No sibling checkout or inherited expected-answer runner
is used.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / "catalog/puzzles.jsonl").is_file())
SEEDS = (0, 1, 2, 17, 31, 207)


@pytest.fixture(scope="module")
def authority(tmp_path_factory):
    from arcpuzzles import Catalog, runtime

    stage = tmp_path_factory.mktemp("typed-waypoint-runtime")
    runtime.prepare_runtime(Catalog(ROOT), stage, task_ids=[
        "generic_waypoint_route_gen1", "generic_waypoint_route_gen2"])
    prefixes = ("puzzle_generators", "arc_repl", "scripts")
    def is_runtime_module(name):
        return any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)
    previous_modules = {name: value for name, value in tuple(sys.modules.items())
                        if is_runtime_module(name)}
    for name in previous_modules:
        sys.modules.pop(name)
    sys.path.insert(0, str(stage))
    try:
        module = importlib.import_module("puzzle_generators.generic.concepts.waypoint_route.gen2")
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        with RacketBridge() as bridge:
            bridge.eval_text("(define typed-waypoint-rule " + wrap_rule(module.PROGRAM) + ")")

            def apply(grid):
                bridge.define_grid("typed-waypoint-input", grid)
                return bridge.eval_text("(typed-waypoint-rule typed-waypoint-input)")

            yield module, apply
    finally:
        sys.path.remove(str(stage))
        for name in list(sys.modules):
            if is_runtime_module(name):
                sys.modules.pop(name)
        sys.modules.update(previous_modules)


def test_standalone_rule_preserves_the_embedded_authority(authority):
    module, _ = authority
    reference = HOME / "reference.rkt"
    assert reference.is_file(), "missing task-owned Racket authority"
    assert reference.read_bytes() == module.PROGRAM.encode("utf-8")
    normalized = hashlib.sha256(" ".join(reference.read_text().split()).encode()).hexdigest()[:12]
    assert normalized == module.RULE_HASH


def test_canonical_candidate_has_runtime_labeled_teaching_and_four_queries(authority):
    module, apply = authority
    candidate_path = HOME / "workspace/canonical-candidate.json"
    assert candidate_path.is_file(), "missing fixed canonical examples"
    row = json.loads(candidate_path.read_text())
    assert row["task_id"] == module.TASK_ID
    assert row["source"] == "custom"
    assert row["program_solution"] == module.PROGRAM
    assert row["relationship"] == "semantic_variant"
    assert row["source_task_id"] == "5545f144"
    assert len(row["train"]) == 3 and len(row["test"]) == 4
    pairs = row["train"] + row["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == len(pairs)
    for pair in pairs:
        assert module.strict_canonical_like(pair["input"]) == []
        assert apply(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", SEEDS)
def test_seeded_pairs_match_real_racket_in_each_difficulty(authority, difficulty, seed):
    module, apply = authority
    task = module.generate_task(seed, difficulty=difficulty)
    assert module.self_check_task(task) == []
    for pair in task["train"] + task["test"]:
        assert module.strict_canonical_like(pair["input"]) == []
        assert all(witness(pair["input"]) for witness in module.SEMANTIC_WITNESSES.values())
        assert apply(pair["input"]) == pair["output"]


@pytest.mark.parametrize("offset", range(10))
def test_head_tail_roles_follow_colors_across_the_whole_palette(authority, offset):
    module, apply = authority
    pair = module.generate_task(17, difficulty="medium")["train"][0]
    recolor = lambda grid: [[(value + offset) % 10 for value in row] for row in grid]
    grid, expected = recolor(pair["input"]), recolor(pair["output"])
    state = module._parse_last_state(grid)
    assert state["head_color"] != state["tail_color"]
    assert {state["panel"][r][c] for r, c in state["dots"]} == {state["head_color"]}
    assert apply(grid) == expected


def direction_case(turns):
    """An independently rendered clean route with two still-unseen hops."""
    side, bg, head_color, tail_color, separator = 10, 0, 4, 8, 7
    points = [(7, 1), (2, 1), (2, 6), (6, 6)]
    for _ in range(turns):
        points = [(c, side - 1 - r) for r, c in points]

    def unit(delta):
        return tuple((v > 0) - (v < 0) for v in delta)

    panels = []
    for index in (0, 1):
        head = points[index]
        previous, current = (points[0], points[1]) if index == 0 else (points[index - 1], head)
        dr, dc = unit((current[0] - previous[0], current[1] - previous[1]))
        tail = (head[0] - dr, head[1] - dc)
        panel = [[bg] * side for _ in range(side)]
        panel[head[0]][head[1]] = head_color
        panel[tail[0]][tail[1]] = tail_color
        for r, c in points[index + 1:]:
            panel[r][c] = head_color
        panels.append(panel)
    grid = [a + [separator] + b for a, b in zip(*panels)]
    final, previous = points[-1], points[-2]
    dr, dc = unit((final[0] - previous[0], final[1] - previous[1]))
    expected = [[bg] * side for _ in range(side)]
    expected[final[0]][final[1]] = head_color
    expected[final[0] - dr][final[1] - dc] = tail_color
    return grid, expected, points[1:], (dr, dc)


@pytest.mark.parametrize("turns", range(4))
def test_two_sequential_hops_and_final_orientation_in_each_direction(authority, turns):
    module, apply = authority
    grid, expected, route, final_vector = direction_case(turns)
    state = module._parse_last_state(grid)
    position, remaining = state["head"], list(state["dots"])
    trace = [position]
    while remaining:
        aligned = [p for p in remaining if p[0] == position[0] or p[1] == position[1]]
        assert len(aligned) == 1
        position = aligned[0]
        trace.append(position)
        remaining.remove(position)
    assert trace == route and len(trace) == 3
    assert final_vector in ((1, 0), (0, -1), (-1, 0), (0, 1))
    assert module.strict_canonical_like(grid) == []
    assert apply(grid) == expected


def test_rule_scope_records_that_earlier_panels_are_unused_context(authority):
    module, apply = authority
    pair = module.generate_task(17, difficulty="medium")["train"][0]
    grid = deepcopy(pair["input"])
    panel, bg = module._last_panel(grid)
    last_start = len(grid[0]) - len(panel[0])
    separators = {c for c in range(last_start) if grid[0][c] != bg
                  and all(row[c] == grid[0][c] for row in grid)}
    changed = 0
    for row in grid:
        for c in range(last_start):
            if c not in separators:
                changed += row[c] != bg
                row[c] = bg
    assert changed > 0
    assert apply(grid) == apply(pair["input"]) == pair["output"]
