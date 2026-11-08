"""Focused regressions for ARC generator dcb4d769d19d."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.dcb4d769d19d.generator"
)


def _copy(grid):
    return [row[:] for row in grid]


def _singleton_targets(grid):
    return sorted(
        component[0]
        for component in gen._components_by_color(grid).get(2, [])
        if len(component) == 1
    )


def test_all_canonical_pairs_are_accepted_and_match_the_rule():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_every_profile_is_exactly_observable_and_deterministic():
    for index, profile in enumerate(gen.SCENE_PROFILES):
        first = gen.generate(91, index, difficulty="easy", scene_profile=profile)
        second = gen.generate(91, index, difficulty="hard", scene_profile=profile)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert gen.self_check(first) == []
        assert gen.strict_canonical_like(first) == []
        assert gen.observe_overrides(first) == {"scene_profile": profile}
        assert gen.rule_mirror(first) != first


def test_every_schedule_residue_identifies_the_rule_in_every_band():
    for band in ("easy", "medium", "hard"):
        period = len(gen._PROFILES_BY_BAND[band])
        for start in range(period):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(17, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                17, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            assert {gen._analysis(pair["input"])["target_count"] for pair in demos} == {
                2,
                4,
            }
            assert len(
                {(len(pair["input"]), len(pair["input"][0])) for pair in demos}
            ) >= 2
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_targeted_structural_impostors_are_rejected():
    base = gen.generate(
        510, 0, difficulty="easy", scene_profile="easy_canon_four_a"
    )
    targets = _singleton_targets(base)
    assert len(targets) == 4

    leaked_answer = _copy(base)
    leaked_answer[0][0] = 4
    assert any("yellow 4" in finding for finding in gen.self_check(leaked_answer))

    border_target = _copy(base)
    border_target[0][0] = 2
    assert any("must be interior" in finding for finding in gen.self_check(border_target))

    merged_target = _copy(base)
    r, c = targets[0]
    arm = next(
        (r + dr, c + dc)
        for dr, dc in gen._DIRS4
        if merged_target[r + dr][c + dc] == 0
    )
    merged_target[arm[0]][arm[1]] = 2
    assert any("singleton red targets" in finding for finding in gen.self_check(merged_target))

    missing_larger_red = _copy(base)
    larger = [
        component
        for component in gen._components_by_color(base).get(2, [])
        if len(component) > 1
    ]
    assert len(larger) == 2
    for rr, cc in larger[0]:
        missing_larger_red[rr][cc] = 0
    assert any("at least two larger red" in finding for finding in gen.self_check(missing_larger_red))

    overlapping_crosses = _copy(base)
    source = targets[0]
    moved = targets[-1]
    overlap_center = None
    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        rr, cc = source[0] + dr, source[1] + dc
        if not (1 <= rr < len(base) - 1 and 1 <= cc < len(base[0]) - 1):
            continue
        if overlapping_crosses[rr][cc] != 0:
            continue
        if any(
            overlapping_crosses[rr + adr][cc + adc] == 2
            for adr, adc in gen._DIRS4
        ):
            continue
        overlap_center = (rr, cc)
        break
    assert overlap_center is not None
    overlapping_crosses[moved[0]][moved[1]] = 0
    overlapping_crosses[overlap_center[0]][overlap_center[1]] = 2
    assert any("crosses overlap" in finding for finding in gen.self_check(overlapping_crosses))

    missing_palette_color = _copy(base)
    components = gen._components_by_color(base)
    color_to_remove = next(color for color in components if color not in (2,))
    for rr, row in enumerate(missing_palette_color):
        for cc, value in enumerate(row):
            if value == color_to_remove:
                missing_palette_color[rr][cc] = 0
    assert any("exactly four colors" in finding for finding in gen.self_check(missing_palette_color))


def test_unknown_override_profile_and_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis="value")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        gen.generate(0, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(0, 0, difficulty="impossible")


def test_generation_preserves_process_global_random_state():
    random.seed(20260727)
    state = random.getstate()
    gen.generate(333, 11, difficulty="hard")
    assert random.getstate() == state
