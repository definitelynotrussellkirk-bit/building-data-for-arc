from pathlib import Path
import importlib.util
import json
import random

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return load(TASK_HOME / "generator.py", "beams_test_base")


@pytest.fixture(scope="module")
def adapter():
    return load(TASK_HOME / "workspace/parametric/adapter.py", "beams_test_adapter")


def blank(h, w, phase=0):
    return [[int((r + c) % 2 == phase) for c in range(w)] for r in range(h)]


def small_core(h, w, r, c, core=6, cap=4):
    g = blank(h, w, (r + c) % 2)
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if abs(dr) + abs(dc) == 2:
                g[r + dr][c + dc] = core
    for dr, dc in [(-3, 1), (-2, 2), (-1, 3)]:
        if 0 <= r + dr < h and 0 <= c + dc < w:
            g[r + dr][c + dc] = cap
    return g


@pytest.mark.parametrize("index", range(3))
def test_all_original_labels(base, index):
    raw = REPO / "shared/data/raw"
    challenge = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["80a900e0"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["80a900e0"]
    pairs = challenge["train"] + [dict(input=p["input"], output=o) for p, o in zip(challenge["test"], gold)]
    assert base.solve(pairs[index]["input"], "walls") == pairs[index]["output"]


def test_clipped_cap_keeps_visible_endpoint(base):
    g = small_core(5, 7, 2, 2)
    expected = [row[:] for row in g]
    expected[0][6] = 4
    assert base.solve(g, "walls") == expected


def test_walls_and_solid_have_distinct_interiors(base):
    g = small_core(11, 13, 5, 6)
    walls, solid = base.solve(g, "walls"), base.solve(g, "solid")
    for p in [(1, 8), (0, 9), (3, 10), (2, 11), (1, 12)]:
        assert walls[p[0]][p[1]] == solid[p[0]][p[1]] == 4
    for p in [(2, 9), (1, 10), (0, 11)]:
        assert walls[p[0]][p[1]] == 1 and solid[p[0]][p[1]] == 4
    assert all(walls[r][c] == solid[r][c] == v for r, row in enumerate(g) for c, v in enumerate(row) if v != 1)


def test_no_core_no_beam(base):
    g = blank(11, 13)
    g[2][6], g[3][7], g[4][8] = 4, 4, 4
    assert base.solve(g, "walls") == g


def test_larger_nonsquare_core_uses_measured_side(base):
    g = blank(21, 21)
    for i in range(3):
        for j in range(5):
            if i in (0, 2) or j in (0, 4):
                g[6 + i + j][8 + i - j] = 7
    for j in range(5):
        g[5 + j][7 - j] = 2
    out = base.solve(g, "walls")
    assert out[4][6] == out[8][2] == 2
    assert out[6][4] == 1
    assert base.solve(g, "solid")[6][4] == 2


@pytest.mark.parametrize("bad", [[], [[0]], [[True] * 5] * 5, [[1.0] * 5] * 5,
    [[10] * 5] * 5, [[1] * 5] * 5, [tuple([0] * 5)] * 5, [[0] * 5, [0] * 6]])
def test_grid_domain_is_strict(base, bad):
    with pytest.raises((ValueError, TypeError)):
        base.solve(bad)


@pytest.mark.parametrize("mode", ["walls", "solid"])
def test_counts_prefixes_matched_inputs_and_aliasing(adapter, mode):
    state = random.getstate()
    full = adapter.generate(17, {"beam": mode}, 6, 4)
    short = adapter.generate(17, {"beam": mode}, 3, 1)
    assert random.getstate() == state
    assert short["train"] == full["train"][:3] and short["test"] == full["test"][:1]
    other = adapter.generate(17, {"beam": "solid" if mode == "walls" else "walls"}, 6, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in full[split]] == [p["input"] for p in other[split]]
    pairs = full["train"] + full["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == 10
    rows = [row for p in pairs for k in ("input", "output") for row in p[k]]
    assert len({id(row) for row in rows}) == len(rows)


def test_exact_default_and_two_complete_programs(adapter):
    from arc_repl.parser import parse_all, Symbol
    assert adapter.program({"beam": "walls"}).encode() == (TASK_HOME / "reference.rkt").read_bytes()
    for mode in ("walls", "solid"):
        forms = parse_all(adapter.program({"beam": mode}))
        assert len(forms) == 1 and forms[0][0] == Symbol("rule!")


@pytest.mark.parametrize("seed,settings,demos,queries", [
    (True, {"beam": "walls"}, 3, 4), (-1, {"beam": "walls"}, 3, 4),
    (2**63, {"beam": "walls"}, 3, 4), (0, {"beam": "bad"}, 3, 4),
    (0, {"beam": "walls", "extra": 1}, 3, 4), (0, {"beam": "walls"}, True, 4),
    (0, {"beam": "walls"}, 2, 4), (0, {"beam": "walls"}, 7, 4),
    (0, {"beam": "walls"}, 3, 0), (0, {"beam": "walls"}, 3, 5),
])
def test_invalid_requests(adapter, seed, settings, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(seed, settings, demos, queries)


def test_minimum_and_large_scene_and_max_seed(adapter):
    episode = adapter.generate(2**63 - 1, {"beam": "walls"}, 3, 4)
    shapes = {(len(p["input"]), len(p["input"][0])) for p in episode["test"]}
    assert (30, 30) in shapes and ((5, 7) in shapes or (7, 5) in shapes)
    large = next(p for p in episode["test"] if len(p["input"]) == len(p["input"][0]) == 30)
    assert sum(a != b for ra, rb in zip(large["input"], large["output"]) for a, b in zip(ra, rb)) >= 30


def test_base_generator_is_input_only_and_distinct(base):
    grids = [base.generate(29, k) for k in range(7)]
    assert len({json.dumps(g) for g in grids}) == 7
    for g in grids:
        assert type(g) is list and base.self_check(g) == []
    assert base.AXES == {}
    findings = base.self_check([[0]])
    assert findings and all(type(value) is str for value in findings)


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("mode", ["walls", "solid"])
def test_demos_expose_single_cap_behavior(adapter, seed, mode):
    episode = adapter.generate(seed, {"beam": mode}, 3, 4)
    def teaches_one_cap(pair):
        a = adapter.analyze(pair["input"], {"beam": mode})
        return len(a["cores"]) == len(a["caps"]) == 1 and pair["output"] != pair["input"]
    assert any(teaches_one_cap(p) for p in episode["train"])
    assert any(teaches_one_cap(p) for p in episode["test"])
