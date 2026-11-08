from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "07eaf5f238ad"
HERE = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HERE / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
AUDIT_PATH = PARAMETRIC / "audit.py"
CHOICES = ("first", "last")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "parametric_object_choice_prototype_07eaf5f238ad")


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
    grid = [[0] * 12 for _ in range(10)]
    grid[0][0] = 2
    grid[0][4] = 4
    grid[0][8] = 6
    # Body scan order: colour 6, first colour-2 object, colour 4, last colour-2 object.
    grid[2][0] = grid[3][0] = 6
    grid[2][4] = grid[3][4] = grid[3][5] = 2
    grid[5][0] = grid[5][1] = 4
    grid[7][8] = grid[7][9] = grid[7][10] = 2
    return grid


def test_prototype_exports_required_interface_and_exact_default_program():
    prototype = _prototype()

    for name in (
        "canonical_program",
        "program_for",
        "input_facts",
        "selection_facts",
        "apply_choice",
        "episode_inputs",
        "generate_episode",
        "public_turn",
    ):
        assert callable(getattr(prototype, name))
    assert prototype.OBJECT_CHOICES == CHOICES
    assert prototype.DEFAULT_OBJECT_CHOICE == "first"
    assert prototype.canonical_program() == _canonical_source()
    assert prototype.program_for("first") == _canonical_source()
    assert prototype.program_for("last") != _canonical_source()
    assert prototype.program_for("last").startswith("(rule!")


def test_first_and_last_select_distinct_row_major_components_then_pack_header_order():
    prototype = _prototype()
    grid = _fixture()

    facts = prototype.input_facts(grid)
    assert facts["header"] == [2, 4, 6]
    assert facts["object_counts"] == {2: 2, 4: 1, 6: 1}
    assert facts["duplicate_header_positions"] == [0]
    assert facts["body_first_colour_order"] == [6, 2, 4]

    first = prototype.apply_choice(grid, "first")
    last = prototype.apply_choice(grid, "last")
    assert first == [
        [2, 0, 0, 4, 4, 0, 6],
        [2, 2, 0, 0, 0, 0, 6],
    ]
    assert last == [
        [2, 2, 2, 0, 4, 4, 0, 6],
        [0, 0, 0, 0, 0, 0, 0, 6],
    ]
    assert prototype.selection_facts(grid, "first")[0]["component_rank"] == 0
    assert prototype.selection_facts(grid, "last")[0]["component_rank"] == 1



def test_every_constructor_shape_is_one_four_connected_component():
    prototype = _prototype()

    for tier in (3, 4, 5):
        groups = prototype._shape_sets(tier)
        for shape in [candidate for group in groups for candidate in group]:
            cells = set(shape)
            reached = {next(iter(cells))}
            frontier = list(reached)
            while frontier:
                row, col = frontier.pop()
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (row + delta_row, col + delta_col)
                    if neighbor in cells and neighbor not in reached:
                        reached.add(neighbor)
                        frontier.append(neighbor)
            assert reached == cells, (tier, shape)

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
        (14, 18),
        (18, 22),
        (24, 27),
        (30, 30),
    ]
    large = queries[-1]
    nonzero = sum(cell != 0 for row in large for cell in row)
    assert nonzero >= 90
    facts = prototype.input_facts(large)
    assert facts["header_count"] == 4
    assert facts["duplicate_header_positions"] == [0, 1, 2, 3]
    assert facts["component_count"] == 8
    assert prototype.apply_choice(large, "first") != prototype.apply_choice(large, "last")


def test_minimum_demos_cross_parity_shape_size_header_count_and_duplicate_position():
    prototype = _prototype()
    first, second = prototype.episode_inputs(11, demos=2, queries=1)[:2]
    a = prototype.input_facts(first)
    b = prototype.input_facts(second)

    assert (a["height"], a["width"], a["header_count"]) == (12, 12, 3)
    assert (b["height"], b["width"], b["header_count"]) == (13, 17, 4)
    assert a["duplicate_header_positions"] == [0]
    assert b["duplicate_header_positions"] == [3]
    assert a["first_duplicate_size_relation"] == "larger"
    assert b["first_duplicate_size_relation"] == "smaller"
    assert a["body_order_differs"] is True
    assert b["body_order_differs"] is True
    assert prototype.apply_choice(first, "first") != prototype.apply_choice(first, "last")
    assert prototype.apply_choice(second, "first") != prototype.apply_choice(second, "last")


