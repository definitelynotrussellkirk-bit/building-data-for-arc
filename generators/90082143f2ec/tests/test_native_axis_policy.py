"""Native adapter contracts: teaching, count stability, boundaries and privacy."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]


def load_adapter():
    path = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("native_axis_policy_test", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError:
        pytest.fail("Native root adapter is not implemented")
    return module


@pytest.fixture(scope="module")
def adapter():
    return load_adapter()


def test_native_default_is_exact_canonical_and_settings_change_labels():
    adapter = load_adapter()
    from arcpuzzles import Catalog
    canonical = {v["program_solution"] for v in Catalog(find_root(__file__))._variants()["90082143f2ec"]}
    assert canonical == {adapter.program({"axis_policy": "more_coherent"})}
    first = adapter.generate(0, {"axis_policy": "more_coherent"}, 2, 4)
    second = adapter.generate(0, {"axis_policy": "less_coherent"}, 2, 4)
    assert first["train"][0]["output"] != second["train"][0]["output"]


def test_native_worker_wrapper_executes_both_programs_as_grid_functions(adapter):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    with RacketBridge(timeout=10.0, startup_timeout=30.0) as bridge:
        assert bridge.runtime_identity["protected"] is True
        for policy in ("more_coherent", "less_coherent"):
            settings = {"axis_policy": policy}
            pair = adapter.generate(0, settings, 2, 1)["train"][0]
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
            actual = bridge.eval_text(f"({wrap_rule(adapter.program(settings))} {literal})")
            assert actual == pair["output"], policy


@pytest.mark.parametrize("demos,queries", [(2, 1), (3, 4), (6, 4)])
def test_independent_counts_and_settings_use_distinct_matched_inputs(adapter, demos, queries):
    episodes = [adapter.generate(17, {"axis_policy": mode}, demos, queries)
                for mode in ("more_coherent", "less_coherent")]
    for episode in episodes:
        assert len(episode["train"]) == demos and len(episode["test"]) == queries
        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(pair["input"]) for pair in pairs}) == demos + queries
        assert all(type(v) is int and 0 <= v <= 9 for pair in pairs
                   for side in ("input", "output") for row in pair[side] for v in row)
    assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]


def test_count_changes_preserve_both_prefixes_and_single_query_first_turn(adapter):
    settings = {"axis_policy": "less_coherent"}
    small = adapter.generate(5, settings, 2, 1)
    large = adapter.generate(5, settings, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    same_demos = adapter.generate(5, settings, 6, 1)
    first = adapter.visible_turn(large, 0)
    assert public_challenge_bytes(first) == public_challenge_bytes(same_demos)
    assert set(first) == {"train", "test"} and len(first["test"]) == 1


@pytest.mark.parametrize("mode", ["more_coherent", "less_coherent"])
def test_two_demos_teach_axis_policy_and_tie_rule(adapter, mode):
    episode = adapter.generate(0, {"axis_policy": mode}, 2, 4)
    demos = episode["train"]
    assert {(len(p["input"]), len(p["input"][0])) for p in demos} == {(6, 6)}
    facts = [adapter.observables(p["input"]) for p in demos]
    assert {f["dominant_axis"] for f in facts} == {"rows", "columns"}
    for pair in demos:
        weak = adapter.solve(pair["input"], {"axis_policy": "less_coherent"})
        assert len({v for row in weak for v in row}) == 3
    report = adapter.teaching_report(demos, {"axis_policy": mode})
    assert report["all_refuted"], report
    assert report["rival_count"] >= 8


def test_full_canvas_sizes_and_fresh_noise(adapter):
    episode = adapter.generate(1, {"axis_policy": "more_coherent"}, 3, 4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [
        (13, 14), (15, 15), (24, 24), (30, 30)]
    for pair in episode["test"][2:]:
        grid = pair["input"]
        noise = sum(v != pair["output"][r][c]
                    for r, row in enumerate(grid) for c, v in enumerate(row))
        assert 0.13 <= noise / (len(grid) * len(grid[0])) <= 0.21
        assert {v for row in grid for v in row} == set(range(1, 10))
        assert any(len({grid[r+dr][c+dc] for dr in (0, 1) for dc in (0, 1)}) > 1
                   for r in range(0, len(grid)-1, 2) for c in range(0, len(grid[0])-1, 2))


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5), (True, 4), (3, 4.0)])
def test_native_count_limits_reject_invalid_requests(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"axis_policy": "more_coherent"}, demos, queries)


@pytest.mark.parametrize("seed", [True, -1, 1.5, "1", 2**63])
def test_invalid_seeds_are_rejected(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"axis_policy": "more_coherent"}, 3, 4)


@pytest.mark.parametrize("setting", [{}, {"axis_policy": True}, {"axis_policy": "other"},
    {"axis_policy": "more_coherent", "hidden": 1}])
def test_invalid_settings_are_rejected(adapter, setting):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(setting)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, setting, 3, 4)


def test_public_bytes_and_ids_ignore_private_changes(adapter):
    episode = adapter.generate(0, {"axis_policy": "less_coherent"}, 3, 4)
    before = public_challenge_bytes(episode)
    altered = deepcopy(episode)
    altered.update(seed=-10, settings={"secret": 1}, program_solution="private")
    altered["test"][0]["output"][0][0] = 0
    assert public_challenge_bytes(altered) == before
    assert public_challenge_id(altered) == hashlib.sha256(before).hexdigest()
    turn = adapter.visible_turn(episode, 0)
    turn["train"][0]["input"][0][0] = 0
    assert episode["train"][0]["input"][0][0] != 0


def test_writer_hashes_exact_bytes_sorts_and_rejects_visible_duplicates(adapter, tmp_path):
    episodes = [adapter.generate(0, {"axis_policy": mode}, 3, 4)
                for mode in ("less_coherent", "more_coherent")]
    receipt = adapter.write_batch(episodes, tmp_path / "examples")
    assert receipt["public_ids"] == sorted(receipt["public_ids"])
    files = list((tmp_path / "examples/public").glob("*.json"))
    assert len(files) == 2
    for path in files:
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
        assert all(set(p) == {"input"} for p in json.loads(path.read_bytes())["test"])
    turns = list((tmp_path / "examples/turns").glob("*.json"))
    assert len(turns) == 8
    assert all(len(json.loads(p.read_bytes())["test"]) == 1 for p in turns)
    private_change = deepcopy(episodes[0])
    private_change["test"][0]["output"][0][0] = 0
    with pytest.raises(ValueError, match="duplicate"):
        adapter.write_batch([episodes[0], private_change], tmp_path / "duplicate")
    assert not (tmp_path / "duplicate").exists()
