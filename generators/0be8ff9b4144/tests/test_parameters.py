"""Focused tests for the native intersection-policy parametric family."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "0be8ff9b4144"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("intersection_policy_prototype_tests", HOME / "prototype.py")
ADAPTER = _load("intersection_policy_adapter_tests", HOME / "adapter.py")
POLICIES = ("all", "same_parity", "opposite_parity")


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


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


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
        "parameters": {"intersection_policy": list(POLICIES)},
        "default": {"intersection_policy": "all"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/same_parity.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/opposite_parity.rkt",
        ],
    }
    assert ADAPTER.program({"intersection_policy": "all"}) == _canonical_program()
    assert PROTOTYPE.rule_text("all") == _canonical_program()
    assert tuple(PROTOTYPE.POLICIES) == POLICIES


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_inputs_are_matched_across_settings_and_outputs_change(seed):
    episodes = {
        policy: ADAPTER.generate(
            seed, {"intersection_policy": policy}, demos=3, queries=4
        )
        for policy in POLICIES
    }
    baseline_inputs = _inputs(episodes["all"])
    assert len({json.dumps(grid) for grid in baseline_inputs}) == 7
    for policy, episode in episodes.items():
        assert _inputs(episode) == baseline_inputs
        assert episode["program_solution"] == ADAPTER.program(
            {"intersection_policy": policy}
        )
        assert all(
            pair["output"] == PROTOTYPE.apply_policy(pair["input"], policy)
            for pair in episode["train"] + episode["test"]
        )
    for pair_index in range(len(baseline_inputs)):
        outputs = {
            json.dumps(
                (episodes[policy]["train"] + episodes[policy]["test"])[pair_index][
                    "output"
                ]
            )
            for policy in POLICIES
        }
        assert len(outputs) == len(POLICIES)


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
@pytest.mark.parametrize("policy", POLICIES)
def test_two_to_six_demonstrations_identify_the_setting(seed, demos, policy):
    episode = ADAPTER.generate(
        seed, {"intersection_policy": policy}, demos=demos, queries=4
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert _survivors(episode["train"]) == [policy]
    assert len({json.dumps(grid) for grid in _inputs(episode)}) == demos + 4


@pytest.mark.parametrize("policy", POLICIES)
def test_one_query_is_the_same_first_turn_as_four_queries(policy):
    settings = {"intersection_policy": policy}
    one = ADAPTER.generate(431, settings, demos=3, queries=1)
    four = ADAPTER.generate(431, settings, demos=3, queries=4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert PROTOTYPE.public_projection(one) == {
        "train": one["train"],
        "test": [{"input": one["test"][0]["input"]}],
    }


def test_four_query_curriculum_has_wide_tall_and_substantive_30x30_stress():
    episode = ADAPTER.generate(
        20261024, {"intersection_policy": "same_parity"}, demos=3, queries=4
    )
    shapes = [
        (len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]
    ]
    assert shapes == [(12, 14), (18, 25), (25, 18), (30, 30)]
    grid = episode["test"][-1]["input"]
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    non_background = sum(value != background for row in grid for value in row)
    rows, cols = PROTOTYPE.active_axes(grid)
    assert len(rows) == 6 and len(cols) == 6
    assert {1, 29} <= set(rows)
    assert {1, 29} <= set(cols)
    assert non_background >= 120
    assert any(
        grid[row][col] not in (background, 5) for row in rows for col in cols
    )
    assert all(value != 5 for row in grid for value in row)


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("policy", POLICIES)
def test_bounded_self_audit_refutes_each_declared_plausible_rival(seed, policy):
    episode = ADAPTER.generate(
        seed, {"intersection_policy": policy}, demos=2, queries=4
    )
    rivals = PROTOTYPE.audit_rivals(policy)
    assert set(rivals) == {
        "absolute_coordinate_parity",
        "rank_diagonal_only",
        "single_axis_rank_parity",
        "any_nonbackground_header",
        "preserve_occupied_selected_cells",
    }
    for name, rival in rivals.items():
        assert any(
            rival(pair["input"]) != pair["output"] for pair in episode["train"]
        ), (seed, policy, name)
        assert any(
            rival(pair["input"]) != pair["output"] for pair in episode["test"]
        ), (seed, policy, name)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"intersection_policy": "unknown"},
        {"intersection_policy": True},
        {"intersection_policy": "all", "extra": 1},
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
        ADAPTER.generate(
            seed, {"intersection_policy": "all"}, demos=demos, queries=queries
        )


def test_public_identifier_depends_only_on_visible_projection():
    episode = PROTOTYPE.generate_episode(
        77, intersection_policy="same_parity", demos=3, queries=4
    )
    public = PROTOTYPE.public_projection(episode)
    identifier = PROTOTYPE.public_challenge_id(episode)
    altered = dict(episode)
    altered["private_note"] = "changed"
    altered["settings"] = {"intersection_policy": "opposite_parity"}
    for pair in altered["test"]:
        pair["output"] = [[9]]
    assert PROTOTYPE.public_projection(altered) == public
    assert PROTOTYPE.public_challenge_id(altered) == identifier
