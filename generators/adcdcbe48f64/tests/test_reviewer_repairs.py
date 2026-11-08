"""Regressions for defects reproduced by the 2026-10-21 review battery."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "adcdcbe48f64"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_reviewer_repairs", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


@pytest.mark.parametrize(
    "difficulty",
    [True, False, 0, 1, "", "expert", "__invalid_difficulty__", [], {}],
)
def test_generate_rejects_invalid_difficulty_scalars(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 0, difficulty=difficulty)


def test_width_four_competitor_fits_canonical_but_stays_in_lesson_contract():
    # The frozen selected-task semantic registry is an exact public contract.
    # Keep this executable shortcut in lesson scoring and prove its canonical
    # fit here rather than silently widening that registry.
    assert GEN.CANONICAL_SHORTCUTS == {}
    assert set(GEN.LESSON_COMPETITORS) == {"fixed_width_4"}
    shortcut = GEN.LESSON_COMPETITORS["fixed_width_4"]

    pairs = _canonical()
    assert pairs
    for pair in pairs:
        assert shortcut(pair["input"]) == pair["output"]

    wide = GEN.generate(2026, 7, difficulty="medium", grid_h=4, grid_w=5, palette_size=2)
    assert GEN.self_check(wide) == []
    assert shortcut(wide) != GEN.rule_mirror(wide)
    assert len(shortcut(wide)[0]) == 20
    assert len(GEN.rule_mirror(wide)[0]) == 25


def test_width_four_only_demonstrations_do_not_license_a_wide_query():
    pairs = _canonical()
    demos = pairs[:3]
    wide = GEN.generate(2026, 7, difficulty="medium", grid_h=4, grid_w=5, palette_size=2)
    query = {"input": wide, "output": GEN.rule_mirror(wide)}

    errors = GEN.lesson_identifiable(demos, query)
    assert any("fixed_width_4" in error for error in errors)

    wide_demo = {"input": wide, "output": GEN.rule_mirror(wide)}
    assert GEN.lesson_identifiable([*demos, wide_demo], query) == []


def test_canonical_shortcut_gate_preserves_the_public_semantic_registry():
    # The width shortcut belongs to the canonical-shortcut gate.  Expanding the
    # established semantic registry is an API compatibility regression because
    # repository tests and downstream tooling consume its exact contract.
    assert set(GEN.SEMANTIC_WITNESSES) == {"visible_lr_mirror"}
    assert set(GEN.SEMANTIC_RIVALS) == {"plain_repeat", "mirror_first"}
    assert GEN.WITNESS_RIVALS == {
        "visible_lr_mirror": ["plain_repeat", "mirror_first"]
    }
    assert set(GEN.LESSON_COMPETITORS) == {"fixed_width_4"}

    wide = GEN.generate(44, 0, grid_w=5)
    assert GEN.LESSON_COMPETITORS["fixed_width_4"](wide) != GEN.rule_mirror(wide)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_width_schedule_keeps_every_four_pair_lesson_rotation_identifiable(difficulty):
    """Every possible query rotation must leave a variable-width demo behind."""
    assert GEN.LESSON_SCHEDULE_PERIOD == 3
    for seed in (17, 2026):
        grids = [GEN.generate(seed, index, difficulty=difficulty) for index in range(24)]
        for index, grid in enumerate(grids):
            if index % GEN.LESSON_SCHEDULE_PERIOD == 0:
                assert GEN.strict_canonical_like(grid) == []
            else:
                assert len(grid[0]) in {5, 6}
        for start in range(len(grids) - 3):
            widths = [len(grid[0]) for grid in grids[start : start + 4]]
            assert sum(width != 4 for width in widths) >= 2


def test_width_schedule_never_overrides_explicit_controls():
    scheduled_wide = GEN.generate(
        99,
        1,
        difficulty="hard",
        grid_h=15,
        grid_w=4,
        palette_size=4,
    )
    assert GEN.observe_overrides(scheduled_wide) == {
        "grid_h": 15,
        "grid_w": 4,
        "palette_size": 4,
    }
