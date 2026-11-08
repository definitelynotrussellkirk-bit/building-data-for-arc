from pathlib import Path
import copy
import importlib.util
import json
import random

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return load(HOME / "generator.py", "cut_test_base")


@pytest.fixture(scope="module")
def adapter():
    return load(HOME / "workspace/parametric/adapter.py", "cut_test_adapter")


def grid(h, w, points, markers, colors=(1, 7, 2)):
    bg, fg, ray = colors
    g = [[bg] * w for _ in range(h)]
    for r, c in points: g[r][c] = fg
    for r, c in markers: g[r][c] = ray
    return g


@pytest.mark.parametrize("index", range(5))
def test_all_original_labels(base, index):
    raw = REPO / "shared/data/raw"
    d = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["4a21e3da"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["4a21e3da"]
    pairs = d["train"] + [dict(input=p["input"], output=o) for p, o in zip(d["test"], gold)]
    assert base.solve(pairs[index]["input"], "union") == pairs[index]["output"]


@pytest.mark.parametrize("selection", ["union", "intersection"])
def test_whole_region_translation_and_axis_endpoint(base, selection):
    points = [(2, 1), (5, 2), (3, 6), (5, 7), (3, 4), (4, 4)]
    g = grid(9, 9, points, [(0, 4)])
    expected = grid(9, 9, [(0, 0), (3, 1), (0, 7), (2, 8), (3, 4), (4, 4)],
                    [(0, 4), (1, 4), (2, 4)])
    assert base.solve(g, selection) == expected
    assert base.solve([list(row) for row in zip(*g)], selection) == [list(row) for row in zip(*expected)]


@pytest.mark.parametrize("selection", ["union", "intersection"])
def test_two_axes_corner_selection(base, selection):
    groups = [(2, 2), (2, 3), (3, 3), (2, 5), (3, 6), (5, 2), (6, 3), (5, 5), (6, 5), (6, 6)]
    anchors = [(2, 4), (6, 4), (4, 2), (4, 6)]
    g = grid(9, 9, groups + anchors, [(0, 4), (4, 8)])
    moved = [(0, 7), (1, 8)]
    if selection == "union": moved += [(0, 0), (0, 1), (1, 1), (7, 7), (8, 7), (8, 8)]
    rays = [(r, 4) for r in range(7)] + [(4, c) for c in range(2, 9)]
    expected = grid(9, 9, [], rays)
    for r, c in moved + anchors: expected[r][c] = 7
    assert base.solve(g, selection) == expected


def test_zero_foreground_and_nonmodal_background(base):
    points = [(r, c) for r in range(1, 8) for c in range(1, 8) if r != 4 or c in (1, 7)]
    g = grid(9, 9, points, [(0, 4), (4, 8)], colors=(7, 0, 1))
    assert sum(v == 0 for row in g for v in row) > sum(v == 7 for row in g for v in row)
    a = base.analyze(g, "union")
    assert a["background"] == 7 and a["foreground"] == 0 and a["ray_color"] == 1
    assert len(a["output"]) == 9


@pytest.mark.parametrize("bad", [[], [[0]], [[True] * 8] * 8, [[1.0] * 8] * 8,
    [[10] * 8] * 8, [[1] * 8] * 8, [[1] * 8, [1] * 9], [tuple([1] * 8)] * 8])
def test_strict_grid_types(base, bad):
    with pytest.raises((ValueError, TypeError)):
        base.solve(bad)


@pytest.mark.parametrize("mutation", ["corner", "extra_marker", "mixed_marker", "off_axis", "extra_color"])
def test_marker_grammar(base, mutation):
    g = grid(7, 7, [(2, 2), (3, 3), (4, 4)], [(0, 3)])
    if mutation == "corner": g[0][0] = 2
    elif mutation == "extra_marker": g[6][3] = 2
    elif mutation == "mixed_marker": g[3][0] = 8
    elif mutation == "off_axis": g[3][3] = 1
    else: g[1][1] = 8
    with pytest.raises((ValueError, TypeError)):
        base.solve(g)


@pytest.mark.parametrize("selection", ["union", "intersection"])
def test_prefixes_matching_inputs_and_ownership(adapter, selection):
    settings = {"selection": selection}
    before = random.getstate()
    full = adapter.generate(17, settings, 6, 4)
    short = adapter.generate(17, settings, 3, 1)
    other = adapter.generate(17, {"selection": "intersection" if selection == "union" else "union"}, 6, 4)
    assert random.getstate() == before
    assert short["train"] == full["train"][:3] and short["test"] == full["test"][:1]
    for split in ("train", "test"):
        assert [p["input"] for p in full[split]] == [p["input"] for p in other[split]]
    pairs = full["train"] + full["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == 10
    rows = [row for p in pairs for side in ("input", "output") for row in p[side]]
    assert len({id(row) for row in rows}) == len(rows)


def test_native_identity_and_programs(base, adapter):
    from arc_repl.parser import parse_all, Symbol
    assert base.RULE_TASK_ID == "ee_4a21e3da"
    assert (HOME / "generator.py").read_bytes() == (HOME / "workspace/parametric/sampler.py").read_bytes()
    assert adapter.program({"selection": "union"}).encode() == (HOME / "reference.rkt").read_bytes()
    for setting in ("union", "intersection"):
        forms = parse_all(adapter.program({"selection": setting}))
        assert len(forms) == 1 and forms[0][0] == Symbol("rule!")


@pytest.mark.parametrize("seed,settings,demos,queries", [
    (True, {"selection": "union"}, 3, 4), (-1, {"selection": "union"}, 3, 4),
    (2**63, {"selection": "union"}, 3, 4), (0, {"selection": "bad"}, 3, 4),
    (0, {"selection": "union", "extra": 1}, 3, 4), (0, {"selection": "union"}, True, 4),
    (0, {"selection": "union"}, 2, 4), (0, {"selection": "union"}, 7, 4),
    (0, {"selection": "union"}, 3, 0), (0, {"selection": "union"}, 3, 5)])
def test_invalid_episode_requests(adapter, seed, settings, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(seed, settings, demos, queries)


def test_minimum_and_substantive_large_boundary(adapter):
    e = adapter.generate(2**63 - 1, {"selection": "union"}, 3, 4)
    shapes = {(len(p["input"]), len(p["input"][0])) for p in e["test"]}
    assert (5, 5) in shapes and (30, 30) in shapes
    p = next(p for p in e["test"] if len(p["input"]) == len(p["input"][0]) == 30)
    a = adapter.analyze(p["input"], {"selection": "union"})
    assert a["foreground_count"] >= 450
    assert sum(x != y for rx, ry in zip(p["input"], p["output"]) for x, y in zip(rx, ry)) >= 100


def test_root_input_only_contract(base):
    grids = [base.generate(29, i) for i in range(7)]
    assert len({json.dumps(g) for g in grids}) == 7 and base.AXES == {}
    for g in grids:
        before = copy.deepcopy(g)
        assert type(g) is list and base.self_check(g) == [] and g == before
    assert base.self_check([[0]])
