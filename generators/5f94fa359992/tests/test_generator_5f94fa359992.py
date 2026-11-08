"""Focused semantic regressions for the framed-crop ordering generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from itertools import product
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.5f94fa359992.generator")
ROOT = find_root(__file__)
BANDS = ("easy", "medium", "hard")


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError(f"canonical task {gen.TASK_ID} not found")


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_five_canonical_pairs() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 5
    signatures = set()
    for pair in pairs:
        snapshot = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == snapshot
        signatures.add(gen.canonical_profile_signature(pair["input"]))
    assert signatures == set(gen._CANONICAL_SIGNATURES)

    normalized = " ".join(_canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH


def test_default_prior_reaches_every_linked_profile_in_every_band() -> None:
    for band in BANDS:
        signatures = []
        for index in range(200):
            grid = gen.generate(71000 + index, index, difficulty=band)
            signature = gen.canonical_profile_signature(grid)
            if not gen.strict_canonical_like(grid):
                signatures.append(signature)
        assert len(signatures) == 50
        assert set(signatures) == set(gen._CANONICAL_SIGNATURES)


def test_every_exact_axis_is_observable_and_unknowns_are_rejected() -> None:
    values = {
        "n_frames": (3, 4),
        "frame_size": (5, 6),
        "key_order": ("ascending", "descending", "mixed"),
        "figure_height_pattern": ("uniform", "varied"),
        "color_relation": ("disjoint", "overlap"),
        "key_position": ("centered", "varied"),
    }
    names = tuple(values)
    for index, combination in enumerate(product(*(values[name] for name in names))):
        requested = dict(zip(names, combination))
        grid = gen.generate(83000 + index, 17, difficulty="hard", **requested)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, difficulty="easy", fake_texture="ignored-before-repair")


@pytest.mark.parametrize("start", range(12))
@pytest.mark.parametrize("band", BANDS)
def test_every_sliding_four_example_window_is_identifiable(start: int, band: str) -> None:
    demos = [_pair(91001, index, band) for index in range(start, start + gen.EXAMPLES_NEEDED)]
    query = _pair(91001, start + gen.EXAMPLES_NEEDED, band)
    assert gen.lesson_identifiable(demos, query) == []

    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(demo["input"]) != demo["output"] for demo in demos), name
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(demo["input"]) for demo in demos), name

    observed = [gen.observe_overrides(demo["input"]) for demo in demos]
    assert {item["n_frames"] for item in observed} == {3, 4}
    assert {item["frame_size"] for item in observed} == {5, 6}
    assert {item["key_order"] for item in observed} == {"ascending", "descending", "mixed"}
    assert {item["figure_height_pattern"] for item in observed} == {"uniform", "varied"}
    assert {item["color_relation"] for item in observed} == {"disjoint", "overlap"}
    assert {item["key_position"] for item in observed} == {"centered", "varied"}


def test_task_local_mutation_fixtures_are_all_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_lawful_noncanonical_recombination_is_not_mislabeled_official() -> None:
    grid = copy.deepcopy(canonical_pairs(gen.TASK_ID, root=ROOT)[0]["input"])
    record = gen._frame_records(grid)[0]
    figure_color = next(iter(record["figure_colors"]))
    for r, c, _ in record["figure_cells"]:
        grid[r][c] = 0
    r0, c0, r1, c1 = record["bbox"]
    grid[(r0 + r1) // 2][(c0 + c1) // 2] = figure_color

    assert gen.self_check(grid) == []
    assert gen.canonical_profile_signature(grid) not in gen._CANONICAL_SIGNATURES
    assert gen.strict_canonical_like(grid) == [
        "scene is lawful but not one complete linked official profile"
    ]
    assert gen.rule_mirror(grid)


def test_regression_anchor_uses_true_five_by_five_frames() -> None:
    grid = gen.generate(101, 0, difficulty="medium")
    records = gen._frame_records(grid)
    assert len(records) == 3
    assert {record["bbox"][2] - record["bbox"][0] + 1 for record in records} == {5}
    assert gen.canonical_profile_signature(grid) in gen._CANONICAL_SIGNATURES


def test_generation_is_replayable_fresh_and_global_rng_neutral() -> None:
    random.seed(424242)
    before = random.getstate()
    first = gen.generate(51, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(51, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(51, 7, difficulty="hard")


def test_three_demos_are_the_smallest_schedule_wide_identifiable_count() -> None:
    for band_index, band in enumerate(BANDS):
        for start in range(24):
            seed = 780000 + band_index * 10000 + start
            demos = [_pair(seed, index, band) for index in range(start, start + 3)]
            query = _pair(seed, start + 3, band)
            assert gen.lesson_identifiable(demos, query) == []

    two_demos = [_pair(780000, index, "easy") for index in range(2)]
    two_demo_query = _pair(780000, 2, "easy")
    assert gen.lesson_identifiable(two_demos, two_demo_query) == [
        "competing rule 'reading_order' fits every demo but changes the query answer"
    ]


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(sample_index) -> None:
    expected = ValueError if sample_index == -1 and type(sample_index) is int else TypeError
    with pytest.raises(expected):
        gen.generate(991, sample_index, difficulty="easy")
