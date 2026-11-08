"""Behavioral regressions for the 2026-10-20 scalar and teaching defects."""
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from review_diagnostics import search_lesson

TASK_ID = "af840d59f24c"
ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def intended(grid):
    columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
    ranks = {column: index + 1 for index, column in enumerate(columns)}
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)]
            for row in grid]


def erase_nonmodal(grid):
    counts = Counter(value for row in grid for value in row if value)
    modal = min(counts, key=lambda color: (-counts[color], color))
    truth = intended(grid)
    return [[truth[r][c] if value == 0 else modal for c, value in enumerate(row)]
            for r, row in enumerate(grid)]


def first_seen_template(grid):
    """A shortcut learned from v2.0's row templates, without horizontal sorting."""
    seen = list(dict.fromkeys(c for row in grid for c, value in enumerate(row) if not value))
    size = len(seen)
    full = any(all(row[c] == 0 for row in grid) for c in seen)
    if full:
        middle = size // 2
        rank_order = [middle] + list(reversed([i for i in range(size) if i != middle]))
    else:
        rank_order = [size - 1]
        left, right = 0, size - 2
        while left <= right:
            rank_order.append(left)
            left += 1
            if left <= right:
                rank_order.append(right)
                right -= 1
    ranks = {column: rank + 1 for column, rank in zip(seen, rank_order)}
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)]
            for row in grid]


def frequency_template(grid):
    counts = Counter(c for row in grid for c, value in enumerate(row) if value == 0)
    patterns = {
        4: (2, 4, 3, 1), 5: (2, 4, 3, 1, 2), 6: (2, 5, 4, 1, 3, 2),
        7: (2, 5, 4, 1, 3, 2, 4), 8: (2, 5, 4, 1, 3, 2, 4, 5),
    }
    template = (3, 5, 2, len(grid), 4, 6) if len(grid) in counts.values() else patterns[len(counts)]
    ranks = {}
    for count in set(template):
        columns = sorted(c for c, actual in counts.items() if actual == count)
        expected = [i + 1 for i, actual in enumerate(template) if actual == count]
        if len(columns) != len(expected):
            return [row[:] for row in grid]
        ranks.update(zip(columns, expected, strict=True))
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)]
            for row in grid]


INVALID_ARGUMENTS = [
    ("seed", value) for value in (True, False, 1.0, 1.75, "1", None)
] + [
    ("sample_index", value) for value in (True, False, 1.0, 1.75, "1", None, -1)
]


@pytest.mark.parametrize("entrypoint", ["generate", "schedule_profile"])
@pytest.mark.parametrize("argument,value", INVALID_ARGUMENTS)
def test_stream_arguments_reject_coercions_and_negative_positions(entrypoint, argument, value):
    kwargs = {"seed": 991, "sample_index": 0, argument: value}
    with pytest.raises((TypeError, ValueError), match=argument):
        getattr(gen, entrypoint)(**kwargs)


def test_integer_seed_domain_includes_negative_seeds_and_large_positions():
    for seed, index in ((-1, 0), (0, 10000), (2**80, 17)):
        grid = gen.generate(seed, index)
        assert gen.self_check(grid) == []
        assert gen.generate(seed, index) == grid


@pytest.mark.parametrize("profile", gen.PROFILES)
def test_generation_breaks_the_first_seen_template(profile):
    for seed in range(8):
        grid = gen.generate(seed, 0, scene_profile=profile)
        assert first_seen_template(grid) != intended(grid), (profile, seed)


@pytest.mark.parametrize("profile", gen.PROFILES)
def test_generation_breaks_the_frequency_template(profile):
    for seed in range(8):
        grid = gen.generate(seed, 0, scene_profile=profile)
        assert frequency_template(grid) != intended(grid), (profile, seed)


@pytest.mark.parametrize("profile", gen.PROFILES)
def test_column_frequency_vectors_vary_within_each_profile(profile):
    signatures = set()
    for seed in range(16):
        grid = gen.generate(seed, 0, scene_profile=profile)
        columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
        signatures.add(tuple(sum(row[c] == 0 for row in grid) for c in columns))
    assert len(signatures) > 1, (profile, signatures)


def test_erasing_nonmodal_color_is_a_canonical_fitting_rival():
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert erase_nonmodal(pair["input"]) == pair["output"]
    assert "erase_nonmodal" in gen.CANONICAL_SHORTCUTS


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_rotated_lesson_teaches_nonmodal_preservation(band):
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        grids = [gen.generate(1009 + start, start + offset, difficulty=band)
                 for offset in range(gen.EXAMPLES_NEEDED + 1)]
        for query_index in range(len(grids)):
            demos = [grid for index, grid in enumerate(grids) if index != query_index]
            assert any(erase_nonmodal(grid) != intended(grid) for grid in demos), (
                band, start, query_index,
            )


def test_every_five_pair_window_keeps_two_canonical_and_two_mixed_profiles():
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        profiles = [gen.schedule_profile(0, start + offset) for offset in range(5)]
        assert profiles.count("canonical_sparse") == 2, (start, profiles)
        assert profiles.count("dense_mixed") == 2, (start, profiles)


def test_dense_separator_has_rank_evidence_on_both_sides():
    for seed in range(16):
        grid = gen.generate(seed, 0, scene_profile="dense_mixed")
        columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
        full = [c for c in columns if all(row[c] == 0 for row in grid)]
        assert len(full) == 1
        assert columns[0] < full[0] < columns[-1], (seed, full, columns)


@pytest.mark.parametrize("band,seed,start", [
    ("easy", 224237499091295, 22),
    ("hard", 223992438681064, 11),
    ("hard", 99617028687797, 22),
])
def test_retained_object_attribution_rivals_are_refuted_in_every_holdout(band, seed, start):
    pairs = []
    for offset in range(5):
        grid = gen.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": intended(grid)})
    for held_out in range(5):
        lesson = {"train": [p for i, p in enumerate(pairs) if i != held_out],
                  "test": [pairs[held_out]]}
        report = search_lesson(gen, lesson)
        assert report["errors"] == []
        assert not report["ambiguous"], (seed, start, held_out, report)
