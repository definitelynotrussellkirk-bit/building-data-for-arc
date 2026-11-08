"""Review regressions for stronger canonical-equivalent shortcuts."""
from __future__ import annotations

import importlib

import pytest


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.8c6fbfbe20d4.generator"
)


def _legend_union_filter(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: erase body colors absent from both sparse header lists."""
    sources = [value for value in grid[0] if value != 0]
    targets = [value for value in grid[1] if value != 0]
    mapping = dict(zip(sources, targets))
    mentioned = set(sources) | set(targets)
    return [
        [
            mapping.get(value, value)
            if value == 0 or value in mentioned
            else 0
            for value in row
        ]
        for row in grid[2:]
    ]


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


@pytest.mark.parametrize(
    ("difficulty", "seed", "sample_index"),
    [
        ("easy", 126142983109973, 0),
        ("medium", 271096593352463, 0),
        ("hard", 27891514752213, 165),
    ],
)
def test_four_profile_lessons_refute_legend_union_filter(
    difficulty: str, seed: int, sample_index: int
) -> None:
    """Every complete scheduled lesson must expose a truly neutral body value."""
    demos = [
        _pair(seed, sample_index + offset, difficulty)
        for offset in range(gen.EXAMPLES_NEEDED)
    ]

    assert any(
        _legend_union_filter(pair["input"]) != pair["output"]
        for pair in demos
    )


def test_legend_union_filter_is_bound_into_the_semantic_contract() -> None:
    name = "erase_body_colors_absent_from_headers"
    assert name in gen.SEMANTIC_RIVALS
    assert name in gen.LESSON_COMPETITORS
    assert name in gen.CANONICAL_SHORTCUTS
    assert name in gen.WITNESS_RIVALS["neutral_body_value_is_preserved"]
