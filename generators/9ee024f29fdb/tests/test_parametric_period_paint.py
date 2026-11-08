"""Native-contract checks for episode-level period and paint variants."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "9ee024f29fdb"
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


def test_adapter_default_is_exact_canonical_and_declares_bounded_contract():
    adapter = load_module("adapter")
    assert adapter.program({"period": 4, "paint_color": 2}) == canonical_program()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["parameters"] == {"period": [3, 4, 5], "paint_color": [2, 4]}
    assert contract["default"] == {"period": 4, "paint_color": 2}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_counts_prefixes_and_inputs_are_setting_independent_with_30x30_stress():
    adapter = load_module("adapter")
    a = adapter.generate(17, {"period": 3, "paint_color": 2}, demos=2, queries=4)
    b = adapter.generate(17, {"period": 5, "paint_color": 4}, demos=2, queries=4)
    long = adapter.generate(91, {"period": 4, "paint_color": 2}, demos=6, queries=1)
    one = adapter.generate(17, {"period": 3, "paint_color": 2}, demos=2, queries=1)

    assert set(a) == {"train", "test", "program_solution"}
    assert (len(a["train"]), len(a["test"])) == (2, 4)
    assert (len(long["train"]), len(long["test"])) == (6, 1)
    assert all_inputs(a) == all_inputs(b)
    assert one["test"][0]["input"] == a["test"][0]["input"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(a)}) == 6
    stress = a["test"][-1]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    changed = sum(
        x != y
        for row_x, row_y in zip(stress["input"], stress["output"])
        for x, y in zip(row_x, row_y)
    )
    assert changed >= 500


def test_two_demonstrations_identify_every_declared_setting_and_all_queries_differ():
    adapter = load_module("adapter")
    episodes = {
        (period, color): adapter.generate(
            23, {"period": period, "paint_color": color}, demos=2, queries=4
        )
        for period in (3, 4, 5)
        for color in (2, 4)
    }
    for chosen, episode in episodes.items():
        survivors = []
        for candidate, rival in episodes.items():
            if all(
                a["output"] == b["output"]
                for a, b in zip(episode["train"], rival["train"])
            ):
                survivors.append(candidate)
            if candidate != chosen:
                assert all(
                    a["output"] != b["output"]
                    for a, b in zip(episode["test"], rival["test"])
                )
        assert survivors == [chosen]


def test_public_projection_omits_private_data_and_id_ignores_query_answers():
    adapter = load_module("adapter")
    episode = adapter.generate(31, {"period": 5, "paint_color": 4}, demos=3, queries=4)
    public = public_projection(episode)
    text = json.dumps(public, sort_keys=True)
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "paint_color" not in text and "period" not in text and "rule!" not in text
    before = public_challenge_id(public)
    mutated = deepcopy(episode)
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(public_projection(mutated)) == before


def test_invalid_settings_seed_and_count_boundaries_are_rejected():
    adapter = load_module("adapter")
    bad_settings = (
        {"period": 2, "paint_color": 2},
        {"period": 4, "paint_color": 8},
        {"period": True, "paint_color": 2},
        {"period": 4, "paint_color": 2, "other": 1},
    )
    for settings in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, demos=3, queries=4)
    for seed in (True, -1, 1.5):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"period": 4, "paint_color": 2}, demos=3, queries=4)
    for demos, queries in ((1, 4), (7, 4), (3, 0), (3, 5)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"period": 4, "paint_color": 2}, demos=demos, queries=queries)


def test_materialized_gallery_executes_six_settings_and_uses_opaque_public_names(tmp_path):
    proto = load_module("prototype")
    report = proto.materialize(tmp_path / "gallery", base_seed=20261019)
    assert report["complete_episodes"] == 6
    assert report["pairs_per_episode"] == {"train": 3, "test": 4}
    assert report["racket_rule_applications"] == 42
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    assert report["all_demo_only_teaching_checks_pass"] is True
    assert report["max_query_shape"] == [30, 30]
    public_files = sorted((tmp_path / "gallery" / "public").glob("*.json"))
    private_files = sorted((tmp_path / "gallery" / "private" / "episodes").glob("*.json"))
    assert len(public_files) == len(private_files) == 6
    assert all(path.stem.startswith("challenge-") for path in public_files)
    for path in public_files:
        raw = path.read_bytes()
        payload = json.loads(raw)
        assert raw == public_challenge_bytes(payload)
        assert path.name == f"challenge-{public_challenge_id(payload)}.json"
        assert len(payload["train"]) == 3 and len(payload["test"]) == 4
        assert all(set(pair) == {"input"} for pair in payload["test"])
