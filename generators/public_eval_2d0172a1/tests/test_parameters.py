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
    return load(HOME / "generator.py", "diagram_test_base")


@pytest.fixture(scope="module")
def adapter():
    return load(HOME / "workspace/parametric/adapter.py", "diagram_test_adapter")


def frame(grid, r0, c0, r1, c1, color):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                grid[r][c] = color


@pytest.mark.parametrize("index", range(6))
def test_every_original_label(base, index):
    raw = REPO / "shared/data/raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["2d0172a1"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["2d0172a1"]
    pairs = task["train"] + [dict(input=p["input"], output=o) for p, o in zip(task["test"], gold)]
    assert base.solve(pairs[index]["input"]) == pairs[index]["output"]


@pytest.mark.parametrize("policy,size", [("all", 9), ("outermost", 5)])
def test_literal_nested_frames_select_before_compression(base, policy, size):
    grid = [[1] * 17 for _ in range(17)]
    frame(grid, 1, 1, 15, 15, 4)
    frame(grid, 5, 5, 11, 11, 4)
    grid[8][8] = 4
    expected = [[1] * size for _ in range(size)]
    frame(expected, 0, 0, size - 1, size - 1, 4)
    if policy == "all":
        frame(expected, 2, 2, 6, 6, 4)
    expected[size // 2][size // 2] = 4
    assert base.solve(grid, policy) == expected


def test_empty_frame_and_singleton_halo(base):
    grid = [[7] * 10 for _ in range(9)]
    frame(grid, 2, 2, 6, 7, 9)
    assert base.solve(grid) == [[9, 9, 9], [9, 7, 9], [9, 9, 9]]
    lone = [[0] * 5 for _ in range(5)]
    lone[2][2] = 6
    assert base.solve(lone) == [[0, 0, 0], [0, 6, 0], [0, 0, 0]]


def test_transitive_interval_overlap_is_not_center_alignment(base):
    grid = [[0] * 17 for _ in range(11)]
    for r0, c0 in [(2, 2), (4, 7), (6, 12)]:
        for r in range(r0, r0 + 3):
            for c in range(c0, c0 + 2):
                grid[r][c] = 3
    assert base.solve(grid) == [[0] * 7, [0, 3, 0, 3, 0, 3, 0], [0] * 7]


def test_diagonal_foreground_contacts_remain_distinct(base):
    grid = [[1] * 8 for _ in range(8)]
    grid[3][3] = grid[4][4] = 2
    expected = [[1] * 5 for _ in range(5)]
    expected[1][1] = expected[3][3] = 2
    assert base.solve(grid) == expected


def test_open_shape_does_not_become_a_frame_by_bounding_box(base):
    grid = [[0] * 10 for _ in range(10)]
    frame(grid, 1, 1, 7, 7, 5)
    grid[1][4] = 0
    grid[4][4] = 5
    assert base.solve(grid) == [[0, 0, 0], [0, 5, 0], [0, 0, 0]]


@pytest.mark.parametrize("bad", [[], [[0]], [[True] * 6] * 6, [[1.0] * 6] * 6,
                                      [[10] * 6] * 6, [[8] * 6] * 6,
                                      [tuple([0] * 6)] * 6, [[0] * 6, [0] * 7]])
def test_strict_grid_admission(base, bad):
    with pytest.raises((ValueError, TypeError)):
        base.solve(bad)


def test_tied_palette_multiple_holes_and_collapsed_frame_rejected(base):
    tied = [[0, 1] * 3 for _ in range(6)]
    with pytest.raises(ValueError):
        base.solve(tied)
    double = [[0] * 12 for _ in range(12)]
    frame(double, 2, 2, 8, 8, 4)
    for r in range(2, 9):
        double[r][5] = 4
    with pytest.raises(ValueError):
        base.solve(double)
    collapsed = [[0] * 15 for _ in range(12)]
    frame(collapsed, 3, 3, 8, 8, 4)
    for r in range(1, 11):
        collapsed[r][12] = 4
    with pytest.raises(ValueError):
        base.solve(collapsed)


@pytest.mark.parametrize("policy", ["all", "outermost"])
def test_prefixes_matched_inputs_determinism_and_ownership(adapter, policy):
    before = random.getstate()
    full = adapter.generate(17, {"frame_policy": policy}, 6, 4)
    short = adapter.generate(17, {"frame_policy": policy}, 2, 1)
    other = adapter.generate(17, {"frame_policy": "outermost" if policy == "all" else "all"}, 6, 4)
    assert full == adapter.generate(17, {"frame_policy": policy}, 6, 4)
    assert random.getstate() == before
    assert short["train"] == full["train"][:2] and short["test"] == full["test"][:1]
    pairs = full["train"] + full["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == 10
    for split in ("train", "test"):
        assert [p["input"] for p in full[split]] == [p["input"] for p in other[split]]
    rows = [row for p in pairs for field in ("input", "output") for row in p[field]]
    assert len({id(row) for row in rows}) == len(rows)


def test_resource_closure_and_native_root_api(base, adapter):
    from arc_repl.parser import parse_all, Symbol
    assert base.RULE_TASK_ID == "ee_2d0172a1" and base.AXES == {}
    assert (HOME / "generator.py").read_bytes() == (HOME / "workspace/parametric/sampler.py").read_bytes()
    assert adapter.program({"frame_policy": "all"}).encode() == (HOME / "reference.rkt").read_bytes()
    for policy in ("all", "outermost"):
        forms = parse_all(adapter.program({"frame_policy": policy}))
        assert len(forms) == 1 and forms[0][0] == Symbol("rule!")
    grids = [base.generate(29, i) for i in range(6)]
    assert len({json.dumps(g) for g in grids}) == 6
    for grid in grids:
        original = copy.deepcopy(grid)
        assert base.self_check(grid) == [] and grid == original
    assert base.self_check([[0]])
    with pytest.raises(ValueError):
        base.generate(29, unknown=1)


@pytest.mark.parametrize("seed,settings,demos,queries", [
    (True, {"frame_policy": "all"}, 2, 4), (-1, {"frame_policy": "all"}, 2, 4),
    (2**63, {"frame_policy": "all"}, 2, 4), (0, {"frame_policy": "bad"}, 2, 4),
    (0, {"frame_policy": "all", "extra": 1}, 2, 4), (0, {"frame_policy": "all"}, True, 4),
    (0, {"frame_policy": "all"}, 1, 4), (0, {"frame_policy": "all"}, 7, 4),
    (0, {"frame_policy": "all"}, 2, 0), (0, {"frame_policy": "all"}, 2, 5)])
def test_invalid_episode_requests(adapter, seed, settings, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(seed, settings, demos, queries)


def test_substantive_thirty_by_thirty_query(adapter):
    episode = adapter.generate(2**63 - 1, {"frame_policy": "all"}, 2, 4)
    large = [p for p in episode["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert len(large) >= 2
    for pair in large:
        counts = {value: sum(row.count(value) for row in pair["input"]) for value in set(sum(pair["input"], []))}
        assert min(counts.values()) >= 180
        assert max(len(pair["output"]), len(pair["output"][0])) <= 30


def test_rounded_corner_keeps_inner_blob_disconnected(base):
    grid = base.sample_profile(0, "probe-5", 5)
    objects = base.parse(grid)["objects"]
    assert len(objects) == 6
    assert sum(obj["kind"] == "frame" for obj in objects) == 3


def test_stress_profile_preserves_empty_frame_endpoint_groups(base):
    grid = base.sample_profile(0, "probe-9", 9)
    frames = [shape for shape in base.first_stage(grid)["shapes"] if shape["kind"] == "frame"]
    assert len(frames) == 4
    assert all(s["rows"][0] < s["rows"][1] and s["cols"][0] < s["cols"][1] for s in frames)


def test_core_teaches_deep_frame_selection_and_halos_on_both_sides(base):
    grid = base.sample_profile(0, "demo-0", 0)
    parts = base.parse(grid)
    assert max(len(obj["containers"]) for obj in parts["objects"] if obj["kind"] == "frame") == 2
    for policy in ("all", "outermost"):
        stage = base.first_stage(grid, policy)
        top, left, bottom, right = stage["extent"]
        assert top == left == -1
        assert bottom == 2 * (len(stage["row_groups"]) - 1) + 1
        assert right == 2 * (len(stage["column_groups"]) - 1) + 1


@pytest.mark.parametrize("policy", ["all", "outermost"])
def test_complete_rule_survives_executor_serialization(adapter, policy):
    from arc_repl.builtins import Grid, _unwrap
    from arc_repl.executor import ArcExecutor
    grid = [[0] * 10 for _ in range(9)]
    frame(grid, 2, 2, 6, 7, 3)
    expected = [[3, 3, 3], [3, 0, 3], [3, 3, 3]]
    with ArcExecutor({"train": [], "test": []}, use_racket=True) as executor:
        assert executor._bridge.runtime_identity["protected"] is True
        observation = executor.step(adapter.program({"frame_policy": policy}))
        assert not observation.startswith("ERROR")
        assert _unwrap(executor._apply_rule(Grid(grid))) == expected
