from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("46b45dd2aff8", root=ROOT)


def _pair(seed: int, sample_index: int, band: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_all_canonical_inputs_are_accepted_and_python_mirror_is_exact():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_ambiguous_nearest_rule_is_killed_by_generated_color_trap():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert all(
        gen.CANONICAL_SHORTCUTS["nearest_aligned_ignoring_color"](pair["input"])
        == pair["output"]
        for pair in pairs
    )
    trap = gen.generate(17, 1, difficulty="medium")
    assert gen.schedule_profile(17, 1, "medium") == "color_trap"
    assert gen.SEMANTIC_WITNESSES["color_identity_beats_nearest_rectangle"](trap)
    assert gen.rule_mirror(trap) != gen._nearest_aligned_ignoring_color(trap)


def test_every_three_pair_window_survives_every_query_holdout():
    witness = gen.SEMANTIC_WITNESSES["color_identity_beats_nearest_rectangle"]
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            episode = [_pair(101, start + offset, band) for offset in range(3)]
            assert sum(witness(pair["input"]) for pair in episode) >= 2, (band, start)
            for held_out in range(3):
                demos = [pair for index, pair in enumerate(episode) if index != held_out]
                query = episode[held_out]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    held_out,
                    gen.lesson_identifiable(demos, query),
                )


def test_declared_override_boundaries_are_exact_and_unknown_axes_reject():
    for band in ("easy", "medium", "hard"):
        for h, w, bg, n_colors in ((13, 13, 0, 1), (30, 30, 9, 3)):
            grid = gen.generate(
                5,
                7,
                difficulty=band,
                grid_h=h,
                grid_w=w,
                background=bg,
                n_colors=n_colors,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {
                "grid_h": h,
                "grid_w": w,
                "background": bg,
                "n_colors": n_colors,
            }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, unexpected_axis=1)


def test_self_check_rejects_four_structural_impostors():
    grid = gen.generate(3, 0, difficulty="easy")
    facts = gen._scene_facts(grid)
    color = next(iter(facts["by_color"]))
    rect = facts["by_color"][color]["rects"][0]["bbox"]
    dots = facts["by_color"][color]["dots"]
    bg = facts["background"]

    no_dots = copy.deepcopy(grid)
    for r, c in dots:
        no_dots[r][c] = bg
    assert any("one to three isolated dots" in error for error in gen.self_check(no_dots))

    hollow_rect = copy.deepcopy(grid)
    r1, c1, r2, c2 = rect
    hollow_rect[(r1 + r2) // 2][(c1 + c2) // 2] = bg
    assert gen.self_check(hollow_rect)

    diagonal_dot = copy.deepcopy(grid)
    r, c = dots[0]
    diagonal_dot[r][c] = bg
    diagonal_dot[2][2] = color
    assert any("not axis-aligned" in error for error in gen.self_check(diagonal_dot))

    second_rect = copy.deepcopy(grid)
    for rr in range(len(grid) - 3, len(grid) - 1):
        for cc in range(2, 4):
            second_rect[rr][cc] = color
    assert any("exactly one solid rectangle" in error for error in gen.self_check(second_rect))


def test_deterministic_replay_fresh_objects_and_global_rng_purity():
    state = random.getstate()
    first = gen.generate(909, 11, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(909, 11, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(909, 11, difficulty="hard")


def test_all_semantic_witnesses_fire_in_each_band():
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        for sample_index in range(16):
            grid = gen.generate(700 + sample_index, sample_index, difficulty=band)
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                hits[name] += int(predicate(grid))
        assert all(count > 0 for count in hits.values()), (band, hits)
