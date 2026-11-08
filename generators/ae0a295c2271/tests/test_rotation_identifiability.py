"""Leave-one-out teaching regressions for the four-pair lesson window."""
from __future__ import annotations

from reviewer_support import find_root, load_selected_generator

TASK_ID = "ae0a295c2271"
ROOT = find_root(__file__)
GEN, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_every_four_pair_window_is_identifiable_under_each_query_rotation() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [
                _pair(GEN.generate(1364470557, start + offset, difficulty=band))
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                    GEN.lesson_identifiable(demos, query),
                )
