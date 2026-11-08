from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d48317a7c7c8"


def load_module(name: str):
    path = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / f"{name}.py"
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


def execute(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    bridge.define_grid("g", grid)
    body = program[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    return bridge.eval_text(expression)


def inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def public_projection(episode):
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def test_default_program_is_exact_canonical_bytes():
    adapter = load_module("adapter")
    assert adapter.program({"target_length": 3}) == canonical_program()


def test_counts_inputs_and_settings_are_independent_with_substantive_30x30_query():
    adapter = load_module("adapter")
    short3 = adapter.generate(17, {"target_length": 3}, demos=2, queries=4)
    short4 = adapter.generate(17, {"target_length": 4}, demos=2, queries=4)
    long3 = adapter.generate(91, {"target_length": 3}, demos=6, queries=1)

    assert set(short3) == {"train", "test", "program_solution"}
    assert (len(short3["train"]), len(short3["test"])) == (2, 4)
    assert (len(long3["train"]), len(long3["test"])) == (6, 1)
    assert inputs(short3) == inputs(short4)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs(short3)}) == 6
    assert len(short3["test"][-1]["input"]) == 30
    assert len(short3["test"][-1]["input"][0]) == 30
    changed = sum(
        a != b
        for row_a, row_b in zip(short3["test"][-1]["input"], short3["test"][-1]["output"])
        for a, b in zip(row_a, row_b)
    )
    assert changed >= 8


def test_two_demonstrations_distinguish_both_target_lengths_before_queries():
    adapter = load_module("adapter")
    episode3 = adapter.generate(23, {"target_length": 3}, demos=2, queries=4)
    episode4 = adapter.generate(23, {"target_length": 4}, demos=2, queries=4)
    assert all(a["output"] != b["output"] for a, b in zip(episode3["train"], episode4["train"]))
    assert all(a["output"] != b["output"] for a, b in zip(episode3["test"], episode4["test"]))


def test_public_projection_omits_private_data_and_id_ignores_query_answer():
    adapter = load_module("adapter")
    episode = adapter.generate(31, {"target_length": 4}, demos=3, queries=4)
    public = public_projection(episode)
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    payload = json.dumps(public, sort_keys=True)
    assert "target_length" not in payload and "rule!" not in payload

    before = public_challenge_id(public)
    mutated = deepcopy(episode)
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(public_projection(mutated)) == before


def test_invalid_settings_and_count_boundaries_are_rejected():
    adapter = load_module("adapter")
    for settings in ({"target_length": 2}, {"target_length": True}, {"other": 3}):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, demos=3, queries=4)
    for demos, queries in ((1, 4), (7, 4), (3, 0), (3, 5)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"target_length": 3}, demos=demos, queries=queries)


def test_racket_matches_python_labels_for_both_settings():
    adapter = load_module("adapter")
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for target_length in (3, 4):
            episode = adapter.generate(7, {"target_length": target_length}, demos=2, queries=1)
            for pair in episode["train"] + episode["test"]:
                assert execute(bridge, episode["program_solution"], pair["input"]) == pair["output"]


def test_materialized_evidence_is_four_query_racket_backed_and_publicly_opaque(tmp_path):
    prototype = load_module("prototype")
    report = prototype.materialize(tmp_path / "evidence", base_seed=41)
    assert report["complete_episodes"] == 2
    assert report["pairs_per_episode"] == {"train": 3, "test": 4}
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
        serialized = json.dumps(payload, sort_keys=True)
        assert "target_length" not in serialized and "rule!" not in serialized
