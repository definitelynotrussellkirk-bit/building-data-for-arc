from __future__ import annotations

import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.8d4c7f482c25.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "8d4c7f482c25"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/cf5246d38569/easy_p01__8d4c7f482c25.json"
)
RING = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _independent_rule(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 2):
        for c in range(w - 2):
            perimeter = [grid[r + dr][c + dc] for dr, dc in RING]
            nonzero = [value for value in perimeter if value]
            if perimeter.count(0) != 1 or len(set(nonzero)) != 1:
                continue
            hole_index = perimeter.index(0)
            dr, dc = RING[hole_index]
            output[r + dr][c + dc] = nonzero[0]
    return output


def test_rule_pin_canonical_pairs_and_selected_source_are_exact() -> None:
    row = _canonical_row()
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == "4f529a98ea53"

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._official_python(pair["input"]) == pair["output"]
        assert _independent_rule(pair["input"]) == pair["output"]

    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]


def test_four_step_schedule_is_identifiable_and_refutes_every_declared_rival() -> None:
    for start in range(12):
        grids = [
            gen.generate(1701, start + offset, difficulty="medium")
            for offset in range(5)
        ]
        demos = [
            {"input": grid, "output": gen._official_python(grid)}
            for grid in grids[:4]
        ]
        query = {"input": grids[4], "output": gen._official_python(grids[4])}
        assert gen.lesson_identifiable(demos, query) == []

        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids[:4]), (start, name)

        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            witness_grid = next(
                grid
                for grid in grids[:4]
                if gen.SEMANTIC_WITNESSES[witness_name](grid)
            )
            answer = gen._official_python(witness_grid)
            for rival_name in rival_names:
                assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != answer


def test_override_full_boundary_matrix_is_exact_observable_and_band_safe() -> None:
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (8, 12):
            for grid_w in (8, 12):
                for ring_count in (2, 3):
                    for scene_profile in gen.SCENE_PROFILES:
                        for hole_class in gen.HOLE_CLASSES:
                            requested = {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "ring_count": ring_count,
                                "scene_profile": scene_profile,
                                "hole_class": hole_class,
                            }
                            grid = gen.generate(
                                20_000 + case_index,
                                case_index * 7 + 1,
                                difficulty=difficulty,
                                **requested,
                            )
                            assert gen.self_check(grid) == []
                            assert gen.observe_overrides(grid) == requested
                            assert _independent_rule(grid) == gen._official_python(grid)
                            case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


@pytest.mark.parametrize(
    "axis,value",
    [
        ("grid_h", 7),
        ("grid_h", 13),
        ("grid_w", 7),
        ("grid_w", 13),
        ("ring_count", 1),
        ("ring_count", 4),
        ("scene_profile", "helpful_noise"),
        ("hole_class", "center"),
    ],
)
def test_invalid_override_values_reject(axis: str, value: object) -> None:
    with pytest.raises(ValueError):
        gen.generate(7, 9, difficulty="hard", **{axis: value})


def test_replay_is_fresh_deterministic_global_rng_pure_and_band_live() -> None:
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second

    by_band = {
        band: gen.generate(991, 17, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in by_band.values()}) >= 2


def test_structural_mutation_impostors_are_rejected() -> None:
    valid = gen.generate(9, 6, difficulty="medium")
    assert gen.self_check(valid) == []
    impostors = gen.mutation_impostors(valid)
    assert len(impostors) >= 4
    for name, grid in impostors:
        assert gen.self_check(grid), name


def test_profiles_are_observable_and_semantically_distinct() -> None:
    rows = {}
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(
            31415,
            index,
            difficulty="medium",
            grid_h=10,
            grid_w=10,
            ring_count=3,
            scene_profile=profile,
            hole_class="mixed",
        )
        rows[profile] = grid
        observed = gen.observe_overrides(grid)
        assert observed["scene_profile"] == profile
        assert observed["hole_class"] == "mixed"
        assert len(gen._qualifying_rings(grid)) == 3

    assert all(ring["center"] == 0 for ring in gen._qualifying_rings(rows["canonical"]))
    assert all(ring["center"] != 0 for ring in gen._qualifying_rings(rows["filled_centers"]))
    shared = [ring["color"] for ring in gen._qualifying_rings(rows["shared_colors"])]
    assert len(set(shared)) == 1
    assert gen._mixed_almost_rings(rows["distractors"])


def test_returned_draw_census_keeps_every_declared_branch_live() -> None:
    witness_counts = Counter()
    profile_counts = Counter()
    hole_counts = Counter()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(80):
            grid = gen.generate(700_000 + band_index, sample_index, difficulty=band)
            assert gen.strict_canonical_like(grid) == []
            observed = gen.observe_overrides(grid)
            profile_counts[(band, observed["scene_profile"])] += 1
            hole_counts[(band, observed["hole_class"])] += 1
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_counts[(band, name)] += int(witness(grid))

    for band in ("easy", "medium", "hard"):
        assert all(profile_counts[(band, profile)] > 0 for profile in gen.SCENE_PROFILES)
        assert all(hole_counts[(band, hole)] > 0 for hole in gen.HOLE_CLASSES)
        assert all(witness_counts[(band, name)] > 0 for name in gen.SEMANTIC_WITNESSES)
