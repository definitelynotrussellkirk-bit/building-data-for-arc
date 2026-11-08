"""Behavioral tests for the separate native cap/bridge family."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/native_family.py"


def family():
    assert SOURCE.is_file(), "The native cap/bridge family has not been implemented"
    spec = importlib.util.spec_from_file_location("caps_native_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid(h=7, w=11):
    return [[0] * w for _ in range(h)]


def test_default_is_exact_selected_canonical():
    mod = family()
    assert hashlib.sha256(mod.program({"cap_mode": "caps"}).encode()).hexdigest() == "15debbc2b09d7b591e587879a201e865beeaa5153cac1d262ca493c6da156cfd"
    assert mod.program() == mod.program(mod.DEFAULT)
    assert mod.program({"cap_mode": "bridge_caps"}) != mod.program(mod.DEFAULT)


def test_caps_use_two_horizontal_neighbors_and_keep_occupied_cells():
    mod = family()
    source = grid(7, 12)
    source[0] = [6, 6, 0, 0, 6, 6, 6, 6, 0, 0, 6, 0]
    source[2] = [0, 6, 6, 0, 6, 6, 0, 0, 0, 0, 0, 0]
    source[3][10] = source[4][10] = 6
    source[6] = [0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 6, 6]
    want = deepcopy(source)
    for r, c in ((0, 2), (0, 3), (0, 8), (2, 0), (2, 3), (2, 6)):
        want[r][c] = 8
    before = deepcopy(source)
    assert mod.transform(source, {"cap_mode": "caps"}) == want
    assert source == before


@pytest.mark.parametrize("blocker", [2, 6, 8])
def test_bridge_requires_clear_whole_gap_and_uses_only_new_caps(blocker):
    mod = family()
    source = grid()
    for r in (0, 3, 6):
        source[r][2:5] = [6, 6, 6]
    source[1][1] = blocker
    source[0][9] = source[6][9] = 8
    want = deepcopy(source)
    for r in (0, 3, 6):
        want[r][1] = want[r][5] = 8
    for r in (1, 2, 4, 5):
        want[r][5] = 8
    for r in (4, 5):
        want[r][1] = 8
    assert mod.transform(source, {"cap_mode": "bridge_caps"}) == want


def test_no_new_caps_does_not_join_original_cyan_or_recolor_singletons():
    mod = family()
    source = grid()
    source[0][2] = source[6][2] = 8
    source[2][7] = source[3][7] = 6
    for setting in mod.SETTINGS:
        assert mod.transform(source, setting) == source
        assert mod.transform(grid(), setting) == grid()


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_inputs_labels_and_prefixes_are_independent(seed):
    mod = family()
    inputs = None
    for setting in mod.SETTINGS:
        full = mod.generate(seed, setting, 6, 4)
        small = mod.generate(seed, setting, 2, 1)
        ordinary = mod.generate(seed, setting)
        assert len(full["train"]) == 6 and len(full["test"]) == 4
        assert len(ordinary["train"]) == 3 and len(ordinary["test"]) == 4
        assert small["train"] == full["train"][:2]
        assert small["test"] == full["test"][:1]
        assert ordinary["train"] == full["train"][:3]
        assert ordinary["test"] == full["test"]
        assert full == mod.generate(seed, setting, 6, 4)
        assert full["program_solution"] == mod.program(setting)
        current = [pair["input"] for split in ("train", "test") for pair in full[split]]
        assert len({json.dumps(x) for x in current}) == 10
        if inputs is None:
            inputs = deepcopy(current)
        assert inputs == current
        full["train"][0]["input"][0][0] = 9
        assert mod.generate(seed, setting, 2, 1) == small


def test_full_bank_hits_minimum_and_real_maximum_content():
    mod = family()
    episode = mod.generate(0, {"cap_mode": "bridge_caps"}, 6, 4)
    all_pairs = episode["train"] + episode["test"]
    assert any(len(pair["input"]) == len(pair["input"][0]) == 7 for pair in all_pairs)
    large = [pair for pair in all_pairs if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 2
    for pair in large:
        source, output = pair["input"], pair["output"]
        assert sum(bool(cell) for row in source for cell in row) >= 200
        assert sum(a != b for ar, br in zip(source, output) for a, b in zip(ar, br)) >= 80
        assert all(any(source[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
                   for r0 in (0, 15) for c0 in (0, 15))
        assert all((any(source[0]), any(source[-1]), any(row[0] for row in source), any(row[-1] for row in source)))


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.5},
    {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
    {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": "4"},
    {"settings": {}}, {"settings": {"cap_mode": "unknown"}},
    {"settings": {"cap_mode": "caps", "extra": 2}}, {"settings": "caps"},
])
def test_bad_requests_are_rejected(kwargs):
    mod = family()
    args = {"seed": 0, "settings": {"cap_mode": "caps"}, "demos": 3, "queries": 4}
    args.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        mod.generate(**args)


@pytest.mark.parametrize("source", [[], [[]], [[0] * 7] * 6, [[0] * 31] * 7,
    [[0] * 7] * 6 + [[0] * 6], [[False] * 7] * 7, [[10] * 7] * 7, [[0.0] * 7] * 7])
def test_malformed_or_outside_native_grid_rejected(source):
    with pytest.raises((TypeError, ValueError)):
        family().transform(source, {"cap_mode": "caps"})
