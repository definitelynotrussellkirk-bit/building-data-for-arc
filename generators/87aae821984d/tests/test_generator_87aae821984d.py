"""Focused contract tests for ARC task 87aae821984d."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "87aae821984d"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def independent_rule(grid):
    fours = sum(value == 4 for row in grid for value in row)
    eights = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    assert eights
    r2 = max(r for r, _ in eights)
    c2 = max(c for _, c in eights)
    tile = [
        [8 if 0 <= r2 - 2 + r < len(grid)
              and 0 <= c2 - 2 + c < len(grid[0])
              and grid[r2 - 2 + r][c2 - 2 + c] == 8 else 0
         for c in range(3)]
        for r in range(3)
    ]
    return [row * fours for row in tile]


def pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_honest_surface():
    assert GEN.RULE_HASH == "6f52927247b0"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_4_cells", "shape_kind"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 7
    saw_disconnected = False
    saw_padding = False
    for item in pairs:
        grid = item["input"]
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == item["output"] == independent_rule(grid)
        eights = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
        if eights:
            todo = [next(iter(eights))]
            reached = {todo[0]}
            while todo:
                r, c = todo.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (r + dr, c + dc)
                    if nxt in eights and nxt not in reached:
                        reached.add(nxt); todo.append(nxt)
            saw_disconnected |= reached != eights
            sh = max(r for r, _ in eights) - min(r for r, _ in eights) + 1
            sw = max(c for _, c in eights) - min(c for _, c in eights) + 1
            saw_padding |= (sh, sw) != (3, 3)
    assert saw_disconnected and saw_padding


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("overrides", [
    {"grid_h": 9, "grid_w": 9, "n_4_cells": 1, "shape_kind": "span_3x3"},
    {"grid_h": 14, "grid_w": 14, "n_4_cells": 5, "shape_kind": "pad_top"},
    {"grid_h": 9, "grid_w": 14, "n_4_cells": 3, "shape_kind": "pad_left"},
    {"grid_h": 14, "grid_w": 9, "n_4_cells": 4, "shape_kind": "pad_top_left"},
])
def test_exact_overrides_are_constructive_and_observable(band, overrides):
    grid = GEN.generate(4242, 7, difficulty=band, **overrides)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize("kwargs", [
    {"grid_h": 8}, {"grid_h": 15}, {"grid_w": 8}, {"grid_w": 15},
    {"n_4_cells": 0}, {"n_4_cells": 6}, {"shape_kind": "unknown"},
    {"grid_h": True}, {"grid_w": 9.5}, {"n_4_cells": "3"},
    {"shape_kind": 3}, {"unknown_axis": 1}, {"grid_h": None},
])
def test_invalid_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_every_cyclic_lesson_and_query_rotation_refutes_all_declared_rivals():
    assert set(GEN.SEMANTIC_RIVALS) == set(GEN.LESSON_COMPETITORS)
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = [pair(GEN.generate(8100 + start, start + offset, difficulty=band))
                      for offset in range(4)]
            assert {GEN.schedule_profile(0, start + i, band) for i in range(4)} == set(GEN.SCHEDULE_PROFILES)
            for query_index, query in enumerate(lesson):
                demos = [item for index, item in enumerate(lesson) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(item["input"]) != item["output"] for item in demos), name


def test_witness_claims_are_real_counterexamples_to_named_rivals():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(20):
        grid = GEN.generate(9001, index, difficulty="hard")
        truth = independent_rule(grid)
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            if witness(grid):
                hits[name] += 1
                for rival_name in GEN.WITNESS_RIVALS[name]:
                    assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(count > 0 for count in hits.values())


def test_pinned_profile_floor_has_at_least_25_percent_exact_support():
    exact = 0
    strict = 0
    per_band = {}
    for band in ("easy", "medium", "hard"):
        band_exact = 0
        for index in range(20):
            digest = hashlib.sha256(f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            hit = profile == (9, 9, 3)
            exact += hit
            band_exact += hit
            strict += not GEN.strict_canonical_like(grid)
        per_band[band] = band_exact
    assert all(count > 0 for count in per_band.values())
    assert exact >= 15
    assert strict >= 15


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261007)
    state = random.getstate()
    first = GEN.generate(77, 5, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(77, 5, difficulty="medium")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    original = deepcopy(second)
    first[0][0] = 9
    assert second == original


def test_self_check_rejects_rule_hiding_near_misses_without_requiring_connectivity():
    disconnected = GEN.generate(3, 2, shape_kind="pad_left")
    assert GEN.self_check(disconnected) == []
    blank = [[0] * 9 for _ in range(9)]
    assert GEN.self_check(blank)
    bad_palette = deepcopy(disconnected); bad_palette[0][0] = 7
    assert GEN.self_check(bad_palette)
    adjacent_four = deepcopy(disconnected)
    fours = [(r, c) for r, row in enumerate(adjacent_four) for c, value in enumerate(row) if value == 4]
    r, c = fours[0]
    for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(adjacent_four) and 0 <= nc < len(adjacent_four[0]) and adjacent_four[nr][nc] == 0:
            adjacent_four[nr][nc] = 4
            break
    assert GEN.self_check(adjacent_four)


def test_retained_counterexample_refutes_every_declared_rival():
    path = HOME / "counterexamples" / "padding-fragmentation-count.json"
    record = json.loads(path.read_text())
    grid = record["input"]
    expected = record["expected_output"]
    assert GEN.self_check(grid) == []
    assert expected == independent_rule(grid) == GEN.rule_mirror(grid)
    assert set(record["refutes"]) == set(GEN.SEMANTIC_RIVALS)
    for name in record["refutes"]:
        assert GEN.SEMANTIC_RIVALS[name](grid) != expected


def test_horizontal_left_alignment_shortcut_fits_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    shortcut = GEN.CANONICAL_SHORTCUTS["left_align_narrow_motif"]
    assert all(shortcut(item["input"]) == item["output"] for item in pairs)
    record = json.loads(
        (HOME / "counterexamples" / "padding-fragmentation-count.json").read_text()
    )
    assert shortcut(record["input"]) != record["expected_output"]
