"""Regressions for strict draw inputs and learnable size-class lessons."""
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("48283e01e8ab", root=ROOT)


@pytest.mark.parametrize("argument", ["seed", "sample_index"])
@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", -1])
def test_draw_rejects_noninteger_and_negative_identity(argument, bad):
    kwargs = {"seed": 17, "sample_index": 0, "scene_profile": "public_train_1"}
    kwargs[argument] = bad
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(**kwargs)


def test_public_profile_does_not_bypass_difficulty_validation():
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="unknown", scene_profile="public_train_1")


def test_oversized_grid_is_rejected_without_validator_exception():
    grid = [[7] * 31 for _ in range(31)]
    grid[0][0] = 6
    reasons = GEN.self_check(grid)
    assert isinstance(reasons, list) and reasons


def test_canonical_shortcuts_fit_every_usable_canonical_pair():
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert rivals, "The task needs executable canonical-fitting rival declarations"
    for pair in canonical_pairs("48283e01e8ab", root=ROOT):
        for name, rival in rivals.items():
            assert rival(deepcopy(pair["input"])) == pair["output"], name


def test_nonrectangular_sixes_refute_template_memorization():
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert "canonical_shapes_only" in rivals
    grid = GEN.generate(17, 0, scene_profile="size6_nonrect")
    expected = [[5 if value == 6 else value for value in row] for row in grid]
    assert GEN.rule_mirror(grid) == expected
    assert rivals["canonical_shapes_only"](grid) != expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_lessons_teach_queries_under_every_holdout(band):
    hook = getattr(GEN, "lesson_identifiable", None)
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert callable(hook) and rivals, "Missing executable lesson contract"
    for seed in (0, 19):
        pairs = []
        for index in range(8):
            grid = GEN.generate(seed, index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for start in range(4):
            lesson = pairs[start:start + 5]
            for held_out in range(5):
                demos = [pair for i, pair in enumerate(lesson) if i != held_out]
                query = lesson[held_out]
                before = deepcopy((demos, query))
                assert hook(demos, query) == [], (seed, start, held_out)
                assert (demos, query) == before
                for name, rival in rivals.items():
                    if all(rival(pair["input"]) == pair["output"] for pair in demos):
                        assert rival(query["input"]) == query["output"], (name, seed, start, held_out)


def test_lesson_hook_detects_unseen_query_classes():
    hook = getattr(GEN, "lesson_identifiable", None)
    assert callable(hook)
    demo = GEN.generate(11, 0, scene_profile="repeated_lines")
    query = GEN.generate(11, 1, scene_profile="size6_nonrect")
    assert hook([{"input": demo, "output": GEN.rule_mirror(demo)}],
                {"input": query, "output": GEN.rule_mirror(query)})
