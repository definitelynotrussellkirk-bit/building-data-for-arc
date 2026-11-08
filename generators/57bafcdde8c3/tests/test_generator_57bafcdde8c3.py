"""Focused regressions for the reviewed e0fb7511 generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

import pytest


TASK_ID = "57bafcdde8c3"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    f"reviewed_{TASK_ID}", HERE.parents[1] / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
BASE_PATHS = (
    REPO / "shared/data/base/solutions/augmented/e0fb7511__7ae46a600503.json",
    REPO / "shared/data/base/solutions/training/e0fb7511__57bafcdde8c3.json",
)


def _canonical_rows() -> list[dict]:
    rows = []
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    return rows


def _canonical_pairs() -> list[dict]:
    return [
        pair
        for row in _canonical_rows()
        for split in ("train", "test")
        for pair in row[split]
    ]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _component_sizes(grid: list[list[int]]) -> list[int]:
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != background
    }
    sizes = []
    while unseen:
        stack = [unseen.pop()]
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sizes


def test_rule_pin_canonical_pairs_and_selected_sources_are_exact():
    rows = _canonical_rows()
    assert len(rows) == 2
    selected = {row["program_solution"] for row in rows}
    assert len(selected) == 1
    canonical_source = selected.pop()
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "e47ef90b42c0"
    assert GEN.RULE_HASH == _normalized_hash(canonical_source)

    for pair in _canonical_pairs():
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before

    for path in BASE_PATHS:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == canonical_source
        assert target["raw_code"] != canonical_source


def test_default_census_matches_canonical_scale_density_and_topology():
    grids = [GEN.generate(10_000 + index, index, difficulty="medium") for index in range(80)]
    object_counts = []
    strict = 0
    for grid in grids:
        assert len(grid) == 13
        assert {len(row) for row in grid} == {13}
        assert len({value for row in grid for value in row}) == 2
        assert GEN.self_check(grid) == []
        strict += not GEN.strict_canonical_like(grid)
        sizes = _component_sizes(grid)
        object_counts.append(len(sizes))
        assert sum(size == 1 for size in sizes) >= 8
        assert sum(size > 1 for size in sizes) >= 4
        assert max(sizes) >= 3
    assert 18 <= statistics.median(object_counts) <= 30
    assert strict >= len(grids) * 0.45


def test_four_slot_lesson_refutes_every_declared_competitor():
    for start in range(8):
        grids = [GEN.generate(20_000 + start, start + offset, difficulty="hard") for offset in range(5)]
        assert [GEN.schedule_profile(20_000 + start, start + offset) for offset in range(5)] == [
            (start + offset) % 4 for offset in range(5)
        ]
        pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
        assert GEN.lesson_identifiable(pairs[:4], pairs[4]) == []
        official = [GEN.rule_mirror(grid) for grid in grids[:4]]
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(grid) != answer for grid, answer in zip(grids[:4], official)), name

    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(witness(GEN.generate(30_000 + i, i, difficulty="medium")) for i in range(12)), name


def test_override_boundaries_round_trip_and_invalid_requests_fail_loudly():
    cases = (
        {"foreground_count": 27, "background_color": 1, "foreground_color": 0},
        {"foreground_count": 52, "background_color": 7, "foreground_color": 3},
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(40_000 + index, index, difficulty=difficulty, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, bogus_axis=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, foreground_count=26)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, background_color=8)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, background_color=3, foreground_color=3)


def test_self_check_rejects_structural_and_palette_mutations():
    grid = GEN.generate(50_001, 3, difficulty="medium", foreground_count=27)
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    foreground = next(value for row in grid for value in row if value != background)

    fixtures = {
        "blank": [[0] * 13 for _ in range(13)],
        "third_color": copy.deepcopy(grid),
        "missing_foreground": copy.deepcopy(grid),
        "inverted": [[foreground if value == background else background for value in row] for row in grid],
    }
    fixtures["third_color"][0][0] = next(color for color in range(10) if color not in {background, foreground, 8})
    removed = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == foreground)
    fixtures["missing_foreground"][removed[0]][removed[1]] = background
    for name, malformed in fixtures.items():
        assert GEN.self_check(malformed), name


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20260928)
    state = random.getstate()
    first = GEN.generate(61_001, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(61_001, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_rule_mirror_recolors_only_four_connected_components_larger_than_one():
    grid = [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 1, 2],
        [1, 1, 1, 2, 1],
        [3, 1, 4, 4, 1],
        [1, 1, 1, 1, 1],
    ]
    assert GEN.rule_mirror(grid) == [
        [1, 1, 1, 1, 1],
        [1, 8, 8, 1, 2],
        [1, 1, 1, 2, 1],
        [3, 1, 8, 8, 1],
        [1, 1, 1, 1, 1],
    ]


def test_difficulty_rotates_safe_profiles_without_changing_the_profile_set():
    seed, sample_index = 71_001, 6
    outputs = {
        band: GEN.generate(seed, sample_index, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in outputs.values()}) == 3
    assert [GEN.schedule_profile(seed, sample_index, band) for band in ("easy", "medium", "hard")] == [2, 3, 0]
    for grid in outputs.values():
        assert GEN.self_check(grid) == []


def test_every_declared_witness_has_a_verified_rival_claim():
    assert set(GEN.SEMANTIC_WITNESSES) <= set(GEN.WITNESS_RIVALS)
    for witness_name, rivals in GEN.WITNESS_RIVALS.items():
        assert witness_name in GEN.SEMANTIC_WITNESSES
        assert rivals
        assert set(rivals) <= set(GEN.SEMANTIC_RIVALS)
