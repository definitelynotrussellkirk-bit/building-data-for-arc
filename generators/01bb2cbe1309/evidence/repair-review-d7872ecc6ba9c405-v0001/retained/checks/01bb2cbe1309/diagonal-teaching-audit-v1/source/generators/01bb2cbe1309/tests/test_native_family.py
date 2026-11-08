"""Native-only request and snapshot semantics; production is unchanged."""
import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/native_family.py"


def test_native_module_exists():
    assert SOURCE.is_file(), "native diagonal-pass family has not been implemented"


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("diagonal_native_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_snapshot_cascade_exact_two_passes(native):
    grid = [[2, 0, 2, 0], [0, 0, 0, 2], [0, 2, 0, 0]]
    assert native.solve(grid, 1) == [[2, 0, 2, 2], [0, 0, 2, 2], [0, 2, 0, 0]]
    assert native.solve(grid, 2) == [[2, 0, 2, 2], [0, 2, 2, 2], [0, 2, 2, 0]]
    assert grid == [[2, 0, 2, 0], [0, 0, 0, 2], [0, 2, 0, 0]]


def test_row_major_conflict_uses_original_reads_and_last_write(native):
    grid = [[0, 2, 0], [2, 0, 3], [0, 3, 0]]
    assert native.solve(grid, 1) == [[2, 2, 0], [2, 3, 3], [0, 3, 3]]


@pytest.mark.parametrize("grid,expected", [
    ([[4, 0], [0, 4]], [[4, 4], [4, 4]]),
    ([[0, 5], [5, 0]], [[5, 5], [5, 5]]),
    ([[4, 7], [0, 4]], [[4, 7], [0, 4]]),
    ([[4, 0], [0, 7]], [[4, 0], [0, 7]]),
    ([[4, 4], [0, 0]], [[4, 4], [0, 0]]),
    ([[4]], [[4]]),
    ([[0, 2, 0, 2]], [[0, 2, 0, 2]]),
    ([[0], [2], [0]], [[0], [2], [0]]),
])
def test_literal_rule_boundaries(native, grid, expected):
    assert native.solve(grid, 1) == expected
    assert native.solve(grid, 2) == expected


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 1]], [[True]], [[1.0]], [[-1]], [[10]], [["2"]], (0,), [[0] * 31], [[0]] * 31])
def test_strict_grid_rejection(native, grid):
    with pytest.raises(ValueError):
        native.solve(grid, 1)


@pytest.mark.parametrize("settings", [{}, {"passes": True}, {"passes": 1.0}, {"passes": "1"}, {"passes": 0}, {"passes": 3}, {"passes": 1, "x": 2}, None])
def test_program_rejects_invalid_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0}, {"demos": 1}, {"demos": 7}, {"demos": True}, {"queries": 0}, {"queries": 5}, {"queries": 1.0}])
def test_request_rejects_invalid_controls(native, kwargs):
    arguments = {"seed": 0, "settings": {"passes": 1}, "demos": 3, "queries": 4}
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**arguments)


def test_exact_canonical_default(native):
    assert native.program({"passes": 1}) == (SOURCE.parent / "canonical.rkt").read_text()
    assert native.program({"passes": 2}).startswith("(rule!")
    assert native.program({"passes": 1}) != native.program({"passes": 2})


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_full_bank_matched_settings_count_prefix_and_freshness(native, seed):
    first = native.generate(seed, {"passes": 1}, 6, 4)
    second = native.generate(seed, {"passes": 2}, 6, 4)
    assert [p["input"] for p in first["train"] + first["test"]] == [p["input"] for p in second["train"] + second["test"]]
    assert any(a["output"] != b["output"] for a, b in zip(first["train"][:2], second["train"][:2]))
    keys = {tuple(map(tuple, pair["input"])) for pair in first["train"] + first["test"]}
    assert len(keys) == 10
    short = native.generate(seed, {"passes": 1}, 2, 1)
    assert short["train"] == first["train"][:2]
    assert short["test"] == first["test"][:1]
    for pair in first["train"] + first["test"]:
        assert pair["output"] == native.solve(pair["input"], 1)
    first["train"][0]["input"][0][0] = 99
    assert native.generate(seed, {"passes": 1}, 2, 1) == short


def test_large_profiles_have_content_and_different_geometry(native):
    episode = native.generate(0, {"passes": 2}, 6, 4)
    large = [p for p in episode["train"] + episode["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert len(large) == 2
    for pair in large:
        grid = pair["input"]
        assert sum(v != 0 for row in grid for v in row) >= 180
        for r in (0, 15):
            for c in (0, 15):
                assert sum(grid[y][x] != 0 for y in range(r, r + 15) for x in range(c, c + 15)) >= 20
        assert sum(a != b for row_a, row_b in zip(grid, pair["output"]) for a, b in zip(row_a, row_b)) >= 60
