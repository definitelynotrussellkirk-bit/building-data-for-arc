from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.c181f41a09f0 import generator as gen


TASK_ID = "c181f41a09f0"


def _canonical_inputs():
    rows = []
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            rows.extend(pair["input"] for pair in row.get(split, []))
    return rows


def _witness_grid():
    return gen.generate(
        991,
        0,
        difficulty="medium",
        grid_h=14,
        grid_w=14,
        orientation="horizontal",
        source_side="low",
        strip_count=3,
        marked_count=2,
        decoy_count=2,
        cap_color=9,
    )


def test_all_canonical_inputs_pass_structural_self_check():
    canonical = _canonical_inputs()
    assert len(canonical) == 8
    assert all(gen.self_check(grid) == [] for grid in canonical)


def test_exact_override_round_trip_and_four_sample_schedule():
    grid = _witness_grid()
    assert gen.observe_overrides(grid) == {
        "grid_h": 14,
        "grid_w": 14,
        "orientation": "horizontal",
        "source_side": "low",
        "strip_count": 3,
        "marked_count": 2,
        "decoy_count": 2,
        "cap_color": 9,
    }
    scheduled = [
        gen.observe_overrides(gen.generate(73, index, difficulty="medium"))
        for index in range(gen.EXAMPLES_NEEDED)
    ]
    assert {(item["orientation"], item["source_side"]) for item in scheduled} == {
        ("horizontal", "low"),
        ("vertical", "high"),
        ("horizontal", "high"),
        ("vertical", "low"),
    }
    assert all(1 <= item["marked_count"] < item["strip_count"] for item in scheduled)


def test_self_check_rejects_targeted_structural_impostors():
    grid = _witness_grid()
    facts = gen.profile_signature(grid)
    strips = facts["strip_bboxes"]

    no_caps = copy.deepcopy(grid)
    for r1, c1, r2, c2 in strips:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if no_caps[r][c] == 9:
                    no_caps[r][c] = 0
    assert gen.self_check(no_caps)

    both_ends = copy.deepcopy(grid)
    r1, c1, r2, c2 = next(
        bbox for bbox in strips
        if any(grid[r][c] == 9 for r in range(bbox[0], bbox[2] + 1) for c in range(0, 3))
    )
    both_ends[r1 + 1][c2 - 1] = 9
    assert any("both ends" in error for error in gen.self_check(both_ends))

    bridged = copy.deepcopy(grid)
    first, second = sorted(strips)[:2]
    for r in range(first[2] + 1, second[0]):
        bridged[r][5] = 0
    assert gen.self_check(bridged)

    second_color = copy.deepcopy(grid)
    changed = False
    for r, row in enumerate(second_color):
        for c, value in enumerate(row):
            if value == 9:
                second_color[r][c] = 8
                changed = True
                break
        if changed:
            break
    assert any("exactly one marker color" in error for error in gen.self_check(second_color))

    middle_marker = copy.deepcopy(grid)
    r1, c1, r2, c2 = strips[0]
    middle_marker[r1 + 1][(c1 + c2) // 2] = 9
    assert any("outside both end blocks" in error for error in gen.self_check(middle_marker))


def test_determinism_fresh_returns_and_global_rng_preservation():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(77, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    third = gen.generate(77, 2, difficulty="hard")
    assert third == second


def test_incompatible_exact_overrides_reject_loudly():
    try:
        gen.generate(
            1,
            0,
            difficulty="easy",
            grid_h=8,
            orientation="horizontal",
            strip_count=4,
        )
    except ValueError as exc:
        assert "outside" in str(exc) or "place" in str(exc) or "fit" in str(exc)
    else:
        raise AssertionError("incompatible grid_h/strip_count override was silently accepted")
