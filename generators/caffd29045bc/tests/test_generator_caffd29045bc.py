"""Portable regression and semantic-contract tests for caffd29045bc."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "caffd29045bc"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent reading of the unchanged canonical reflection rule."""
    axes = [
        c for c in range(len(grid[0]))
        if all(row[c] == 9 for row in grid)
    ]
    assert len(axes) == 1
    axis = axes[0]
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirrored = 2 * axis - c
            if value not in (0, 9) and 0 <= mirrored < len(row):
                out[r][mirrored] = value
    return out


def labelled(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": intended_output(grid)}


def pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_contract_surface_pins_authority_and_balanced_schedule() -> None:
    assert GEN.RULE_HASH == "71b211cdd7c0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "center_left_connected_gapped",
        "offcenter_right_connected_adjacent",
        "offcenter_left_split_adjacent",
        "center_right_split_gapped",
    )
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "source_cell_count",
        "source_color_count",
        "source_side",
        "layout",
        "guide_contact",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "off_center_axis",
        "right_side_source",
        "split_source",
        "guide_adjacent_source",
    }
    assert set(GEN.SEMANTIC_RIVALS) == {
        "geometric_center_axis",
        "left_source_only",
        "largest_component_only",
        "skip_guide_adjacent_cells",
    }
    assert GEN.CANONICAL_SHORTCUTS.keys() == GEN.SEMANTIC_RIVALS.keys()
    assert GEN.LESSON_COMPETITORS.keys() == GEN.SEMANTIC_RIVALS.keys()


def test_all_canonical_pairs_are_lawful_and_match_independent_oracle() -> None:
    canonical = pairs()
    assert len(canonical) == 3
    for pair in canonical:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert intended_output(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 6,
            "grid_w": 8,
            "source_cell_count": 3,
            "source_color_count": 1,
            "source_side": "left",
            "layout": "connected",
            "guide_contact": "adjacent",
        },
        {
            "grid_h": 6,
            "grid_w": 8,
            "source_cell_count": 8,
            "source_color_count": 3,
            "source_side": "right",
            "layout": "split",
            "guide_contact": "gapped",
        },
        {
            "grid_h": 14,
            "grid_w": 17,
            "source_cell_count": 8,
            "source_color_count": 3,
            "source_side": "left",
            "layout": "connected",
            "guide_contact": "gapped",
        },
        {
            "grid_h": 14,
            "grid_w": 17,
            "source_cell_count": 3,
            "source_color_count": 2,
            "source_side": "right",
            "layout": "split",
            "guide_contact": "adjacent",
        },
    ],
)
def test_joint_exact_overrides_are_constructive_and_observable(band, requested) -> None:
    grid = GEN.generate(917, 7, difficulty=band, **requested)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "bad",
    [
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_w": 7},
        {"source_cell_count": 9},
        {"source_color_count": 0},
        {"source_side": "both"},
        {"layout": "three_parts"},
        {"guide_contact": "sometimes"},
    ],
)
def test_invalid_or_unknown_controls_fail_loudly(bad) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **bad)


def test_each_four_profile_window_survives_every_query_rotation() -> None:
    # Four consecutive accepted draws are one three-demo/one-query lesson.
    # Every holdout must leave a witness against every canonical shortcut.
    for start in range(12):
        grids = [GEN.generate(4_000 + start, start + offset, difficulty="medium") for offset in range(4)]
        assert [GEN.schedule_profile(0, start + offset) for offset in range(4)] == [
            GEN.SCHEDULE_PROFILES[(start + offset) % 4] for offset in range(4)
        ]
        for held_out in range(4):
            demos = [grid for index, grid in enumerate(grids) if index != held_out]
            for witness, predicate in GEN.SEMANTIC_WITNESSES.items():
                assert any(predicate(grid) for grid in demos), (start, held_out, witness)
            reasons = GEN.lesson_identifiable(
                [labelled(grid) for grid in demos],
                labelled(grids[held_out]),
            )
            assert reasons == [], (start, held_out, reasons)


def test_declared_shortcuts_fit_every_canonical_label() -> None:
    canonical = pairs()
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical), name


def test_generated_witnesses_are_real_counterexamples_to_named_rivals() -> None:
    for sample_index, profile in enumerate(GEN.SCHEDULE_PROFILES):
        grid = GEN.generate(5_000, sample_index, difficulty="medium")
        assert GEN.schedule_profile(5_000, sample_index, "medium") == profile
        expected = intended_output(grid)
        for witness, rival_names in GEN.WITNESS_RIVALS.items():
            if GEN.SEMANTIC_WITNESSES[witness](grid):
                assert any(GEN.SEMANTIC_RIVALS[name](grid) != expected for name in rival_names), (
                    profile,
                    witness,
                )


def test_lesson_hook_reports_the_exact_left_only_ambiguity() -> None:
    # Canonical demonstrations are all left-sided, so the left-only rival fits.
    # A right-sided query must make the ambiguity explicit.
    demos = pairs()[:2]
    query_grid = GEN.generate(
        8_001,
        1,
        difficulty="medium",
        source_side="right",
        layout="connected",
        guide_contact="adjacent",
    )
    reasons = GEN.lesson_identifiable(demos, labelled(query_grid))
    assert any("left_source_only" in reason for reason in reasons)


def test_structural_impostors_are_rejected() -> None:
    fixtures = list(GEN.mutation_fixtures())
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_generation_is_replayable_fresh_and_global_rng_pure() -> None:
    state = random.getstate()
    first = GEN.generate(77, 9, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(77, 9, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert GEN.generate(77, 9, difficulty="medium") == second


def test_reference_probe_emits_replayable_counterexamples(tmp_path) -> None:
    probe_path = HOME / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.build_report(seed=5_000)
    assert report["task_id"] == TASK_ID
    assert report["canonical"]["all_shortcuts_fit"] is True
    assert report["schedule"]["all_rotations_identifiable"] is True
    assert set(report["counterexamples"]) == set(GEN.SEMANTIC_RIVALS)
    for name, row in report["counterexamples"].items():
        assert row["different_cells"] > 0, name
    out = tmp_path / "probe.json"
    probe.write_report(out, report)
    assert out.exists() and out.read_text(encoding="utf-8").endswith("\n")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_profile_zero_cycles_exact_canonical_dimension_and_count_anchors(band) -> None:
    canonical_profiles = ((7, 9, 3), (8, 11, 4), (9, 11, 4))
    for cycle, expected in enumerate(canonical_profiles):
        sample_index = cycle * GEN.LESSON_SCHEDULE_PERIOD
        grid = GEN.generate(9100 + cycle, sample_index, difficulty=band)
        observed = GEN.observe_overrides(grid)
        assert (
            observed["grid_h"],
            observed["grid_w"],
            observed["source_cell_count"],
        ) == expected
