"""Focused repair contract for matching-corner rectangle borders."""
from __future__ import annotations

import copy
import json
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "8c82d72dafe9"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))


def positions(grid):
    found = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                found.setdefault(value, []).append((r, c))
    return found


def border(cells):
    (r1, c1), (r2, c2) = cells
    r0, r3 = sorted((r1, r2))
    c0, c3 = sorted((c1, c2))
    return {
        (r, c)
        for r in range(r0, r3 + 1)
        for c in range(c0, c3 + 1)
        if r in (r0, r3) or c in (c0, c3)
    }


def intended(grid):
    """Independent mirror of the row-major color-order Racket authority."""
    out = copy.deepcopy(grid)
    for color, cells in positions(grid).items():
        if len(cells) != 2:
            continue
        if cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]:
            continue
        for r, c in border(cells):
            out[r][c] = color
    return out


def higher_color_wins(grid):
    out = copy.deepcopy(grid)
    candidates = {}
    for color, cells in positions(grid).items():
        if len(cells) == 2 and cells[0][0] != cells[1][0] and cells[0][1] != cells[1][1]:
            for point in border(cells):
                candidates.setdefault(point, []).append(color)
    for (r, c), colors in candidates.items():
        out[r][c] = max(colors)
    return out


def expand_collinear(grid):
    out = copy.deepcopy(grid)
    for color, cells in positions(grid).items():
        if len(cells) != 2:
            continue
        for r, c in border(cells):
            out[r][c] = color
    return out


def pair(seed, sample_index, difficulty="medium"):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": intended(grid)}


def test_rule_pin_public_controls_and_schedule_surface():
    assert GEN.RULE_HASH == "70532d39072c"
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == {
        "grid_h", "grid_w", "n_rects", "n_nonpair", "n_collinear"
    }
    assert GEN.EXAMPLES_NEEDED == 4
    assert len(GEN.SCHEDULE_PROFILES) == 5
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


@pytest.mark.parametrize("canonical", CANONICAL)
def test_all_canonical_inputs_are_accepted_and_exact(canonical):
    grid = canonical["input"]
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert intended(grid) == canonical["output"]
    assert GEN.rule_mirror(grid) == canonical["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(9, 10), (18, 18)])
@pytest.mark.parametrize("n_rects", [1, 4])
@pytest.mark.parametrize("n_nonpair", [0, 2])
@pytest.mark.parametrize("n_collinear", [0, 1])
def test_boundary_overrides_are_exact_and_constructive(
    difficulty, grid_h, grid_w, n_rects, n_nonpair, n_collinear
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_rects": n_rects,
        "n_nonpair": n_nonpair,
        "n_collinear": n_collinear,
    }
    grid = GEN.generate(71, 19, difficulty=difficulty, **requested)
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid) == requested
    assert grid == GEN.generate(71, 19, difficulty=difficulty, **requested)


@pytest.mark.parametrize("overrides", [
    {"unknown_axis": 1},
    {"grid_h": 8}, {"grid_h": 19}, {"grid_h": 10.0}, {"grid_h": True},
    {"grid_w": 9}, {"grid_w": 19}, {"grid_w": "10"},
    {"n_rects": 0}, {"n_rects": 5}, {"n_rects": 2.0},
    {"n_nonpair": -1}, {"n_nonpair": 3}, {"n_nonpair": False},
    {"n_collinear": -1}, {"n_collinear": 2}, {"n_collinear": "1"},
])
def test_unknown_noninteger_and_out_of_range_overrides_reject(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


def test_declared_canonical_shortcuts_reproduce_every_public_pair():
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "expand_all_exactly_two_bboxes", "higher_color_wins_crossings"
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(row["input"]) == row["output"] for row in CANONICAL), name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_schedule_visits_all_profiles_and_named_witnesses(difficulty):
    profiles = [GEN.schedule_profile(0, index, difficulty) for index in range(5)]
    assert profiles == list(GEN.SCHEDULE_PROFILES)
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(10):
        grid = GEN.generate(400 + index, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            if witness(grid):
                hits[name] += 1
                truth = intended(grid)
                for rival_name in GEN.WITNESS_RIVALS[name]:
                    assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(count > 0 for count in hits.values()), hits


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_cyclic_five_pair_window_and_query_rotation_is_identifiable(difficulty):
    for start in range(5):
        rows = [pair(9000 + start, start + offset, difficulty) for offset in range(5)]
        for query_index in range(5):
            demos = [row for index, row in enumerate(rows) if index != query_index]
            query = rows[query_index]
            assert GEN.lesson_identifiable(demos, query) == [], (
                difficulty, start, query_index,
                GEN.lesson_identifiable(demos, query),
            )


def test_lower_color_overlap_is_exact_counterexample_to_canonical_fitting_rival():
    grid = next(
        GEN.generate(1234, index, difficulty="medium")
        for index in range(10)
        if GEN.SEMANTIC_WITNESSES["lower_color_wins_overlap"](
            GEN.generate(1234, index, difficulty="medium")
        )
    )
    assert GEN.self_check(grid) == []
    truth = intended(grid)
    rival = higher_color_wins(grid)
    assert GEN.rule_mirror(grid) == truth
    assert GEN.CANONICAL_SHORTCUTS["higher_color_wins_crossings"](grid) == rival
    assert truth != rival


def test_collinear_pair_is_preserved_and_refutes_bbox_shortcut():
    grid = next(
        GEN.generate(4321, index, difficulty="medium")
        for index in range(10)
        if GEN.SEMANTIC_WITNESSES["collinear_exact_pair"](
            GEN.generate(4321, index, difficulty="medium")
        )
    )
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == intended(grid)
    assert expand_collinear(grid) != intended(grid)


def test_self_check_rejects_malformed_and_no_qualifying_rectangle():
    for grid in (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[0, 0], [0, 0]],
        [[0, 2, 0], [0, 0, 2]],  # diagonal but only 2x2 span is still lawful
        [[0, True, 0], [0, 0, 0], [0, 0, 0]],
    ):
        if grid == [[0, 2, 0], [0, 0, 2]]:
            # A non-degenerate two-row/two-column rectangle is allowed by authority.
            assert GEN.self_check(grid) == []
        else:
            assert GEN.self_check(grid)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20261008)
    state = random.getstate()
    first = GEN.generate(77, 8, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 8, difficulty="hard")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_actual_racket_matches_independent_mirror_on_canonical_and_generated():
    from arcpuzzles import Catalog

    inputs = [row["input"] for row in CANONICAL]
    inputs.extend(GEN.generate(812, index, difficulty="medium") for index in range(10))
    result = Catalog(root=find_root(__file__)).apply(TASK_ID, inputs, timeout=120)
    assert result["executed_rule_hash"] == GEN.RULE_HASH
    assert result["rule_hash_matches_catalog"] is True
    assert [row["output"] for row in result["results"]] == [intended(grid) for grid in inputs]


@pytest.mark.parametrize("filename,rival_name", [
    ("lower_color_precedence.json", "higher_color_wins_crossings"),
    ("collinear_exact_pair.json", "expand_all_exactly_two_bboxes"),
])
def test_retained_counterexamples_refute_canonical_fitting_shortcuts(filename, rival_name):
    payload = json.loads((HOME / "counterexamples" / filename).read_text(encoding="utf-8"))
    grid = payload["input"]
    expected = payload["expected_output"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == expected
    assert intended(grid) == expected
    rival = GEN.CANONICAL_SHORTCUTS[rival_name](grid)
    assert rival == payload["rival_output"]
    assert rival != expected
