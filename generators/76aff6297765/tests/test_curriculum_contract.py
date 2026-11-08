from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.76aff6297765.generator")
TASK_ID = "76aff6297765"
EXPECTED_RULE_HASH = "5b347fef0b78"


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _labelled(seed: int, sample_index: int, difficulty: str):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _is_same_foreground(grid) -> bool:
    info = gen._analysis(grid)
    return info["top_color"] == info["bot_color"]


def _is_distinct_noncanonical(grid) -> bool:
    info = gen._analysis(grid)
    return (
        info["top_color"] != info["bot_color"]
        and gen.strict_canonical_like(grid) != []
    )


def test_rule_hash_and_all_canonical_pairs_are_grounded():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_shortcut_declaration_contains_only_actual_canonical_fits():
    pairs = _canonical_pairs()
    declared = set(gen.CANONICAL_SHORTCUTS)
    actual = {
        name
        for name, rival in gen.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    }
    assert declared == actual == {"equal_cells", "profile_gated_count_only"}


def test_profile_gated_count_shortcut_is_registered():
    assert "profile_gated_count_only" in gen.SEMANTIC_RIVALS
    assert "profile_gated_count_only" in gen.LESSON_COMPETITORS


def test_schedule_has_two_anchors_two_same_colour_and_two_broad_distinct_slots():
    assert gen.EXAMPLES_NEEDED == 5
    profiles = tuple(gen.SCHEDULE_PROFILES)
    assert len(profiles) == 6
    assert sum(name.startswith("canonical_anchor") for name in profiles) == 2
    assert sum(name.startswith("same_foreground") for name in profiles) == 2
    assert sum(name.startswith("distinct_broad") for name in profiles) == 2


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 31, 91])
@pytest.mark.parametrize("start", range(6))
def test_every_cyclic_six_pair_window_is_identifiable_under_every_query_rotation(
    difficulty: str, seed: int, start: int
):
    pairs = [_labelled(seed, start + offset, difficulty) for offset in range(6)]

    assert sum(gen.strict_canonical_like(pair["input"]) == [] for pair in pairs) == 2
    assert sum(_is_same_foreground(pair["input"]) for pair in pairs) == 2
    assert sum(_is_distinct_noncanonical(pair["input"]) for pair in pairs) == 2

    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(
                rival(demo["input"]) != demo["output"] for demo in demos
            ), (difficulty, seed, start, query_index, name)


@pytest.mark.parametrize(
    "difficulty,seed,sample_index",
    [
        ("easy", 31, 6),
        ("easy", 54, 3),
        ("easy", 57, 15),
        ("easy", 70, 9),
        ("easy", 72, 3),
        ("medium", 31, 6),
        ("hard", 31, 6),
    ],
)
def test_every_draw_refutes_row_major_count_shortcut(
    difficulty: str, seed: int, sample_index: int
):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    assert gen._rival_count_only_row_major(grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_profiles_match_observable_scene_categories(difficulty: str):
    for sample_index, profile in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(2026, sample_index, difficulty=difficulty)
        assert gen.schedule_profile(2026, sample_index, difficulty) == profile
        if profile.startswith("canonical_anchor"):
            assert gen.strict_canonical_like(grid) == []
        elif profile.startswith("same_foreground"):
            assert _is_same_foreground(grid)
            assert gen.strict_canonical_like(grid) != []
        elif profile.startswith("distinct_broad"):
            assert _is_distinct_noncanonical(grid)
        else:  # pragma: no cover - makes an unknown profile fail loudly
            raise AssertionError(f"unknown profile {profile!r}")


@pytest.mark.parametrize(
    "panel_h,panel_w,top_color,bot_color",
    [(3, 3, 1, 1), (8, 8, 9, 9), (6, 4, 2, 6), (5, 7, 4, 3)],
)
def test_exact_overrides_remain_observable(
    panel_h: int, panel_w: int, top_color: int, bot_color: int
):
    grid = gen.generate(
        77,
        4,
        difficulty="medium",
        panel_h=panel_h,
        panel_w=panel_w,
        top_color=top_color,
        bot_color=bot_color,
    )
    assert gen.observe_overrides(grid) == {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "top_color": top_color,
        "bot_color": bot_color,
    }
    assert gen.self_check(grid) == []


def test_unknown_override_rejected_and_generation_is_rng_pure():
    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(0, 0, typo_axis=3)

    state = random.getstate()
    first = gen.generate(23, 7, difficulty="medium")
    second = gen.generate(23, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == state


def test_every_semantic_witness_names_a_rival_it_actually_refutes():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
