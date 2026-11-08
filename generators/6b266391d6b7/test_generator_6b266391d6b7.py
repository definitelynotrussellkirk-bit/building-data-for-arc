from __future__ import annotations

import copy
import importlib
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GEN = importlib.import_module("puzzle_generators.per_puzzle.6b266391d6b7.generator")


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != GEN.TASK_ID:
            continue
        pairs = list(row["train"]) + [row["test"]]
        return [
            [[int(value) for value in text_row] for text_row in pair["input"]]
            for pair in pairs
        ]
    raise AssertionError("canonical task not found")


def test_all_canonical_inputs_pass_strict_contract():
    grids = _canonical_inputs()
    assert len(grids) == 5
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
    assert {GEN.canonical_profile_index(grid) for grid in grids} == set(range(5))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generation_is_deterministic_fresh_and_rng_pure(band):
    random.seed(918273)
    state = random.getstate()
    first = GEN.generate(12345, 17, difficulty=band)
    assert random.getstate() == state
    second = GEN.generate(12345, 17, difficulty=band)
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert GEN.self_check(first) == []
    observed = GEN.observe_overrides(first)
    assert set(observed) == set(GEN.AXES)


def test_every_exact_axis_override_is_observable():
    cases = [
        {"grid_h": 10},
        {"grid_w": 12},
        {"n_markers": 5},
        {"motif_shape": "main_diag"},
        {"palette_kind": "mixed"},
        {
            "grid_h": 10,
            "grid_w": 12,
            "n_markers": 5,
            "motif_shape": "upper_l",
            "palette_kind": "mixed",
        },
    ]
    for overrides in cases:
        grid = GEN.generate(777, 4, difficulty="hard", **overrides)
        observed = GEN.observe_overrides(grid)
        for key, value in overrides.items():
            assert observed[key] == value


def test_unknown_override_fails_closed():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, bogus_axis=1)


def test_mutation_sensitive_self_check_rejects_structural_impostors():
    base = GEN.generate(13, 0, difficulty="easy")
    mutations = []

    blank_motif = copy.deepcopy(base)
    blank_motif[0][0] = 0
    blank_motif[1][0] = 0
    blank_motif[1][1] = 0
    mutations.append(blank_motif)

    edge_marker = copy.deepcopy(base)
    r, c = GEN._analyze(edge_marker)["markers"][0]
    edge_marker[r][c] = 0
    edge_marker[-1][-1] = 9
    mutations.append(edge_marker)

    foreign_color = copy.deepcopy(base)
    foreign_color[2][-1] = 6
    mutations.append(foreign_color)

    overlap = copy.deepcopy(base)
    markers = GEN._analyze(overlap)["markers"]
    for r, c in markers:
        overlap[r][c] = 0
    overlap[3][2] = 9
    overlap[4][3] = 9
    mutations.append(overlap)

    unsupported_mask = copy.deepcopy(base)
    unsupported_mask[0][1] = unsupported_mask[0][0]
    unsupported_mask[1][1] = unsupported_mask[0][0]
    mutations.append(unsupported_mask)

    assert all(GEN.self_check(grid) for grid in mutations)


def test_named_rivals_are_refuted_by_scheduled_three_demo_windows():
    for start in range(5):
        demos = []
        for offset in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(991 + start, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": GEN._truth(grid)})
        query_grid = GEN.generate(991 + start, start + GEN.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": GEN._truth(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []
