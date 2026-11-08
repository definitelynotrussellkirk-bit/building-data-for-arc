from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "9a1459fe40d0"
TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
ADAPTER_PATH = TASK_DIR / "workspace" / "parametric" / "adapter.py"
PROMOTION_PATH = TASK_DIR / "workspace" / "parametric" / "promotion.json"
AUDIT_PATH = TASK_DIR / "workspace" / "parametric" / "audit.py"
POLICIES = ("project_right", "occupied_side")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]["program_solution"]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _fixture():
    grid = [[0 for _ in range(9)] for _ in range(5)]
    for row in range(5):
        grid[row][4] = 8
    grid[0][0] = 1                  # left-only, mirror at 8
    grid[1][7] = 2                  # right-only, partner at 1
    grid[2][2] = grid[2][6] = 3    # both same
    grid[3][3], grid[3][5] = 4, 5  # both different
    return grid


def test_prototype_exports_exact_default_and_distinct_alternate_program():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_prototype")

    for name in (
        "canonical_program",
        "program_for",
        "apply_policy",
        "pair_facts",
        "episode_inputs",
        "generate_episode",
        "public_turn",
    ):
        assert callable(getattr(prototype, name))
    assert prototype.POLICIES == POLICIES
    assert prototype.DEFAULT_POLICY == "project_right"
    assert prototype.canonical_program() == _canonical_source()
    assert prototype.program_for("project_right") == _canonical_source()
    assert prototype.program_for("occupied_side") != _canonical_source()
    assert prototype.program_for("occupied_side").startswith("(rule!")


def test_occupied_side_policy_consumes_directed_xor_intermediate():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_fixture")
    grid = _fixture()
    facts = prototype.pair_facts(grid)

    assert facts["bar_col"] == 4
    assert facts["state_counts"] == {
        "both_different": 1,
        "both_empty": 16,
        "both_same": 1,
        "left_only": 1,
        "right_only": 1,
    }
    assert [(row["state"], row["occupied_col"]) for row in facts["mismatches"]] == [
        ("left_only", 0),
        ("right_only", 7),
    ]

    projected = prototype.apply_policy(grid, "project_right")
    occupied = prototype.apply_policy(grid, "occupied_side")
    assert projected != occupied
    assert projected[0][8] == 7 and projected[0][0] == 0
    assert occupied[0][0] == 7 and occupied[0][8] == 0
    assert projected[1][7] == occupied[1][7] == 7
    assert all(projected[2][col] == occupied[2][col] == 0 for col in range(9))
    assert all(projected[3][col] == occupied[3][col] == 0 for col in range(9))


def test_counts_are_independent_prefix_stable_and_queries_reach_lawful_maximum():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_counts")
    minimum = prototype.episode_inputs(7, demos=2, queries=1)
    maximum = prototype.episode_inputs(7, demos=6, queries=4)

    assert len(minimum) == 3
    assert len(maximum) == 10
    assert minimum == maximum[:2] + [maximum[6]]
    assert len({_freeze(grid) for grid in maximum}) == 10
    assert [(len(g), len(g[0])) for g in maximum[6:]] == [
        (14, 21),
        (20, 25),
        (26, 27),
        (30, 29),
    ]
    large = maximum[-1]
    assert sum(cell != 0 for row in large for cell in row) >= 150


def test_minimum_demos_expose_both_xor_directions_and_matched_controls():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_teaching")
    first, second = prototype.episode_inputs(11, demos=2, queries=1)[:2]

    for grid in (first, second):
        facts = prototype.pair_facts(grid)
        counts = facts["state_counts"]
        assert counts["left_only"] >= 3
        assert counts["right_only"] >= 3
        assert counts["both_same"] >= 2
        assert counts["both_different"] >= 2
        assert prototype.apply_policy(grid, "project_right") != prototype.apply_policy(
            grid, "occupied_side"
        )


