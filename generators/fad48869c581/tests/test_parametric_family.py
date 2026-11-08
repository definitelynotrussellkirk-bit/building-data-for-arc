"""Behavioral tests for the native L-completion parametric family."""
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
HOME = ROOT / "generators" / "fad48869c581" / "workspace" / "parametric"
SOURCE = HOME / "native_family.py"


def _load():
    spec = importlib.util.spec_from_file_location("l_completion_native_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def native():
    assert SOURCE.is_file(), "native family has not been implemented"
    return _load()


def _blank(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _l(grid, top: int, left: int, color: int, missing: int) -> None:
    cells = [(top, left), (top, left + 1), (top + 1, left), (top + 1, left + 1)]
    for index, (r, c) in enumerate(cells):
        if index != missing:
            grid[r][c] = color


def test_literal_canonical_and_square_halo(native):
    grid = _blank(7, 11)
    _l(grid, 1, 1, 2, 3)
    _l(grid, 3, 7, 7, 0)

    canonical = [row[:] for row in grid]
    canonical[2][2] = 2
    canonical[3][7] = 7
    halo = _blank(7, 11)
    for r in range(0, 4):
        for c in range(0, 4):
            halo[r][c] = 2
    for r in range(2, 6):
        for c in range(6, 10):
            halo[r][c] = 7

    original = [row[:] for row in grid]
    assert native.solve(grid, "canonical") == canonical
    assert native.solve(grid, "square_halo") == halo
    assert grid == original


def test_exact_canonical_default(native):
    canonical = (HOME / "canonical.rkt").read_text()
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "65f702bea3179cdb91f0099a20d278ec01eaf15c3266d003d132934453d8bfce"
    )
    assert native.program({"mode": "canonical"}) == canonical
    assert native.program({"mode": "square_halo"}) != canonical
    assert native.program({"mode": "square_halo"}).startswith("(rule!")


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
    halo = native.generate(seed, {"mode": "square_halo"}, 6, 4)
    canonical_inputs = [p["input"] for p in canonical["train"] + canonical["test"]]
    halo_inputs = [p["input"] for p in halo["train"] + halo["test"]]
    assert canonical_inputs == halo_inputs
    assert len({tuple(map(tuple, grid)) for grid in canonical_inputs}) == 10
    assert all(
        a["output"] != b["output"]
        for a, b in zip(canonical["train"][:2], halo["train"][:2])
    )
    for pair in canonical["train"] + canonical["test"]:
        assert pair["output"] == native.solve(pair["input"], "canonical")
    for pair in halo["train"] + halo["test"]:
        assert pair["output"] == native.solve(pair["input"], "square_halo")
    short = native.generate(seed, {"mode": "canonical"}, 2, 1)
    assert short["train"] == canonical["train"][:2]
    assert short["test"] == canonical["test"][:1]
    canonical["train"][0]["input"][0][0] = 8
    assert native.generate(seed, {"mode": "canonical"}, 2, 1) == short


def test_default_contract_uses_three_demos():
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["qualification_demos"] == 3
    assert contract["default"] == {"mode": "canonical"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_square_halo_is_a_real_stage_a_dependency(native):
    episode = native.generate(11, {"mode": "square_halo"}, 2, 1)
    for pair in episode["train"] + episode["test"]:
        intermediate = native.solve(pair["input"], "canonical")
        assert native._solid_squares(pair["input"]) == []
        assert native._solid_squares(intermediate)
        assert native._halo_squares(intermediate) == pair["output"]
        assert native._halo_squares(pair["input"]) != pair["output"]


def test_large_profiles_are_substantive_spread_and_keep_distractors(native):
    episode = native.generate(0, {"mode": "square_halo"}, 6, 4)
    pairs = episode["train"] + episode["test"]
    large = [pair for pair in pairs if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 2
    for pair in large:
        grid = pair["input"]
        output = pair["output"]
        assert sum(value != 0 for row in grid for value in row) >= 40
        assert sum(a != b for row_a, row_b in zip(grid, output) for a, b in zip(row_a, row_b)) >= 120
        for r0, c0 in ((0, 0), (0, 15), (15, 0), (15, 15)):
            assert sum(
                grid[r][c] != 0
                for r in range(r0, r0 + 15)
                for c in range(c0, c0 + 15)
            ) >= 6
        distractors = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 9
        ]
        assert len(distractors) >= 4
        assert all(output[r][c] == 9 for r, c in distractors)
    assert any(
        any(value != 0 for value in pair["input"][0] + pair["input"][-1])
        or any(row[0] != 0 or row[-1] != 0 for row in pair["input"])
        for pair in pairs
    ), "the bank should include a lawful boundary-contact scene"


def test_missing_corner_geometry_varies_across_seeds(native):
    fire_sets = set()
    for seed in range(12):
        pair = native.generate(seed, {"mode": "canonical"}, 2, 1)["train"][0]
        fire_sets.add(
            tuple(
                (r, c)
                for r, (before, after) in enumerate(zip(pair["input"], pair["output"]))
                for c, (a, b) in enumerate(zip(before, after))
                if a != b
            )
        )
    assert len(fire_sets) >= 5, "fixed-location corner filling should not solve the first profile"
