"""Execute hand-derived component/relay cases in the protected reference runtime."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load_rules():
    path = HOME / "workspace/parametric/rules.py"
    assert path.is_file(), "The native parametric Racket rules have not been implemented"
    spec = importlib.util.spec_from_file_location("a4fb_rules_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    from arc_repl.racket_bridge import RacketBridge
    value = RacketBridge()
    assert value.runtime_identity["backend"] == "racket"
    assert value.runtime_identity["protected"] is True
    yield value
    value.close()


def execute(bridge, source, grid):
    from puzzle_generators.rule_wrap import wrap_rule
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(source)} {literal})")


def fixture(relay_color=2):
    grid = [[0] * 12 for _ in range(12)]
    roles = {
        "anchor": (1, {(5, 5)}),
        "large": (relay_color, {(5, 6), (5, 7), (5, 8), (5, 9)}),
        "small": (3, {(5, 4), (5, 3)}),
        "already4": (4, {(4, 5)}),
        "child": (6, {(4, 8), (3, 8)}),
        "wrong_child": (7, {(4, 3)}),
        "grandchild": (8, {(2, 8)}),
        "diagonal": (9, {(6, 4)}),
        "global_large": (5, {(9, c) for c in range(2, 9)}),
        "same_color_remote": (relay_color, {(10, 10)}),
        "same_color_diagonal": (relay_color, {(6, 10)}),
    }
    for color, cells in roles.values():
        for r, c in cells:
            grid[r][c] = color
    return grid, roles


@pytest.mark.parametrize("mode", ["direct", "largest_relay"])
@pytest.mark.parametrize("relay_color", [2, 4])
def test_exact_original_components_choose_relay_without_repainting_anchor(bridge, mode, relay_color):
    rules = load_rules()
    grid, roles = fixture(relay_color)
    expected = [row[:] for row in grid]
    for role in ["large", "small", "already4"] + (["child"] if mode == "largest_relay" else []):
        for r, c in roles[role][1]:
            expected[r][c] = 4
    assert execute(bridge, rules.program({"mode": mode}), grid) == expected
    assert grid[5][5] == 1


def test_default_program_preserves_exact_canonical_authority():
    rules = load_rules()
    from reviewer_support import canonical_path, find_root
    root = find_root(__file__)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row["task_id"] == "a4fb12580b3f"}
    assert programs == {rules.program({"mode": "direct"})}


@pytest.mark.parametrize("settings", [{}, {"mode": "bad"}, {"mode": True}, {"mode": "direct", "seed": 1}, None])
def test_undeclared_settings_are_rejected(settings):
    with pytest.raises(ValueError):
        load_rules().program(settings)


def test_wrong_relay_changes_only_the_competing_branch(bridge):
    rules = load_rules()
    grid, _ = fixture()
    correct = execute(bridge, rules.program({"mode": "largest_relay"}), grid)
    wrong = execute(bridge, rules.rival_programs("largest_relay")["smallest_relay"], grid)
    assert correct[3][8] == 4 and wrong[3][8] == 6
    assert correct[4][3] == 7
    assert correct != wrong


def test_all_declared_rivals_execute_and_some_are_refuted_by_hand_fixture(bridge):
    rules = load_rules()
    grid, _ = fixture()
    for mode in ("direct", "largest_relay"):
        correct = execute(bridge, rules.program({"mode": mode}), grid)
        outputs = {name: execute(bridge, source, grid) for name, source in rules.rival_programs(mode).items()}
        assert all(len(out) == 12 and all(len(row) == 12 for row in out) for out in outputs.values())
        assert outputs["eight_contact"] != correct
        assert outputs["eight_components"] != correct
        assert outputs["global_color"] != correct


@pytest.mark.parametrize("seed", [0, 17])
def test_minimum_lesson_refutes_prefer_yellow_else_largest_selector(bridge, seed):
    rules = load_rules()
    spec = importlib.util.spec_from_file_location("a4fb_prefer4_prototype", HOME / "workspace/parametric/prototype.py")
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    correct = rules.program({"mode": "largest_relay"})
    rival = correct.replace(
        "(define relay (pick-max direct obj-size))",
        "(define relay (let ((yellow (filter (lambda (o) (= (obj-color o) 4)) direct))) "
        "(if (null? yellow) (pick-max direct obj-size) (pick-max yellow obj-size))))",
    )
    episode = prototype.episode_inputs(seed, 2, 4)
    assert any(execute(bridge, correct, grid) != execute(bridge, rival, grid) for grid in episode["train"]), \
        "Two-demo lesson leaves the prefer-yellow selector unidentified before the query"
