from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "4e16917b1bde"
TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
ADAPTER_PATH = TASK_DIR / "workspace" / "parametric" / "adapter.py"
PROMOTION_PATH = TASK_DIR / "workspace" / "parametric" / "promotion.json"
AUDIT_PATH = TASK_DIR / "workspace" / "parametric" / "audit.py"
POLICIES = ("same_depth", "reverse_depth")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "parametric_depth_policy_prototype")


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
    return [
        [0, 0, 0, 2, 5, 0, 0, 0, 0],
        [0, 3, 0, 0, 5, 0, 0, 0, 0],
        [0, 0, 0, 0, 5, 0, 0, 0, 0],
        [0, 0, 4, 0, 5, 0, 0, 0, 0],
        [0, 0, 0, 0, 5, 0, 0, 0, 0],
    ]


def test_prototype_exports_required_interface_and_exact_default_program():
    prototype = _prototype()

    for name in (
        "canonical_program",
        "program_for",
        "apply_policy",
        "episode_inputs",
        "generate_episode",
        "public_turn",
        "depth_facts",
    ):
        assert callable(getattr(prototype, name))
    assert prototype.POLICIES == POLICIES
    assert prototype.DEFAULT_POLICY == "same_depth"
    assert prototype.canonical_program() == _canonical_source()
    assert prototype.program_for("same_depth") == _canonical_source()
    assert prototype.program_for("reverse_depth") != _canonical_source()
    assert prototype.program_for("reverse_depth").startswith("(rule!")


def test_reverse_depth_uses_input_maximum_depth_and_changes_placement():
    prototype = _prototype()
    grid = _fixture()

    facts = prototype.depth_facts(grid)
    assert facts["divider_col"] == 4
    assert facts["source_side"] == "left"
    assert facts["depths"] == [1, 2, 3]
    assert facts["max_depth"] == 3

    same = prototype.apply_policy(grid, "same_depth")
    reverse = prototype.apply_policy(grid, "reverse_depth")
    assert same != reverse
    assert same[0][5] == 2 and same[1][7] == 3 and same[3][6] == 4
    assert reverse[0][7] == 2 and reverse[1][5] == 3 and reverse[3][6] == 4
    assert all(same[r][4] == reverse[r][4] == 5 for r in range(5))


def test_episode_counts_are_independent_inputs_distinct_and_queries_reach_30x30():
    prototype = _prototype()
    minimum = prototype.episode_inputs(7, demos=2, queries=1)
    maximum = prototype.episode_inputs(7, demos=6, queries=4)

    assert len(minimum) == 3
    assert len(maximum) == 10
    assert len({_freeze(grid) for grid in maximum}) == len(maximum)
    assert minimum == maximum[:2] + [maximum[6]]

    queries = maximum[6:]
    assert [(len(grid), len(grid[0])) for grid in queries] == [
        (14, 17),
        (18, 21),
        (24, 27),
        (30, 30),
    ]
    large = queries[-1]
    nonzero = sum(cell != 0 for row in large for cell in row)
    assert nonzero >= 70  # 30-cell divider plus substantive source content.


def test_minimum_demos_cover_opposite_sides_width_parities_colors_and_depth_gaps():
    prototype = _prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    first, second = prototype.episode_inputs(11, demos=2, queries=1)[:2]
    first_facts = prototype.depth_facts(first)
    second_facts = prototype.depth_facts(second)

    assert generator.self_check(first) == []
    assert generator.self_check(second) == []
    assert first_facts["source_side"] == "left"
    assert second_facts["source_side"] == "right"
    assert len(first[0]) % 2 == 1
    assert len(second[0]) % 2 == 0
    assert first_facts["divider_color"] != second_facts["divider_color"]
    assert min(first_facts["depths"]) == 1
    assert min(second_facts["depths"]) == 2
    assert first_facts["max_depth"] != second_facts["max_depth"]
    assert prototype.apply_policy(first, "same_depth") != prototype.apply_policy(
        first, "reverse_depth"
    )
    assert prototype.apply_policy(second, "same_depth") != prototype.apply_policy(
        second, "reverse_depth"
    )


