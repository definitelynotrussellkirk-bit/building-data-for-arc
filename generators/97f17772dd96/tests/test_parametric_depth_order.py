from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "97f17772dd96"
HERE = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HERE / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
AUDIT_PATH = PARAMETRIC / "audit.py"
ORDERS = ("outer_to_inner", "inner_to_outer")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "parametric_depth_order_prototype_97f17772dd96")


def _canonical_source() -> str:
    matches = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    assert len(matches) == 1
    return matches[0]["program_solution"]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _outline(grid, box):
    top, left, bottom, right = box
    for col in range(left, right + 1):
        grid[top][col] = 1
        grid[bottom][col] = 1
    for row in range(top, bottom + 1):
        grid[row][left] = 1
        grid[row][right] = 1


def _fixture():
    grid = [[0] * 11 for _ in range(11)]
    _outline(grid, (1, 1, 9, 9))
    _outline(grid, (3, 3, 7, 7))
    return grid


def test_prototype_exports_required_interface_and_exact_default_program():
    prototype = _prototype()

    for name in (
        "canonical_program",
        "program_for",
        "apply_order",
        "episode_inputs",
        "generate_episode",
        "public_turn",
        "depth_facts",
    ):
        assert callable(getattr(prototype, name))
    assert prototype.DEPTH_ORDERS == ORDERS
    assert prototype.DEFAULT_DEPTH_ORDER == "outer_to_inner"
    assert prototype.canonical_program() == _canonical_source()
    assert prototype.program_for("outer_to_inner") == _canonical_source()
    assert prototype.program_for("inner_to_outer") != _canonical_source()
    assert prototype.program_for("inner_to_outer").startswith("(rule!")


def test_inner_to_outer_uses_input_frame_count_and_reverses_depth_colors():
    prototype = _prototype()
    grid = _fixture()

    facts = prototype.depth_facts(grid)
    assert facts["max_depth"] == 2
    assert len(facts["frames"]) == 2

    increasing = prototype.apply_order(grid, "outer_to_inner")
    decreasing = prototype.apply_order(grid, "inner_to_outer")
    assert increasing != decreasing
    assert increasing[0][0] == decreasing[0][0] == 0
    assert increasing[1][1] == decreasing[1][1] == 1
    assert increasing[2][2] == 2
    assert decreasing[2][2] == 3
    assert increasing[4][4] == 3
    assert decreasing[4][4] == 2


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
        (18, 23),
        (24, 27),
        (30, 30),
    ]
    large = queries[-1]
    nonzero = sum(cell != 0 for row in large for cell in row)
    assert nonzero >= 200
    facts = prototype.depth_facts(large)
    assert facts["max_depth"] == 3
    assert facts["offset"] is True


def test_minimum_demos_cover_frame_counts_offset_and_rectangularity():
    prototype = _prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    first, second = prototype.episode_inputs(11, demos=2, queries=1)[:2]
    first_facts = prototype.depth_facts(first)
    second_facts = prototype.depth_facts(second)

    assert generator.self_check(first) == []
    assert generator.self_check(second) == []
    assert first_facts["max_depth"] == 2
    assert second_facts["max_depth"] == 3
    assert first_facts["offset"] is False
    assert second_facts["offset"] is True
    assert len(first) == len(first[0])
    assert len(second) != len(second[0])
    assert prototype.apply_order(first, "outer_to_inner") != prototype.apply_order(
        first, "inner_to_outer"
    )
    assert prototype.apply_order(second, "outer_to_inner") != prototype.apply_order(
        second, "inner_to_outer"
    )


def test_two_demos_identify_each_order_and_inputs_are_setting_matched():
    prototype = _prototype()
    episodes = {
        order: prototype.generate_episode(29, order, demos=2, queries=4)
        for order in ORDERS
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
            for candidate in ORDERS
            if all(
                prototype.apply_order(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [selected]
        assert all(
            pair["output"] == prototype.apply_order(pair["input"], selected)
            for pair in episode["train"] + episode["test"]
        )


def test_seed_order_and_pair_count_validation_is_strict():
    prototype = _prototype()

    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(bad_seed, demos=2, queries=4)
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, "outer_to_inner", demos=2, queries=4)

    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=bad_demos, queries=4)

    for bad_queries in (False, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=2, queries=bad_queries)

    for bad_order in (None, True, "", "outside_in", 0):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, bad_order, demos=2, queries=4)


def test_protected_racket_matches_python_on_two_frame_and_30x30_cases():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _prototype()
    inputs = prototype.episode_inputs(41, demos=2, queries=4)
    witnesses = (inputs[0], inputs[-1])
    assert [(len(grid), len(grid[0])) for grid in witnesses] == [(12, 12), (30, 30)]

    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        for index, grid in enumerate(witnesses):
            name = f"g{index}"
            bridge.define_grid(name, grid)
            for order in ORDERS:
                actual = bridge.eval_text(
                    f"({wrap_rule(prototype.program_for(order))} {name})"
                )
                assert actual == prototype.apply_order(grid, order)
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True


def test_native_adapter_and_contract_have_exact_bounded_surface():
    prototype = _prototype()
    adapter = _load(ADAPTER_PATH, "parametric_depth_order_adapter")
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/97f17772dd96/workspace/parametric/adapter.py",
        "parameters": {"depth_order": list(ORDERS)},
        "default": {"depth_order": "outer_to_inner"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            "generators/97f17772dd96/workspace/parametric/prototype.py",
            "generators/97f17772dd96/workspace/parametric/canonical.rkt",
            "generators/97f17772dd96/workspace/parametric/inner-to-outer.rkt",
        ],
    }
    for order in ORDERS:
        settings = {"depth_order": order}
        assert adapter.program(settings) == prototype.program_for(order)
        assert adapter.generate(53, settings, 2, 4) == prototype.generate_episode(
            53, order, 2, 4
        )


def test_adapter_rejects_wrong_setting_shapes_and_values():
    adapter = _load(ADAPTER_PATH, "parametric_depth_order_adapter_validation")

    for bad in (
        None,
        [],
        {},
        {"depth_order": "outer_to_inner", "extra": 1},
        {"order": "outer_to_inner"},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, bad, 2, 4)

    for bad_value in (None, True, "", "outside_in", 0):
        settings = {"depth_order": bad_value}
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 2, 4)


def test_sequential_public_turn_reveals_exactly_one_query_without_private_hints():
    prototype = _prototype()
    full = prototype.generate_episode(83, "inner_to_outer", 3, 4)
    single = prototype.generate_episode(83, "inner_to_outer", 3, 1)

    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    serialized = json.dumps(first, sort_keys=True)
    assert "inner_to_outer" not in serialized
    assert "depth_order" not in serialized
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
    audit = _load(AUDIT_PATH, "parametric_depth_order_audit")

    report = audit.run_audit(seeds=(0, 17), demo_counts=(2, 3, 6), queries=4)
    assert report["schema"] == "arcpuzzles-parametric-depth-order-audit-v1"
    assert report["episodes"] == 12
    assert report["queries_checked"] == 48
    assert report["harmful_survivors"] == []
    assert report["input_failures"] == []
    assert set(report["settings_checked"]) == set(ORDERS)
    assert len(report["rival_names"]) >= 8
