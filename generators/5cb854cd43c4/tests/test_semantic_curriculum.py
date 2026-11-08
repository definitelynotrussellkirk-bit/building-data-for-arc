"""Regression tests for lesson-level identifiability in 5cb854cd43c4."""
from __future__ import annotations

import importlib
import json
from pathlib import Path


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.5cb854cd43c4.generator"
)
TASK_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = TASK_ROOT / "data/canonical/puzzles.jsonl"


def canonical_pairs():
    with CANONICAL.open() as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                test = row["test"]
                return row["train"] + (
                    test if isinstance(test, list) else [test]
                )
    raise AssertionError("canonical row not found")


def pair(grid):
    return {"input": grid, "output": generator.rule_mirror(grid)}


def test_semantic_contract_names_the_two_canonical_shortcuts():
    assert generator.SIZE_REGIMES == ("canonical", "varied")
    assert set(generator.SEMANTIC_WITNESSES) == {
        "split_same_color_components",
        "equal_size_color_tie",
    }
    assert set(generator.SEMANTIC_RIVALS) == {
        "merge_disconnected_same_color",
        "larger_color_first_on_ties",
    }
    assert set(generator.CANONICAL_SHORTCUTS) == set(generator.SEMANTIC_RIVALS)
    assert set(generator.LESSON_COMPETITORS) == set(generator.SEMANTIC_RIVALS)
    assert generator.SCHEDULE_PROFILES == (
        "split_color_witness",
        "tie_break_witness",
        "ordinary",
    )


def test_shortcuts_fit_canonical_pairs_but_scheduled_witnesses_refute_them():
    for rival in generator.CANONICAL_SHORTCUTS.values():
        assert all(rival(p["input"]) == p["output"] for p in canonical_pairs())

    for profile_index, profile in enumerate(generator.SCENE_PROFILES):
        repeated = generator.generate(
            41_000 + profile_index,
            30,
            difficulty="medium",
            scene_profile=profile,
        )
        assert generator.schedule_profile(0, 30) == "split_color_witness"
        assert generator.observe_overrides(repeated) == {
            "scene_profile": profile,
            "size_regime": "varied",
        }
        assert generator.SEMANTIC_WITNESSES[
            "split_same_color_components"
        ](repeated)
        assert generator.SEMANTIC_RIVALS[
            "merge_disconnected_same_color"
        ](repeated) != generator.rule_mirror(repeated)

        tied = generator.generate(
            42_000 + profile_index,
            31,
            difficulty="hard",
            scene_profile=profile,
        )
        assert generator.schedule_profile(0, 31) == "tie_break_witness"
        assert generator.observe_overrides(tied) == {
            "scene_profile": profile,
            "size_regime": "varied",
        }
        assert generator.SEMANTIC_WITNESSES[
            "equal_size_color_tie"
        ](tied)
        assert generator.SEMANTIC_RIVALS[
            "larger_color_first_on_ties"
        ](tied) != generator.rule_mirror(tied)


def test_every_default_three_demo_window_refutes_both_shortcuts():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            seed = 71_000 + 1_000 * band_index + start
            demos = [
                generator.generate(seed, start + offset, difficulty=band)
                for offset in range(generator.EXAMPLES_NEEDED)
            ]
            query = generator.generate(
                seed,
                start + generator.EXAMPLES_NEEDED,
                difficulty=band,
            )
            for rival in generator.LESSON_COMPETITORS.values():
                assert any(
                    rival(grid) != generator.rule_mirror(grid)
                    for grid in demos
                )
            assert generator.lesson_identifiable(
                [pair(grid) for grid in demos], pair(query)
            ) == []
