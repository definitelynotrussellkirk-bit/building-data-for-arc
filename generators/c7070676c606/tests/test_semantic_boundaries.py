"""Frozen reference boundaries and observable self-check regressions.

Run through ``review.py run ... -m pytest`` or the public task_tests stage.
Frozen outputs came from the selected Racket rule, not generator helpers.
The independent union-find oracle is test-only and never supplies labels to
generation. Real reference replay is in workspace/check_semantics.py.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK = "c7070676c606"
ROOT = find_root(__file__)
HOMES = (ROOT / "generators" / TASK,
         ROOT / "puzzle_generators" / "per_puzzle" / TASK)
SOURCE = next(home / "generator.py" for home in HOMES
              if (home / "generator.py").is_file())
FIXTURE_PATH = next(home / "counterexamples" / "semantic_boundaries.json"
                    for home in HOMES
                    if (home / "counterexamples" / "semantic_boundaries.json").is_file())
SPEC = importlib.util.spec_from_file_location("c7070676c606_boundary_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
FIXTURES = json.loads(FIXTURE_PATH.read_text())
CASES = {case["id"]: case for case in FIXTURES["cases"]}
LAWFUL = [case for case in CASES.values() if case["valid_rank"]]
UNDEFINED = [case for case in CASES.values() if not case["valid_rank"]]
CANONICAL = canonical_pairs(TASK, root=ROOT, labeled_only=True)


def independent_candidates(grid):
    """Union adjacent green cells, then discard any entire row-0 component."""
    parents = {(r, c): (r, c) for r, row in enumerate(grid)
               for c, color in enumerate(row) if color == 3}

    def representative(cell):
        while parents[cell] != cell:
            cell = parents[cell]
        return cell

    for r, c in parents:
        for neighbor in ((r + 1, c), (r, c + 1)):
            if neighbor in parents:
                parents[representative(neighbor)] = representative((r, c))
    groups = {}
    for cell in parents:
        groups.setdefault(representative(cell), set()).add(cell)
    return [cells for cells in groups.values() if min(r for r, c in cells) > 0]


def independent_output(grid):
    candidates = sorted(independent_candidates(grid), key=lambda cells: (-len(cells), min(cells)))
    rank = grid[0].count(1)
    if not 1 <= rank <= len(candidates):
        raise ValueError("rank is undefined for the eligible component count")
    output = deepcopy(grid)
    for r, c in candidates[rank - 1]:
        output[r][c] = 2
    return output


def checked_messages(grid):
    original = deepcopy(grid)
    messages = GEN.self_check(grid)
    assert isinstance(messages, list) and all(isinstance(message, str) for message in messages)
    assert grid == original, "self_check must not mutate its input"
    return messages


def test_fixtures_are_bound_to_the_current_selected_rule():
    with canonical_path(ROOT).open() as handle:
        rows = (json.loads(line) for line in handle if line.strip())
        records = [row for row in rows if row.get("task_id") == TASK]
    assert len(records) == 1
    digest = hashlib.sha256(records[0]["program_solution"].encode()).hexdigest()
    assert digest == FIXTURES["reference"]["rule_text_sha256"]


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=[f"canonical-{p['variant']}-{p['split']}-{p['pair_index']}" for p in CANONICAL])
def test_all_labeled_canonical_inputs_are_accepted(pair):
    assert checked_messages(deepcopy(pair["input"])) == []
    assert independent_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("case", LAWFUL, ids=[case["id"] for case in LAWFUL])
def test_lawful_reference_boundaries_are_accepted(case):
    assert checked_messages(deepcopy(case["input"])) == [], case["purpose"]


@pytest.mark.parametrize("case", UNDEFINED, ids=[case["id"] for case in UNDEFINED])
def test_undefined_ranks_are_rejected(case):
    with pytest.raises(ValueError, match="rank is undefined"):
        independent_output(case["input"])
    assert checked_messages(deepcopy(case["input"])), case["purpose"]


@pytest.mark.parametrize("case", LAWFUL, ids=[case["id"] for case in LAWFUL])
def test_frozen_output_recolors_exactly_the_reference_target(case):
    assert independent_output(case["input"]) == case["output"]
    changed = [[r, c] for r, row in enumerate(case["input"])
               for c, color in enumerate(row) if case["output"][r][c] != color]
    assert changed == case["expected_target_cells"]
    assert all(case["input"][r][c] == 3 and case["output"][r][c] == 2
               for r, c in changed)


def test_tie_counterexample_separates_first_occupied_cell_from_bbox_corner():
    case = CASES["ties_first_occupied_vs_bbox"]
    tied = [cells for cells in independent_candidates(case["input"]) if len(cells) == 11]
    occupied_order = sorted(tied, key=min)
    bbox_order = sorted(tied, key=lambda cells: (min(r for r, c in cells), min(c for r, c in cells)))
    assert [min(cells) for cells in occupied_order] == [(2, 4), (2, 9)]
    assert bbox_order == occupied_order[::-1]
    assert set(map(tuple, case["expected_target_cells"])) == occupied_order[1]


def test_compact_witness_has_two_marker_cells_but_one_marker_run():
    case = CASES["compact_eight_rival_witness"]
    grid = case["input"]
    assert grid[0].count(1) == 2
    assert sum(value == 1 for row in grid for value in row) == 3
    assert sum(value == 1 and (c == 0 or grid[0][c - 1] != 1)
               for c, value in enumerate(grid[0])) == 1
    assert sorted(map(len, independent_candidates(grid))) == [2, 3, 4]
    assert len(case["reference_refuted_rivals"]) == 8
