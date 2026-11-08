"""Focused regressions for the contact-degree generator and lesson contract."""
from __future__ import annotations

import json
from pathlib import Path
import sys

try:
    from reviewer_support import canonical_pairs, find_root, load_selected_generator
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "7f2dafa2bee4"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)
COUNTEREXAMPLE = (
    Path(__file__).resolve().parents[1]
    / "counterexamples/review-f11e3f284c61d419-v0001/retained/checks/audit"
    / TASK_ID
    / "counterexample.json"
)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_match_python_rule_mirror():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_retained_unseen_degree_zero_lesson_is_rejected():
    retained = json.loads(COUNTEREXAMPLE.read_text(encoding="utf-8"))
    records = retained["records"]
    demos = [
        {"input": row["input"], "output": row["racket_output"]}
        for row in records
        if row["role"] == "demo"
    ]
    query_row = next(row for row in records if row["role"] == "query")
    query = {"input": query_row["input"], "output": query_row["racket_output"]}
    assert gen.lesson_identifiable(demos, query) == [
        "competitor degree_zero_as_two fits every demonstration"
    ]


def test_every_four_pair_window_survives_query_rotation():
    assert gen.EXAMPLES_NEEDED == 3
    for difficulty in (None, "easy", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _pair(gen.generate(20261024 + start, index, difficulty=difficulty))
                for index in range(start, start + gen.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    query_index,
                    [gen.semantic_observables(pair["input"]) for pair in pairs],
                )


def test_every_four_pair_window_has_two_degree_zero_witnesses():
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        grids = [gen.generate(99, index) for index in range(start, start + 4)]
        witnesses = sum(
            gen.semantic_observables(grid)["has_degree_zero"] for grid in grids
        )
        assert witnesses >= 2


def test_degree_zero_rival_is_lesson_only_not_a_canonical_shortcut():
    assert gen.CANONICAL_SHORTCUTS == {}
    assert set(gen.LESSON_COMPETITORS) == {"degree_zero_as_two"}
    assert set(gen.SEMANTIC_RIVALS) == {"degree_zero_as_two"}
