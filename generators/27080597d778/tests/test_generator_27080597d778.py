"""Source-local regressions; canonical Racket parity is exercised separately."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

TASK = "27080597d778"
LIBRARY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(LIBRARY / "shared/runtime"))
SOURCE = Path(os.environ.get("ARCPUZZLES_TEST_GENERATOR", LIBRARY / f"generators/{TASK}/generator.py"))
spec = importlib.util.spec_from_file_location("subject_27080597d778", SOURCE)
assert spec is not None and spec.loader is not None
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


def canonical():
    with (LIBRARY / "shared/data/canonical/puzzles.jsonl").open() as handle:
        return next(row for line in handle if (row := json.loads(line)).get("task_id") == TASK)


def occupancy(grid):
    return Counter((row[c] != 0, row[c + 5] != 0) for row in grid for c in range(4))


def oracle(grid):
    """Audit-only predicate, independently checked against canonical stored labels."""
    cells = occupancy(grid)
    accept = cells[(False, False)] == cells[(True, True)] == 0
    return [[row[c] or row[c + 5] if accept else row[c] for c in range(4)] for row in grid]


def classify(grid):
    cells = occupancy(grid)
    overlaps, gaps = cells[(True, True)], cells[(False, False)]
    if overlaps and gaps:
        return "balanced" if overlaps == gaps else "mixed"
    return "overlap" if overlaps else "gap" if gaps else "complement"


def pair(grid):
    return {"input": grid, "output": oracle(grid)}


def test_all_nine_canonical_inputs_are_accepted_without_mutation():
    row = canonical()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 9
    for item in pairs:
        before = deepcopy(item["input"])
        assert subject.self_check(item["input"]) == []
        assert oracle(item["input"]) == item["output"]
        assert item["input"] == before


def test_unchanged_authority_is_pinned():
    code = canonical()["program_solution"]
    assert hashlib.sha256(" ".join(code.split()).encode()).hexdigest()[:12] == "7362bea2dda7"
    assert getattr(subject, "RULE_HASH", None) == "7362bea2dda7"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_draw_window_covers_both_sides_of_each_boolean_condition(band):
    for seed in range(12):
        for start in range(8):
            grids = [subject.generate(seed, start + i, difficulty=band) for i in range(4)]
            assert {classify(g) for g in grids} == {"complement", "overlap", "gap", "balanced"}
            assert all(subject.self_check(g) == [] for g in grids)


@pytest.mark.parametrize("bad", [None, 0, "", [], [[]], [[0] * 9, [0]], [[0] * 8] * 4,
                                 [[0] * 10] * 4, [[True] * 9] * 4, [[-1] * 9] * 4,
                                 [[10] * 9] * 4, [[1.0] * 9] * 4])
def test_malformed_inputs_report_errors_instead_of_raising(bad):
    before = deepcopy(bad)
    assert subject.self_check(bad)
    assert bad == before


@pytest.mark.parametrize("overrides", [
    {"bogus": 1}, {"grid_h": 2}, {"grid_h": 11}, {"grid_h": 4.5}, {"grid_h": True},
    {"color_left": 0}, {"color_right": 5}, {"color_right": 10}, {"color_left": True},
    {"palette_kind": "typo"}, {"fill_layout": "typo"}, {"balance": "typo"},
    {"branch": "typo"}, {"max_defects": 0}, {"max_defects": 4},
    {"anchor_endpoints": True}, {"asymmetry_force": True},
    {"palette_kind": "same", "color_left": 1, "color_right": 2},
    {"palette_kind": "distinct", "color_left": 1, "color_right": 1},
    {"texture": "checker", "fill_layout": "diag"},
])
def test_invalid_or_retired_overrides_are_loud(overrides):
    with pytest.raises(ValueError):
        subject.generate(17, 3, **overrides)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height", [3, 4, 10])
@pytest.mark.parametrize("branch", ["complement", "overlap", "gap", "balanced"])
def test_explicit_height_and_branch_are_observed_in_every_band(band, height, branch):
    grid = subject.generate(11, 5, difficulty=band, grid_h=height, branch=branch)
    assert len(grid) == height
    assert classify(grid) == branch
    assert subject.self_check(grid) == []
    observed = subject.observe_overrides(grid)
    assert observed["grid_h"] == height and observed["branch"] == branch


@pytest.mark.parametrize("seed", range(10))
def test_single_fault_counterfactuals_keep_the_left_panel_and_localize_the_cause(seed):
    base = subject.generate(seed, 7, branch="complement")
    grids = {name: subject.generate(seed, 7, branch=name, max_defects=1)
             for name in ("overlap", "gap", "balanced")}
    for name, grid in grids.items():
        assert [row[:5] for row in grid] == [row[:5] for row in base]
        changes = sum(a != b for ra, rb in zip(grid, base) for a, b in zip(ra, rb))
        assert changes == (2 if name == "balanced" else 1)
        assert oracle(grid) == [row[:4] for row in grid]
        assert oracle(grid) != [[row[c] or row[c + 5] for c in range(4)] for row in grid]
        # A clean row still has an observable fill, falsifying a row-local rule.
        assert any(all((row[c] == 0) != (row[c + 5] == 0) for c in range(4))
                   and any(row[c] == 0 and row[c + 5] != 0 for c in range(4)) for row in grid)
    assert oracle(base) != [row[:4] for row in base]
    assert occupancy(base).total() == occupancy(grids["balanced"]).total()
    assert sum(v != 0 for row in base for v in row) == sum(v != 0 for row in grids["balanced"] for v in row)


def test_named_rivals_are_falsified_and_three_demo_count_shortcut_is_rejected():
    assert getattr(subject, "EXAMPLES_NEEDED", None) == 4
    grids = [subject.generate(49, 8, branch=b, **({} if b == "complement" else {"max_defects": 1}))
             for b in ("complement", "overlap", "gap", "balanced")]
    lessons = [pair(g) for g in grids]
    assert subject.lesson_identifiable(lessons[:3], lessons[3])
    for start in range(8):
        demos = [pair(subject.generate(113, start + i)) for i in range(4)]
        for branch in ("complement", "overlap", "gap", "balanced"):
            query = pair(subject.generate(271, 31, branch=branch))
            assert subject.lesson_identifiable(demos, query) == []
    for name, solver in subject.SEMANTIC_RIVALS.items():
        assert any(solver(p["input"]) != p["output"] for p in lessons), name


def test_color_pins_are_honored_including_same_palette():
    for left in (1, 3, 9):
        for right in (1, 6, 9):
            g = subject.generate(13, 5, color_left=left, color_right=right)
            seen = subject.observe_overrides(g)
            assert seen["color_left"] == left and seen["color_right"] == right
            assert seen["palette_kind"] == ("same" if left == right else "distinct")
    for key in ("color_left", "color_right"):
        g = subject.generate(17, 0, palette_kind="same", **{key: 7})
        seen = subject.observe_overrides(g)
        assert seen["color_left"] == seen["color_right"] == 7


def test_replay_is_fresh_and_does_not_change_global_rng():
    random.seed(1234)
    saved = random.getstate()
    a = subject.generate(823, 103, difficulty="hard")
    assert random.getstate() == saved
    b = subject.generate(823, 103, difficulty="hard")
    assert a == b and a is not b
    assert all(ra is not rb for ra, rb in zip(a, b))
    a[0][0] = 0 if a[0][0] else 9
    assert a != b


@pytest.mark.parametrize("layout", ["alternating", "checker", "diag", "left_heavy", "right_heavy"])
def test_balance_is_rejected_for_fixed_density_layouts(layout):
    with pytest.raises(ValueError, match="balance"):
        subject.generate(17, 3, fill_layout=layout, balance="left")
    with pytest.raises(ValueError, match="balance"):
        subject.generate(17, 3, texture=layout, balance="right")


@pytest.mark.parametrize("cap", [1, 2, 3])
def test_explicit_fault_cap_is_rejected_on_explicit_fault_free_branch(cap):
    with pytest.raises(ValueError, match="max_defects"):
        subject.generate(17, 3, branch="complement", max_defects=cap)
