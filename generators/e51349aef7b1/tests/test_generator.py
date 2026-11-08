"""Focused regressions for the cropped color+transform analogy generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "e51349aef7b1"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
BANDS = (None, "easy", "medium", "hard")
PALETTES = ((2, 7, 4), (3, 8, 6), (4, 2, 7), (6, 3, 8), (7, 4, 2))


def _transform(grid, code):
    if code == 1:
        return [list(row) for row in grid]
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [list(reversed(row)) for row in grid]
    if code == 6:
        return [list(row) for row in reversed(grid)]
    raise ValueError(code)


def _crop(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not points:
        raise ValueError("empty panel")
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def _binary(grid):
    return [[int(value != 0) for value in row] for row in grid]


def _split(grid):
    h = len(grid)
    dividers = [c for c in range(len(grid[0])) if all(grid[r][c] == 5 for r in range(h))]
    assert len(dividers) == 2
    d1, d2 = dividers
    return (
        [list(row[:d1]) for row in grid],
        [list(row[d1 + 1 : d2]) for row in grid],
        [list(row[d2 + 1 :]) for row in grid],
    )


def _matches(a, b):
    aa, bb = _binary(_crop(a)), _binary(_crop(b))
    return [code for code in range(1, 7) if _transform(aa, code) == bb]


def independent_rule(grid):
    a, b, c = _split(grid)
    matches = _matches(a, b)
    code = matches[0] if matches else 1
    color_b = next(value for row in b for value in row if value not in (0, 5))
    return [[color_b if value else 0 for value in row] for row in _transform(_crop(c), code)]


def full_panel_shortcut(grid):
    a, b, c = _split(grid)
    aa, bb = _binary(a), _binary(b)
    matches = [code for code in range(1, 7) if _transform(aa, code) == bb]
    code = matches[0] if matches else 1
    color_b = next(value for row in b for value in row if value not in (0, 5))
    return [[color_b if value else 0 for value in row] for row in _transform(_crop(c), code)]


def last_match_shortcut(grid):
    a, b, c = _split(grid)
    matches = _matches(a, b)
    code = matches[-1] if matches else 1
    color_b = next(value for row in b for value in row if value not in (0, 5))
    return [[color_b if value else 0 for value in row] for row in _transform(_crop(c), code)]


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_small_exact_axis_contract():
    assert GEN.RULE_HASH == "cb2d64bc2f44"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"panel_n", "c_cells", "palette_id"}


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("panel_n", (5, 6))
@pytest.mark.parametrize("c_cells", (4, 6, 8))
@pytest.mark.parametrize("palette_id", range(5))
def test_exact_controls_are_constructive_observable_and_source_correct(
    band, panel_n, c_cells, palette_id
):
    grid = GEN.generate(
        109,
        5,
        difficulty=band,
        panel_n=panel_n,
        c_cells=c_cells,
        palette_id=palette_id,
    )
    expected = {
        "panel_n": panel_n,
        "c_cells": c_cells,
        "palette_id": palette_id,
    }
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == expected
    assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"panel_n": 4},
        {"panel_n": 7},
        {"c_cells": 3},
        {"c_cells": 9},
        {"palette_id": -1},
        {"palette_id": 5},
        {"panel_n": True},
        {"c_cells": 4.0},
        {"palette_id": "2"},
        {"unknown_axis": 1},
        {"transform": 2},
        {"texture": "default"},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_or_retired_controls_are_rejected(kwargs):
    kwargs = dict(kwargs)
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


def test_none_override_values_retain_default_convention():
    assert GEN.generate(22, 1, panel_n=None, c_cells=None, palette_id=None) == GEN.generate(22, 1)


def test_all_canonical_pairs_are_accepted_and_match_the_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_uncropped_full_panel_shortcut_fits_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    shortcut = GEN.CANONICAL_SHORTCUTS["uncropped_full_panels"]
    for pair in pairs:
        assert full_panel_shortcut(pair["input"]) == pair["output"]
        assert shortcut(pair["input"]) == pair["output"]


@pytest.mark.parametrize("profile,expected_matches", [(0, [2, 6]), (1, [3, 6])])
def test_ambiguous_profiles_teach_crop_and_first_match_precedence(profile, expected_matches):
    for c_cells in range(4, 9):
        grid = GEN.generate(712, profile, panel_n=5, c_cells=c_cells, palette_id=profile)
        a, b, _ = _split(grid)
        assert _matches(a, b) == expected_matches
        truth = independent_rule(grid)
        assert full_panel_shortcut(grid) != truth
        assert last_match_shortcut(grid) != truth
        assert GEN.SEMANTIC_WITNESSES["cropped_alignment"](grid)
        assert GEN.SEMANTIC_WITNESSES["first_match_precedence"](grid)
        assert GEN.SEMANTIC_RIVALS["uncropped_full_panels"](grid) == full_panel_shortcut(grid)
        assert GEN.SEMANTIC_RIVALS["last_matching_transform"](grid) == last_match_shortcut(grid)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_four_profile_window_and_query_rotation_refutes_both_rivals(band):
    rivals = GEN.LESSON_COMPETITORS
    assert set(rivals) == {"uncropped_full_panels", "last_matching_transform"}
    for start in range(12):
        pairs = [_pair(GEN.generate(1207 + start, start + offset, difficulty=band)) for offset in range(4)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in rivals.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_distribution_hits_canonical_profile_and_all_schedule_roles(band):
    grids = [GEN.generate(314, index, difficulty=band) for index in range(80)]
    observations = [GEN.observe_overrides(grid) for grid in grids]
    assert any(len(grid) == 5 and len(grid[0]) == 17 and len({v for row in grid for v in row}) == 5 for grid in grids)
    assert {item["panel_n"] for item in observations} == {5, 6}
    assert {item["c_cells"] for item in observations} == set(range(4, 9))
    assert {item["palette_id"] for item in observations} == set(range(5))
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 76
    for residue in range(4):
        assert any(index % 4 == residue for index in range(len(grids)))


def test_generation_helpers_and_rivals_are_deterministic_fresh_and_pure():
    for band in BANDS:
        for index in range(16):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first, difficulty=band) == []
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                assert rival(first) == rival(deepcopy(first))
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 17 for _ in range(5)],
        [[0] * 17 for _ in range(5)],
        [[10] * 17 for _ in range(5)],
        ["0" * 17 for _ in range(5)],
    ],
)
def test_malformed_self_check_is_diagnostic_not_exception(grid):
    result = GEN.self_check(grid)
    assert isinstance(result, list) and result


def test_validator_rejects_semantic_near_misses_but_accepts_translations():
    grid = GEN.generate(404, 0, panel_n=5, c_cells=6, palette_id=0)
    assert GEN.self_check(grid) == []

    bad_divider = deepcopy(grid)
    bad_divider[0][5] = 0
    assert GEN.self_check(bad_divider)

    mixed_panel_color = deepcopy(grid)
    a, _, _ = _split(mixed_panel_color)
    point = next((r, c) for r, row in enumerate(a) for c, value in enumerate(row) if value)
    mixed_panel_color[point[0]][point[1]] = 9
    assert GEN.self_check(mixed_panel_color)

    unrelated_b = deepcopy(grid)
    # Move one B cell without preserving the cropped transform relation.
    d1, d2 = [c for c in range(len(grid[0])) if all(grid[r][c] == 5 for r in range(len(grid)))]
    b_points = [(r, c) for r, row in enumerate(unrelated_b) for c, value in enumerate(row) if d1 < c < d2 and value not in (0, 5)]
    r, c = b_points[0]
    unrelated_b[r][c] = 0
    candidates = [(rr, cc) for rr in range(len(grid)) for cc in range(d1 + 1, d2) if unrelated_b[rr][cc] == 0]
    rr, cc = candidates[-1]
    unrelated_b[rr][cc] = PALETTES[0][1]
    assert GEN.self_check(unrelated_b)


def test_real_racket_reference_matches_python_mirror():
    grids = [GEN.generate(319, index, difficulty="hard") for index in range(16)]
    result = Catalog(find_root(__file__)).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert result["rule_hash_matches_catalog"]
    outputs = [item["output"] for item in result["results"]]
    assert all(item["error"] is None and item["valid_output"] for item in result["results"])
    assert outputs == [independent_rule(grid) for grid in grids]


def test_retained_uncropped_counterexample_is_reproducible_and_source_bound():
    path = HOME / "counterexamples" / "uncropped_full_panels.json"
    record = json.loads(path.read_text())
    assert record["task_id"] == TASK_ID
    assert record["generator_sha256"] == hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    params = record["generator_parameters"]
    reproduced = GEN.generate(
        params["seed"],
        params["sample_index"],
        difficulty=params["difficulty"],
        panel_n=params["panel_n"],
        c_cells=params["c_cells"],
        palette_id=params["palette_id"],
    )
    assert reproduced == record["input"]
    assert independent_rule(reproduced) == record["intended_output"]
    assert full_panel_shortcut(reproduced) == record["rival_output"]
    assert record["canonical_racket_output"] == record["intended_output"]
    assert record["rival_output"] != record["intended_output"]
    assert record["cropped_match_codes"] == [2, 6]
    assert record["full_panel_match_codes"] == []
