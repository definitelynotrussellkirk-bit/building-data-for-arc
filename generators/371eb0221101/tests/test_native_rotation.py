"""Native rotation-family behavior; labels also receive protected Racket replay."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"
ROOT = find_root(__file__)
RULES = ("clockwise", "counterclockwise", "color_count")


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "Native adapter with color-count rotation is missing"
    spec = importlib.util.spec_from_file_location("rotation_native_test_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_contract_preserves_the_exact_canonical_default():
    a = load_adapter()
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    canonical = next(row["program_solution"] for row in rows if row["task_id"] == "371eb0221101")
    assert a.program({"rotation_rule": "clockwise"}) == canonical
    assert len({a.program({"rotation_rule": name}) for name in RULES}) == 3
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["default"] == {"rotation_rule": "clockwise"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}


@pytest.mark.parametrize("seed", [0, 17, 934])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_matched_inputs_and_teaching_across_supported_demo_counts(seed, demos):
    a = load_adapter()
    inputs = []
    for rule in RULES:
        setting = {"rotation_rule": rule}
        episode = a.generate(seed, setting, demos, 4)
        assert episode == a.generate(seed, setting, demos, 4)
        assert len(episode["train"]) == demos and len(episode["test"]) == 4
        seq = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in seq}) == demos + 4
        assert a.teaching_check(episode)["survivors"] == [rule]
        assert not a.teaching_check(episode)["ambiguities"]
        assert {(row["scale"]) for pair in episode["train"][:2]
                for row in a.analyze(pair["input"])["objects"]} == {1, 2}
        large = a.analyze(episode["test"][3]["input"])
        assert (large["height"], large["width"]) == (30, 30)
        assert large["n_objects"] >= 25
        assert sum(cell != 0 for row in seq[-1] for cell in row) >= 300
        assert a.analyze(seq[demos])["height"] == 7
        inputs.append(seq)
    assert inputs[0] == inputs[1] == inputs[2]


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_first_turn_and_private_projection_are_query_count_independent(queries):
    a = load_adapter()
    settings = {"rotation_rule": "color_count"}
    episode = a.generate(17, settings, 2, queries)
    one = a.generate(17, settings, 2, 1)
    visible = a.model_view(episode, 0)
    assert public_challenge_bytes(visible) == public_challenge_bytes(a.model_view(one, 0))
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    hidden = deepcopy(episode)
    hidden.update(seed=-123, settings={"secret": True}, program_solution="private")
    hidden["train"][0]["private"] = "private"
    for pair in hidden["test"]:
        pair["output"] = [[9]]
    assert a.model_view(hidden, 0) == visible
    visible["train"][0]["input"][0][0] = 9
    assert episode == a.generate(17, settings, 2, queries)


def test_remote_recolor_changes_unchanged_objects_and_teaches_count_gaps():
    a = load_adapter()
    episode = a.generate(0, {"rotation_rule": "color_count"}, 2, 4)
    first, second = episode["train"]
    before, after = a.analyze(first["input"]), a.analyze(second["input"])
    assert sorted(before["color_counts"].values()) == [1, 2, 3, 4]
    assert sorted(after["color_counts"].values()) == [1, 1, 4, 4]
    identical_objects_changed = 0
    recolored = 0
    for left, right in zip(before["objects"], after["objects"], strict=True):
        assert (left["r"], left["c"], left["scale"], left["corner"]) == (right["r"], right["c"], right["scale"], right["corner"])
        if left["color"] != right["color"]:
            recolored += 1
        else:
            r, c, width = left["r"], left["c"], 2 * left["scale"]
            lout = [row[c:c+width] for row in first["output"][r:r+width]]
            rout = [row[c:c+width] for row in second["output"][r:r+width]]
            identical_objects_changed += lout != rout
    assert recolored == 1 and identical_objects_changed == 4


def test_seed_121_minimum_lesson_rejects_column_only_shortcut():
    a = load_adapter()
    for rule in RULES:
        episode = a.generate(121, {"rotation_rule": rule}, 2, 4)
        certificate = a.teaching_check(episode)
        assert certificate["survivors"] == [rule]
        assert not certificate["ambiguities"]


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (1.0, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, True, 4), (0, 1, 4), (0, 7, 4), (0, 3, 0), (0, 3, 5), (0, 3, 4.0)])
def test_invalid_generation_counts_and_seed_fail_visibly(seed, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        load_adapter().generate(seed, {"rotation_rule": "color_count"}, demos, queries)


@pytest.mark.parametrize("setting", [{}, {"rotation_rule": 1}, {"rotation_rule": True}, {"rotation_rule": "unknown"}, {"rotation_rule": "clockwise", "extra": 0}])
def test_settings_are_exact_and_typed(setting):
    with pytest.raises((ValueError, TypeError)):
        load_adapter().program(setting)


def test_observer_rejects_bad_shapes_and_noninteger_pixels():
    a = load_adapter()
    episode = a.generate(0, {"rotation_rule": "clockwise"}, 2, 1)
    grid = episode["test"][0]["input"]
    for bad in ([], [[0]], [grid[0], grid[1][:-1]]):
        with pytest.raises(ValueError):
            a.analyze(bad)
    for bad_value in (True, 1.0, -1, 10):
        bad = deepcopy(grid)
        bad[2][2] = bad_value
        with pytest.raises(ValueError):
            a.analyze(bad)
    bad = deepcopy(grid)
    bad[2][2] = 9
    with pytest.raises(ValueError):
        a.analyze(bad)


def test_literal_color_count_fixture_through_protected_racket():
    # Two red Ls and one blue L. Red turns twice; blue turns once.
    a = load_adapter()
    grid = [[0] * 10 for _ in range(7)]
    for r, c, color in [(0, 0, 2), (0, 5, 2), (5, 0, 1)]:
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            grid[r+dr][c+dc] = color
    expected = [[0] * 10 for _ in range(7)]
    for r, c in [(0, 0), (0, 5)]:
        for dr, dc in [(0, 0), (0, 1), (1, 1)]:
            expected[r+dr][c+dc] = 2
    for dr, dc in [(0, 0), (0, 1), (1, 0)]:
        expected[5+dr][dc] = 1
    assert a.transform(grid, "color_count") == expected
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        assert identity["protected"] is True
        assert apply(a.program({"rotation_rule": "color_count"}), grid) == expected
        assert apply(a.program({"rotation_rule": "clockwise"}), grid) != expected
    finally:
        bridge.close()
