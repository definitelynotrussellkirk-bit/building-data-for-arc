"""Regressions for the unresolved axis-trimming audit and strict call contract."""
from __future__ import annotations

import importlib.util

import pytest

from reviewer_support import find_root


TASK_ID = "d2b3402dde86"
BANDS = ("easy", "medium", "hard")


@pytest.fixture(scope="module")
def generator():
    root = find_root(__file__)
    candidates = (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("axis_trim_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def pair(generator, seed, index, *, difficulty):
    grid = generator.generate(seed, index, difficulty=difficulty)
    return {"input": grid, "output": generator.rule_mirror(grid)}


def test_axis_specific_trimming_rivals_are_declared_and_refuted_in_rotated_windows(generator):
    names = ("trim_zero_rows_only", "trim_zero_cols_only")
    assert set(names) <= set(generator.LESSON_COMPETITORS)

    # Cover all cyclic residues of the four-pair schedule at multiple seed phases.
    for band in BANDS:
        for seed in range(8):
            population = [pair(generator, seed, index, difficulty=band) for index in range(11)]
            for start in range(8):
                window = population[start:start + 4]
                for query_index, query in enumerate(window):
                    demos = [item for i, item in enumerate(window) if i != query_index]
                    for name in names:
                        rival = generator.LESSON_COMPETITORS[name]
                        survives = all(rival(item["input"]) == item["output"] for item in demos)
                        assert not (survives and rival(query["input"]) != query["output"]), (
                            band,
                            seed,
                            start,
                            query_index,
                            name,
                        )


def test_default_schedule_supplies_two_row_and_two_column_trim_witnesses(generator):
    for band in BANDS:
        for seed in range(8):
            for start in range(8):
                answers = [
                    generator.rule_mirror(generator.generate(seed, index, difficulty=band))
                    for index in range(start, start + 4)
                ]
                blank_outer_row = [
                    (not any(answer[0])) or (not any(answer[-1]))
                    for answer in answers
                ]
                blank_outer_col = [
                    (not any(row[0] for row in answer))
                    or (not any(row[-1] for row in answer))
                    for answer in answers
                ]
                assert sum(blank_outer_row) >= 2, (band, seed, start, "rows")
                assert sum(blank_outer_col) >= 2, (band, seed, start, "cols")


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, "easy"),
        (False, 0, "easy"),
        (0, True, "easy"),
        (0, False, "easy"),
        (0, -1, "easy"),
        (0, 0, True),
        (0, 0, False),
        (0, 0, 0),
        (0, 0, 1.0),
        (0, 0, "__invalid_difficulty__"),
    ],
)
def test_invalid_generation_scalars_are_rejected(generator, seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(seed, sample_index, difficulty=difficulty)
