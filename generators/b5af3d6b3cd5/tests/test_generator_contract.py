"""Focused regression and curriculum tests for ARC generator b5af3d6b3cd5.

The tests are portable through ``arcpuzzles check --stage task_tests``.  They
use an independent Python implementation of the written rule so that the
selected Racket authority, the generator mirror, and the tests cannot all drift
silently in the same direction.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "b5af3d6b3cd5"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_contract_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def independent_rule(grid):
    """Apply stable downward gravity per column in each non-wall component."""
    h, w = len(grid), len(grid[0])
    seen = set()
    rooms = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            room = []
            while stack:
                rr, cc = stack.pop()
                room.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rooms.append(room)

    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for room in rooms:
        for c in sorted({cc for _r, cc in room}):
            cells = sorted(r for r, cc in room if cc == c)
            values = [grid[r][c] for r in cells if grid[r][c] != 0]
            for r, value in zip(cells[-len(values):] if values else (), values):
                out[r][c] = value
    return out


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def marker_count(grid):
    return sum(value not in (0, 5) for row in grid for value in row)


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_is_pinned_and_all_canonical_pairs_are_owned_exactly():
    canonical_path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    if not canonical_path.is_file():
        canonical_path = ROOT / "data" / "canonical" / "puzzles.jsonl"
    source = None
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row["program_solution"]
                break
    assert source is not None
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert digest == gen.RULE_HASH == "f37a4766f778"
    assert len(PAIRS) == 5
    for pair in PAIRS:
        before = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_public_axes_are_only_exact_pixel_observable_dimensions():
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []
    for difficulty in (None, "easy", "medium", "hard"):
        for h, w in ((8, 9), (8, 18), (12, 13), (16, 9), (16, 18)):
            grid = gen.generate(1701, h * 100 + w, difficulty=difficulty, grid_h=h, grid_w=w)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1}, {"texture": "default"},
        {"grid_h": 7}, {"grid_h": 17}, {"grid_w": 8}, {"grid_w": 19},
        {"grid_h": True}, {"grid_h": 8.0}, {"grid_h": "8"},
        {"grid_w": False}, {"grid_w": 9.0}, {"grid_w": None},
    ],
)
def test_unknown_invalid_and_coercible_controls_reject_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


@pytest.mark.parametrize("difficulty", ["extreme", "", 0, 0.5, True, [], {}])
def test_unsupported_difficulty_rejects_loudly(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, difficulty=difficulty)


def test_default_schedule_has_canonical_anchors_and_repairs_marker_count_drift():
    canonical_profiles = {profile(pair["input"]) for pair in PAIRS}
    canonical_counts = [marker_count(pair["input"]) for pair in PAIRS]
    assert min(canonical_counts) == 11 and max(canonical_counts) == 16
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(8128, index, difficulty=difficulty) for index in range(40)]
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert sum(profile(grid) in canonical_profiles for grid in grids) >= 16
        anchor_counts = [marker_count(grid) for grid in grids
                         if profile(grid) in canonical_profiles]
        assert anchor_counts
        assert all(11 <= count <= 16 for count in anchor_counts)
        assert sum(marker_count(grid) for grid in grids) / len(grids) >= 11.0


def test_every_production_draw_refutes_declared_rivals_and_hits_witnesses():
    for difficulty in ("easy", "medium", "hard"):
        profiles = set()
        for index in range(48):
            grid = gen.generate(4400 + index, index, difficulty=difficulty)
            official = independent_rule(grid)
            assert gen.rule_mirror(grid) == official
            assert gen.self_check(grid) == []
            profiles.add(gen.schedule_profile(4400 + index, index, difficulty))
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (difficulty, index, name)
                for rival_name in gen.WITNESS_RIVALS[name]:
                    assert gen.SEMANTIC_RIVALS[rival_name](grid) != official
        assert profiles == set(gen.SCHEDULE_PROFILES)


def test_canonical_palette_shortcut_fits_every_canonical_pair_but_generated_demos_refute_it():
    shortcut = gen.CANONICAL_SHORTCUTS["canonical_colors_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS)
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for index in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(991, 73 + index, difficulty=difficulty)
            pairs.append({"input": grid, "output": independent_rule(grid)})
        assert all(shortcut(pair["input"]) != pair["output"] for pair in pairs)
        for query_index in range(len(pairs)):
            query = pairs[query_index]
            demos = pairs[:query_index] + pairs[query_index + 1:]
            assert gen.lesson_identifiable(demos, query) == []


def test_cyclic_lesson_starts_and_all_query_rotations_are_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(2026, start + offset, difficulty=difficulty)
                pairs.append({"input": grid, "output": independent_rule(grid)})
            for query_index in range(len(pairs)):
                query = pairs[query_index]
                demos = pairs[:query_index] + pairs[query_index + 1:]
                assert gen.lesson_identifiable(demos, query) == [], (
                    difficulty, start, query_index
                )


def test_self_check_rejects_minimal_and_structural_impostors_without_mutating():
    cases = [
        [], [[0]], [[1] * 9 for _ in range(8)], [[5] * 9 for _ in range(8)],
        [[0] * 9 for _ in range(8)], [[True] * 9 for _ in range(8)],
        [[0] * 9 for _ in range(7)] + [[0] * 8],
    ]
    valid = gen.generate(3, 5, difficulty="medium", grid_h=9, grid_w=11)
    broken_frame = deepcopy(valid)
    broken_frame[0][1] = 0
    cases.append(broken_frame)
    stray_wall = deepcopy(valid)
    for r in range(1, len(stray_wall) - 1):
        for c in range(1, len(stray_wall[0]) - 1):
            if stray_wall[r][c] == 0:
                stray_wall[r][c] = 5
                break
        else:
            continue
        break
    cases.append(stray_wall)
    no_markers = [[5 if value == 5 else 0 for value in row] for row in valid]
    cases.append(no_markers)

    for grid in cases:
        before = deepcopy(grid)
        findings = gen.self_check(grid)
        assert isinstance(findings, list) and findings
        assert all(isinstance(item, str) for item in findings)
        assert grid == before


def test_generation_and_python_rule_are_deterministic_fresh_and_rng_pure():
    random.seed(987654321)
    state = random.getstate()
    first = gen.generate(111, 222, difficulty="hard")
    second = gen.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]

    expected = frozen(second)
    first[0][0] = 9
    assert frozen(gen.generate(111, 222, difficulty="hard")) == expected

    before = deepcopy(second)
    out = gen.rule_mirror(second)
    assert second == before
    expected_out = frozen(out)
    out[0][0] = 9
    assert frozen(gen.rule_mirror(second)) == expected_out

    by_seed = {frozen(gen.generate(seed, 17, difficulty="medium")) for seed in range(20)}
    by_index = {frozen(gen.generate(17, index, difficulty="medium")) for index in range(20)}
    assert len(by_seed) >= 18
    assert len(by_index) >= 18
