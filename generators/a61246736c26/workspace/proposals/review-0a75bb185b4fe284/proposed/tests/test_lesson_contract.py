"""Behavioral regression tests for the v4 review repairs.

Python mirrors keep the local schedule census cheap. The retained public
semantic gate and lesson census independently obtain labels from Racket.
"""
from pathlib import Path
import json
import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "a61246736c26"
ROOT = find_root(__file__)
MOD, SOURCE, SOURCE_HASH = load_selected_generator(TASK, root=ROOT)


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None])
@pytest.mark.parametrize("argument", ["seed", "sample_index"])
def test_generation_rejects_non_integer_identifiers(argument, value):
    kwargs = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    kwargs[argument] = value
    with pytest.raises((TypeError, ValueError)):
        MOD.generate(**kwargs)


def test_generation_rejects_negative_sample_index():
    with pytest.raises(ValueError):
        MOD.generate(991, -1)


def test_named_shortcuts_fit_every_labeled_canonical_pair():
    shortcuts = getattr(MOD, "CANONICAL_SHORTCUTS", {})
    assert {"same_row_zero_frame", "fixed_row_palette", "strip_only_when_same_row"} <= set(shortcuts), "Missing source-bound shortcut contract"
    for pair in canonical_pairs(TASK, root=ROOT):
        for name, rival in shortcuts.items():
            assert rival(pair["input"]) == pair["output"], name


def test_default_lessons_refute_rivals_after_every_query_rotation():
    rivals = getattr(MOD, "LESSON_COMPETITORS", {})
    assert rivals, "A missing lesson contract is not a pass"
    assert getattr(MOD, "EXAMPLES_NEEDED", None) == 5
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for start in range(8):
                grids, seen = [], set()
                for offset in range(30):
                    grid = MOD.generate(seed, start + offset, difficulty=band)
                    assert MOD.self_check(grid) == []
                    key = tuple(map(tuple, grid))
                    if key not in seen:
                        seen.add(key)
                        grids.append(grid)
                    if len(grids) == 6:
                        break
                assert len(grids) == 6, (band, seed, start)
                pairs = [{"input": grid, "output": MOD.rule_mirror(grid)} for grid in grids]
                for query_index in range(6):
                    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                    query = pairs[query_index]
                    assert MOD.lesson_identifiable(demos, query) == [], (band, seed, start, query_index)
                    for name, rival in rivals.items():
                        assert any(rival(pair["input"]) != pair["output"] for pair in demos), (band, seed, start, query_index, name)


def test_explicit_profiles_remain_observable_and_canonical_inputs_unchanged():
    pairs = canonical_pairs(TASK, root=ROOT)
    for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs):
        assert MOD.generate(13, 0, scene_profile=profile) == pair["input"]
    for band in ("easy", "medium", "hard"):
        for profile in MOD.GENERAL_PROFILES:
            grid = MOD.generate(17, 9, difficulty=band, scene_profile=profile)
            assert MOD.self_check(grid) == []
            assert MOD.observe_overrides(grid) == {"scene_profile": profile}


def test_retained_mixed_row_shortcut_lesson_is_flagged():
    path = ROOT / "generators" / TASK / "counterexamples" / "conditional_swatch_shortcut.json"
    lesson = json.loads(path.read_text())
    reasons = MOD.lesson_identifiable(lesson["train"], lesson["test"][0])
    assert any("strip_only_when_same_row" in reason for reason in reasons), reasons


def test_default_scene_profile_has_observable_keyed_provenance(monkeypatch):
    contexts = []
    factory = MOD.gen_ctx

    def capture_context(**kwargs):
        context = factory(**kwargs)
        contexts.append(context)
        return context

    monkeypatch.setattr(MOD, "gen_ctx", capture_context)
    for band in ("easy", "medium", "hard"):
        for sample_index in range(MOD.LESSON_SCHEDULE_PERIOD):
            grid = MOD.generate(0, sample_index, difficulty=band)
            context = contexts[-1]
            observed = MOD.observe_overrides(grid)["scene_profile"]
            assert context.axis_value("scene_profile") == observed, (band, sample_index)
            assert observed in context.draw_options("scene_profile")
