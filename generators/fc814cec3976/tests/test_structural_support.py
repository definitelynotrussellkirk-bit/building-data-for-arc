"""Regressions for scalar validation and the retained fixed-red-layout shortcut."""
from collections import defaultdict

import pytest

from reviewer_support import find_root, load_selected_generator


gen, _, _ = load_selected_generator("fc814cec3976", root=find_root(__file__))


def _legacy_lookup(grid):
    """Use only original template masks; never examine candidate-relevant context."""
    template = gen._RED_LAYOUT_TO_TEMPLATE.get(gen._red_key(grid))
    result = [list(row) for row in grid]
    if template is None:
        return result
    original = template["grid"]
    mask = gen.rule_mirror(original)
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if mask[r][c] != original[r][c] and grid[r][c] == 5:
                result[r][c] = mask[r][c]
    return result


@pytest.mark.parametrize("axis,bad", [
    ("seed", True), ("seed", False),
    ("sample_index", True), ("sample_index", False), ("sample_index", -1),
])
def test_invalid_scalar_call_arguments_are_rejected(axis, bad):
    args = {"seed": 991, "sample_index": 0}
    args[axis] = bad
    with pytest.raises((TypeError, ValueError)):
        gen.generate(**args, difficulty="easy")


@pytest.mark.parametrize("seed", [-1, 2**32, 169446987945668, 2**96 + 17])
def test_integer_seed_domain_includes_large_internal_census_seeds(seed):
    grid = gen.generate(seed, 6445, difficulty="easy")
    assert gen.self_check(grid) == []
    assert grid == gen.generate(seed, 6445, difficulty="easy")


def test_known_red_layout_on_wrong_shape_is_rejected_without_indexing_error():
    # This crop retains public_2's red key but removes scene-code bit positions.
    grid = gen.generate(0, 0, scene_code=5)
    cropped = [row[:16] for row in grid[:16]]
    assert gen._red_key(cropped) == gen._red_key(grid)
    errors = gen.self_check(cropped)
    assert errors and any("19x19" in error for error in errors)
    assert gen.strict_canonical_like(cropped) == errors
    assert gen.observe_overrides(cropped) == {}


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_five_draw_window_refutes_red_layout_lookup_twice(difficulty):
    # Two refutations in six labeled pairs survive every one-query holdout.
    for seed in (0, 17, 991):
        disagree = []
        for index in range(24):
            grid = gen.generate(seed, index, difficulty=difficulty)
            disagree.append(gen.rule_mirror(grid) != _legacy_lookup(grid))
        for start in range(20):
            assert sum(disagree[start:start + 5]) >= 2, (seed, start, disagree)


def test_same_red_key_does_not_determine_selected_centers():
    centers_by_red_key = defaultdict(set)
    for code in range(840):
        grid = gen.generate(0, 0, scene_code=code)
        output = gen.rule_mirror(grid)
        centers = tuple((r, c) for r, row in enumerate(output)
                        for c, value in enumerate(row) if value == 4)
        centers_by_red_key[gen._red_key(grid)].add(centers)
    assert sum(len(values) > 1 for values in centers_by_red_key.values()) == 21


def test_lesson_contract_reports_actual_lookup_ambiguity():
    assert callable(getattr(gen, "lesson_identifiable", None))
    demos = []
    for code in (0, 5, 10):
        grid = gen.generate(0, 0, scene_code=code)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_input = gen.generate(0, 0, scene_code=1)
    query = {"input": query_input, "output": gen.rule_mirror(query_input)}
    assert gen.lesson_identifiable(demos, query)
    assert gen.lesson_identifiable([*demos, query], query) == []
