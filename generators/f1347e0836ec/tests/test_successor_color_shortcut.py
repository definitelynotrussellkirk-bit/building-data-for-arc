from __future__ import annotations

from puzzle_generators.per_puzzle.f1347e0836ec import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


RIVAL_NAME = "dot_successor_predicate"


def _demos(seed: int, start: int, band: str):
    return [
        {
            "input": grid,
            "output": gen.rule_mirror(grid),
        }
        for grid in (
            gen.generate(seed, sample_index, difficulty=band)
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED)
        )
    ]


def test_dot_successor_shortcut_is_declared_and_fits_all_canonical_pairs():
    rival = gen.CANONICAL_SHORTCUTS[RIVAL_NAME]
    pairs = canonical_pairs(gen.TASK_ID)

    assert len(pairs) == 4
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_known_surviving_lesson_now_refutes_dot_successor_shortcut():
    rival = gen.LESSON_COMPETITORS[RIVAL_NAME]

    for band in ("easy", "medium", "hard"):
        demos = _demos(seed=18, start=1, band=band)
        assert any(rival(demo["input"]) != demo["output"] for demo in demos)
        assert gen.lesson_identifiable(
            demos,
            {
                "input": gen.generate(
                    18, 1 + gen.EXAMPLES_NEEDED, difficulty=band
                )
            },
        ) == []
