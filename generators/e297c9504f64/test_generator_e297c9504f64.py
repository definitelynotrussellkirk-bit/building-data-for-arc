"""Focused regressions for the repaired e297c9504f64 generator."""
from __future__ import annotations

import importlib
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.e297c9504f64.generator"
)
TASK_ID = MODULE.TASK_ID


def _canonical_pairs():
    source = Path(__file__).resolve().parents[3] / "data" / "canonical" / "puzzles.jsonl"
    row = next(
        json.loads(line)
        for line in source.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    for split in ("train", "test"):
        for pair in row[split]:
            yield split, pair


def _assert_rejected(grid, label):
    errors = MODULE.self_check(grid)
    assert errors, f"impostor {label!r} was accepted"


def _pair(grid):
    return {"input": grid, "output": MODULE.rule_mirror(grid)}


def main() -> None:
    assert MODULE.RULE_HASH == "a6e9d91342d0"

    random.seed(928374)
    before_state = random.getstate()
    first = MODULE.generate(41, 7, difficulty="medium")
    assert random.getstate() == before_state, "generator mutated global random state"
    second = MODULE.generate(41, 7, difficulty="medium")
    assert first == second, "deterministic replay mismatch"
    assert first is not second
    assert all(a is not b for a, b in zip(first, second)), "grid rows were aliased"
    assert not MODULE.self_check(first)

    # Every exact axis boundary works in every band and every scheduled profile.
    checked = 0
    for band in ("easy", "medium", "hard"):
        for h in (8, 10):
            for w in (11, 14):
                for count in (3, 4):
                    for sample_index in range(9):
                        grid = MODULE.generate(
                            1000 + checked,
                            sample_index,
                            difficulty=band,
                            grid_h=h,
                            grid_w=w,
                            n_red_components=count,
                        )
                        assert not MODULE.self_check(grid)
                        assert MODULE.observe_overrides(grid) == {
                            "grid_h": h,
                            "grid_w": w,
                            "n_red_components": count,
                        }
                        checked += 1

    canonical = list(_canonical_pairs())
    assert len(canonical) == 4
    for index, (_split, pair) in enumerate(canonical):
        assert not MODULE.self_check(pair["input"]), (
            index,
            MODULE.self_check(pair["input"]),
        )
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]

    # The real canonical set cannot refute the fixed-column-1 rival, while the
    # repaired generator produces explicit column-0/2 counterexamples.
    assert all(
        MODULE._rival_fixed_column_one(pair["input"]) == pair["output"]
        for _split, pair in canonical
    )
    fixed_column_refutations = 0
    for band in ("easy", "medium", "hard"):
        for sample_index in range(18):
            grid = MODULE.generate(700 + sample_index, sample_index, difficulty=band)
            if MODULE._witness_target_not_canonical_column(grid):
                fixed_column_refutations += 1
                assert MODULE._rival_fixed_column_one(grid) != MODULE.rule_mirror(grid)
    assert fixed_column_refutations > 0

    # Every sliding three-demo lesson refutes every named competitor.
    for band in ("easy", "medium", "hard"):
        for start in range(27):
            demos = [
                _pair(MODULE.generate(9001, start + offset, difficulty=band))
                for offset in range(3)
            ]
            query = _pair(MODULE.generate(9001, start + 3, difficulty=band))
            assert not MODULE.lesson_identifiable(demos, query), (
                band,
                start,
                MODULE.lesson_identifiable(demos, query),
            )
            for name, competitor in MODULE.LESSON_COMPETITORS.items():
                assert not all(
                    competitor(demo["input"]) == demo["output"] for demo in demos
                ), (band, start, name)

    blank = [[0] * 11 for _ in range(8)]
    _assert_rejected(blank, "no red components")

    single = [[0] * 11 for _ in range(8)]
    single[1][1] = single[2][1] = 2
    _assert_rejected(single, "single red component")

    tied_left = [[0] * 11 for _ in range(8)]
    tied_left[0][1] = tied_left[1][1] = 2
    tied_left[4][1] = tied_left[5][1] = 2
    tied_left[2][7] = tied_left[3][7] = 2
    _assert_rejected(tied_left, "two red components share the left column")

    generated = MODULE.generate(123, 0, difficulty="easy")
    two_distractors = [row[:] for row in generated]
    zeros = [
        (r, c)
        for r, row in enumerate(two_distractors)
        for c, value in enumerate(row)
        if value == 0
    ]
    two_distractors[zeros[-1][0]][zeros[-1][1]] = 3
    _assert_rejected(two_distractors, "multiple non-red distractors")

    touching = [row[:] for row in MODULE.generate(321, 1, difficulty="easy")]
    target_cell = next(
        (r, c)
        for r, row in enumerate(touching)
        for c, value in enumerate(row)
        if value == 2
        and c > 0
        and touching[r][c - 1] == 0
    )
    touching[target_cell[0]][target_cell[1] - 1] = 3
    _assert_rejected(touching, "different colors touch orthogonally")

    for kwargs in ({"texture": "no_objects"}, {"unknown_axis": 3}):
        try:
            MODULE.generate(1, 0, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unknown override was silently accepted: {kwargs}")

    print(
        "focused regressions: PASS; 4 canonical pairs, "
        f"{checked} exact override/profile cases, 81 lesson windows"
    )


def test_generator_contract() -> None:
    main()


if __name__ == "__main__":
    main()
