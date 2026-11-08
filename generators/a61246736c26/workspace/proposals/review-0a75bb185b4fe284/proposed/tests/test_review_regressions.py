"""Portable regressions for the two retained v4 a61246736c26 findings.

The literal input below was generated on source SHA-256
33e5c3a10739251440d40b658e523234ff2ef3fe823b9fbe76f74a1717a41767
with seed=3, sample_index=0, difficulty="easy", scene_profile="permuted_frames".
Keeping its cells makes the malformed-input regression independent of RNG/version.
The valid recombination's expected output was independently confirmed by public
`arcpuzzles apply`; see checks/regression/before/racket.json in the review return.
The bounded census uses Python output semantics and is not a Racket-label census.
"""
from __future__ import annotations

import copy

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a61246736c26"
ROOT = find_root(__file__)
MOD, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = ("easy", "medium", "hard")
CENSUS_SEEDS = range(12)

BASE_ROWS = (
    "8888888888888888",
    "9111181111811118",
    "9133181821812818",
    "9133181881812818",
    "9111181111811118",
    "8888888888888888",
    "0111181111811118",
    "0122181441812818",
    "0188181441812818",
    "0111181111811118",
    "8888888888888888",
    "5111181111811118",
    "5122181821817718",
    "5188181881817718",
    "5111181111811118",
    "8888888888888888",
)
SAME_ROW_ROWS = (
    "8888888888888888",
    "9111181111811118",
    "9133181441817718",
    "9133181441817718",
    "9111181111811118",
    "8888888888888888",
    "0111181111811118",
    "0122181821812818",
    "0188181881812818",
    "0111181111811118",
    "8888888888888888",
    "5111181111811118",
    "5122181821812818",
    "5188181881812818",
    "5111181111811118",
    "8888888888888888",
)
SAME_ROW_RACKET_OUTPUT_ROWS = (
    "99998999989999",
    "93398984989789",
    "98898988989789",
    "99998999989999",
)


def _decode(rows):
    return [[int(value) for value in row] for row in rows]


def _row_selection(grid):
    """Read the documented equal lattice directly, without generator helpers."""
    assert (len(grid) - 4) % 3 == 0
    size = (len(grid) - 4) // 3
    assert (len(grid[0]) - 1) % (size + 1) == 0
    columns = (len(grid[0]) - 1) // (size + 1)
    solid_rows = []
    frames = []
    for column in range(columns):
        solids = []
        for row_band in range(3):
            row = 1 + row_band * (size + 1)
            col = 1 + column * (size + 1)
            interior = {
                grid[row + dy][col + dx]
                for dy in range(1, size - 1)
                for dx in range(1, size - 1)
            }
            if len(interior) == 1 and interior <= {3, 4, 6, 7}:
                solids.append(row_band)
        assert len(solids) == 1, (column, solids)
        solid_rows.append(solids[0])
        frames.append(grid[1 + solids[0] * (size + 1)][0])
    return size, solid_rows, frames


def _separator_variants(grid):
    """Every separator-cell replacement by 0/9, then full separator deletion."""
    height, width = len(grid), len(grid[0])
    rows = [r for r in range(height) if set(grid[r]) == {8}]
    cols = [c for c in range(width) if {grid[r][c] for r in range(height)} == {8}]
    cells = sorted({(r, c) for r in rows for c in range(width)} |
                   {(r, c) for c in cols for r in range(height)})
    for r, c in cells:
        for color in (0, 9):
            candidate = copy.deepcopy(grid)
            candidate[r][c] = color
            yield f"cell=({r},{c}) 8->{color}", candidate
    for r in rows:
        candidate = copy.deepcopy(grid)
        del candidate[r]
        yield f"delete separator row {r}", candidate
    for c in cols:
        candidate = copy.deepcopy(grid)
        for row in candidate:
            del row[c]
        yield f"delete separator column {c}", candidate


def test_public_profile_controls_remain_exact_and_observable():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == len(MOD.PUBLIC_PROFILES)
    for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs):
        generated = MOD.generate(7, 11, difficulty="medium", scene_profile=profile)
        assert generated == pair["input"], profile
        assert MOD.self_check(generated) == [], profile
        assert MOD.observe_overrides(generated) == {"scene_profile": profile}
        assert MOD.rule_mirror(generated) == pair["output"], profile


def test_retained_same_row_nonzero_witness_matches_racket_label():
    grid = _decode(SAME_ROW_ROWS)
    assert MOD.self_check(grid) == []
    size, solid_rows, frames = _row_selection(grid)
    assert (size, solid_rows, frames) == (4, [0, 0, 0], [9, 9, 9])
    output = MOD.rule_mirror(grid)
    assert output == _decode(SAME_ROW_RACKET_OUTPUT_ROWS)
    rival = [[0 if value == 9 else value for value in row] for row in output]
    assert sum(a != b for ar, br in zip(output, rival) for a, b in zip(ar, br)) == 36


def test_retained_single_separator_mutation_returns_errors():
    malformed = _decode(BASE_ROWS)
    assert malformed[5][0] == 8
    malformed[5][0] = 9
    try:
        errors = MOD.self_check(malformed)
    except Exception as exc:
        pytest.fail(f"self_check raised {type(exc).__name__}: {exc}; expected a nonempty error list")
    assert isinstance(errors, list) and errors


@pytest.mark.parametrize("case", ("retained_v4", *BANDS))
def test_bounded_separator_mutation_and_deletion_sweep_fails_closed(case):
    base = (_decode(BASE_ROWS) if case == "retained_v4" else
            MOD.generate(3, 0, difficulty=case, scene_profile="permuted_frames"))
    assert MOD.self_check(base) == []
    failures = []
    count = 0
    for label, malformed in _separator_variants(base):
        count += 1
        try:
            errors = MOD.self_check(malformed)
        except Exception as exc:
            failures.append((label, type(exc).__name__, str(exc)))
        else:
            if not isinstance(errors, list) or not errors:
                failures.append((label, "not_rejected", errors))
    assert count > 0
    assert not failures, f"{case}: {len(failures)}/{count} malformed cases did not fail closed: {failures[:8]}"


@pytest.mark.parametrize("band", BANDS)
def test_finite_generated_support_has_zero_and_nonzero_same_row_frames(band):
    """All general profile controls; seeds 0..11; index=seed*29 in each band."""
    frames_seen = set()
    same_row_draws = 0
    for profile in MOD.GENERAL_PROFILES:
        for seed in CENSUS_SEEDS:
            grid = MOD.generate(seed, seed * 29, difficulty=band, scene_profile=profile)
            assert MOD.self_check(grid) == [], (band, profile, seed)
            assert MOD.observe_overrides(grid) == {"scene_profile": profile}, (band, profile, seed)
            size, rows, frames = _row_selection(grid)
            output = MOD.rule_mirror(grid)
            assert [output[0][column * (size + 1)] for column in range(len(rows))] == frames
            if len(set(rows)) == 1:
                same_row_draws += 1
                frames_seen.update(frames)
    assert same_row_draws > 0, band
    assert 0 in frames_seen, (band, frames_seen)
    assert frames_seen & {5, 9}, (band, frames_seen, same_row_draws, SOURCE_SHA256)
