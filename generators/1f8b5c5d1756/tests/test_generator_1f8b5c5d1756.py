"""Focused structural and semantic regressions for generator 1f8b5c5d1756."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from src.core.canonical_pairs import load_task_pairs


TASK_ID = "1f8b5c5d1756"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.1f8b5c5d1756.generator"
)
AUTHORITY = ROOT / (
    "data/base/solutions/banks/534c4be491a1/"
    "S10_H3__1f8b5c5d1756.json"
)
BANDS = ("easy", "medium", "hard")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def test_metadata_and_authoritative_rule_hash_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == "d67f50454e7f"
    authority = json.loads(AUTHORITY.read_text())
    canonical = _canonical_row()
    assert _normalized_hash(authority["racket_target"]["target_code"]) == GEN.RULE_HASH
    assert _normalized_hash(canonical["program_solution"]) == GEN.RULE_HASH


def test_all_canonical_pairs_are_accepted_and_exact():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        analysis = GEN._analyze(pair["input"])
        assert analysis["pair_families"] in (1, 2)
        assert sorted(analysis["frequencies"].values()).count(1) == 1
        assert all(count in (1, 2) for count in analysis["frequencies"].values())


def test_every_band_and_schedule_profile_is_strict_and_exact():
    for band_index, band in enumerate(BANDS):
        profiles = Counter()
        for index in range(120):
            grid = GEN.generate(10_000 * band_index + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            observed = GEN.observe_overrides(grid)
            assert observed["pair_families"] in (1, 2)
            profiles[GEN.schedule_profile(index, index, band)] += 1
            output = GEN.rule_mirror(grid)
            analysis = GEN._analyze(grid)
            cyan = {
                (row, col)
                for row, values in enumerate(output)
                for col, value in enumerate(values)
                if value == 8
            }
            assert cyan == set(analysis["target"])
            assert {value for row in output for value in row} <= {0, 8}
        assert set(profiles) == set(GEN.SCHEDULE_PROFILES)


def test_every_four_demo_window_is_identifiable():
    for band_index, band in enumerate(BANDS):
        for start in range(16):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                index = start + offset
                grid = GEN.generate(20_000 + 1_000 * band_index + start, index, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(30_000 + start, start + 4, difficulty=band)
            assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []


@pytest.mark.parametrize("grid_h", [9, 16])
@pytest.mark.parametrize("grid_w", [13, 18])
@pytest.mark.parametrize("pair_families", [1, 2])
@pytest.mark.parametrize("unique_relation", list(GEN._RELATIONS))
@pytest.mark.parametrize("unique_location", list(GEN._LOCATIONS))
def test_full_boundary_override_cross_product_is_observable(
    grid_h, grid_w, pair_families, unique_relation, unique_location
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "pair_families": pair_families,
        "unique_relation": unique_relation,
        "unique_location": unique_location,
    }
    grid = GEN.generate(40_001, 23, difficulty="hard", **requested)
    assert GEN.self_check(grid, meta=requested) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.strict_canonical_like(grid) == []


def test_unknown_and_invalid_controls_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="solid")
    with pytest.raises(ValueError, match="grid_h must be an integer"):
        GEN.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError, match="unique_relation"):
        GEN.generate(1, 0, unique_relation="reflection")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_semantic_witnesses_fire_and_their_rivals_disagree():
    seen = set()
    for index in range(80):
        grid = GEN.generate(50_000 + index, index, difficulty="medium")
        exact = GEN.rule_mirror(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            seen.add(witness_name)
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != exact
    assert seen == set(GEN.SEMANTIC_WITNESSES)


def test_self_check_rejects_targeted_semantic_impostors():
    base = GEN.generate(60_000, 1, difficulty="hard")
    info = GEN._analyze(base)

    wrong_color = copy.deepcopy(base)
    row, col = info["target"][0]
    wrong_color[row][col] = 3
    assert GEN.self_check(wrong_color)

    missing_copy = copy.deepcopy(base)
    repeated = next(
        cells
        for cells, signature in zip(info["components"], info["signatures"])
        if info["frequencies"][signature] == 2
    )
    for row, col in repeated:
        missing_copy[row][col] = 0
    assert GEN.self_check(missing_copy)

    extra_singleton = copy.deepcopy(base)
    location = next(
        (row, col)
        for row, values in enumerate(extra_singleton)
        for col, value in enumerate(values)
        if value == 0
        and all(
            not (0 <= row + dr < len(extra_singleton) and 0 <= col + dc < len(values))
            or extra_singleton[row + dr][col + dc] == 0
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
    )
    extra_singleton[location[0]][location[1]] = 4
    assert GEN.self_check(extra_singleton)

    all_blank = [[0 for _ in row] for row in base]
    assert GEN.self_check(all_blank)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(70_000, 31, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(70_000, 31, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert _freeze(GEN.generate(70_000, 31, difficulty="medium")) == _freeze(second)
