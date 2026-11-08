from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "97bcb3b9194e"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/7bb29440__97bcb3b9194e.json",
    ROOT / "data/base/solutions/augmented/7bb29440__9e9db6816deb.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def records(grid):
    result, errors = MODULE._component_records(grid)
    assert not errors
    return result


def test_rule_hash_all_canonical_pairs_and_task_local_sources_are_exact():
    rows = canonical_rows()
    assert len(rows) == 2
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    program = programs.pop()
    normalized = " ".join(program.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH

    pairs = [pair for row in rows for pair in row["train"] + row["test"]]
    assert len(pairs) == 12
    for pair in pairs:
        original = frozen(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert frozen(pair["input"]) == original

    for path in BASE_PATHS:
        target = json.loads(path.read_text())["racket_target"]
        assert target["raw_code"] == program
        assert target["target_code"] == program
        assert target["canonicalization_status"] == (
            "synchronized_to_canonical_program_solution"
        )


def test_exact_boundary_overrides_are_observable_and_unknowns_fail_loudly():
    cases = [
        {
            "grid_h": 12,
            "grid_w": 11,
            "n_boxes": 7,
            "winner_marks": 3,
            "mark_palette": "canonical",
            "winner_position": "middle",
        },
        {
            "grid_h": 28,
            "grid_w": 28,
            "n_boxes": 2,
            "winner_marks": 1,
            "mark_palette": "four_only",
            "winner_position": "last",
        },
        {"mark_palette": "six_only", "winner_position": "first"},
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(10_000 + index, 100 + index, difficulty="hard", **overrides)
        observed = MODULE.observe_overrides(grid)
        assert MODULE.self_check(grid) == []
        for axis, requested in overrides.items():
            assert observed[axis] == requested
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 2, obsolete_axis=3)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, mark_palette="not_a_palette")


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(123456789)
    state = random.getstate()
    first = MODULE.generate(42, 7, difficulty="hard")
    assert random.getstate() == state
    replay = MODULE.generate(42, 7, difficulty="hard")
    assert replay == first
    assert replay is not first
    assert all(a is not b for a, b in zip(replay, first))
    replay[0][0] = (replay[0][0] + 1) % 10
    assert MODULE.generate(42, 7, difficulty="hard") == first


def test_linked_semantic_distribution_200_per_band_and_stability():
    summaries = {}
    for band in ("easy", "medium", "hard"):
        grids = [MODULE.generate(20_000 + seed, seed, difficulty=band) for seed in range(200)]
        observations = [MODULE.observe_overrides(grid) for grid in grids]
        assert all(MODULE.self_check(grid, difficulty=band) == [] for grid in grids)
        assert all(MODULE.rule_mirror(grid) != grid for grid in grids)
        assert len({frozen(grid) for grid in grids}) == 200
        assert len({frozen(MODULE.rule_mirror(grid)) for grid in grids}) >= 160
        assert {item["winner_position"] for item in observations} == {"first", "middle", "last"}
        assert {item["winner_marks"] for item in observations} == {1, 2, 3}
        assert {item["mark_palette"] for item in observations} == set(MODULE.MARK_PALETTES)
        expected_boxes = {
            "easy": {2, 3, 4},
            "medium": {3, 4, 5, 6},
            "hard": {5, 6, 7},
        }[band]
        assert {item["n_boxes"] for item in observations} == expected_boxes
        target_pairs = {
            (item["n_boxes"], 0 if item["winner_position"] == "first" else (item["n_boxes"] - 1 if item["winner_position"] == "last" else item["n_boxes"] // 2))
            for item in observations
        }
        assert target_pairs == {
            (width, index)
            for width in expected_boxes
            for index in ((0, width - 1) if width == 2 else (0, width // 2, width - 1))
        }
        counts = Counter(item["winner_position"] for item in observations)
        assert min(counts.values()) >= 40
        canonical_like = 0
        for grid in grids:
            recs = records(grid)
            mark_colors = {
                grid[r][c]
                for record in recs
                for r, c in record["cells"]
                if grid[r][c] not in (0, 1)
            }
            canonical_like += int(
                12 <= len(grid) <= 22
                and 11 <= len(grid[0]) <= 25
                and len(recs) in {2, 4, 5, 6, 7}
                and mark_colors == {4, 6}
            )
        assert canonical_like >= 20
        summaries[band] = {"inputs": len({frozen(grid) for grid in grids})}

    # A disjoint seed range must remain fully varied rather than replaying a
    # small template bank.
    for band in ("easy", "medium", "hard"):
        grids = [MODULE.generate(80_000 + seed, seed + 1000, difficulty=band) for seed in range(200)]
        assert len({frozen(grid) for grid in grids}) == 200


def test_sequential_schedule_rebuts_position_size_and_palette_shortcuts():
    grids = [MODULE.generate(777, index, difficulty="medium") for index in range(6)]
    observations = [MODULE.observe_overrides(grid) for grid in grids]
    assert [item["winner_position"] for item in observations] == [
        "first",
        "middle",
        "last",
        "first",
        "middle",
        "last",
    ]
    assert [item["winner_marks"] for item in observations] == [1, 2, 3, 1, 2, 3]
    assert [item["mark_palette"] for item in observations] == [
        "canonical",
        "canonical",
        "four_only",
        "four_only",
        "six_only",
        "six_only",
    ]

    for index, grid in enumerate(grids):
        recs = records(grid)
        mark_counts = [record["marks"] for record in recs]
        winner = mark_counts.index(min(mark_counts))
        areas = [record["dims"][0] * record["dims"][1] for record in recs]
        if len(recs) >= 3:
            assert areas.count(areas[winner]) >= 2
            if index % 2 == 0:
                assert min(areas) < areas[winner]
            else:
                assert max(areas) > areas[winner]


def test_self_check_rejects_targeted_structural_impostors():
    grid = MODULE.generate(
        123,
        4,
        difficulty="medium",
        n_boxes=5,
        winner_marks=2,
        mark_palette="canonical",
        winner_position="first",
    )
    recs = records(grid)
    winner = min(range(len(recs)), key=lambda i: recs[i]["marks"])

    tied = copy.deepcopy(grid)
    competitor = 1 if winner == 0 else 0
    comp_marks = [
        (r, c)
        for r, c in recs[competitor]["cells"]
        if tied[r][c] not in (0, 1)
    ]
    for r, c in comp_marks[recs[winner]["marks"] :]:
        tied[r][c] = 1

    no_marks = copy.deepcopy(grid)
    for r, c in recs[winner]["cells"]:
        if no_marks[r][c] not in (0, 1):
            no_marks[r][c] = 1

    holed = copy.deepcopy(grid)
    r1, c1, r2, c2 = recs[winner]["bbox"]
    target = next(
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if holed[r][c] == 1
    )
    holed[target[0]][target[1]] = 0

    stray = copy.deepcopy(grid)
    occupied = {cell for record in recs for cell in record["cells"]}
    sr, sc = next(
        (r, c)
        for r, row in enumerate(stray)
        for c, value in enumerate(row)
        if value == 0
        and (r, c) not in occupied
        and all((r + dr, c + dc) not in occupied for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    )
    stray[sr][sc] = 3  # replacement feature absent from every legitimate box

    touching = copy.deepcopy(grid)
    first, second = recs[0]["bbox"], recs[1]["bbox"]
    # Draw a Manhattan bridge between two components; this either merges them
    # into an irregular component or violates the one-cell gap.
    r = first[2]
    c = first[3]
    tr, tc = second[0], second[1]
    while r != tr:
        r += 1 if tr > r else -1
        touching[r][c] = 1
    while c != tc:
        c += 1 if tc > c else -1
        touching[r][c] = 1

    for impostor in (tied, no_marks, holed, stray, touching):
        assert MODULE.self_check(impostor), impostor
