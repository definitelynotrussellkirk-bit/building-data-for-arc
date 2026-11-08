"""Adversarial checks for the finite native audit, including live Racket rivals."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("tested_mode_glyph_native_audit", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def native(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield audit.CachedEvaluator(apply)
        finally:
            bridge.close()


def scene():
    # Two 4-connected blue blocks touch diagonally. Three green objects are
    # separate; green is first, red is last, and yellow is least frequent too.
    grid = [[0] * 8 for _ in range(8)]
    for r, c in ((0, 2), (0, 3), (1, 2), (1, 3),
                 (2, 4), (2, 5), (3, 4), (3, 5)):
        grid[r][c] = 2
    for r, c in ((0, 0), (3, 0), (6, 6)):
        grid[r][c] = 3
    grid[5][0] = 4
    grid[7][7] = 1
    return grid


def three_component_scene():
    grid = [[0] * 8 for _ in range(8)]
    for r, c in ((0, 1), (0, 2), (2, 3), (2, 4), (4, 6), (5, 6)):
        grid[r][c] = 2
    grid[7][0] = 3
    return grid


def glyph(color, turns):
    expected = {
        1: [[0, 5, 0], [5, 5, 5], [0, 5, 0]],
        2: [[5, 5, 5], [0, 5, 0], [0, 5, 0]],
        3: [[0, 0, 5], [0, 0, 5], [5, 5, 5]],
    }.get(color, [[0] * 3 for _ in range(3)])
    for _ in range(turns):
        expected = [[expected[2 - c][r] for c in range(3)] for r in range(3)]
    return expected


def test_policy_aware_selectors_count_the_selected_color(audit, native):
    selected = {
        "first_nonzero": 3, "last_nonzero": 1, "smallest_nonzero": 1,
        "largest_nonzero": 4, "least_frequent_nonzero": 1,
        "endpoint_complement": 2, "endpoint_limited_mode": 3,
        "largest_component_4": 2, "largest_component_8": 2,
        "largest_color_bbox": 3,
    }
    counts = {1: 1, 2: 2, 3: 3, 4: 1}
    for orientation in ("canonical", "modal_components"):
        settings = {"orientation": orientation}
        for name, color in selected.items():
            turns = 0 if orientation == "canonical" else (counts[color] - 1) % 4
            expected = glyph(color, turns)
            assert audit.rival_reference(scene(), settings, name) == expected
            assert native(audit.rival_program(settings, name), scene()) == expected
    # The original unrotated rival and using the true mode's component count
    # both give the wrong result for the first-color hypothesis on this scene.
    actual = native(audit.rival_program({"orientation": "modal_components"}, "first_nonzero"), scene())
    assert actual != glyph(3, 0) and actual != glyph(3, 1)


def test_topology_and_fixed_turn_rivals_have_executable_distinct_meanings(audit, native):
    settings = {"orientation": "modal_components"}
    expected_turns = {
        "count_modal_8": (0, 2), "count_all_objects": (2, 3),
        "count_modal_cells": (3, 1), "parity_only": (1, 0),
        "fragmented_once": (1, 1), "opposite_rotation": (3, 2),
        "off_by_one": (2, 3),
        **{f"fixed_rotation_{turn}": (turn, turn) for turn in range(4)},
    }
    assert len(audit.rival_names()) == 23
    for name, turns in expected_turns.items():
        for grid, turn in zip((scene(), three_component_scene()), turns):
            expected = glyph(2, turn)
            assert audit.rival_reference(grid, settings, name) == expected
            assert native(audit.rival_program(settings, name), grid) == expected


def test_color_gated_rotation_rivals_require_active_rotation_for_each_class(audit, native):
    settings = {"orientation": "modal_components"}
    blue = scene()
    green = [[3 if cell == 2 else 2 if cell == 3 else cell for cell in row] for row in blue]
    for grid, color in ((blue, 2), (green, 3)):
        for gated_color in (2, 3):
            name = f"rotate_only_color_{gated_color}"
            expected = glyph(color, 1 if color == gated_color else 0)
            assert audit.rival_reference(grid, settings, name) == expected
            assert native(audit.rival_program(settings, name), grid) == expected
    # A third demonstration of green at zero turns does not teach that green
    # also obeys the component rotation. This is a real survivor, not an error.
    unfragmented = [[0] * 8 for _ in range(8)]
    unfragmented[0][:5] = [3] * 5
    pair = lambda grid: {"input": grid, "output": audit.reference(grid, settings)}
    train = [pair(blue), pair(three_component_scene()), pair(unfragmented)]
    rival = audit.rival_program(settings, "rotate_only_color_2")
    missing_lesson = audit.assess_hypothesis("rotate_only_color_2", rival, train, [pair(green)], native)
    assert missing_lesson["survives_demonstrations"] is True
    assert missing_lesson["query_disagreement_indices"] == [0]
    repaired = audit.assess_hypothesis("rotate_only_color_2", rival,
                                        train[:2] + [pair(green)], [pair(green)], native)
    assert repaired["rejected_by_demo_indices"] == [2]


def test_survivor_selection_uses_demos_before_queries_and_records_prefix_risk(audit):
    train = [{"input": [[i]], "output": [[output]]} for i, output in ((1, 1), (2, 1), (3, 2))]
    test = [{"input": [[4]], "output": [[2]]}]
    seen = []
    def execute(program, grid):
        seen.append(grid[0][0])
        return [[1]]
    result = audit.assess_hypothesis("rival", "program", train, test, execute)
    assert seen == [1, 2, 3, 4]
    assert result["rejected_by_demo_indices"] == [2]
    assert result["survives_demonstrations"] is False
    assert result["survives_first_two"] is True
    assert result["query_disagreement_indices"] == [0]
    assert result["query_checked_for"] == ["first_two_prefix"]


def test_refuted_hypothesis_does_not_claim_unexecuted_query_results(audit):
    train = [{"input": [[1]], "output": [[2]]}, {"input": [[2]], "output": [[2]]}]
    def execute(program, grid):
        assert grid != [[3]], "query was unnecessarily evaluated"
        return [[1]]
    result = audit.assess_hypothesis("rival", "program", train,
                                     [{"input": [[3]], "output": [[2]]}], execute)
    assert result["survives_demonstrations"] is False
    assert result["query_outputs"] is None
    assert result["query_disagreement_indices"] is None
    assert result["query_checked_for"] == []


def test_execution_error_is_not_negative_semantic_evidence(audit):
    def fail(program, grid):
        raise RuntimeError("protected evaluator failure")
    pair = {"input": [[1]], "output": [[2]]}
    with pytest.raises(RuntimeError, match="protected evaluator failure"):
        audit.assess_hypothesis("broken", "program", [pair, pair], [pair], fail)


def test_cache_is_exact_immutable_and_does_not_cache_failures(audit):
    calls = []
    def apply(program, grid):
        calls.append((program, deepcopy(grid)))
        if program == "broken":
            raise RuntimeError("failure")
        grid[0][0] = 8
        return grid
    execute = audit.CachedEvaluator(apply)
    source = [[1]]
    output = execute("one", source)
    output[0][0] = 9
    assert source == [[1]] and execute("one", source) == [[8]]
    assert len(calls) == 1 and execute.cache_hits == 1
    execute("two", source)
    execute("one", [[2]])
    for _ in range(2):
        with pytest.raises(RuntimeError, match="failure"):
            execute("broken", source)
    assert len(calls) == 5


def test_independent_scene_observer_rejects_ties_and_measures_connectivity(audit):
    facts = audit.scene_facts(scene())
    assert facts["mode_color"] == 2 and facts["mode_count"] == 8
    assert facts["modal_components_4"] == 2 and facts["modal_components_8"] == 1
    assert facts["objects_4"] == 7 and facts["objects_8"] == 6
    assert facts["nonzero_cells"] == 13
    assert facts["occupied_rows"] == 7 and facts["occupied_columns"] == 7
    tied = [[0] * 8 for _ in range(8)]
    tied[0][:4] = [1, 1, 2, 2]
    with pytest.raises(ValueError, match="unique"):
        audit.scene_facts(tied)
    with pytest.raises(ValueError):
        audit.scene_facts([[2] * 7 for _ in range(8)])
