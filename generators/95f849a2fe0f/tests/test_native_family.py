"""Focused contracts for the expanded independently aligned shape family."""
import importlib.util
import json
from pathlib import Path
import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/native_family.py"


def test_native_exists():
    assert SOURCE.is_file(), "native shape-combination family is not implemented"


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("xor_native_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_default_and_count(native):
    assert native.program({"combine": "xor"}) == (SOURCE.parent / "canonical.rkt").read_text()
    assert native.program({"combine": "difference"}) != native.program({"combine": "xor"})
    assert json.loads((SOURCE.parent / "promotion.json").read_text())["qualification_demos"] == 3


def test_literal_origin_and_trailing_cancellation(native):
    f = {(r, c) for r in range(4) for c in range(4) if r in (0, 3) or c in (0, 3)}
    a, b = f | {(1, 1), (1, 2), (1, 4)}, f | {(2, 1)}
    grid = [[0] * 14 for _ in range(8)]
    for r, c in a:
        grid[r + 1][c + 1] = 2
    for r, c in b:
        grid[r + 3][c + 9] = 7
    assert native.solve(grid, "xor") == [[0] * 5, [0, 8, 8, 0, 8], [0, 8, 0, 0, 0]]
    assert native.solve(grid, "difference") == [[0] * 5, [0, 8, 8, 0, 8]]


def test_identical_subset_and_touching_components(native):
    assert native.solve([[2, 3]], "xor") == [[0]]
    assert native.solve([[2, 3]], "difference") == [[0]]
    assert native.solve([[2, 0, 3, 3]], "xor") == [[0, 8]]
    assert native.solve([[2, 0, 3, 3]], "difference") == [[0]]
    assert native.solve([[3, 3, 2]], "difference") == [[0]]
    assert native.solve([[3], [3], [2]], "xor") == [[0], [8]]


@pytest.mark.parametrize("grid", [[], [[]], [[0], [2, 3]], [[True, 3]], [[2.0, 3]], [[2, 10]], [[0]], [[2]], [[2, 3, 4]], [[2, 0, 2, 3]], [[2, 3] + [0] * 29], [[2, 3]] + [[0, 0]] * 30])
def test_bad_grid_rejected(native, grid):
    with pytest.raises(ValueError):
        native.solve(grid)


@pytest.mark.parametrize("settings", [None, {}, {"combine": "union"}, {"combine": 1}, {"combine": True}, {"combine": "xor", "extra": 0}])
def test_bad_settings_rejected(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0}, {"demos": 1}, {"demos": 7}, {"demos": True}, {"queries": 0}, {"queries": 5}, {"queries": 1.0}])
def test_strict_controls(native, kwargs):
    arguments = {"seed": 0, "settings": {"combine": "xor"}, "demos": 3, "queries": 4}
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**arguments)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_fresh_matched_distinct_prefix_banks(native, seed):
    x = native.generate(seed, {"combine": "xor"}, 6, 4)
    d = native.generate(seed, {"combine": "difference"}, 6, 4)
    assert [p["input"] for p in x["train"] + x["test"]] == [p["input"] for p in d["train"] + d["test"]]
    assert len({tuple(map(tuple, p["input"])) for p in x["train"] + x["test"]}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(x["train"][:2], d["train"][:2]))
    short = native.generate(seed, {"combine": "xor"}, 2, 1)
    assert short["train"] == x["train"][:2] and short["test"] == x["test"][:1]
    x["train"][0]["input"][0][0] = 9
    assert native.generate(seed, {"combine": "xor"}, 2, 1) == short


def test_cores_reverse_position_and_size_roles(native):
    demos, _ = native.input_bank(0)
    a0, b0 = native.analyze(demos[0])
    a1, b1 = native.analyze(demos[1])
    assert len(a0) > len(b0) and len(a1) < len(b1)
    assert min(a0) < min(b0) and min(a1) > min(b1)
    assert min(c for r, c in a0) < min(c for r, c in b0)
    assert min(c for r, c in a1) > min(c for r, c in b1)


def test_large_scenes_have_substantive_content(native):
    e = native.generate(0, {"combine": "xor"}, 6, 4)
    large = [p["input"] for p in e["train"] + e["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert [sum(bool(v) for row in grid for v in row) for grid in large] == [360, 346]
    for grid in large:
        for r in (0, 15):
            for c in (0, 15):
                assert sum(bool(grid[y][x]) for y in range(r, r + 15) for x in range(c, c + 15)) >= 40
