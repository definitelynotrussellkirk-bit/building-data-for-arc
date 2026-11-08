"""Behavioral regressions for the crop-smallest distribution repair."""

import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
gen, SOURCE, _ = load_selected_generator("7f03452e81df", root=ROOT)


def normalize_colors(grid):
    mapping = {0: 0}
    for row in grid:
        for color in row:
            if color not in mapping:
                mapping[color] = len(mapping)
    return tuple(tuple(mapping[color] for color in row) for row in grid)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", -1])
def test_sample_index_rejects_lossy_or_negative_values(value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(19, value)


@pytest.mark.parametrize("profile", gen.SCENE_PROFILES)
def test_each_profile_varies_geometry_and_target_placement(profile):
    scenes = set()
    bounds = set()
    for seed in range(24):
        grid = gen.generate(seed, 0, scene_profile=profile)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        scenes.add(normalize_colors(grid))
        target = gen._chosen(gen._components(grid))
        bounds.add(tuple(target[key] for key in ("r1", "c1", "r2", "c2")))
    assert len(scenes) >= 12, (profile, "palette-normalized scenes", len(scenes))
    assert len(bounds) >= 4, (profile, "selected bounding boxes", len(bounds))


def test_query_is_not_a_palette_copy_of_any_demonstration():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 7, 19):
            for start in range(5):
                pairs = [gen.generate(seed, start + offset, difficulty=band)
                         for offset in range(gen.EXAMPLES_NEEDED + 1)]
                query = normalize_colors(pairs[-1])
                assert all(query != normalize_colors(grid) for grid in pairs[:-1]), (
                    band, seed, start)


def _counterexample():
    # Repository mirror is deliberately preferred in portable task-test copies.
    path = ROOT / "generators/7f03452e81df/counterexamples/non_template_tie.json"
    if not path.is_file():
        path = SOURCE.parent / "counterexamples/non_template_tie.json"
    return json.loads(path.read_text())


def test_lawful_non_template_witness_is_valid_teaching_evidence():
    record = _counterexample()
    grid = record["input"]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.rule_mirror(grid) == record["expected_output"]
    demos = []
    for profile in gen.SCENE_PROFILES:
        item = grid if profile == "tie_col" else gen.generate(19, 0, scene_profile=profile)
        demos.append({"input": item, "output": gen.rule_mirror(item)})
    query = gen.generate(19, 5)
    assert gen.lesson_identifiable(demos, {"input": query}) == []


def test_under_taught_non_template_lesson_returns_reasons():
    grid = _counterexample()["input"]
    demos = [{"input": grid, "output": gen.rule_mirror(grid)} for _ in range(5)]
    reasons = gen.lesson_identifiable(demos, {"input": grid})
    assert isinstance(reasons, list)
    assert any("competitor" in reason for reason in reasons)
