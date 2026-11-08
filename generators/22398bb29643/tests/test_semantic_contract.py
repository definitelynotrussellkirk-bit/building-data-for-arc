"""Executable shortcut and lesson-identifiability regressions."""
from __future__ import annotations

import importlib

from reviewer_support import canonical_pairs, find_root


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.22398bb29643.generator"
)
ROOT = find_root(__file__)
BANDS = ("easy", "medium", "hard")
RIVAL = "deduplicate_component_colors"
WITNESS = "repeated_component_color"


def _labeled(seed, sample_index, band):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_declared_shortcut_fits_every_canonical_pair():
    shortcut = GEN.CANONICAL_SHORTCUTS[RIVAL]
    for pair in canonical_pairs(GEN.TASK_ID, root=ROOT):
        assert shortcut(pair["input"]) == pair["output"]


def test_schedule_alternates_canonical_support_and_exact_counterexamples():
    rival = GEN.SEMANTIC_RIVALS[RIVAL]
    witness = GEN.SEMANTIC_WITNESSES[WITNESS]
    assert GEN.WITNESS_RIVALS[WITNESS] == [RIVAL]

    for band in BANDS:
        for sample_index in range(20):
            grid = GEN.generate(100 + sample_index, sample_index, difficulty=band)
            truth = GEN.rule_mirror(grid)
            expected_witness = sample_index % 2 == 1
            assert witness(grid) is expected_witness
            if expected_witness:
                assert rival(grid) != truth
                assert len(truth[0]) > len(rival(grid)[0])
            else:
                assert rival(grid) == truth


def test_three_demonstrations_identify_every_query_rotation():
    assert GEN.EXAMPLES_NEEDED == 3
    for band in BANDS:
        for start in (0, 7, 19):
            rows = [_labeled(200 + start, start + offset, band) for offset in range(4)]
            for query_index, query in enumerate(rows):
                demos = [row for index, row in enumerate(rows) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []


def test_schedule_profile_is_finite_and_complete():
    assert len(GEN.SCHEDULE_PROFILES) == 10
    for band in BANDS:
        observed = {
            GEN.schedule_profile(123, index, difficulty=band)
            for index in range(len(GEN.SCHEDULE_PROFILES))
        }
        assert observed == set(GEN.SCHEDULE_PROFILES)
