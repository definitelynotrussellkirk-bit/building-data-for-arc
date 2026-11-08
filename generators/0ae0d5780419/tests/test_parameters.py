"""Focused tests for the native transform-matching parametric family."""
from __future__ import annotations

from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "0ae0d5780419"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
POLICIES = ("first_exact", "last_exact", "first_shape")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("panel_match_parametric_prototype_tests", HOME / "prototype.py")
ADAPTER = _load("panel_match_parametric_adapter_tests", HOME / "adapter.py")


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl")
        .read_text()
        .splitlines()
    ]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == TASK_ID and row.get("program_solution")
    }
    assert len(programs) == 1
    return next(iter(programs))


def _pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _survivors(demos):
    return [
        policy
        for policy in POLICIES
        if all(
            PROTOTYPE.apply_policy(pair["input"], policy) == pair["output"]
            for pair in demos
        )
    ]


def test_promotion_contract_and_exact_canonical_default():
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"match_policy": list(POLICIES)},
        "default": {"match_policy": "first_exact"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/last_exact.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/first_shape.rkt",
        ],
    }
    canonical = _canonical_program()
    assert ADAPTER.program({"match_policy": "first_exact"}) == canonical
    assert PROTOTYPE.rule_text("first_exact") == canonical
    assert tuple(PROTOTYPE.MATCH_POLICIES) == POLICIES


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_inputs_are_matched_across_settings_and_first_two_demos_separate_them(seed):
    episodes = {
        policy: ADAPTER.generate(seed, {"match_policy": policy}, demos=2, queries=4)
        for policy in POLICIES
    }
    baseline_inputs = _inputs(episodes["first_exact"])
    assert len({json.dumps(grid) for grid in baseline_inputs}) == 6
    for policy, episode in episodes.items():
        assert _inputs(episode) == baseline_inputs
        assert episode["program_solution"] == ADAPTER.program({"match_policy": policy})
        assert all(
            pair["output"] == PROTOTYPE.apply_policy(pair["input"], policy)
            for pair in _pairs(episode)
        )

    first = {policy: episodes[policy]["train"][0]["output"] for policy in POLICIES}
    second = {policy: episodes[policy]["train"][1]["output"] for policy in POLICIES}
    assert first["first_exact"] == first["first_shape"] != first["last_exact"]
    assert second["first_exact"] == second["last_exact"] != second["first_shape"]


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
@pytest.mark.parametrize("policy", POLICIES)
def test_two_to_six_demonstrations_identify_the_setting(seed, demos, policy):
    episode = ADAPTER.generate(seed, {"match_policy": policy}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert _survivors(episode["train"]) == [policy]
    assert len({json.dumps(grid) for grid in _inputs(episode)}) == demos + 4


@pytest.mark.parametrize("policy", POLICIES)
def test_one_query_is_the_same_first_turn_as_four_queries(policy):
    settings = {"match_policy": policy}
    one = ADAPTER.generate(431, settings, demos=3, queries=1)
    four = ADAPTER.generate(431, settings, demos=3, queries=4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert PROTOTYPE.public_projection(one) == {
        "train": one["train"],
        "test": [{"input": one["test"][0]["input"]}],
    }


def test_four_query_curriculum_reaches_lawful_maximum_and_has_substantive_content():
    episode = ADAPTER.generate(
        20261024, {"match_policy": "last_exact"}, demos=3, queries=4
    )
    shapes = [(len(p["input"]), len(p["input"][0])) for p in episode["test"]]
    assert shapes == [(8, 17), (14, 23), (24, 29), (30, 29)]

    large = episode["test"][-1]["input"]
    counts = Counter(value for row in large for value in row)
    assert counts[5] == 60
    assert sum(value != 0 for row in large for value in row) >= 260
    facts = PROTOTYPE.analyse(large)
    assert facts["panel_h"] == 30 and facts["panel_n"] == 9
    assert facts["exact_matches"] == (1, 3)
    assert facts["bboxes"][0][0] <= 1 and facts["bboxes"][0][2] >= 28
    assert facts["bboxes"][2][0] <= 1 and facts["bboxes"][2][2] >= 28


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("policy", POLICIES)
def test_bounded_self_audit_refutes_each_declared_plausible_rival(seed, policy):
    episode = ADAPTER.generate(seed, {"match_policy": policy}, demos=2, queries=4)
    rivals = PROTOTYPE.audit_rivals(policy)
    assert set(rivals) == {
        "other_finite_policy_1",
        "other_finite_policy_2",
        "last_shape_match",
        "rotate_cw_on_no_exact_match",
        "transform_padded_c_without_crop",
        "always_identity",
        "always_rotate_cw",
    }
    for name, rival in rivals.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["train"]), (
            seed,
            policy,
            name,
            "demo",
        )
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["test"]), (
            seed,
            policy,
            name,
            "query",
        )


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"match_policy": "unknown"},
        {"match_policy": True},
        {"match_policy": "first_exact", "extra": 1},
    ],
)
def test_invalid_settings_reject(settings):
    with pytest.raises(ValueError):
        ADAPTER.program(settings)
    with pytest.raises(ValueError):
        ADAPTER.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4),
        (-1, 3, 4),
        (0, True, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 3, True),
        (0, 3, 0),
        (0, 3, 5),
    ],
)
def test_invalid_count_and_seed_controls_reject(seed, demos, queries):
    with pytest.raises(ValueError):
        ADAPTER.generate(seed, {"match_policy": "first_exact"}, demos=demos, queries=queries)


def test_public_identifier_depends_only_on_visible_projection():
    episode = PROTOTYPE.generate_episode(77, match_policy="first_shape", demos=3, queries=4)
    public = PROTOTYPE.public_projection(episode)
    identifier = PROTOTYPE.public_challenge_id(episode)
    altered = copy.deepcopy(episode)
    altered["private_note"] = "changed"
    altered["settings"] = {"match_policy": "last_exact"}
    for pair in altered["test"]:
        pair["output"] = [[9]]
    assert PROTOTYPE.public_projection(altered) == public
    assert PROTOTYPE.public_challenge_id(altered) == identifier