def test_two_demos_identify_each_choice_and_inputs_are_setting_matched():
    prototype = _prototype()
    episodes = {
        choice: prototype.generate_episode(29, choice, demos=2, queries=4)
        for choice in CHOICES
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
            for candidate in CHOICES
            if all(
                prototype.apply_choice(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [selected]
        assert all(
            pair["output"] == prototype.apply_choice(pair["input"], selected)
            for pair in episode["train"] + episode["test"]
        )


def test_seed_choice_and_pair_count_validation_is_strict():
    prototype = _prototype()

    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(bad_seed, demos=2, queries=4)
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, "first", demos=2, queries=4)

    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=bad_demos, queries=4)

    for bad_queries in (False, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=2, queries=bad_queries)

    for bad_choice in (None, True, "", "largest", 0):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, bad_choice, demos=2, queries=4)


def test_input_validation_rejects_leaks_malformed_grammar_and_equal_duplicate_crops():
    prototype = _prototype()
    good = _fixture()
    assert prototype.input_facts(good)["component_count"] == 4

    bad_cases = []
    bad_cases.append(good[:-1] + [good[-1][:-1]])
    bad_separator = [row[:] for row in good]
    bad_separator[1][1] = 9
    bad_cases.append(bad_separator)
    repeated_header = [row[:] for row in good]
    repeated_header[0][10] = 2
    bad_cases.append(repeated_header)
    decoy = [row[:] for row in good]
    decoy[8][3] = decoy[8][4] = 9
    bad_cases.append(decoy)
    equal_crops = [row[:] for row in good]
    equal_crops[7][9] = 0
    equal_crops[7][10] = 0
    equal_crops[8][8] = 2
    equal_crops[8][9] = 2
    bad_cases.append(equal_crops)

    for grid in bad_cases:
        with pytest.raises((TypeError, ValueError)):
            prototype.input_facts(grid)


def test_protected_racket_matches_python_on_fixture_and_30x30_case():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _prototype()
    large = prototype.episode_inputs(41, demos=2, queries=4)[-1]
    witnesses = (_fixture(), large)
    assert [(len(grid), len(grid[0])) for grid in witnesses] == [(10, 12), (30, 30)]

    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        for index, grid in enumerate(witnesses):
            name = f"g{index}"
            bridge.define_grid(name, grid)
            for choice in CHOICES:
                actual = bridge.eval_text(
                    f"({wrap_rule(prototype.program_for(choice))} {name})"
                )
                assert actual == prototype.apply_choice(grid, choice)
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True


def test_native_adapter_and_contract_have_exact_bounded_surface():
    prototype = _prototype()
    adapter = _load(ADAPTER_PATH, "parametric_object_choice_adapter")
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/07eaf5f238ad/workspace/parametric/adapter.py",
        "parameters": {"object_choice": list(CHOICES)},
        "default": {"object_choice": "first"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            "generators/07eaf5f238ad/workspace/parametric/prototype.py",
            "generators/07eaf5f238ad/workspace/parametric/canonical.rkt",
            "generators/07eaf5f238ad/workspace/parametric/last.rkt",
        ],
    }
    for choice in CHOICES:
        settings = {"object_choice": choice}
        assert adapter.program(settings) == prototype.program_for(choice)
        assert adapter.generate(53, settings, 2, 4) == prototype.generate_episode(
            53, choice, 2, 4
        )


def test_adapter_rejects_wrong_setting_shapes_and_values():
    adapter = _load(ADAPTER_PATH, "parametric_object_choice_adapter_validation")

    for bad in (
        None,
        [],
        {},
        {"object_choice": "first", "extra": 1},
        {"choice": "first"},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, bad, 2, 4)

    for bad_value in (None, True, "", "largest", 0):
        settings = {"object_choice": bad_value}
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 2, 4)


def test_sequential_public_turn_reveals_exactly_one_query_without_private_hints():
    prototype = _prototype()
    full = prototype.generate_episode(83, "last", 3, 4)
    single = prototype.generate_episode(83, "last", 3, 1)

    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    serialized = json.dumps(first, sort_keys=True)
    assert "object_choice" not in serialized
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
    audit = _load(AUDIT_PATH, "parametric_object_choice_audit")

    report = audit.run_audit(seeds=(0, 17), demo_counts=(2, 3, 6), queries=4)
    assert report["schema"] == "arcpuzzles-parametric-object-choice-audit-v1"
    assert report["episodes"] == 12
    assert report["queries_checked"] == 48
    assert report["harmful_survivors"] == []
    assert report["input_failures"] == []
    assert set(report["settings_checked"]) == set(CHOICES)
    assert len(report["rival_names"]) >= 10
