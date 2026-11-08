"""Focused regressions for the reviewed corner-component recolor generator."""
from __future__ import annotations

import copy
import importlib.util
import os
import random
import sys

import pytest
from pathlib import Path

TASK_ID = "59ccf6f5cc65"
TEST_DIR = Path(__file__).resolve().parent
GENERATOR_PATH = Path(
    os.environ.get("GENERATOR_UNDER_TEST", TEST_DIR.parent / "generator.py")
).resolve()

# Source-tree and portable task-test layouts.
for candidate in (
    TEST_DIR.parents[2] / "shared" / "runtime",
    TEST_DIR.parents[3] / "shared" / "runtime",
    TEST_DIR.parents[2],
    TEST_DIR.parents[3],
):
    if (candidate / "reviewer_support.py").exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_pin_mirror_and_input_contract_match_every_canonical_pair():
    assert GEN.RULE_HASH == "bf30289ab720"
    assert GEN.VERSION == "3.0.0"
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def _orange_component_facts(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    }
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    facts = []
    while unseen:
        start = unseen.pop()
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        edges = set()
        for row, col in cells:
            if row == 0:
                edges.add("top")
            if row == height - 1:
                edges.add("bottom")
            if col == 0:
                edges.add("left")
            if col == width - 1:
                edges.add("right")
        facts.append({"cells": cells, "corner": bool(cells & corners), "edges": edges})
    return facts


def test_four_profile_schedule_generates_canonical_palette_and_corner_gap_witnesses():
    for difficulty in (None, "easy", "medium", "hard"):
        grids = [GEN.generate(1701, index, difficulty=difficulty) for index in range(4)]
        assert [GEN.schedule_profile(1701, index, difficulty) for index in range(4)] == list(
            GEN.SCHEDULE_PROFILES
        )
        assert sorted((len(grid), len(grid[0])) for grid in grids) == sorted(
            GEN.CANONICAL_PROFILES
        )
        for grid in grids:
            assert GEN.self_check(grid) == []
            assert {value for row in grid for value in row} == {0, 5, 7}
            facts = _orange_component_facts(grid)
            assert any(fact["corner"] for fact in facts)
            assert any(not fact["corner"] and len(fact["edges"]) >= 2 for fact in facts)
            assert any(not fact["edges"] for fact in facts)


def _intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent exact-corner oracle used by the review tests."""
    out = copy.deepcopy(grid)
    for fact in _orange_component_facts(grid):
        if fact["corner"]:
            for row, col in fact["cells"]:
                out[row][col] = 1
    return out


def test_named_semantic_witnesses_are_real_counterexamples_to_named_rivals():
    expected_witnesses = {
        "true_corner_component",
        "corner_gap_decoy",
        "strictly_interior_component",
        "nonrectangular_true_corner",
        "color5_corner_marker",
        "multiple_true_corners",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == expected_witnesses
    assert set(GEN.SEMANTIC_RIVALS) == {
        "identity",
        "recolor_all_orange",
        "touches_any_border",
        "touches_two_borders",
        "bbox_contains_corner",
        "solid_rectangle_at_corner_only",
        "any_nonzero_component_at_corner",
        "first_true_corner_only",
    }
    fired = set()
    for index in range(4):
        grid = GEN.generate(811, index, difficulty="hard")
        intended = _intended_output(grid)
        assert GEN.rule_mirror(grid) == intended
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            fired.add(witness_name)
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != intended
    assert fired == expected_witnesses


def test_every_three_consecutive_examples_refute_all_declared_competitors():
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(16):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(1207 + start, start + offset, difficulty=difficulty)
                demos.append({"input": grid, "output": _intended_output(grid)})
            query_grid = GEN.generate(
                1207 + start,
                start + GEN.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {"input": query_grid, "output": _intended_output(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_canonical_test_refutes_the_two_strongest_demo_shortcuts():
    demos = [pair for pair in _canonical_pairs() if pair["split"] == "train"]
    query = next(pair for pair in _canonical_pairs() if pair["split"] == "test")
    for rival_name in ("touches_two_borders", "bbox_contains_corner"):
        rival = GEN.SEMANTIC_RIVALS[rival_name]
        assert all(rival(pair["input"]) == pair["output"] for pair in demos)
        assert rival(query["input"]) != query["output"]
        assert GEN.rule_mirror(query["input"]) == query["output"]


def test_reusable_shortcut_probe_reports_declared_rivals_and_all_schedule_starts():
    probe_path = TEST_DIR.parent / "workspace" / "shortcut_probe.py"
    probe_spec = importlib.util.spec_from_file_location("shortcut_probe_59ccf6f5cc65", probe_path)
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.build_report(per_band=4, lesson_starts=4, seed=20261004)
    assert report["task_id"] == TASK_ID
    assert len(report["generator_sha256"]) == 64
    assert set(report["declared_rivals"]) == set(GEN.SEMANTIC_RIVALS)
    assert set(report["declared_witnesses"]) == set(GEN.SEMANTIC_WITNESSES)
    assert {
        item["name"]
        for item in report["canonical_rivals"]
        if item["fits_all_train"] and not item["fits_all_test"]
    } >= {"touches_two_borders", "bbox_contains_corner"}
    assert all(count > 0 for count in report["generated_witness_counts"].values())
    assert all(not lesson["query_changing_survivors"] for lesson in report["lessons"])
    assert all(not lesson["hook_reasons"] for lesson in report["lessons"])


def test_exact_override_round_trip_determinism_and_validation():
    global_state = random.getstate()
    draws = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for profile in range(4):
            for n_corner in (1, 2):
                for n_interior in (1, 2):
                    for layout_rotation in range(4):
                        overrides = {
                            "profile": profile,
                            "n_corner": n_corner,
                            "n_interior": n_interior,
                            "layout_rotation": layout_rotation,
                        }
                        first = GEN.generate(4401, draws, difficulty=difficulty, **overrides)
                        second = GEN.generate(4401, draws, difficulty=difficulty, **overrides)
                        assert first == second
                        assert first is not second
                        assert all(a is not b for a, b in zip(first, second))
                        assert GEN.observe_overrides(first) == overrides
                        assert GEN.self_check(first) == []
                        draws += 1
    assert draws == 256
    assert random.getstate() == global_state

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, not_an_axis=1)
    with pytest.raises(TypeError, match="profile must be an integer"):
        GEN.generate(1, 0, profile=True)
    with pytest.raises(ValueError, match="n_corner must be in 1..2"):
        GEN.generate(1, 0, n_corner=3)
    with pytest.raises(ValueError, match="difficulty must be"):
        GEN.generate(1, 0, difficulty="expert")
