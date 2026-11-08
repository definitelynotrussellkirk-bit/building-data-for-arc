"""Native promotion boundaries, finite teaching rivals, and visible-byte IDs."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]


def load(name):
    path = HOME / "workspace/parametric" / (name + ".py")
    spec = importlib.util.spec_from_file_location("cf5ccd73cfe5_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load("orientation")


@pytest.fixture(scope="module")
def bridge():
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as live:
        yield live


@pytest.fixture(scope="module")
def lessons(p, bridge):
    return {s: p.build_episode(17, bridge, s, demos=3, queries=4) for s in p.SETTINGS}


def test_public_identity_ignores_seed_and_all_private_fields(p):
    visible = {"train": [{"input": [[0, 1]], "output": [[1, 0]]}],
               "test": [{"input": [[2, 0]]}]}
    hidden = dict(visible, seed=99, parameters={"orientation": "flip_lr"},
                  test=[{"input": [[2, 0]], "output": [[9]]}])
    expected = public_challenge_id(visible) + ".json"
    assert p.public_filename(17, visible) == expected
    assert p.public_filename(999, hidden) == expected


def test_native_adapter_reuses_exact_programs_and_rejects_invalid_settings(p):
    adapter = load("adapter")
    for setting in p.SETTINGS:
        assert adapter.program({"orientation": setting}) == p.program(setting)
    for settings in ({}, {"orientation": True}, {"orientation": "rot90"},
                     {"orientation": "identity", "extra": None}, None):
        with pytest.raises(ValueError):
            adapter.program(settings)


def test_four_query_labels_are_distinct_and_inputs_are_matched_across_settings(p, lessons):
    input_lists = []
    for setting, (public, private) in lessons.items():
        assert (len(public["train"]), len(public["test"])) == (3, 4)
        inputs = [pair["input"] for pair in public["train"] + public["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == 7
        input_lists.append(inputs)
        assert len(private["query_outputs"]) == 4
        assert private["parameters"] == {"orientation": setting}
        assert all(item["demo_mismatches"] for item in private["rivals"].values())
        assert all(len(item["query_differs"]) == 4 for item in private["rivals"].values())
        assert private["self_review"]["ambiguous_rivals"] == []
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in public["test"])
    assert all(inputs == input_lists[0] for inputs in input_lists)


def test_first_turn_is_identical_for_one_query_and_four(p, bridge, lessons):
    public, private = p.build_episode(17, bridge, "identity", demos=3, queries=1)
    multi = lessons["identity"][0]
    assert public_challenge_bytes(public) == public_challenge_bytes(
        {"train": multi["train"], "test": multi["test"][:1]})
    assert private["query_outputs"][0] == lessons["identity"][1]["query_outputs"][0]


@pytest.mark.parametrize("demos", [2, 6])
def test_supported_demo_boundaries_keep_four_queries(p, bridge, demos):
    public, private = p.build_episode(5, bridge, "rot180", demos=demos, queries=4)
    assert (len(public["train"]), len(public["test"])) == (demos, 4)
    assert private["self_review"]["ambiguous_rivals"] == []


@pytest.mark.parametrize("kwargs", [
    {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
    {"queries": 0}, {"queries": 5}, {"queries": False}, {"queries": "4"},
    {"max_attempts": -1}, {"max_attempts": True},
])
def test_bad_counts_fail_before_execution(p, kwargs):
    with pytest.raises(ValueError):
        p.build_episode(17, None, "identity", **kwargs)


@pytest.mark.parametrize("seed", [-1, True, 1.0, "1", 2**63])
def test_native_seed_domain_is_strict(p, seed):
    with pytest.raises(ValueError):
        p.build_episode(seed, None, "identity")


def test_stress_content_scales_with_canvas_and_contacts_boundaries(p, lessons):
    public, private = lessons["identity"]
    facts = [p.generator()._analyze(pair["input"])[0] for pair in public["test"]]
    assert (facts[0]["grid_h"], facts[0]["grid_w"]) == (8, 8)
    large = facts[-1]
    assert (large["grid_h"], large["grid_w"]) == (30, 30)
    assert (large["frame_h"], large["frame_w"]) == (26, 26)
    assert sorted((large["scale_h"], large["scale_w"])) == [4, 8]
    assert len(private["query_outputs"][-1]) == 26
    occupied = [(r, c) for r, row in enumerate(public["test"][-1]["input"])
                for c, v in enumerate(row) if v]
    assert {r for r, _ in occupied} >= {0, 29}
    assert {c for _, c in occupied} >= {0, 29}


def test_native_adapter_independent_counts(p):
    adapter = load("adapter")
    result = adapter.generate(19, {"orientation": "flip_ud"}, 2, 4)
    assert len(result["train"]) == 2 and len(result["test"]) == 4
    assert result["program_solution"] == p.program("flip_ud")
    assert all(set(pair) == {"input", "output"} for pair in result["test"])


def test_writer_receipt_binds_native_contract_and_visible_projection(p):
    bound = p.source_hashes()
    assert set(("generators/cf5ccd73cfe5/tests/test_native_orientation.py",
                "generators/cf5ccd73cfe5/workspace/parametric/promotion.json",
                "shared/runtime/reviewer_support.py")) <= set(bound)
