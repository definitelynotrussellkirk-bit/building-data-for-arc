"""Canonical rival honesty and scheduled lesson evidence for c1ae510562f9.

The labels used by the schedule test are an independent interpretation of the
documented row predicate. The final public Racket lesson census checks actual
reference labels; these tests do not claim to replace that execution.
"""

from __future__ import annotations

import importlib.util
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "c1ae510562f9"
SPIRAL = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2),
          (2, 1), (2, 0), (1, 0), (1, 1))


@pytest.fixture(scope="module")
def selected():
    root = find_root(__file__)
    path = root / "generators" / TASK_ID / "generator.py"
    if not path.is_file():
        path = root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("semantic_review_selected", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def independent_label(grid):
    gray = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 5]
    top, floor = min(r for r, _ in gray), max(r for r, _ in gray)
    left, right = min(c for _, c in gray), max(c for _, c in gray)
    count = sum(all(grid[r][c] == 0 for c in range(left + 1, right))
                for r in range(top, floor))
    output = [[0] * 3 for _ in range(3)]
    for r, c in SPIRAL[:min(9, count)]:
        output[r][c] = 8
    return output


def declared_rivals(selected, namespace):
    declaration = getattr(selected, namespace, None)
    assert isinstance(declaration, dict) and declaration, f"missing {namespace}"
    assert all(isinstance(name, str) and callable(rival)
               for name, rival in declaration.items())
    return declaration.items()


def test_canonical_shortcuts_fit_every_labeled_pair(selected):
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert pairs
    for pair in pairs:
        assert independent_label(pair["input"]) == pair["output"]
    for name, rival in declared_rivals(selected, "CANONICAL_SHORTCUTS"):
        failures = [(pair["variant"], pair["split"], pair["pair_index"])
                    for pair in pairs if rival(pair["input"]) != pair["output"]]
        assert not failures, f"{name} is refuted by canonical pairs {failures}"


def test_combined_witness_refutes_every_canonical_shortcut(selected):
    # Public apply receipt checks/semantic_review/racket.json, result index 3,
    # rule 7a7c1a560527: five empty rows and two complementary partial rows.
    rows = [[8, 0], [0, 0], [0, 0], [0, 8], [0, 0], [0, 0], [0, 0]]
    grid = [[0] * 6] + [[0, 5, *row, 5, 0] for row in rows] + [[0, 5, 5, 5, 5, 0]]
    racket_output = [[8, 8, 8], [0, 0, 8], [0, 0, 8]]
    assert independent_label(grid) == racket_output
    for name, rival in declared_rivals(selected, "CANONICAL_SHORTCUTS"):
        assert rival(grid) != racket_output, f"{name} lacks the claimed combined witness"


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 1, 17))
def test_every_default_schedule_start_and_query_holdout(selected, difficulty, seed):
    period = getattr(selected, "LESSON_SCHEDULE_PERIOD", None)
    assert isinstance(period, int) and not isinstance(period, bool) and period > 0
    demonstrations = getattr(selected, "EXAMPLES_NEEDED", None)
    assert demonstrations == 4, "This curriculum claims four demonstrations plus one query."
    window_size = demonstrations + 1
    grids = [selected.generate(seed, index, difficulty=difficulty)
             for index in range(period + demonstrations)]
    labels = [independent_label(grid) for grid in grids]
    rivals = [(f"{namespace}.{name}", rival)
              for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")
              for name, rival in declared_rivals(selected, namespace)]
    for name, rival in rivals:
        predictions = [rival(grid) for grid in grids]
        for start in range(period):
            positions = list(range(start, start + window_size))
            refuting = [index for index in positions if predictions[index] != labels[index]]
            for query in positions:
                assert query not in refuting or any(index != query for index in refuting), (
                    f"{name}: difficulty={difficulty}, seed={seed}, start={start}, "
                    f"query={query}, refuting sample indices={refuting}"
                )


def test_column_and_area_offset_shortcuts_preserve_a_demo_witness(selected):
    # A real omitted-rival failure from the first Racket census. At seed
    # 894201600, easy start 3, its query holdout at position 1 was the only
    # positive canonical example. Subtracting one from a column's zero count
    # fit all four remaining labels but undercounted that query. The same
    # failure appears in checks/semantic_review/offsets-before.json.
    grids = [selected.generate(894201600, index, difficulty="easy") for index in range(3, 8)]
    labels = [independent_label(grid) for grid in grids]
    rows_by_grid = []
    for grid in grids:
        gray = [(r, c) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value == 5]
        top, floor = min(r for r, _ in gray), max(r for r, _ in gray)
        left, right = min(c for _, c in gray), max(c for _, c in gray)
        rows_by_grid.append([row[left + 1:right] for row in grid[top:floor]])
    for role in ("left", "middle", "right", "area"):
        for offset in (1, 2):
            predictions = []
            for rows in rows_by_grid:
                if role == "area":
                    count = sum(value == 0 for row in rows for value in row) // len(rows[0])
                else:
                    col = {"left": 0, "middle": len(rows[0]) // 2, "right": len(rows[0]) - 1}[role]
                    count = sum(row[col] == 0 for row in rows)
                result = [[0] * 3 for _ in range(3)]
                for r, c in SPIRAL[:max(0, min(9, count - offset))]:
                    result[r][c] = 8
                predictions.append(result)
            refuting = [index for index, (expected, actual) in enumerate(zip(labels, predictions))
                        if expected != actual]
            assert len(refuting) != 1, f"{role} minus {offset}: sole refuting holdout {refuting}"
