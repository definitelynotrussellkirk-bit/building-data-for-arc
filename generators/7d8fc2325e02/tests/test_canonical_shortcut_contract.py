"""Regression for the canonical-shortcut namespace contract."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7d8fc2325e02"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"shortcut_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_only_a_rule_that_fits_every_canonical_pair_is_declared_canonical_shortcut():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"canonical_colors_only"}
    shortcut = GEN.CANONICAL_SHORTCUTS["canonical_colors_only"]
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__)):
        assert shortcut(pair["input"]) == pair["output"]

    assert {"copy_top", "copy_bottom", "and", "xor", "constant_filled"} <= set(
        GEN.LESSON_COMPETITORS
    )
    assert not ({"copy_top", "copy_bottom", "and", "xor", "constant_filled"} & set(
        GEN.CANONICAL_SHORTCUTS
    ))


def test_noncanonical_role_colors_are_a_generated_counterexample_to_the_shortcut():
    shortcut = GEN.CANONICAL_SHORTCUTS["canonical_colors_only"]
    witness = GEN.SEMANTIC_WITNESSES["palette_generalization"]
    assert GEN.WITNESS_RIVALS["palette_generalization"] == ["canonical_colors_only"]

    grid = GEN.generate(
        991,
        7,
        grid_w=5,
        top_color=9,
        bot_color=8,
        sep_color=4,
    )
    assert GEN.self_check(grid) == []
    assert witness(grid)
    assert shortcut(grid) != GEN.rule_mirror(grid)

    # The ordinary unpinned schedule, not only explicit overrides, emits such cases.
    assert any(witness(GEN.generate(991, index)) for index in range(1, 8))