def test_two_demos_identify_each_policy_and_inputs_are_setting_matched():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_identification")
    episodes = {
        policy: prototype.generate_episode(29, policy, demos=2, queries=4)
        for policy in POLICIES
    }
    assert [p["input"] for p in episodes[POLICIES[0]]["train"] + episodes[POLICIES[0]]["test"]] == [
        p["input"] for p in episodes[POLICIES[1]]["train"] + episodes[POLICIES[1]]["test"]
    ]

    for selected, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        survivors = [
            candidate
            for candidate in POLICIES
            if all(
                prototype.apply_policy(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [selected]
        assert all(
            pair["output"] == prototype.apply_policy(pair["input"], selected)
            for pair in episode["train"] + episode["test"]
        )


def test_seed_policy_and_count_validation_is_strict():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_validation")

    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(bad_seed, demos=2, queries=4)
    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=bad_demos, queries=4)
    for bad_queries in (False, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=2, queries=bad_queries)
    for bad_policy in (None, True, "", "mark_both", 0):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, bad_policy, demos=2, queries=4)


def test_protected_racket_matches_python_on_demo_and_maximum_query():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _load(PROTOTYPE_PATH, "mark_policy_racket")
    inputs = prototype.episode_inputs(41, demos=2, queries=4)
    witnesses = (inputs[0], inputs[-1])
    assert [(len(g), len(g[0])) for g in witnesses] == [(10, 15), (30, 29)]

    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        for index, grid in enumerate(witnesses):
            name = f"g{index}"
            bridge.define_grid(name, grid)
            for policy in POLICIES:
                actual = bridge.eval_text(f"({wrap_rule(prototype.program_for(policy))} {name})")
                assert actual == prototype.apply_policy(grid, policy)
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True


def test_native_adapter_and_contract_have_exact_bounded_surface():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_contract_prototype")
    adapter = _load(ADAPTER_PATH, "mark_policy_contract_adapter")
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/9a1459fe40d0/workspace/parametric/adapter.py",
        "parameters": {"mark_policy": list(POLICIES)},
        "default": {"mark_policy": "project_right"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": ["generators/9a1459fe40d0/workspace/parametric/canonical.rkt"],
    }
    for policy in POLICIES:
        settings = {"mark_policy": policy}
        assert adapter.program(settings) == prototype.program_for(policy)
        assert adapter.generate(53, settings, 2, 4) == prototype.generate_episode(
            53, policy, 2, 4
        )


def test_adapter_rejects_wrong_setting_shapes_and_values():
    adapter = _load(ADAPTER_PATH, "mark_policy_adapter_validation")

    for bad in (None, [], {}, {"mark_policy": "project_right", "extra": 1}, {"policy": "project_right"}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, bad, 2, 4)
    for bad_value in (None, True, "", "mark_both", 0):
        with pytest.raises((TypeError, ValueError)):
            adapter.program({"mark_policy": bad_value})


def test_sequential_public_turn_reveals_one_query_without_private_hints():
    prototype = _load(PROTOTYPE_PATH, "mark_policy_public")
    full = prototype.generate_episode(83, "occupied_side", 3, 4)
    single = prototype.generate_episode(83, "occupied_side", 3, 1)

    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3
    assert first["test"] == [{"input": full["test"][0]["input"]}]
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("occupied_side", "mark_policy", "program_solution", "query_count", "remaining"):
        assert forbidden not in text
    for index in range(4):
        assert prototype.public_turn(full, index)["test"] == [
            {"input": full["test"][index]["input"]}
        ]


def test_finite_rival_audit_has_no_harmful_survivor():
    audit = _load(AUDIT_PATH, "mark_policy_audit")
    report = audit.run_audit()

    assert report["episodes"] == 12
    assert report["queries_checked"] == 48
    assert len(report["rival_names"]) >= 10
    assert report["harmful_survivors"] == []
    assert report["input_failures"] == []
