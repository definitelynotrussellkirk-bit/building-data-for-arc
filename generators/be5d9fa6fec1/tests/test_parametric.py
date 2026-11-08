"""Behavioral regressions for the separate native row-run adapter."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]


def load_adapter():
    path = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("tested_be5d9fa6fec1_adapter", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError:
        pytest.fail("Native row-run adapter is not implemented")
    return module


@pytest.fixture(scope="module")
def adapter():
    return load_adapter()


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        def execute(program, grid):
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            return bridge.eval_text(f"({wrap_rule(program)} {literal})")
        yield execute


ROWS = [[1, 0, 1], [0, 1, 0], [1, 0, 1], [8, 8, 0],
        [0, 8, 8], [1, 1, 0], [8, 0, 8], [0, 1, 1], [8, 8, 8]]
HEIGHTS = [2, 1, 1, 3, 1, 1, 1, 2, 1]
HAND_INPUT = [row[:] for row, height in zip(ROWS, HEIGHTS) for _ in range(height)]


@pytest.mark.parametrize("mode,paint_rows", [
    ("fixed3", {0, 1, 4, 5, 6, 9}),
    ("height_plus_one", {0, 1, 4, 5, 6, 10, 11}),
])
def test_hand_checked_run_walk(racket, mode, paint_rows):
    adapter = load_adapter()
    # Run indices are fixed3=[0,3,6], adaptive=[0,3,7].
    expected = [[2 if r in paint_rows and value else value for value in row]
                for r, row in enumerate(HAND_INPUT)]
    settings = {"step_mode": mode}
    assert adapter.solve(HAND_INPUT, settings) == expected
    assert racket(adapter.program(settings), HAND_INPUT) == expected


def test_canonical_default_preserves_exact_reference(adapter):
    from arcpuzzles import Catalog
    root = find_root(__file__)
    programs = {v["program_solution"] for v in Catalog(root)._variants()["be5d9fa6fec1"]}
    assert programs == {adapter.program({"step_mode": "fixed3"})}
    for pair in canonical_pairs("be5d9fa6fec1", root=root, labeled_only=True):
        assert adapter.solve(pair["input"], {"step_mode": "fixed3"}) == pair["output"]


@pytest.mark.parametrize("demos,queries", [(2, 4), (3, 1), (6, 4)])
def test_independent_counts_unique_inputs_and_matched_settings(adapter, demos, queries):
    episodes = [adapter.generate(17, {"step_mode": mode}, demos, queries)
                for mode in ("fixed3", "height_plus_one")]
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        inputs = [json.dumps(pair["input"]) for pair in episode["train"] + episode["test"]]
        assert len(inputs) == len(set(inputs))
        assert all(type(v) is int and 0 <= v <= 9
                   for pair in episode["train"] + episode["test"]
                   for side in ("input", "output") for row in pair[side] for v in row)
    assert [[p["input"] for p in e["train"] + e["test"]] for e in episodes][0] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]
    assert episodes[0]["train"][0]["output"] != episodes[1]["train"][0]["output"]


def test_demo_and_query_prefixes_do_not_depend_on_requested_counts(adapter):
    setting = {"step_mode": "height_plus_one"}
    short = adapter.generate(23, setting, 2, 1)
    long = adapter.generate(23, setting, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]


@pytest.mark.parametrize("mode", ["fixed3", "height_plus_one"])
def test_minimum_and_30_square_labels_execute(adapter, racket, mode):
    episode = adapter.generate(0, {"step_mode": mode}, 2, 4)
    for index, shape in ((0, (8, 3)), (3, (30, 30))):
        pair = episode["test"][index]
        assert (len(pair["input"]), len(pair["input"][0])) == shape
        assert racket(episode["program_solution"], pair["input"]) == pair["output"]
    large = episode["test"][3]["input"]
    assert any(row[0] != 0 for row in large)
    assert any(row[-1] != 0 for row in large)
    assert len({tuple(row) for row in large}) >= 10


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5),
                                          (True, 4), (3, 4.0)])
def test_invalid_counts_are_rejected(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"step_mode": "fixed3"}, demos, queries)


@pytest.mark.parametrize("settings", [{}, {"step_mode": "other"},
    {"step_mode": True}, {"step_mode": "fixed3", "hidden": 1}])
def test_invalid_settings_are_rejected(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, 3, 4)
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


def test_public_projection_ignores_private_answers_and_metadata(adapter):
    from reviewer_support import public_challenge_id
    episode = adapter.generate(0, {"step_mode": "height_plus_one"}, 3, 4)
    before = public_challenge_bytes(episode)
    edited = deepcopy(episode)
    edited.update(seed=987, settings={"secret": True}, program_solution="private")
    edited["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(edited) == before
    assert public_challenge_id(edited) == hashlib.sha256(before).hexdigest()
    assert all(set(pair) == {"input"} for pair in json.loads(before)["test"])


def test_sequential_projection_hides_future_inputs(adapter):
    episode = adapter.generate(2, {"step_mode": "fixed3"}, 3, 4)
    first = adapter.visible_turn(episode, 0)
    single = adapter.generate(2, {"step_mode": "fixed3"}, 3, 1)
    assert public_challenge_bytes(first) == public_challenge_bytes(single)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    with pytest.raises(ValueError):
        adapter.visible_turn(episode, -1)


@pytest.mark.parametrize("mode", ["fixed3", "height_plus_one"])
def test_demonstrations_reject_declared_shortcuts_without_queries(adapter, mode):
    episode = adapter.generate(3, {"step_mode": mode}, 2, 4)
    report = adapter.teaching_report(episode["train"], {"step_mode": mode})
    assert report["all_refuted"] is True, report
    assert report["rival_count"] >= 10
    assert all(row["counterexample_demo"] is not None for row in report["rivals"])


def test_writer_hashes_exact_visible_bytes_and_keeps_private_data_separate(adapter, tmp_path):
    episodes = [adapter.generate(seed, {"step_mode": mode}, 3, 4)
                for seed, mode in ((1, "height_plus_one"), (0, "fixed3"))]
    target = tmp_path / "export"
    receipt = adapter.write_batch(episodes, target)
    assert receipt["public_ids"] == sorted(receipt["public_ids"])
    for path in (target / "public").glob("*.json"):
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
        value = json.loads(path.read_bytes())
        assert set(value) == {"train", "test"}
        assert all(set(p) == {"input"} for p in value["test"])
    turns = list((target / "turns").glob("*.json"))
    assert len(turns) == 8
    assert all(len(json.loads(p.read_bytes())["test"]) == 1 for p in turns)
    assert len(json.loads((target / "private.json").read_text())["episodes"]) == 2
    changed = deepcopy(episodes[0])
    changed["test"][0]["output"][0][0] = 9
    changed.update(seed=99, settings={"private": 99}, program_solution="private")
    changed_receipt = adapter.write_batch([changed], tmp_path / "changed")
    assert changed_receipt["public_ids"][0] in receipt["public_ids"]
    with pytest.raises(ValueError, match="duplicate"):
        adapter.write_batch([episodes[0], changed], tmp_path / "duplicate")
    assert not (tmp_path / "duplicate").exists()
