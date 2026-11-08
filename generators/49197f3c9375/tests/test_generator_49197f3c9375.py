"""Source-bound regressions for the repaired singleton-shape generator."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.49197f3c9375.generator")
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "49197f3c9375"
ROOT = find_root(__file__)
CANONICAL_LEDGER = canonical_path(ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
COUNTEREXAMPLE = ROOT / "generators" / TASK_ID / "counterexamples" / "strongest-rivals.json"


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pinned_profile_grid(band: str, index: int):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    seed = int(digest[:12], 16)
    return gen.generate(seed, seed % 7919 + index, difficulty=band)


def test_rule_hash_and_python_mirror_match_every_canonical_pair():
    assert gen.RULE_HASH == "4303be5db475"
    assert len(PAIRS) == 3
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_wrong_rules_fit_all_canonical_pairs():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "whole_singleton",
        "last_motif_boundary",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name


def test_saved_counterexample_reproduces_racket_truth_and_declared_rivals():
    assert CANONICAL_LEDGER.is_file()
    record = json.loads(COUNTEREXAMPLE.read_text(encoding="utf-8"))
    grid = record["input"]
    truth = gen.rule_mirror(grid)

    assert record["task_id"] == TASK_ID
    assert record["generator_version"] == gen.VERSION
    assert record["generator_sha256"] == hashlib.sha256(
        Path(gen.__file__).read_bytes()
    ).hexdigest()
    assert record["executed_rule_hash"] == gen.RULE_HASH
    assert record["validator_errors"] == []
    assert gen.self_check(grid) == []
    assert truth == record["racket_output"]

    for name, rival_output in record["rival_outputs"].items():
        assert name in gen.CANONICAL_SHORTCUTS
        assert gen.CANONICAL_SHORTCUTS[name](grid) == rival_output
        assert rival_output != truth


def test_generated_counterexamples_refute_both_canonical_shortcuts():
    interior = gen.generate(
        1701,
        0,
        difficulty="easy",
        grid_h=8,
        grid_w=15,
        target_topology="interior_bearing",
        target_slot="first",
        color_scheme="distinct",
    )
    truth = gen.rule_mirror(interior)
    assert gen.self_check(interior) == []
    assert gen.SEMANTIC_WITNESSES["interior_boundary"](interior)
    assert gen.SEMANTIC_RIVALS["whole_singleton"](interior) != truth
    assert gen.SEMANTIC_WITNESSES["singleton_not_last"](interior)
    assert gen.SEMANTIC_RIVALS["last_motif_boundary"](interior) != truth


def test_every_four_pair_schedule_is_query_rotation_safe_for_declared_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for offset in range(4):
                grid = gen.generate(81173, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )


def test_pinned_twenty_draw_profile_floor_hits_8x15_six_colors_in_every_band():
    for band in ("easy", "medium", "hard"):
        profiles = [_profile(_pinned_profile_grid(band, index)) for index in range(20)]
        assert (8, 15, 6) in profiles, (band, profiles)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_all_exact_overrides_are_observable_in_every_band(band):
    requested = {
        "grid_h": 8,
        "grid_w": 15,
        "target_topology": "interior_bearing",
        "target_slot": "middle",
        "color_scheme": "reused",
    }
    grid = gen.generate(919, 23, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_h": 13},
        {"grid_w": 14},
        {"grid_w": 21},
        {"target_topology": "solid"},
        {"target_slot": "second"},
        {"color_scheme": "rainbow"},
        {"grid_h": True},
        {"grid_w": "15"},
        {"target_slot": 2},
        {"difficulty": "expert"},
    ],
)
def test_invalid_and_unknown_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 15 for _ in range(8)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(20261007)
    before = random.getstate()
    first = gen.generate(404, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(404, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