def test_two_demos_identify_each_policy_and_inputs_are_setting_matched():
    prototype = _prototype()
    episodes = {
        policy: prototype.generate_episode(29, policy, demos=2, queries=4)
        for policy in POLICIES
    }

    inputs = [
        [pair["input"] for pair in episode["train"] + episode["test"]]
        for episode in episodes.values()
    ]
    assert inputs[0] == inputs[1]

    for selected, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program_for(selected)
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


def test_seed_policy_and_pair_count_validation_is_strict():
    prototype = _prototype()

    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(bad_seed, demos=2, queries=4)
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, "same_depth", demos=2, queries=4)

    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=bad_demos, queries=4)

    for bad_queries in (False, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=2, queries=bad_queries)

    for bad_policy in (None, True, "", "reflect_nearest", 0):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, bad_policy, demos=2, queries=4)


def test_protected_racket_matches_python_on_small_gap_case_and_30x30():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _prototype()
    inputs = prototype.episode_inputs(41, demos=2, queries=4)
    witnesses = (inputs[1], inputs[-1])
    assert [(len(grid), len(grid[0])) for grid in witnesses] == [(9, 14), (30, 30)]

    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        for index, grid in enumerate(witnesses):
            name = f"g{index}"
            bridge.define_grid(name, grid)
            for policy in POLICIES:
                actual = bridge.eval_text(
                    f"({wrap_rule(prototype.program_for(policy))} {name})"
                )
                assert actual == prototype.apply_policy(grid, policy)
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True


def test_native_adapter_and_contract_have_exact_bounded_surface():
    prototype = _prototype()
    adapter = _load(ADAPTER_PATH, "parametric_depth_policy_adapter")
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/4e16917b1bde/workspace/parametric/adapter.py",
        "parameters": {"depth_policy": list(POLICIES)},
        "default": {"depth_policy": "same_depth"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
    }
    for policy in POLICIES:
        settings = {"depth_policy": policy}
        assert adapter.program(settings) == prototype.program_for(policy)
        assert adapter.generate(53, settings, 2, 4) == prototype.generate_episode(
            53, policy, 2, 4
        )


def test_adapter_rejects_wrong_setting_shapes_and_values():
    adapter = _load(ADAPTER_PATH, "parametric_depth_policy_adapter_validation")

    for bad in (
        None,
        [],
        {},
        {"depth_policy": "same_depth", "extra": 1},
        {"policy": "same_depth"},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, bad, 2, 4)

    for bad_value in (None, True, "", "reflect_nearest", 0):
        settings = {"depth_policy": bad_value}
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 2, 4)


def test_sequential_public_turn_reveals_exactly_one_query_without_private_hints():
    prototype = _prototype()
    full = prototype.generate_episode(83, "reverse_depth", 3, 4)
    single = prototype.generate_episode(83, "reverse_depth", 3, 1)

    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    serialized = json.dumps(first, sort_keys=True)
    assert "reverse_depth" not in serialized
    assert "depth_policy" not in serialized
    assert "program_solution" not in serialized
    assert "query_count" not in serialized
    assert "remaining" not in serialized

    for index in range(4):
        turn = prototype.public_turn(full, index)
        assert turn["test"] == [{"input": full["test"][index]["input"]}]
    for bad_index in (True, -1, 4, 0.0, "0"):
        with pytest.raises((TypeError, ValueError, IndexError)):
            prototype.public_turn(full, bad_index)


def test_finite_rival_audit_has_no_harmful_survivor_across_settings_and_counts():
    audit = _load(AUDIT_PATH, "parametric_depth_policy_audit")

    report = audit.run_audit(seeds=(0, 17), demo_counts=(2, 3, 6), queries=4)
    assert report["schema"] == "arcpuzzles-parametric-depth-policy-audit-v1"
    assert report["episodes"] == 12
    assert report["queries_checked"] == 48
    assert report["harmful_survivors"] == []
    assert report["input_failures"] == []
    assert set(report["settings_checked"]) == set(POLICIES)
    assert len(report["rival_names"]) >= 8
