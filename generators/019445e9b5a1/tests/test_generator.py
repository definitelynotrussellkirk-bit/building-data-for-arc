"""Portable regression tests for the row-header recoloring generator."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

TASK_ID = "019445e9b5a1"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
from reference_probe import (  # noqa: E402
    analyze,
    erase_headerless_payloads,
    global_first_header,
    identity,
    load_generator,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
CANONICAL_PROFILES = {
    (len(pair["input"]), len(pair["input"][0]),
     len({value for row in pair["input"] for value in row}))
    for pair in PAIRS
}


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def labeled(grid):
    return {"input": deepcopy(grid), "output": rule_output(grid)}


def test_metadata_pins_authority_and_exposes_only_exact_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "f0e910e5b6d0"
    assert gen.VERSION == "2.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_headers", "n_payload"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_all_canonical_pairs_and_independent_oracle_matches(pair):
    before = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_constructive_observable_and_band_independent(band):
    requested = {"grid_h": 4, "grid_w": 8, "n_headers": 3, "n_payload": 7}
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert {name: analyze(grid)[name] for name in requested} == requested
    assert rule_output(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 3}, {"grid_h": 9}, {"grid_h": True},
        {"grid_w": 5}, {"grid_w": 13}, {"grid_w": 8.0},
        {"n_headers": 0}, {"n_headers": 4}, {"n_headers": "2"},
        {"n_payload": 3}, {"n_payload": 13}, {"n_payload": False},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_sample_window_has_canonical_profile_and_each_grid_teaches_rule(band):
    for start in range(12):
        grids = [gen.generate(700 + start, start + offset, difficulty=band)
                 for offset in range(3)]
        assert any(profile(grid) in CANONICAL_PROFILES for grid in grids)
        for grid in grids:
            stats = analyze(grid)
            assert gen.self_check(grid) == []
            assert stats["n_headers"] >= 2
            assert stats["header_rows_with_mismatch"] == stats["n_headers"]
            assert stats["headerless_payloads"] >= 1
            expected = rule_output(grid)
            assert identity(grid) != expected
            assert global_first_header(grid) != expected
            assert erase_headerless_payloads(grid) != expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_core_profile_occurs_in_each_band_and_is_exact(band):
    core = [gen.generate(900, index, difficulty=band) for index in range(12)
            if gen.schedule_profile(900, index, band) == "canonical_core"]
    assert core
    assert all(profile(grid) == (4, 8, 6) for grid in core)


def test_declared_canonical_shortcut_fits_all_canonical_labels_but_witness_refutes_it():
    assert all(erase_headerless_payloads(pair["input"]) == pair["output"] for pair in PAIRS)
    evidence = json.loads((HOME / "counterexamples" / "headerless-payload.json").read_text())
    grid = evidence["input"]
    assert rule_output(grid) == evidence["intended_output"]
    assert erase_headerless_payloads(grid) == evidence["erase_headerless_shortcut_output"]
    assert rule_output(grid) != erase_headerless_payloads(grid)
    assert gen.CANONICAL_SHORTCUTS["erase_headerless_payloads"](grid) == erase_headerless_payloads(grid)
    assert gen.SEMANTIC_WITNESSES["headerless_payload_kept"](grid)


def test_every_query_rotation_is_identified_by_remaining_default_demos():
    for band in ("easy", "medium", "hard"):
        for start in range(6):
            pairs = [labeled(gen.generate(1300 + start, start + offset, difficulty=band))
                     for offset in range(4)]
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                assert gen.lesson_identifiable(demos, pairs[held_out]) == []


@pytest.mark.parametrize(
    "mutation",
    ["remove_headers", "remove_mismatches", "bad_color", "too_small", "ragged", "bool_cell"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(41, 5)
    if mutation == "remove_headers":
        for row in grid:
            row[0] = 0
    elif mutation == "remove_mismatches":
        for row in grid:
            if row[0]:
                for col in range(1, len(row)):
                    if row[col]:
                        row[col] = row[0]
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "too_small":
        grid = [[0] * 5 for _ in range(3)]
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    assert gen.self_check(grid)


def test_generation_is_deterministic_and_helpers_do_not_mutate_inputs():
    for band in (None, "easy", "medium", "hard"):
        first = gen.generate(8128, 23, difficulty=band)
        assert first == gen.generate(8128, 23, difficulty=band)
        frozen = deepcopy(first)
        _ = rule_output(first)
        for rival in gen.LESSON_COMPETITORS.values():
            _ = rival(first)
        assert first == frozen
