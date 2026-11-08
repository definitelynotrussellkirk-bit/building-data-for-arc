"""Task-linked regressions for generator 1a8932958b14."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "1a8932958b14"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
CANONICAL_PATH = canonical_path(ROOT)
BANDS = ("easy", "medium", "hard")


def _canonical_row():
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _canonical_rule_hash():
    source = _canonical_row()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_pin_selected_authority_and_every_canonical_pair():
    row = _canonical_row()
    assert GEN.RULE_HASH == "42869e666344"
    assert GEN.RULE_HASH == _canonical_rule_hash()

    base = json.loads((
        CANONICAL_PATH.parents[1]
        / "base/solutions/banks/38166e88069b/M24__1a8932958b14.json"
    ).read_text())
    target = base["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != row["program_solution"]
    assert target["canonicalization_status"] == "selected_synchronized_archival_divergent"
    assert target["raw_code_role"] == "archival_executable_source"
    assert target["target_code_role"] == "selected_task_rule"

    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_exact_overrides_are_observable_at_boundaries_in_every_band():
    cases = (
        {"grid_h": 9, "grid_w": 20, "payload_size": 3, "palette_size": 1, "vector_direction": "up_right"},
        {"grid_h": 20, "grid_w": 9, "payload_size": 9, "palette_size": 3, "vector_direction": "down_left"},
        {"grid_h": 12, "grid_w": 17, "payload_size": 6, "palette_size": 2, "vector_direction": "right"},
        {"grid_h": 17, "grid_w": 12, "payload_size": 7, "palette_size": 3, "vector_direction": "up"},
    )
    for band in BANDS:
        for index, requested in enumerate(cases):
            grid = GEN.generate(5000 + index, index, difficulty=band, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested
            assert GEN.rule_mirror(grid) != grid


def test_all_direction_override_tokens_are_realized_exactly():
    for index, direction in enumerate(GEN._DIRECTIONS):
        grid = GEN.generate(
            8000 + index,
            index,
            difficulty="medium",
            grid_h=14,
            grid_w=15,
            payload_size=5,
            palette_size=2,
            vector_direction=direction,
        )
        observed = GEN.observe_overrides(grid)
        assert observed["vector_direction"] == direction
        assert observed["grid_h"] == 14
        assert observed["grid_w"] == 15
        assert observed["payload_size"] == 5
        assert observed["palette_size"] == 2


def test_unknown_invalid_overrides_and_difficulty_fail_closed():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_payload_size=4)
    with pytest.raises((TypeError, ValueError, KeyError)):
        GEN.generate(1, 0, vector_direction="diagonal-ish")
    with pytest.raises((TypeError, ValueError, KeyError)):
        GEN.generate(1, 0, payload_size=99)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises(ValueError, match="seed"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(bad_index):
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(991, bad_index, difficulty="easy")


def test_every_three_sample_schedule_window_survives_every_query_rotation():
    # A production lesson has two demonstrations plus one query. Exhaust every
    # cyclic three-sample window and each possible query holdout. Every remaining
    # demo pair must contain a multicolor case and a case that falsifies the
    # public-only "always up-right" shortcut.
    n = len(GEN.SCHEDULE_PROFILES)
    for start in range(n):
        grids = [
            GEN.generate(20261008, start + offset, difficulty="medium")
            for offset in range(3)
        ]
        pairs = [{"input": g, "output": GEN.rule_mirror(g)} for g in grids]
        for query_offset, query in enumerate(pairs):
            demos = [pair for offset, pair in enumerate(pairs) if offset != query_offset]
            assert any(GEN._witness_multicolor(pair["input"]) for pair in demos), (
                start,
                query_offset,
            )
            assert any(
                GEN._witness_noncanonical_direction(pair["input"]) for pair in demos
            ), (start, query_offset)
            assert GEN.lesson_identifiable(demos, query) == [], (start, query_offset)


def test_public_shortcuts_fit_all_canonical_pairs_but_generated_witnesses_kill_them():
    pairs = _canonical_pairs()
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    orientation_grid = GEN.generate(14001, 1, difficulty="easy")
    assert GEN._witness_noncanonical_direction(orientation_grid)
    assert GEN.CANONICAL_SHORTCUTS["canonical_up_right"](orientation_grid) != GEN.rule_mirror(orientation_grid)

    multicolor_grid = GEN.generate(14002, 2, difficulty="hard")
    assert GEN._witness_multicolor(multicolor_grid)
    assert GEN.CANONICAL_SHORTCUTS["translate_modal_payload_color"](multicolor_grid) != GEN.rule_mirror(multicolor_grid)


def test_mutation_impostors_are_all_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
        assert GEN.strict_canonical_like(grid), name


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20260815)
    before = random.getstate()
    first = GEN.generate(987654, 77, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(987654, 77, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    third = GEN.generate(987654, 77, difficulty="hard")
    assert second == third
