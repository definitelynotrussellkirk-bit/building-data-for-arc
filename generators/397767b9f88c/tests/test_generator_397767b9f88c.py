from __future__ import annotations

import importlib


gen = importlib.import_module("puzzle_generators.per_puzzle.397767b9f88c.generator")


def pair(seed: int, sample: int, band: str = "medium") -> dict:
    grid = gen.generate(seed, sample, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_each_generated_scene_refutes_six_transform_without_diagonals() -> None:
    rival = gen.SEMANTIC_RIVALS["rotations_and_axis_reflections_only"]
    for seed in (0, 10, 37):
        for sample in range(4):
            grid = gen.generate(seed, sample, difficulty="medium")
            assert gen.rule_mirror(grid) != rival(grid)
            assert gen.SEMANTIC_WITNESSES["diagonal_reflection_required"](grid)


def test_three_demo_lessons_falsify_every_named_rival() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            rows = [pair(seed, sample, band) for sample in range(4)]
            assert gen.lesson_identifiable(rows[:3], rows[3]) == []
