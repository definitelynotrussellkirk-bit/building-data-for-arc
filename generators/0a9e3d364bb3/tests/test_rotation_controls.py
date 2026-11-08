from __future__ import annotations

from collections import Counter
import importlib

import pytest

TASK = "0a9e3d364bb3"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_query_rotation_keeps_all_four_shortcut_killers(difficulty):
    """An eight-pair lesson repeats the four-profile schedule exactly twice."""
    period = len(gen.SCHEDULE_PROFILES)
    assert period == 4
    assert gen.EXAMPLES_NEEDED == 2 * period - 1 == 7

    for start in range(period):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            sample_index = start + offset
            grid = gen.generate(2678160609 + start, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

        textures = [gen.observe_overrides(pair["input"])["texture"] for pair in pairs]
        assert Counter(textures) == Counter({texture: 2 for texture in gen.HELPFUL_TEXTURES})

        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert set(gen.observe_overrides(pair["input"])["texture"] for pair in demos) == set(
                gen.HELPFUL_TEXTURES
            )
            assert gen.lesson_identifiable(demos, query) == [], (
                difficulty,
                start,
                query_index,
                textures,
            )
