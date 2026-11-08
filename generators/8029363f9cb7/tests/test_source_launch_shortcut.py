"""Regression tests for the canonical source-anchor shortcut."""
from __future__ import annotations

import importlib

from reviewer_support import canonical_pairs, find_root


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.8029363f9cb7.generator"
)


def _canonical_pairs():
    return canonical_pairs("8029363f9cb7", root=find_root(__file__))


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    pairs = _canonical_pairs()
    assert pairs
    assert GEN.CANONICAL_SHORTCUTS
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_nearest_frame_launch_shortcut_is_declared_and_generated_against():
    name = "launch_away_from_nearest_vertical_frame"
    shortcut = GEN.CANONICAL_SHORTCUTS[name]
    assert GEN.LESSON_COMPETITORS[name] is shortcut

    for difficulty in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(8):
                grids = [
                    GEN.generate(seed, start + offset, difficulty=difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                assert any(
                    GEN._analysis(grid)["source"][1] > (len(grid[0]) - 1) / 2
                    for grid in grids
                ), (difficulty, seed, start)
                assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in grids)

                demos = [
                    {"input": grid, "output": GEN.rule_mirror(grid)}
                    for grid in grids
                ]
                query = _pair(
                    seed,
                    start + GEN.EXAMPLES_NEEDED,
                    difficulty,
                )
                assert GEN.lesson_identifiable(demos, query) == []


def test_scene_profiles_realize_their_declared_source_side():
    for profile_name, profile in GEN._PROFILE_ROWS:
        for seed in (0, 1, 19, 991):
            grid = GEN.generate(
                seed,
                11,
                difficulty=profile.band,
                scene_profile=profile_name,
            )
            analysis = GEN._analysis(grid)
            assert analysis["source_side"] == profile.source_side
            assert GEN.observe_overrides(grid) == {"scene_profile": profile_name}


def test_every_five_pair_window_survives_each_query_rotation():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(8):
                pairs = [
                    _pair(seed, start + offset, difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED + 1)
                ]
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs)
                        if index != query_index
                    ]
                    assert GEN.lesson_identifiable(demos, query) == [], (
                        difficulty,
                        seed,
                        start,
                        query_index,
                    )
