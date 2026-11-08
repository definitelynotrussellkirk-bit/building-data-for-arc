"""Behavioral tests for the native parametric frame-center family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

_HERE = Path(__file__).resolve()
for _candidate in _HERE.parents:
    _runtime = _candidate / "shared" / "runtime"
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
from reviewer_support import find_root  # noqa: E402

ROOT = find_root(__file__)
HOME = ROOT / "generators" / "9df4a42fced1" / "workspace" / "parametric"
SOURCE = HOME / "native_family.py"


def _load():
    spec = importlib.util.spec_from_file_location("frame_center_native_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def native():
    assert SOURCE.is_file(), "native family has not been implemented"
    return _load()


def _blank(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _frame(grid, box, color, seed_pos, seed_color):
    r1, c1, r2, c2 = box
    for c in range(c1, c2 + 1):
        grid[r1][c] = grid[r2][c] = color
    for r in range(r1, r2 + 1):
        grid[r][c1] = grid[r][c2] = color
    grid[seed_pos[0]][seed_pos[1]] = seed_color


def test_literal_canonical_and_center_chain(native):
    grid = _blank(9, 15)
    _frame(grid, (1, 1, 5, 5), 2, (2, 3), 6)
    _frame(grid, (2, 9, 7, 13), 3, (6, 11), 7)

    canonical = _blank(9, 15)
    canonical[3][3] = 6
    canonical[4][11] = 7
    chained = [row[:] for row in canonical]
    for c in range(4, 12):
        chained[3][c] = 1
    chained[4][11] = 7

    original = [row[:] for row in grid]
    assert native.solve(grid, "canonical") == canonical
    assert native.solve(grid, "center_chain") == chained
    assert grid == original


def test_exact_canonical_default(native):
    canonical = (HOME / "canonical.rkt").read_text()
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "a101da2468b25b26eed0c0f33c20604eee008f362d6583be58346ca76e7b84c4"
    )
    assert native.program({"mode": "canonical"}) == canonical
    assert native.program({"mode": "center_chain"}) != canonical
    assert native.program({"mode": "center_chain"}).startswith("(rule!")


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"mode": "bad"}, {"mode": 1}, {"mode": True}, {"mode": "canonical", "x": 1}],
)
def test_program_rejects_invalid_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"demos": 1}, {"demos": 7}, {"demos": True},
        {"queries": 0}, {"queries": 5}, {"queries": 1.0},
    ],
)
def test_request_rejects_invalid_controls(native, kwargs):
    arguments = {
        "seed": 0,
        "settings": {"mode": "canonical"},
        "demos": 3,
        "queries": 4,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**arguments)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_full_bank_is_setting_independent_distinct_prefix_stable_and_fresh(native, seed):
    canonical = native.generate(seed, {"mode": "canonical"}, 6, 4)
    chained = native.generate(seed, {"mode": "center_chain"}, 6, 4)
    canonical_inputs = [p["input"] for p in canonical["train"] + canonical["test"]]
    chained_inputs = [p["input"] for p in chained["train"] + chained["test"]]
    assert canonical_inputs == chained_inputs
    assert len({tuple(map(tuple, grid)) for grid in canonical_inputs}) == 10
    assert all(
        a["output"] != b["output"]
        for a, b in zip(canonical["train"][:2], chained["train"][:2])
    )
    for pair in canonical["train"] + canonical["test"]:
        assert pair["output"] == native.solve(pair["input"], "canonical")
    for pair in chained["train"] + chained["test"]:
        assert pair["output"] == native.solve(pair["input"], "center_chain")
    short = native.generate(seed, {"mode": "canonical"}, 2, 1)
    assert short["train"] == canonical["train"][:2]
    assert short["test"] == canonical["test"][:1]
    canonical["train"][0]["input"][0][0] = 9
    assert native.generate(seed, {"mode": "canonical"}, 2, 1) == short


def test_default_contract_uses_three_demos():
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["qualification_demos"] == 3
    assert contract["default"] == {"mode": "canonical"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_large_profiles_are_substantive_and_cover_canvas(native):
    episode = native.generate(0, {"mode": "center_chain"}, 6, 4)
    pairs = episode["train"] + episode["test"]
    large = [pair for pair in pairs if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 2
    for pair in large:
        grid = pair["input"]
        assert sum(value != 0 for row in grid for value in row) >= 100
        for r0, c0 in ((0, 0), (0, 15), (15, 0), (15, 15)):
            assert sum(
                grid[r][c] != 0
                for r in range(r0, r0 + 15)
                for c in range(c0, c0 + 15)
            ) >= 10
        assert sum(
            value == 1 for row in pair["output"] for value in row
        ) >= 12


def test_derived_center_geometry_varies_across_seeds(native):
    point_sets = set()
    for seed in range(8):
        pair = native.generate(seed, {"mode": "canonical"}, 2, 1)["train"][0]
        point_sets.add(
            tuple(
                (r, c)
                for r, row in enumerate(pair["output"])
                for c, value in enumerate(row)
                if value
            )
        )
    assert len(point_sets) >= 3, "fixed-location painting should not solve the first lesson profile"
