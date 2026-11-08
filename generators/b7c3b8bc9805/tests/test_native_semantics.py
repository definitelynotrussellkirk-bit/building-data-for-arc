"""Behavioral regressions for the composed rule and public query projection."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


ROOT = find_root(__file__)
HOME = ROOT / "generators/b7c3b8bc9805/workspace/parametric"


def load(name):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"native {name} implementation is missing"
    spec = importlib.util.spec_from_file_location(f"test_native_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame(markers):
    grid = [[0] * 12 for _ in range(10)]
    for r in range(2, 8):
        for c in range(3, 9):
            if r in (2, 7) or c in (3, 8):
                grid[r][c] = 5
    for r, c, color in markers:
        grid[r][c] = color
    return grid


def execute(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


@pytest.mark.parametrize("markers,destination,upper_left,upper_right", [
    ([(0, 0, 8), (1, 2, 1)], (8, 9), 1, 8),
    ([(8, 0, 1), (9, 1, 8)], (0, 9), 8, 1),
    ([(0, 0, 8), (8, 9, 1)], (8, 10), 1, 8),
])
def test_move_then_fill_uses_recomputed_marker_order(markers, destination, upper_left, upper_right):
    family = load("family")
    grid = frame(markers)
    before = copy.deepcopy(grid)
    with RacketBridge() as bridge:
        actual = execute(bridge, family.program({"phase_relation": "move_then_fill"}), grid)
    assert grid == before
    assert actual[markers[0][0]][markers[0][1]] == 0
    assert actual[destination[0]][destination[1]] == markers[0][2]
    assert actual[3][4] == upper_left
    assert actual[3][7] == upper_right
    assert actual == family.mirror(grid, "move_then_fill")


def test_stale_order_ablation_changes_only_the_fill_on_a_real_witness():
    family = load("family")
    grid = frame([(0, 0, 8), (1, 2, 1)])
    with RacketBridge() as bridge:
        actual = execute(bridge, family.program({"phase_relation": "move_then_fill"}), grid)
        stale = execute(bridge, family.stale_order_program(), grid)
    differing = {(r, c) for r in range(10) for c in range(12) if actual[r][c] != stale[r][c]}
    assert differing == {(r, c) for r in range(3, 7) for c in range(4, 8)}


@pytest.mark.parametrize("mode", ["same", "opposite", "move_then_fill"])
def test_three_demos_refute_phase_from_second_cue(mode):
    family = load("family")
    base = family.program({"phase_relation": "opposite" if mode == "opposite" else "same"})
    rival = base.replace("(m1qr (if (< (first m1) cr) 0 1))", "(m1qr (if (< (first m2) cr) 0 1))", 1).replace(
        "(m1qc (if (< (second m1) cc) 0 1))", "(m1qc (if (< (second m2) cc) 0 1))", 1)
    if mode == "move_then_fill":
        rival = family.compose_move(rival)
    episode = family.generate(17, {"phase_relation": mode}, 3, 4)
    with RacketBridge() as bridge:
        assert any(execute(bridge, rival, pair["input"]) != pair["output"] for pair in episode["train"]), \
            "the second-cue phase shortcut survives every demonstration"


@pytest.mark.parametrize("mode", ["same", "opposite", "move_then_fill"])
def test_three_demos_refute_grid_aspect_phase(mode):
    family = load("family")
    base = family.program({"phase_relation": "opposite" if mode == "opposite" else "same"})
    rival = base.replace("(m1p (remainder (+ m1qr m1qc) 2))", "(m1p (if (> h w) 1 0))", 1)
    if mode == "move_then_fill":
        rival = family.compose_move(rival)
    episode = family.generate(17, {"phase_relation": mode}, 3, 4)
    with RacketBridge() as bridge:
        assert any(execute(bridge, rival, pair["input"]) != pair["output"] for pair in episode["train"]), \
            "canvas aspect ratio substitutes for reading the controlling marker"


def test_one_query_projection_hides_future_queries_and_private_identity():
    family = load("family")
    episode = family.generate(17, {"phase_relation": "same"}, 3, 4)
    one = family.generate(17, {"phase_relation": "same"}, 3, 1)
    first = family.public_query(episode, 0)
    assert first == family.public_query(one, 0)
    assert len(first["test"]) == 1
    assert set(first) == {"train", "test"}
    assert set(first["test"][0]) == {"input"}
    changed = copy.deepcopy(episode)
    changed.update(seed=999, parameters={"phase_relation": "secret"}, program_solution="secret")
    for pair in changed["test"]:
        pair["output"][0][0] = (pair["output"][0][0] + 1) % 10
    changed["test"][3]["input"][0][0] = 9
    assert public_challenge_bytes(family.public_query(changed, 0)) == public_challenge_bytes(first)
    first["train"][0]["input"][0][0] = 9
    assert episode == family.generate(17, {"phase_relation": "same"}, 3, 4)
    for invalid in (True, -1, 4, 1.0):
        with pytest.raises((ValueError, TypeError)):
            family.public_query(episode, invalid)


def test_legacy_writer_names_public_files_from_exact_visible_bytes(tmp_path):
    prototype = load("prototype")
    report = prototype.write_evidence((0, 1), out=tmp_path / "legacy", root=ROOT)
    ids = []
    for row in report["episodes"]:
        path = tmp_path / "legacy" / row["public_path"]
        public = json.loads(path.read_bytes())
        assert path.stem == public_challenge_id(public)
        assert path.read_bytes() == public_challenge_bytes(public)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["public_sha256"]
        ids.append(path.stem)
    assert ids == sorted(ids)

