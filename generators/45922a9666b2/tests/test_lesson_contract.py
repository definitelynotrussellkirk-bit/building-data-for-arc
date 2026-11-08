"""Behavioral regressions for whole-lesson teaching, including held-out pairs."""
from __future__ import annotations

from itertools import product

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _, _ = load_selected_generator("45922a9666b2", root=ROOT)


def canonical_route_mask(grid):
    """A memorized shape-to-route lookup that fits all published examples."""
    output = [row[:] for row in grid]
    for profile in generator.SCENE_PROFILES:
        rows = generator._PROFILE_ROWS[profile]
        if (len(rows), len(rows[0])) == (len(grid), len(grid[0])):
            for cells, _ in generator._profile_signature(profile)[4]:
                for row, col in cells:
                    output[row][col] = 2
            return output
    return output


def lesson(seed, start, band):
    grids = [generator.generate(seed, start + i, difficulty=band)
             for i in range(4)]
    return [{"input": grid, "output": generator.rule_mirror(grid)}
            for grid in grids]


def assert_no_ambiguous_rotation(pairs, rival):
    matches = [rival(pair["input"]) == pair["output"] for pair in pairs]
    for query in range(len(pairs)):
        if all(matches[i] for i in range(len(pairs)) if i != query):
            assert matches[query], (query, matches)


def test_fixed_template_really_fits_every_labeled_canonical_pair():
    pairs = canonical_pairs(generator.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert canonical_route_mask(pair["input"]) == pair["output"]


def test_observed_baseline_teaching_failure_is_repaired():
    # Baseline v3.0.0: three canonical-layout demonstrations followed by a
    # procedural query; the lookup fits all demonstrations and misses query.
    pairs = lesson(4, 46, "medium")
    assert_no_ambiguous_rotation(pairs, canonical_route_mask)


def test_three_demo_windows_refute_template_for_each_small_schedule_start():
    for seed, start, band in product((0, 4, 19), range(6),
                                     ("easy", "medium", "hard")):
        pairs = lesson(seed, start, band)
        assert_no_ambiguous_rotation(pairs, canonical_route_mask)


def test_canonical_shortcut_declarations_are_truthful():
    rivals = getattr(generator, "CANONICAL_SHORTCUTS", {})
    assert "canonical_route_mask" in rivals
    for rival in rivals.values():
        for pair in canonical_pairs(generator.TASK_ID, root=ROOT,
                                    labeled_only=True):
            assert rival(pair["input"]) == pair["output"]


def test_lesson_hook_detects_a_real_ambiguous_forced_lesson():
    pairs = []
    for index in range(3):
        grid = generator.generate(4, 46 + index, difficulty="medium",
                                  route_layout="canonical")
        pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
    grid = generator.generate(4, 49, difficulty="medium",
                              route_layout="procedural")
    query = {"input": grid, "output": generator.rule_mirror(grid)}
    assert canonical_route_mask(grid) != query["output"]
    hook = getattr(generator, "lesson_identifiable", None)
    assert callable(hook)
    reasons = hook(pairs, query)
    assert any("canonical_route_mask" in reason for reason in reasons)


def test_declared_rivals_and_witnesses_are_input_pure():
    grid = generator.generate(31, 7, difficulty="hard")
    snapshot = [row[:] for row in grid]
    for rival in getattr(generator, "LESSON_COMPETITORS", {}).values():
        first = rival(grid)
        assert first == rival(grid)
        assert grid == snapshot
    witnesses = getattr(generator, "SEMANTIC_WITNESSES", {})
    assert witnesses
    for predicate in witnesses.values():
        assert type(predicate(grid)) is bool
        assert grid == snapshot
