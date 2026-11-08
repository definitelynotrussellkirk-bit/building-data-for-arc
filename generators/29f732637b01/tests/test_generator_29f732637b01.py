from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "29f732637b01"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.29f732637b01.generator"
)
BANDS = ("easy", "medium", "hard")


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": grid, "output": GEN._authoritative_python(grid)}


def test_rule_hash_authorities_and_all_canonical_pairs_are_grounded():
    row = _canonical_row()
    expected = hashlib.sha256(row["program_solution"].encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "12e3ebc2bb96"

    for relpath in (
        "data/base/solutions/training/f25fbde4__29f732637b01.json",
        "data/base/solutions/augmented/f25fbde4__6381da9b6225.json",
    ):
        base = json.loads((ROOT / relpath).read_text())
        assert base["racket_target"]["target_code"] == row["program_solution"]
        assert base["racket_target"]["raw_code"] == row["program_solution"]

    assert len(_canonical_pairs()) == 4
    for pair in _canonical_pairs():
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._authoritative_python(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_every_declared_override_boundary_is_exact_and_observable():
    cases = (
        {"grid_h": 7},
        {"grid_h": 16},
        {"grid_w": 7},
        {"grid_w": 16},
        {"shape_h": 2},
        {"shape_h": 5},
        {"shape_w": 2},
        {"shape_w": 5},
        {"fg_palette_size": 1},
        {"fg_palette_size": 3},
        {
            "grid_h": 7,
            "grid_w": 7,
            "shape_h": 5,
            "shape_w": 5,
            "fg_palette_size": 3,
        },
        {
            "grid_h": 16,
            "grid_w": 16,
            "shape_h": 2,
            "shape_w": 2,
            "fg_palette_size": 1,
        },
    )
    for band in BANDS:
        for index, overrides in enumerate(cases):
            grid = GEN.generate(9100 + index, 100 + index, difficulty=band, **overrides)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            for axis, value in overrides.items():
                assert observed[axis] == value


def test_default_keyed_provenance_matches_observed_axes():
    for band_index, band in enumerate(BANDS):
        for index in range(30):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(
                    20_000 + band_index * 100 + index,
                    300 + index,
                    difficulty=band,
                )
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert set(observed) == set(GEN.AXES)
            for axis, value in observed.items():
                assert captured[0].axis_value(axis) == value


def test_invalid_controls_fail_loudly():
    bad_calls = (
        {"difficulty": "expert"},
        {"unknown_axis": 1},
        {"grid_h": 6},
        {"grid_w": 17},
        {"shape_h": 1},
        {"shape_w": 6},
        {"fg_palette_size": 0},
        {"grid_h": "9"},
        {"shape_h": True},
    )
    for kwargs in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 1, **kwargs)


def test_determinism_fresh_returns_band_signal_and_global_rng_isolation():
    random.seed(7281)
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(444, 19, difficulty="hard") == second

    easy = GEN.generate(444, 19, difficulty="easy")
    medium = GEN.generate(444, 19, difficulty="medium")
    hard = GEN.generate(444, 19, difficulty="hard")
    assert len({_frozen(easy), _frozen(medium), _frozen(hard)}) == 3


def test_self_check_rejects_targeted_impostors_and_strict_rejects_recombination():
    impostors = {
        "empty": [],
        "no_content": [[0] * 9 for _ in range(9)],
        "single_cell": [[0] * 9 for _ in range(9)],
        "border_touch": [[0] * 9 for _ in range(9)],
        "solid_bbox": [[0] * 9 for _ in range(9)],
        "bbox_too_tall": [[0] * 9 for _ in range(9)],
    }
    impostors["single_cell"][4][4] = 2
    impostors["border_touch"][0][2] = 2
    impostors["border_touch"][1][3] = 2
    for r in range(3, 5):
        for c in range(3, 5):
            impostors["solid_bbox"][r][c] = 2
    for r in range(1, 7):
        impostors["bbox_too_tall"][r][3] = 2
    impostors["bbox_too_tall"][2][4] = 2

    for name, grid in impostors.items():
        assert GEN.self_check(grid), name

    # A lawful generalized recombination belongs to the broad rule envelope
    # but not the strict empirical canonical manifold.
    recombined = GEN.generate(
        811,
        2,
        difficulty="medium",
        grid_h=9,
        grid_w=9,
        shape_h=3,
        shape_w=4,
        fg_palette_size=2,
    )
    assert GEN.self_check(recombined) == []
    assert GEN.strict_canonical_like(recombined)


def test_large_linked_census_and_disjoint_stability():
    for cohort in range(2):
        for band_index, band in enumerate(BANDS):
            strict = 0
            unique = set()
            witnesses = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
            draws = 200
            for index in range(draws):
                seed = 100_000 * (cohort + 1) + 10_000 * band_index + index
                sample_index = 1000 + index
                grid = GEN.generate(seed, sample_index, difficulty=band)
                assert GEN.self_check(grid) == []
                strict += not GEN.strict_canonical_like(grid)
                unique.add(_frozen(grid))
                for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    witnesses[name] += bool(predicate(grid))
            strict_hits = draws - strict
            assert strict_hits == 100
            assert len(unique) >= 190
            assert all(count > 0 for count in witnesses.values())
            assert witnesses["multicolor_preserved"] == 100


def test_three_consecutive_demos_identify_rule_and_refute_every_competitor():
    for band in BANDS:
        for start in range(24):
            demos = [_pair(GEN.generate(77 + start, start + j, difficulty=band)) for j in range(3)]
            query = _pair(GEN.generate(77 + start, start + 3, difficulty=band))
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


def test_semantic_rival_claims_hold_on_named_witnesses():
    for index in range(40):
        grid = GEN.generate(1234 + index, 2 * index, difficulty="hard")
        truth = GEN._authoritative_python(grid)
        for witness, rival_names in GEN.WITNESS_RIVALS.items():
            if not GEN.SEMANTIC_WITNESSES[witness](grid):
                continue
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)
