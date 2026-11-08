"""Focused regressions for the enclosed-region area curriculum."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base
from puzzle_generators.per_puzzle.b28619e32f6f import generator as gen
from scripts.canonical_profile_gate import canonical_pairs

REPO_ROOT = Path(__file__).resolve().parents[3]


def _canonical_row() -> dict:
    path = REPO_ROOT / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _pair(seed: int, sample_index: int, difficulty: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_every_canonical_pair_are_pinned() -> None:
    row = _canonical_row()
    actual = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual

    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_all_exact_profiles_are_observable_in_every_band() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for profile_index, profile in enumerate(gen.PROFILES):
            grid = gen.generate(
                20_260_729 + band_index,
                profile_index,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.rule_mirror(grid) != grid


def test_default_axis_is_keyed_and_matches_the_six_slot_schedule() -> None:
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for sample_index in range(18):
                grid = gen.generate(701, sample_index, difficulty=band)
                ctx = captured[-1]
                assert ctx.recorded_draws()["scene_profile"] == gen.schedule_profile(
                    701, sample_index, band
                )
                assert gen.observe_overrides(grid) == {
                    "scene_profile": ctx.recorded_draws()["scene_profile"]
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_every_three_demo_window_identifies_the_rule() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            demos = [_pair(8801, start + offset, band) for offset in range(gen.EXAMPLES_NEEDED)]
            query = _pair(9911, start + gen.EXAMPLES_NEEDED, band)
            assert gen.lesson_identifiable(demos, query) == []
            profiles = {gen.observe_overrides(pair["input"])["scene_profile"] for pair in demos}
            assert "split_all" in profiles
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                ), name


def test_split_profile_is_one_frame_with_three_independent_area_branches() -> None:
    grid = gen.generate(444, 0, difficulty="hard", scene_profile="split_all")
    errors, analysis = gen._analyze(grid)
    assert errors == []
    assert analysis is not None
    assert analysis["bucket_counts"] == {"tiny": 1, "medium": 1, "large": 1}
    split_frames = [frame for frame in analysis["frames"] if len(frame["regions"]) == 3]
    assert len(split_frames) == 1
    sizes = sorted(region["size"] for region in split_frames[0]["regions"])
    assert sizes[0] <= 8 < sizes[1] <= 24 < sizes[2]
    assert sizes[0] not in (8, 24) and sizes[1] not in (8, 24)
    assert {gen.rule_mirror(grid)[next(iter(region["cells"]))[0]][next(iter(region["cells"]))[1]]
            for region in split_frames[0]["regions"]} == {8, 4, 3}


def test_targeted_impostors_and_old_weak_self_check_cases_are_rejected() -> None:
    valid = gen.generate(812, 0, scene_profile="medium")
    assert gen.self_check(valid) == []

    all_background = [[0] * 7 for _ in range(7)]
    short_line = [[0] * 7 for _ in range(7)]
    short_line[3][2:5] = [2, 2, 2]
    solid_2x2 = [[0] * 7 for _ in range(7)]
    for r in (2, 3):
        for c in (2, 3):
            solid_2x2[r][c] = 2

    broken_frame = copy.deepcopy(valid)
    red = [(r, c) for r, row in enumerate(broken_frame) for c, value in enumerate(row) if value == 2]
    r, c = red[len(red) // 2]
    broken_frame[r][c] = 0

    stray_red = copy.deepcopy(valid)
    exterior = next(
        (r, c)
        for r, row in enumerate(stray_red)
        for c, value in enumerate(row)
        if value == 0 and all(
            not (0 <= r + dr < len(stray_red) and 0 <= c + dc < len(row) and stray_red[r + dr][c + dc] == 2)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
    )
    stray_red[exterior[0]][exterior[1]] = 2

    no_exterior = [[2] * 7 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 6):
            no_exterior[r][c] = 0

    invalid_color = copy.deepcopy(valid)
    invalid_color[0][0] = 10
    ragged = [row[:] for row in valid]
    ragged[-1].pop()

    for name, impostor in {
        "all_background": all_background,
        "short_line": short_line,
        "solid_2x2": solid_2x2,
        "broken_frame": broken_frame,
        "stray_red": stray_red,
        "no_exterior": no_exterior,
        "invalid_color": invalid_color,
        "ragged": ragged,
    }.items():
        assert gen.self_check(impostor), name
        assert gen.strict_canonical_like(impostor), name


def test_unknown_and_invalid_generation_calls_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="x")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 0, scene_profile="not-a-profile")


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(314159)
    expected_state = random.getstate()
    first = gen.generate(77, 11, difficulty="hard")
    assert random.getstate() == expected_state
    second = gen.generate(77, 11, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert gen.generate(77, 11, difficulty="hard") == second
    assert gen.generate(78, 11, difficulty="hard") != second
