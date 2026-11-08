"""Focused regression tests for generator 1a4459f1a38f."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import deque
from itertools import combinations
from pathlib import Path

import pytest


TASK_ID = "1a4459f1a38f"
MOD = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _blank():
    return [[0 for _ in range(10)] for _ in range(10)]


def _paint(grid, cells, color):
    for r, c in cells:
        grid[r][c] = color
    return grid


def _frame(top, left, size):
    return {
        (r, c)
        for r in range(top, top + size)
        for c in range(left, left + size)
        if r in (top, top + size - 1) or c in (left, left + size - 1)
    }


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _components(grid, directions):
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in directions:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            objects.append((color, frozenset(cells)))
    return objects


def _largest_crop(grid, directions):
    objects = _components(grid, directions)

    def bbox(obj):
        _, cells = obj
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return min(rows), min(cols), max(rows), max(cols)

    chosen = min(objects, key=lambda obj: (-len(obj[1]), bbox(obj)[:2]))
    r0, c0, r1, c1 = bbox(chosen)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _has_same_color_diagonal_split(grid):
    objects = _components(grid, DIRS4)
    for (color_a, cells_a), (color_b, cells_b) in combinations(objects, 2):
        if color_a != color_b:
            continue
        if any(
            abs(ar - br) == 1 and abs(ac - bc) == 1
            for ar, ac in cells_a
            for br, bc in cells_b
        ):
            return True
    return False


def test_rule_hash_version_and_canonical_acceptance():
    assert MOD.RULE_HASH == "f1a4398aee4e"
    assert MOD.VERSION == "4.1.1"
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        assert MOD.self_check(pair["input"]) == []
        assert MOD.strict_canonical_like(pair["input"]) == []


def test_self_check_rejects_four_targeted_impostors():
    single = _paint(_blank(), _frame(2, 2, 3), 1)

    tie = _blank()
    _paint(tie, _frame(0, 0, 3), 1)
    _paint(tie, _frame(6, 6, 3), 2)

    solid = _blank()
    _paint(solid, {(r, c) for r in range(3) for c in range(3)}, 1)
    _paint(solid, {(7, 7), (7, 8), (8, 7)}, 2)

    inside = _blank()
    _paint(inside, _frame(1, 1, 4), 1)
    _paint(inside, {(2, 2)}, 2)
    _paint(inside, {(7, 7), (7, 8), (8, 7)}, 3)

    cases = {
        "single_component": single,
        "equal_largest_sizes": tie,
        "solid_largest_bbox": solid,
        "distractor_inside_target_bbox": inside,
    }
    findings = {name: MOD.self_check(grid) for name, grid in cases.items()}
    assert all(findings.values()), findings
    assert any("2..4 components" in msg for msg in findings["single_component"])
    assert any("unique" in msg for msg in findings["equal_largest_sizes"])
    assert any("fills its bbox" in msg for msg in findings["solid_largest_bbox"])
    assert any("inside" in msg for msg in findings["distractor_inside_target_bbox"])


def test_pinned_profile_floor_keeps_at_least_twenty_five_percent_canonical_mass():
    hits = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = MOD.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({cell for row in grid for cell in row}),
            )
            hits += profile == (10, 10, 4)
            total += 1
    assert hits >= total // 4, (hits, total)


def test_axis_boundaries_are_exact_and_observable():
    cases = (
        {"grid_h": 10},
        {"grid_h": 14},
        {"grid_w": 10},
        {"grid_w": 16},
        {"component_count": 2},
        {"component_count": 4},
        {"grid_h": 10, "grid_w": 10, "component_count": 2},
        {"grid_h": 14, "grid_w": 16, "component_count": 4},
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = MOD.generate(9000 + index, 17 * index + 3, difficulty=band, **overrides)
            observed = MOD.observe_overrides(grid)
            for key, value in overrides.items():
                assert observed[key] == value
            assert MOD.self_check(grid) == []


def test_semantic_witnesses_are_rival_backed_and_schedule_profiles_are_explicit():
    assert set(MOD.SEMANTIC_WITNESSES) == set(MOD.WITNESS_RIVALS)
    assert MOD.CURRICULUM_SCHEDULE == (
        "canonical",
        "bbox_decoy",
        "repeated_color",
        "irregular",
    )


def test_schedule_covers_all_semantic_witnesses_and_identifies_lessons():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            MOD.generate(12000 + band_index, sample_index, difficulty=band)
            for sample_index in range(16)
        ]
        for name, predicate in MOD.SEMANTIC_WITNESSES.items():
            assert any(predicate(grid) for grid in grids), (band, name)
        for start in range(0, 16, 4):
            pairs = [
                {
                    "input": grid,
                    "output": MOD._candidate_output("largest_cells", grid),
                }
                for grid in grids[start:start + 4]
            ]
            assert MOD.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_semantic_gate_replay_lessons_are_all_identifiable():
    replays = (
        ("easy", 40153500989981, 0),
        ("easy", 280195333242018, 11),
        ("easy", 109089775741595, 22),
        ("easy", 165378347846947, 33),
        ("medium", 146207527082384, 0),
        ("medium", 18592489122590, 11),
        ("medium", 235966572672300, 22),
        ("medium", 175696561292194, 33),
        ("hard", 242482389654651, 0),
        ("hard", 31861494788908, 11),
        ("hard", 127088382898618, 22),
        ("hard", 144119913477374, 33),
    )
    for band, seed, start in replays:
        pairs = []
        for sample_index in range(start, start + 4):
            grid = MOD.generate(seed, sample_index, difficulty=band)
            pairs.append({
                "input": grid,
                "output": MOD._candidate_output("largest_cells", grid),
            })
        assert MOD.lesson_identifiable(pairs[:3], pairs[3]) == [], (
            band,
            seed,
            start,
            MOD.lesson_identifiable(pairs[:3], pairs[3]),
        )


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("slot", (2, 3))
def test_repeated_witness_slots_distinguish_four_from_eight_connectivity(band, slot):
    for episode in range(4):
        grid = MOD.generate(
            47000 + episode,
            4 * episode + slot,
            difficulty=band,
        )
        assert _has_same_color_diagonal_split(grid), (band, slot, episode)
        assert _largest_crop(grid, DIRS4) != _largest_crop(grid, DIRS8), (
            band,
            slot,
            episode,
        )


def test_replay_fresh_returns_and_global_rng_purity():
    random.seed(1234567)
    before = random.getstate()
    first = MOD.generate(77, 11, difficulty="hard")
    after = random.getstate()
    second = MOD.generate(77, 11, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second, strict=True))
    old = second[0][0]
    first[0][0] = (old + 1) % 10
    assert second[0][0] == old


def test_unknown_override_rejects_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        MOD.generate(0, 0, mystery_axis=3)
