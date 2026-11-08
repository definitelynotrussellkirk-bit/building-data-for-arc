"""Focused grammar, literal semantics and sampling contracts for D4 transfer."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/native_family.py"
X = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1))
Y = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0))
XR90 = ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2))


def scene(shapes=(X, Y, XR90), colors=(2, 5, 9), tail=0):
    grid = [[0] * (17 + tail) for _ in range(6)]
    for row in grid:
        row[5] = row[11] = 8
    for index, (cells, color) in enumerate(zip(shapes, colors)):
        for r, c in cells:
            grid[r + 1][index * 6 + c] = color
    return grid


def test_native_exists():
    assert SOURCE.is_file(), "native prototype/transform-transfer family is not implemented"


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("transfer_native_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_default_and_count(native):
    canonical = native.program({"mode": "prototype"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == "d76e03446f2a9f862524d84ccaa866f67dbe9ef2ad22c45cd755fb67c57211a7"
    assert canonical == (SOURCE.parent / "canonical.rkt").read_text()
    assert native.program({"mode": "transfer"}) != canonical
    assert len(native.generate(0, {"mode": "prototype"})["train"]) == 4
    assert json.loads((SOURCE.parent / "promotion.json").read_text())["qualification_demos"] == 4


def test_literal_match_and_transfer(native):
    grid = scene()
    result = native.analyze(grid)
    assert (result["match_index"], result["transform"], result["panel_w"]) == (0, "rot90", 5)
    assert native.solve(grid) == [[9, 9, 9], [9, 9, 0], [0, 9, 0]]
    assert native.solve(grid, "transfer") == [[9, 9, 9], [0, 0, 9], [0, 9, 9]]


@pytest.mark.parametrize("tail", [0, 1, 2])
@pytest.mark.parametrize("colors", [(8, 3, 6), (4, 8, 7), (2, 5, 8)])
def test_geometry_accepts_color8_in_all_roles_and_zero_tail(native, tail, colors):
    g = scene(colors=colors, tail=tail)
    assert native.analyze(g)["match_index"] == 0
    assert set(v for row in native.solve(g, "transfer") for v in row) == {0, colors[2]}


def test_arbitrary_connected_shape_with_hole_is_admitted(native):
    hole = {(r, c) for r in range(4) for c in range(4) if r in (0, 3) or c in (0, 3)} | {(1, 4)}
    g = scene(shapes=(X, hole, XR90))
    assert len(native.orbit(hole)) == 8
    assert native.analyze(g)["panels"][1]["cells"] == native.normalize(hole)
    assert len(native.solve(g, "transfer")) == 5


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 0]], [[True]], [[2.0]], [[10]], [[0]], [[0] * 31], [[0]] * 31, ((0,),)])
def test_bad_grid_types_and_bounds(native, grid):
    with pytest.raises(ValueError):
        native.solve(grid)


@pytest.mark.parametrize("kind", ["separator", "tail", "multicolor", "samecolors", "disconnected", "empty", "symmetric", "equivalent", "no_match"])
def test_bad_structural_grammar(native, kind):
    g = scene(tail=1)
    if kind == "separator":
        g[0][5] = 0
    elif kind == "tail":
        g[0][-1] = 2
    elif kind == "multicolor":
        g[1][0] = 7
    elif kind == "samecolors":
        g = [[2 if v == 5 else v for v in row] for row in g]
    elif kind == "disconnected":
        g[5][4] = 2
    elif kind == "empty":
        g = scene(shapes=(X, (), XR90))
    elif kind == "symmetric":
        g = scene(shapes=(X, ((0, 0),), XR90))
    elif kind == "equivalent":
        g = scene(shapes=(X, XR90, XR90))
    elif kind == "no_match":
        g = scene(shapes=(X, Y, ((0, 0),)))
    with pytest.raises(ValueError):
        native.solve(g)


@pytest.mark.parametrize("settings", [None, {}, {"mode": "rotate"}, {"mode": 1}, {"mode": True}, {"mode": "transfer", "extra": 0}])
def test_bad_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0}, {"demos": 3}, {"demos": 7}, {"demos": True}, {"queries": 0}, {"queries": 5}, {"queries": 1.0}])
def test_strict_controls(native, kwargs):
    arguments = {"seed": 0, "settings": {"mode": "prototype"}, "demos": 4, "queries": 4}
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**arguments)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_fresh_matched_distinct_prefix_banks(native, seed):
    a = native.generate(seed, {"mode": "prototype"}, 6, 4)
    b = native.generate(seed, {"mode": "transfer"}, 6, 4)
    assert [p["input"] for p in a["train"] + a["test"]] == [p["input"] for p in b["train"] + b["test"]]
    assert len({tuple(map(tuple, p["input"])) for p in a["train"] + a["test"]}) == 10
    assert all(x["output"] != y["output"] for x, y in zip(a["train"], b["train"]))
    for demos, queries in ((4, 1), (5, 3), (6, 4)):
        short = native.generate(seed, {"mode": "prototype"}, demos, queries)
        assert short["train"] == a["train"][:demos] and short["test"] == a["test"][:queries]
    before = native.generate(seed, {"mode": "prototype"}, 4, 1)
    a["train"][0]["input"][0][0] = 9
    assert native.generate(seed, {"mode": "prototype"}, 4, 1) == before


def test_four_cores_cover_match_roles_and_transform_categories(native):
    demos, _ = native.input_bank(0)
    expected = ((0, "rot90"), (1, "rot270"), (0, "flip-h"), (1, "transpose"))
    for grid, pair in zip(demos, expected):
        a = native.analyze(grid)
        assert (a["match_index"], a["transform"]) == pair
        p, q = [panel["cells"] for panel in a["panels"][:2]]
        assert len(p) == len(q) == 6
        assert (max(r for r, c in p), max(c for r, c in p)) == (2, 2)
        assert (max(r for r, c in q), max(c for r, c in q)) == (2, 2)
        assert len(native.orbit(p)) == len(native.orbit(q)) == 8
        assert not set(native.orbit(p)).intersection(native.orbit(q))
    assert [native.analyze(demos[i])["panels"][i]["color"] for i in range(3)] == [8, 8, 8]


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_large_scenes_have_substantive_content(native, seed):
    e = native.generate(seed, {"mode": "prototype"}, 6, 4)
    large = [p["input"] for p in e["train"] + e["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert [sum(bool(v) for row in grid for v in row) for grid in large] == [453, 468]
    for grid in large:
        for r in (0, 15):
            for c in (0, 15):
                assert sum(bool(grid[y][x]) for y in range(r, r + 15) for x in range(c, c + 15)) >= 40
