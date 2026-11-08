"""Regression tests for the header-selected object packing contract."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "aa45957d8241"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_pack_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)


def pairs():
    return canonical_pairs(TASK, root=ROOT, labeled_only=True)


def canonical_program():
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise KeyError(TASK)


def components(grid):
    """Independent same-colour 4-connected body components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({
                "color": color,
                "cells": cells,
                "r0": min(rr for rr, _ in cells),
                "c0": min(cc for _, cc in cells),
            })
    return result


def lesson_properties(grid):
    codes = [value for value in grid[0] if value]
    objs = components(grid)
    selected = [obj for obj in objs if obj["color"] in codes]
    left_to_right = [obj["color"] for obj in sorted(selected, key=lambda o: (o["c0"], o["r0"]))]
    return {
        "has_distractor": any(obj["color"] not in codes for obj in objs),
        "order_conflict": left_to_right != codes,
    }


def test_canonical_inputs_are_in_domain_and_reference_labels_match():
    canonical = pairs()
    assert len(canonical) == 4
    assert all(gen.self_check(pair["input"]) == [] for pair in canonical)
    assert hasattr(gen, "rule_mirror")
    assert all(gen.rule_mirror(pair["input"]) == pair["output"] for pair in canonical)


def test_source_bound_semantic_contract_is_declared():
    assert getattr(gen, "RULE_HASH", None) == "b2f937b0b8b5"
    for name in (
        "strict_canonical_like",
        "schedule_profile",
        "SEMANTIC_WITNESSES",
        "SEMANTIC_RIVALS",
        "CANONICAL_SHORTCUTS",
        "LESSON_COMPETITORS",
        "lesson_identifiable",
    ):
        assert hasattr(gen, name), name


def test_rule_hash_matches_canonical_racket_source():
    source = canonical_program()
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected


def test_canonical_left_to_right_shortcut_is_real():
    shortcut = gen.CANONICAL_SHORTCUTS["body_left_to_right"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_four_pair_lessons_survive_every_query_rotation(band):
    for seed in range(12):
        grids = [gen.generate(seed, offset, difficulty=band) for offset in range(4)]
        assert all(gen.self_check(grid) == [] for grid in grids)
        props = [lesson_properties(grid) for grid in grids]
        assert any(item["has_distractor"] for item in props)
        assert any(item["order_conflict"] for item in props)
        assert any(item["has_distractor"] and item["order_conflict"] for item in props)
        labelled = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(labelled) if index != query_index]
            assert gen.lesson_identifiable(demos, labelled[query_index]) == []


def test_retry_path_keeps_every_default_draw_valid():
    for band in (None, "easy", "medium", "hard"):
        for seed in range(200):
            grid = gen.generate(seed, seed * 17, difficulty=band)
            assert gen.self_check(grid) == [], (band, seed, gen.self_check(grid))


def test_exact_controls_are_observable_in_pixels():
    grid = gen.generate(81, 4, difficulty="hard", grid_h=10, grid_w=14,
                        n_codes=3, n_distractors=1)
    assert len(grid) == 10 and len(grid[0]) == 14
    assert gen.observe_overrides(grid) == {
        "grid_h": 10,
        "grid_w": 14,
        "n_codes": 3,
        "n_distractors": 1,
    }
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("overrides", [
    {"grid_h": 7}, {"grid_w": 10}, {"n_codes": 1}, {"n_codes": 4},
    {"n_distractors": -1}, {"n_distractors": 3}, {"grid_h": True},
    {"texture": "legacy"}, {"palette_kind": "warm"},
])
def test_invalid_or_retired_controls_fail_loudly(overrides):
    with pytest.raises(ValueError):
        gen.generate(1, 2, **overrides)


def test_validator_allows_unlisted_distractor_but_rejects_selected_ambiguity():
    grid = [row[:] for row in pairs()[0]["input"]]
    assert lesson_properties(grid)["has_distractor"]
    assert gen.self_check(grid) == []

    selected = next(value for value in grid[0] if value)
    # Row 1 is the separator; place an isolated duplicate selected-colour cell
    # at a blank body coordinate to create a second component.
    for r in range(2, len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 0 and all(
                not (0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0])
                     and grid[r + dr][c + dc] == selected)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                grid[r][c] = selected
                errors = gen.self_check(grid)
                assert errors
                assert any("component" in error for error in errors)
                return
    raise AssertionError("canonical grid had no blank isolated coordinate")


def test_determinism_fresh_returns_and_global_rng_is_untouched():
    random.seed(90210)
    before = random.getstate()
    first = gen.generate(57, 11, difficulty="hard")
    assert random.getstate() == before
    expected = [row[:] for row in first]
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = gen.generate(57, 11, difficulty="hard")
    assert second == expected
    assert second is not expected and second[0] is not expected[0]


def test_explicit_zero_distractors_remains_feasible_on_selection_profile():
    # The override checker uses sample_index = seed * 17 + 3.  For this task
    # that always selects the "selection" curriculum residue, so the explicit
    # zero must override the default witness requirement instead of exhausting
    # the whole-layout retry loop.
    grid = gen.generate(0, 3, difficulty="easy", n_distractors=0)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["n_distractors"] == 0


@pytest.mark.parametrize("sample_index", range(3))
def test_smallest_canvas_supports_maximum_declared_object_counts(sample_index):
    grid = gen.generate(
        19,
        sample_index,
        difficulty="hard",
        grid_h=8,
        grid_w=11,
        n_codes=3,
        n_distractors=2,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 8,
        "grid_w": 11,
        "n_codes": 3,
        "n_distractors": 2,
    }


def test_declared_schedule_period_matches_profile_cycle():
    assert gen.LESSON_SCHEDULE_PERIOD == 3
    for seed in range(7):
        profiles = [gen.schedule_profile(seed, i) for i in range(gen.LESSON_SCHEDULE_PERIOD)]
        assert set(profiles) == set(gen.SCHEDULE_PROFILES)


@pytest.mark.parametrize("seed,sample_index,error", [
    (True, 0, TypeError),
    (False, 0, TypeError),
    (1, True, TypeError),
    (1, False, TypeError),
    (1, -1, ValueError),
])
def test_call_arguments_reject_bool_and_negative_sample_index(seed, sample_index, error):
    with pytest.raises(error):
        gen.generate(seed, sample_index, difficulty="hard")


def test_hard_band_pinned_census_keeps_exact_canonical_support_and_broad_range():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in pairs()
    }
    exact_hits = 0
    broad_hits = 0
    for index in range(20):
        seed = int(hashlib.sha256(
            f"profile-floor:v1:{TASK}:hard:{index}".encode()
        ).hexdigest()[:12], 16)
        sample_index = seed % 7919 + index
        grid = gen.generate(seed, sample_index, difficulty="hard")
        profile = (
            len(grid), len(grid[0]),
            len({value for row in grid for value in row}),
        )
        exact_hits += profile in canonical_profiles
        broad_hits += len(grid) > 10 or len(grid[0]) > 14
    assert exact_hits >= 1
    assert broad_hits >= 1
