"""Literal tile transformations and native sampler boundary contracts."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/native_family.py"


def family():
    assert SOURCE.is_file(), "Native tile rotation/settling is not implemented"
    spec = importlib.util.spec_from_file_location("tiles_native_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_canonical_default_and_four_distinct_programs():
    mod = family()
    assert hashlib.sha256(mod.program().encode()).hexdigest() == "a23915e769b96d7ca844d36d4b8408b311d672bca58166fad83378fa83cf8660"
    assert mod.program() == mod.program(mod.DEFAULT)
    assert len({mod.program(setting) for setting in mod.SETTINGS}) == 4


@pytest.mark.parametrize("turn,post,want", [
    ("cw", "none", [[0, 8, 8], [0, 8, 0], [0, 0, 0]]),
    ("cw", "settle_down", [[0, 0, 0], [0, 8, 8], [0, 8, 0]]),
    ("ccw", "none", [[0, 0, 0], [0, 8, 0], [8, 8, 0]]),
    ("ccw", "settle_down", [[0, 0, 0], [0, 8, 0], [8, 8, 0]]),
])
def test_literal_marked_tile_rotation_then_settle(turn, post, want):
    source = [[2, 0, 3], [2, 2, 0], [0, 0, 0]]
    original = deepcopy(source)
    assert family().transform(source, {"turn": turn, "post": post}) == want
    assert source == original


@pytest.mark.parametrize("turn", ["cw", "ccw"])
def test_unmarked_tile_does_not_turn_but_still_settles(turn):
    mod = family()
    source = [[2, 0, 0], [2, 2, 0], [0, 0, 0]]
    assert mod.transform(source, {"turn": turn, "post": "none"}) == [[8, 0, 0], [8, 8, 0], [0, 0, 0]]
    assert mod.transform(source, {"turn": turn, "post": "settle_down"}) == [[0, 0, 0], [8, 0, 0], [8, 8, 0]]


def test_whole_disconnected_motif_keeps_relative_vertical_offsets():
    source = [[2, 0, 0], [0, 0, 2], [0, 0, 0]]
    assert family().transform(source, {"turn": "cw", "post": "settle_down"}) == [
        [0, 0, 0], [8, 0, 0], [0, 0, 8]]


def test_lattice_is_preserved_and_tiles_are_independent():
    source = [[2, 0, 3, 9, 0, 0, 2], [2, 2, 0, 9, 0, 2, 0], [0, 0, 0, 9, 0, 0, 0]]
    want = [[0, 0, 0, 9, 0, 0, 0], [0, 8, 8, 9, 0, 0, 8], [0, 8, 0, 9, 0, 8, 0]]
    assert family().transform(source, {"turn": "cw", "post": "settle_down"}) == want


def test_empty_motif_and_multiple_markers_are_total():
    mod = family()
    for setting in mod.SETTINGS:
        assert mod.transform([[0] * 3 for _ in range(3)], setting) == [[0] * 3 for _ in range(3)]
        assert mod.transform([[3] * 3 for _ in range(3)], setting) == [[0] * 3 for _ in range(3)]
    once = [[2, 0, 3], [2, 2, 0], [0, 0, 0]]
    thrice = [[2, 3, 3], [2, 2, 0], [3, 0, 0]]
    for setting in mod.SETTINGS:
        assert mod.transform(once, setting) == mod.transform(thrice, setting)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_count_prefixes_matched_inputs_and_two_demo_setting_distinction(seed):
    mod = family()
    shared_inputs = None
    fingerprints = []
    for setting in mod.SETTINGS:
        full = mod.generate(seed, setting, 6, 4)
        small = mod.generate(seed, setting, 2, 1)
        normal = mod.generate(seed, setting)
        assert len(full["train"]) == 6 and len(full["test"]) == 4
        assert len(normal["train"]) == 3 and len(normal["test"]) == 4
        assert small["train"] == full["train"][:2]
        assert small["test"] == full["test"][:1]
        assert normal["train"] == full["train"][:3] and normal["test"] == full["test"]
        assert full == mod.generate(seed, setting, 6, 4)
        assert full["program_solution"] == mod.program(setting)
        current = [pair["input"] for split in ("train", "test") for pair in full[split]]
        assert len({json.dumps(value) for value in current}) == 10
        if shared_inputs is None:
            shared_inputs = deepcopy(current)
        assert shared_inputs == current
        fingerprints.append(json.dumps([pair["output"] for pair in small["train"]]))
        full["train"][0]["input"][0][0] = 9
        assert mod.generate(seed, setting, 2, 1) == small
    assert len(set(fingerprints)) == 4


def test_real_minimum_and_large_lattice_and_single_tile_stress():
    mod = family()
    episode = mod.generate(0, {"turn": "cw", "post": "settle_down"}, 6, 4)
    pairs = episode["train"] + episode["test"]
    assert any(len(pair["input"]) == len(pair["input"][0]) == 3 for pair in pairs)
    multi = [pair for pair in pairs if len(pair["input"]) == len(pair["input"][0]) == 29]
    assert len(multi) == 1
    assert sum(value == 2 for row in multi[0]["input"] for value in row) >= 250
    assert any(9 in row for row in multi[0]["input"])
    large = [pair for pair in pairs if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 2
    assert {sum(value == 3 for row in pair["input"] for value in row) for pair in large} == {2, 3}
    for pair in large:
        source = pair["input"]
        assert not any(9 in row for row in source)
        assert sum(value == 2 for row in source for value in row) >= 300
        assert all(any(source[r][c] == 2 for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
                   for r0 in (0, 15) for c0 in (0, 15))
        assert all((any(source[0]), any(source[-1]), any(row[0] for row in source), any(row[-1] for row in source)))
        for turn in ("cw", "ccw"):
            assert mod.transform(source, {"turn": turn, "post": "none"}) != mod.transform(source, {"turn": turn, "post": "settle_down"})


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": "17"},
    {"demos": 1}, {"demos": 7}, {"demos": False}, {"demos": 3.0},
    {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": "4"},
    {"settings": {}}, {"settings": {"turn": "cw"}},
    {"settings": {"turn": "cw", "post": "down"}},
    {"settings": {"turn": "cw", "post": "none", "x": 1}},
    {"settings": {"turn": True, "post": "none"}}, {"settings": "cw"},
])
def test_invalid_native_requests_fail_explicitly(kwargs):
    args = {"seed": 0, "settings": {"turn": "cw", "post": "none"}, "demos": 3, "queries": 4}
    args.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        family().generate(**args)


@pytest.mark.parametrize("source", [
    [], [[]], [[0] * 3] * 2, [[0] * 31] * 3, [[0] * 4] * 3,
    [[9, 0, 0, 0]] * 3, [[0, 0, 0], [0, 9, 0], [0, 0, 0]],
    [[0, 0, 0, 9, 0, 0, 0, 0]] * 3,
    [[0, 0, 0, 9, 9, 0, 0, 0]] * 3,
    [[6] * 3] * 3, [[False] * 3] * 3, [[0.0] * 3] * 3,
    [[0] * 3, [0] * 2, [0] * 3], [[9] * 3] * 3,
])
def test_native_lattice_validation_rejects_malformed_geometry(source):
    with pytest.raises((TypeError, ValueError)):
        family().transform(source, {"turn": "cw", "post": "none"})
