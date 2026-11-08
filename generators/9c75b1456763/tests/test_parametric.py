"""Focused contract/geometry/privacy checks for the opt-in room-scope family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/9c75b1456763/workspace/parametric"
sys.path.insert(0, str(ROOT / "shared/runtime"))


@pytest.fixture(scope="module")
def p():
    path = HOME / "prototype.py"
    assert path.is_file(), "the native parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("room_scope_test_prototype", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program():
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == "9c75b1456763":
            return row["program_solution"]
    raise AssertionError("canonical rule missing")


def transform(grid, k):
    result = [row[:] for row in grid]
    if k >= 4:
        result = [row[::-1] for row in result]
    for _ in range(k % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def small_scene():
    grid = [[0] * 14 for _ in range(16)]
    for row in (3, 11):
        for col in (3, 9):
            for r in range(row - 2, row + 3):
                for c in range(col - 1, col + 2):
                    grid[r][c] = 1
        for c in range(3, 10):
            grid[row][c] = 1
    grid[3][3] = 2
    grid[11][9] = 4
    return grid


def test_canonical_default_exact(p):
    assert p.program({"fill_scope": "all_interiors"}) == canonical_program()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["default"] == {"fill_scope": "all_interiors"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


def test_remote_rule_excludes_the_marker_room_not_just_the_marker(p):
    grid = small_scene()
    before = copy.deepcopy(grid)
    all_output = p.solve(grid, {"fill_scope": "all_interiors"})
    remote_output = p.solve(grid, {"fill_scope": "unmarked_rooms"})
    expected_all = copy.deepcopy(grid)
    expected_remote = copy.deepcopy(grid)
    for row, color, remote_col in ((3, 2, 9), (11, 4, 3)):
        for r in range(row - 1, row + 2):
            for c in (3, 9):
                expected_all[r][c] = color
            expected_remote[r][remote_col] = color
    assert grid == before
    assert all_output == expected_all
    assert remote_output == expected_remote
    moved = copy.deepcopy(grid)
    moved[3][3], moved[3][9] = 1, 2
    after = p.solve(moved, {"fill_scope": "unmarked_rooms"})
    assert after[2][3] == 2 and after[2][9] == 1


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_counts_determinism_matched_inputs_and_no_duplicates(p, demos, queries):
    episodes = [p.generate(17, s, demos, queries) for s in p.SETTINGS]
    for settings, episode in zip(p.SETTINGS, episodes):
        assert episode == p.generate(17, settings, demos, queries)
        assert len(episode["train"]) == demos and len(episode["test"]) == queries
        assert episode["program_solution"] == p.program(settings)
        pairs = episode["train"] + episode["test"]
        keys = [json.dumps(pair["input"]) for pair in pairs]
        assert len(set(keys)) == len(keys)
        assert all(pair["output"] == p.solve(pair["input"], settings) for pair in pairs)
        assert all(type(v) is int and 0 <= v <= 9 for pair in pairs
                   for field in ("input", "output") for row in pair[field] for v in row)
    assert [x["input"] for x in episodes[0]["train"] + episodes[0]["test"]] == [
        x["input"] for x in episodes[1]["train"] + episodes[1]["test"]]
    assert all(a["output"] != b["output"] for a, b in
               zip(episodes[0]["train"], episodes[1]["train"]))


def test_large_queries_have_substantive_content_and_boundary_contact(p):
    episode = p.generate(0, p.SETTINGS[0], 2, 4)
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert sizes == [(18, 18), (20, 20), (30, 30), (30, 30)]
    for pair in episode["test"][2:]:
        g = pair["input"]
        occupied = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v]
        assert len(occupied) >= 150
        assert max(r for r, c in occupied) - min(r for r, c in occupied) >= 26
        assert max(c for r, c in occupied) - min(c for r, c in occupied) >= 26
    g = episode["test"][3]["input"]
    assert any(g[0]) or any(g[-1]) or any(row[0] or row[-1] for row in g)


@pytest.mark.parametrize("k", range(8))
def test_woven_anchor_defeats_position_only_marker_binding_and_is_equivariant(p, k):
    g = transform(p.sample_scene(0, "demo", 0), k)
    components = [c for c in p.analyze(g) if c["marker"] is not None]
    markers = [c["marker"] for c in components]
    for metric in (lambda r,c,m: abs(r-m[0]), lambda r,c,m: abs(c-m[1]),
                   lambda r,c,m: abs(r-m[0])+abs(c-m[1])):
        assert any(min(markers, key=lambda m: (metric(r,c,m), m))[2] != comp["marker"][2]
                   for comp in components for r,c in comp["interiors"])
    for settings in p.SETTINGS:
        assert p.solve(g, settings) == transform(p.solve(p.sample_scene(0, "demo", 0), settings), k)


def test_public_turn_has_no_future_input_or_private_fields(p):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episode = p.generate(19, p.SETTINGS[1], 3, 4)
    turn = p.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    assert turn["train"] == episode["train"]
    raw = public_challenge_bytes(turn)
    assert hashlib.sha256(raw).hexdigest() == public_challenge_id(turn)
    altered = copy.deepcopy(episode)
    altered.update(seed=999, settings={"hidden": True}, program_solution="private change")
    altered["train"][0]["private_marker_room"] = [[1, 2]]
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [{"input": [[8]], "output": [[7]]}] * 3
    assert p.public_turn(altered, 0) == turn
    single = p.generate(19, p.SETTINGS[1], 3, 1)
    assert p.public_turn(single, 0) == turn
    turn["train"][0]["input"][0][0] = 9
    assert p.public_turn(episode, 0) != turn  # detached public projection


def test_export_payloads_are_visible_byte_identified_and_reject_duplicates(p):
    path = HOME / "export_examples.py"
    assert path.is_file(), "qualified example exporter is missing"
    spec = importlib.util.spec_from_file_location("room_scope_test_exporter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    episode = p.generate(3, p.SETTINGS[1], 2, 4)
    payloads, private = module.build_payloads([episode])
    assert len(payloads) == 4 and len(private) == 1
    assert list(payloads) == sorted(payloads)
    for name, raw in payloads.items():
        assert name == hashlib.sha256(raw).hexdigest() + ".json"
        visible = json.loads(raw)
        assert len(visible["test"]) == 1
        assert set(visible["test"][0]) == {"input"}
        assert set(visible) == {"train", "test"}
    hidden = copy.deepcopy(episode)
    hidden.update(seed=100, settings={"secret": 1}, program_solution="hidden")
    for pair in hidden["test"]:
        pair["output"] = [[9]]
    assert module.build_payloads([hidden])[0] == payloads
    with pytest.raises(ValueError, match="duplicate"):
        module.build_payloads([episode, episode])


@pytest.mark.parametrize("settings", [{}, {"fill_scope": "bad"}, {"fill_scope": True},
                                      {"fill_scope": "all_interiors", "extra": 1}])
def test_rejects_invalid_settings(p, settings):
    with pytest.raises((TypeError, ValueError)):
        p.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True,3,4), (-1,3,4), (0,True,4),
                                                (0,1,4), (0,7,4), (0,3,0), (0,3,5)])
def test_rejects_invalid_requests(p, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        p.generate(seed, p.SETTINGS[0], demos, queries)


def test_strict_grid_validation_and_input_immutability(p):
    for grid in ([[True]], [[1.0]], [[10]], [[1], [1, 2]], []):
        with pytest.raises((TypeError, ValueError)):
            p.solve(grid, p.SETTINGS[0])
    bad = small_scene()
    bad[2][3] = 3
    with pytest.raises(ValueError, match="marker"):
        p.solve(bad, p.SETTINGS[0])


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bridge = RacketBridge()
    assert bridge.runtime_identity["backend"] == "racket"
    assert bridge.runtime_identity["protected"] is True
    def apply(program, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")
    yield apply
    bridge.close()


@pytest.mark.parametrize("k", range(8))
def test_protected_racket_agrees_on_all_orientations(p, racket, k):
    g = transform(p.sample_scene(17, "query", 2), k)
    for settings in p.SETTINGS:
        assert racket(p.program(settings), g) == p.solve(g, settings)
