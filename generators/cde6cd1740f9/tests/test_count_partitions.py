"""Regressions for the missing complete-layer partition and scalar contracts."""
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, SOURCE, SOURCE_SHA256 = load_selected_generator("cde6cd1740f9", root=ROOT)


def grouped_partitions(grid):
    """Observe two-color, nine-cell columns without using generator analysis."""
    partitions = set()
    for col in range(len(grid[0])):
        colors = [row[col] for row in reversed(grid) if row[col]]
        counts = Counter(colors)
        if len(colors) == 9 and len(counts) == 2:
            order = list(dict.fromkeys(colors))
            partitions.add(tuple(counts[color] for color in order))
    return partitions


def count_ignoring_rival(grid):
    """Give each distinct source color one layer, repeating the last color."""
    out = [[0] * len(grid[0]) for _ in grid]
    for col in range(len(grid[0])):
        values = [row[col] for row in reversed(grid) if row[col]]
        if not values:
            continue
        k = int(len(values) ** 0.5)
        colors = list(dict.fromkeys(values))
        for layer in range(k):
            color = colors[min(layer, len(colors) - 1)]
            radius = k - layer - 1
            for c in range(col - radius, col + radius + 1):
                out[len(grid) - layer - 1][c] = color
    return out


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_ordinary_sampling_emits_both_complete_layer_partitions(band):
    for seed in (0, 73):
        partitions = set()
        for index in range(generator.LESSON_SCHEDULE_PERIOD):
            grid = generator.generate(seed, index, difficulty=band)
            assert generator.self_check(grid) == []
            assert generator.strict_canonical_like(grid) == []
            partitions.update(grouped_partitions(grid))
        assert partitions == {(5, 4), (8, 1)}


def test_all_declared_canonical_shortcuts_really_fit_canonical_labels():
    pairs = canonical_pairs(generator.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    failures = {
        name: sum(fn(pair["input"]) != pair["output"] for pair in pairs)
        for name, fn in generator.CANONICAL_SHORTCUTS.items()
    }
    assert not {name: n for name, n in failures.items() if n}, failures
    assert all(count_ignoring_rival(p["input"]) == p["output"] for p in pairs)


def test_8_plus_1_witness_requires_actual_color_counts():
    grid = [[0] * 13 for _ in range(16)]
    grid[1][6] = 5
    for row in range(4, 12):
        grid[row][6] = 2
    assert generator.self_check(grid) == []
    assert generator.strict_canonical_like(grid) == []
    expected = [[0] * 13 for _ in range(16)]
    expected[15][4:9] = [2] * 5
    expected[14][5:8] = [2] * 3
    expected[13][6] = 5
    assert generator.rule_mirror(grid) == expected
    rival = count_ignoring_rival(grid)
    differences = [(r, c) for r in range(16) for c in range(13) if rival[r][c] != expected[r][c]]
    assert differences == [(14, 5), (14, 6), (14, 7)]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_window_retains_both_partitions_after_any_query_holdout(band):
    for seed in (0, 7, 101):
        for start in range(generator.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for index in range(start, start + generator.EXAMPLES_NEEDED + 1):
                grid = generator.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
            for held_out in range(len(pairs)):
                demos = [pair for i, pair in enumerate(pairs) if i != held_out]
                partitions = set().union(*(grouped_partitions(p["input"]) for p in demos))
                assert partitions == {(5, 4), (8, 1)}, (seed, start, held_out, partitions)
                assert any(count_ignoring_rival(p["input"]) != p["output"] for p in demos)
                assert generator.lesson_identifiable(demos, pairs[held_out]) == []


@pytest.mark.parametrize("name,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", -1),
    ("sample_index", 1.0), ("sample_index", "1"),
    ("active_columns", True), ("active_columns", 1.0), ("active_columns", "1"),
    ("primary_color", True), ("primary_color", 1.0), ("primary_color", "1"),
    ("layout_shift", True), ("layout_shift", False), ("layout_shift", 1.0),
    ("layout_shift", "1"),
])
def test_invalid_scalar_controls_are_rejected_before_sampling(name, value):
    args = {"seed": 73, "sample_index": 0, name: value}
    with pytest.raises((ValueError, TypeError)):
        generator.generate(**args)


@pytest.mark.parametrize("name", ["active_columns", "primary_color", "layout_shift"])
def test_self_check_meta_does_not_accept_boolean_or_float_integer_aliases(name):
    kwargs = {"active_columns": 1, "primary_color": 1, "layout_shift": 1}
    grid = generator.generate(73, 0, **kwargs)
    for invalid in (True, 1.0):
        assert generator.self_check(grid, meta={"overrides": {name: invalid}})
