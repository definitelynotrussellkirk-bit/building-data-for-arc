"""Contract tests for the native exact-match bridge family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("_test_6145142974ff_prototype", "prototype.py")
adapter = _load("_test_6145142974ff_adapter", "adapter.py")


@pytest.mark.parametrize("finish", ["canonical", "bridge_matches"])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_generate_honors_independent_counts_and_is_deterministic(finish, demos, queries):
    settings = {"finish": finish}
    episode = prototype.generate(17, settings, demos=demos, queries=queries)
    assert episode == prototype.generate(17, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == prototype.program(settings)
    visible = [pair["input"] for pair in episode["train"] + episode["test"]]
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in visible]
    assert len(frozen) == len(set(frozen))
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.predict(pair["input"], finish)


def test_settings_share_inputs_and_every_demonstration_identifies_the_rule():
    direct = prototype.generate(23, {"finish": "canonical"}, demos=2, queries=4)
    bridge = prototype.generate(23, {"finish": "bridge_matches"}, demos=2, queries=4)
    assert [p["input"] for p in direct["train"] + direct["test"]] == [
        p["input"] for p in bridge["train"] + bridge["test"]
    ]
    assert all(a["output"] != b["output"] for a, b in zip(direct["train"], bridge["train"]))
    for finish, episode in (("canonical", direct), ("bridge_matches", bridge)):
        certificate = prototype.teaching_certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert certificate["survivors"] == [finish]
        assert certificate["harmful_query_survivors"] == []


def test_demo_and_query_prefixes_do_not_depend_on_requested_counts():
    for finish in prototype.FINISHES:
        settings = {"finish": finish}
        full = prototype.generate(91, settings, demos=6, queries=4)
        short = prototype.generate(91, settings, demos=2, queries=1)
        assert full["train"][:2] == short["train"]
        assert full["test"][:1] == short["test"]


def test_fourth_query_is_substantive_30_by_30_stress():
    episode = prototype.generate(5, {"finish": "bridge_matches"}, demos=3, queries=4)
    grid = episode["test"][3]["input"]
    obs = prototype.observe(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert obs["matching_components"] >= 6
    assert obs["distractor_components"] >= 4
    assert obs["colored_cells"] >= 60
    assert obs["boundary_contacts"] >= 1
    assert prototype.predict(grid, "bridge_matches") != prototype.predict(grid, "canonical")


def test_public_turn_has_one_masked_query_and_matches_single_query_use():
    episode = prototype.generate(12, {"finish": "bridge_matches"}, demos=3, queries=4)
    single = prototype.generate(12, {"finish": "bridge_matches"}, demos=3, queries=1)
    first = json.loads(prototype.public_turn_bytes(episode, 0))
    first_single = json.loads(prototype.public_turn_bytes(single, 0))
    assert first == first_single
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert "settings" not in first and "program_solution" not in first


def test_causal_witness_uses_stage_a_and_wrong_intermediate_changes_final():
    witness = prototype.causal_witness(seed=0)
    assert witness["step_a"] == "select exact color-3 template matches and recolor them with the majority marker color"
    assert witness["step_b"] == "connect the Stage-A components in reading order with deterministic horizontal-then-vertical bridges"
    assert witness["stage_a_output"] != witness["wrong_stage_a_output"]
    assert witness["final_output"] != witness["wrong_final_output"]
    assert witness["changed_cells"] > 0


def test_adapter_is_thin_and_returns_only_native_episode_fields():
    settings = {"finish": "canonical"}
    episode = adapter.generate(3, settings, demos=3, queries=4)
    assert set(episode) == {"train", "test", "program_solution"}
    assert adapter.program(settings) == prototype.program(settings)


def test_canonical_program_is_exact_selected_source():
    from arcpuzzles import Catalog

    task = Catalog(HOME.parents[1]).get(prototype.TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in task["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    expected = next(iter(programs))
    actual = prototype.program({"finish": "canonical"})
    assert actual == expected
    assert hashlib.sha256(actual.encode()).hexdigest() == prototype.CANONICAL_PROGRAM_SHA256


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"finish": "unknown"}, 3, 4),
        ({"finish": True}, 3, 4),
        ({"finish": "canonical", "extra": 1}, 3, 4),
        ({"finish": "canonical"}, 1, 4),
        ({"finish": "canonical"}, 7, 4),
        ({"finish": "canonical"}, 3, 0),
        ({"finish": "canonical"}, 3, 5),
        ({"finish": "canonical"}, True, 4),
    ],
)
def test_invalid_contract_requests_fail_loudly(settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, settings, demos=demos, queries=queries)
