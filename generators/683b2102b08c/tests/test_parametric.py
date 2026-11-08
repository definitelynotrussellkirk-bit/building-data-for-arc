"""Focused adapter regression tests; protected label replay is in verify.py."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1]
WORK = HOME / "workspace" / "parametric"


def module(name):
    path = WORK / (name + ".py")
    assert path.is_file(), "native parametric implementation is missing"
    spec = importlib.util.spec_from_file_location("test_683b2102b08c_" + name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_default_preserves_exact_approved_racket_source():
    adapter = module("adapter")
    canonical = adapter.program({"attach_side": "left"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "f88a69caee632bd737dfddf55a84950195f8f79138a9eebc4225393f995e994e"
    )
    assert adapter.program({"attach_side": "right"}) != canonical


def test_counts_setting_independence_and_first_query_prefix():
    adapter = module("adapter")
    for seed in (0, 17, 29):
        for demos in (2, 3, 6):
            left = adapter.generate(seed, {"attach_side": "left"}, demos, 4)
            right = adapter.generate(seed, {"attach_side": "right"}, demos, 4)
            assert len(left["train"]) == demos
            assert len(left["test"]) == 4
            assert inputs(left, "train") == inputs(right, "train")
            assert inputs(left, "test") == inputs(right, "test")
            one = adapter.generate(seed, {"attach_side": "left"}, demos, 1)
            assert one["train"] == left["train"]
            assert one["test"] == left["test"][:1]
            all_inputs = inputs(left, "train") + inputs(left, "test")
            assert len({json.dumps(g) for g in all_inputs}) == demos + 4
        two = adapter.generate(seed, {"attach_side": "left"}, 2, 4)
        six = adapter.generate(seed, {"attach_side": "left"}, 6, 4)
        assert two["train"] == six["train"][:2]
        assert two["test"] == six["test"]


def test_two_demos_teach_whole_color_roles_centering_and_overwrite():
    adapter, prototype = module("adapter"), module("prototype")
    for seed in (0, 17, 29):
        lesson = adapter.generate(seed, {"attach_side": "left"}, 2, 4)
        a, b = [prototype.analyze(pair["input"]) for pair in lesson["train"]]
        assert a["main_component_count"] > 1
        assert a["main_count"] > a["secondary_count"]
        assert a["main_height"] * a["main_width"] < a["secondary_height"] * a["secondary_width"]
        assert a["collision_count"] > 0
        assert (a["main_height"] - a["secondary_height"]) % 2 == 1
        assert a["target_secondary_r1"] > 0
        assert b["secondary_component_count"] > 1
        assert a["main_color"] == b["secondary_color"]
        assert a["secondary_color"] == b["main_color"]
        assert a["secondary_bbox"][1] < a["main_bbox"][1]
        assert b["secondary_bbox"][1] > b["main_bbox"][3]


def test_minimum_and_dense_maximum_queries_are_real_content():
    adapter, prototype = module("adapter"), module("prototype")
    episode = adapter.generate(17, {"attach_side": "right"}, 3, 4)
    first, last = inputs(episode, "test")[0], inputs(episode, "test")[-1]
    assert (len(first), len(first[0])) == (8, 8)
    assert (len(last), len(last[0])) == (30, 30)
    facts = prototype.analyze(last)
    assert facts["main_height"] >= 12
    assert facts["main_width"] >= 8
    assert facts["secondary_width"] >= 8
    assert facts["main_count"] + facts["secondary_count"] >= 100
    assert facts["main_component_count"] >= 2
    for side in ("left", "right"):
        for pair in adapter.generate(17, {"attach_side": side}, 3, 4)["test"]:
            assert len(pair["input"]) == len(pair["output"])
            assert all(type(c) is int and 0 <= c <= 9 for row in pair["output"] for c in row)


def test_two_demo_core_rejects_tallest_mask_tie_shortcut():
    adapter, prototype = module("adapter"), module("prototype")
    lesson = adapter.generate(8, {"attach_side": "left"}, 2, 4)
    witnesses = []
    for pair in lesson["train"]:
        f = prototype.analyze(pair["input"])
        first_color = next(c for row in pair["input"][f["line_row"] + 1:] for c in row if c not in (4, 7))
        witnesses.append(f["main_height"] == f["secondary_height"] and first_color == f["secondary_color"])
    assert any(witnesses), "tallest-mask selector still fits all minimum-count demonstrations"


def test_left_claims_equal_unchanged_canonical_mirror():
    adapter, prototype = module("adapter"), module("prototype")
    episode = adapter.generate(29, {"attach_side": "left"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.analyze(pair["input"])["output"]


def test_invalid_requests_fail_before_sampling():
    adapter = module("adapter")
    for settings in ({}, {"attach_side": "up"}, {"attach_side": True}, {"attach_side": "left", "x": 1}, None):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for seed, demos, queries in ((True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, True)):
        with pytest.raises(ValueError):
            adapter.generate(seed, {"attach_side": "left"}, demos, queries)


def test_seed_purity_determinism_and_fresh_returns():
    adapter = module("adapter")
    random.seed(82391)
    before = random.getstate()
    original = adapter.generate(8, {"attach_side": "right"}, 3, 4)
    saved = copy.deepcopy(original)
    assert before == random.getstate()
    original["train"][0]["input"][0][0] = 9
    assert adapter.generate(8, {"attach_side": "right"}, 3, 4) == saved
