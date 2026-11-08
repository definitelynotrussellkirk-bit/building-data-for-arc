"""Native-contract checks for clockwise/counterclockwise yellow staircases."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "fbf36c193fa6"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load_module(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{TASK_ID}_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    with canonical_path(find_root(__file__)).open() as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]["program_solution"]


def all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def public_projection(episode):
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def execute(bridge, source: str, grid: list[list[int]]):
    bridge.define_grid("g", grid)
    body = source[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    return bridge.eval_text(expression)


def test_default_program_is_exact_canonical_and_contract_is_bounded():
    adapter = load_module("adapter")
    assert adapter.program({"yellow_turn": "clockwise"}) == canonical_program()
    alternate = adapter.program({"yellow_turn": "counterclockwise"})
    assert alternate != canonical_program()
    assert alternate.count("(ycorners") == 1
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["parameters"] == {
        "yellow_turn": ["clockwise", "counterclockwise"]
    }
    assert contract["default"] == {"yellow_turn": "clockwise"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_counts_query_prefix_and_inputs_are_setting_independent_with_30x30_stress():
    adapter = load_module("adapter")
    clockwise = adapter.generate(17, {"yellow_turn": "clockwise"}, demos=2, queries=4)
    counter = adapter.generate(17, {"yellow_turn": "counterclockwise"}, demos=2, queries=4)
    long = adapter.generate(91, {"yellow_turn": "clockwise"}, demos=6, queries=1)
    one = adapter.generate(17, {"yellow_turn": "clockwise"}, demos=2, queries=1)

    assert set(clockwise) == {"train", "test", "program_solution"}
    assert (len(clockwise["train"]), len(clockwise["test"])) == (2, 4)
    assert (len(long["train"]), len(long["test"])) == (6, 1)
    assert all_inputs(clockwise) == all_inputs(counter)
    assert one["test"][0]["input"] == clockwise["test"][0]["input"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(clockwise)}) == 6

    stress = clockwise["test"][-1]
    grid = stress["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(cell == 5 for row in grid for cell in row) >= 50
    assert any(cell == 5 for cell in grid[0] + grid[-1])
    assert any(row[0] == 5 or row[-1] == 5 for row in grid)
    changed = sum(
        a != b
        for row_a, row_b in zip(grid, stress["output"])
        for a, b in zip(row_a, row_b)
    )
    assert changed >= 80


def test_two_demos_identify_turn_and_all_queries_distinguish_with_both_ray_colors():
    adapter = load_module("adapter")
    clockwise = adapter.generate(23, {"yellow_turn": "clockwise"}, demos=2, queries=4)
    counter = adapter.generate(23, {"yellow_turn": "counterclockwise"}, demos=2, queries=4)
    assert all(a["output"] != b["output"] for a, b in zip(clockwise["train"], counter["train"]))
    assert all(a["output"] != b["output"] for a, b in zip(clockwise["test"], counter["test"]))
    for episode in (clockwise, counter):
        for pair in episode["train"] + episode["test"]:
            colors = {cell for row in pair["output"] for cell in row}
            assert {2, 4, 5, 8} <= colors


def test_public_projection_omits_private_data_and_id_ignores_query_answer():
    adapter = load_module("adapter")
    episode = adapter.generate(31, {"yellow_turn": "counterclockwise"}, demos=3, queries=4)
    public = public_projection(episode)
    text = json.dumps(public, sort_keys=True)
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "yellow_turn" not in text and "rule!" not in text
    before = public_challenge_id(public)
    mutated = deepcopy(episode)
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(public_projection(mutated)) == before


def test_invalid_settings_seed_and_count_boundaries_are_rejected():
    adapter = load_module("adapter")
    for settings in (
        {"yellow_turn": "left"},
        {"yellow_turn": 1},
        {"yellow_turn": "clockwise", "other": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, demos=3, queries=4)
    for seed in (True, -1, 1.5):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"yellow_turn": "clockwise"}, demos=3, queries=4)
    for demos, queries in ((1, 4), (7, 4), (3, 0), (3, 5)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"yellow_turn": "clockwise"}, demos=demos, queries=queries)


def test_racket_matches_python_labels_for_both_turns():
    adapter = load_module("adapter")
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for turn in ("clockwise", "counterclockwise"):
            episode = adapter.generate(7, {"yellow_turn": turn}, demos=2, queries=1)
            for pair in episode["train"] + episode["test"]:
                assert execute(bridge, episode["program_solution"], pair["input"]) == pair["output"]


def test_materialized_evidence_is_four_query_racket_backed_and_opaque(tmp_path):
    prototype = load_module("prototype")
    report = prototype.materialize(tmp_path / "evidence", base_seed=41)
    assert report["complete_episodes"] == 2
    assert report["pairs_per_episode"] == {"train": 3, "test": 4}
    assert report["racket_rule_applications"] == 14
    assert report["all_labels_executed_in_racket"] is True
    assert report["all_demo_only_teaching_checks_pass"] is True
    assert report["max_query_shape"] == [30, 30]
    public_files = sorted((tmp_path / "evidence" / "public").glob("*.json"))
    private_files = sorted((tmp_path / "evidence" / "private" / "episodes").glob("*.json"))
    assert len(public_files) == len(private_files) == 2
    assert all(path.stem.startswith("challenge-") for path in public_files)
    for path in public_files:
        raw = path.read_bytes()
        payload = json.loads(raw)
        assert raw == public_challenge_bytes(payload)
        assert path.name == f"challenge-{public_challenge_id(payload)}.json"
        assert len(payload["train"]) == 3 and len(payload["test"]) == 4
        assert all(set(pair) == {"input"} for pair in payload["test"])
