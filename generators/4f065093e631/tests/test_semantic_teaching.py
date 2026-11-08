"""Regressions for the rare-color shortcut and its scheduled counterexample.

These focused checks use canonical labels where available and the Python mirror
for intermediate generated labels. The official semantic gate and census use
the Racket authority independently.
"""
from collections import Counter
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "4f065093e631"
ROOT = find_root(__file__)
generator, _SOURCE, _SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def _counts(grid):
    return Counter(value for row in grid for value in row)


def _box_for_color(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value == color]
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _border(box):
    top, left, bottom, right = box
    return {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)}


def _other_zero_slot(grid, source):
    top, left, bottom, right = source
    height, width = bottom - top + 1, right - left + 1
    for r in range(len(grid) - height + 1):
        for c in range(len(grid[0]) - width + 1):
            box = (r, c, r + height - 1, c + width - 1)
            if box != source and all(
                grid[rr][cc] == 0
                for rr in range(r + 1, r + height - 1)
                for cc in range(c + 1, c + width - 1)
            ):
                return box
    raise AssertionError("No second zero-interior slot")


def _paint_other_slot(grid, color):
    output = [row[:] for row in grid]
    for r, c in _border(_other_zero_slot(grid, _box_for_color(grid, color))):
        output[r][c] = color
    return output


def _rare_color_bbox(grid):
    """Deliberate shortcut: choose the rarest nonzero color, not largest frame."""
    counts = _counts(grid)
    color = min((value for value in counts if value), key=lambda value: (counts[value], value))
    return _paint_other_slot(grid, color)


def _source_color(grid):
    colors = [color for color, count in _counts(grid).items()
              if color and count in (14, 18)]
    assert len(colors) == 1
    return colors[0]


def _disjoint(first, second):
    return (first[2] < second[0] or second[2] < first[0]
            or first[3] < second[1] or second[3] < first[1])


def _assert_decoy(grid):
    counts = _counts(grid)
    assert len(counts) == 5
    colors = [color for color, count in counts.items() if color and count == 8]
    assert len(colors) == 1
    color = colors[0]
    decoy = _box_for_color(grid, color)
    assert decoy[2] - decoy[0] == decoy[3] - decoy[1] == 2
    assert grid[decoy[0] + 1][decoy[1] + 1] == 0
    assert all(grid[r][c] == color for r, c in _border(decoy))
    source = _box_for_color(grid, _source_color(grid))
    target = _other_zero_slot(grid, source)
    assert _disjoint(decoy, source) and _disjoint(decoy, target)
    assert all(count >= 30 for value, count in counts.items()
               if value not in (0, color, _source_color(grid)))
    expected = _paint_other_slot(grid, _source_color(grid))
    assert generator.rule_mirror(grid) == expected
    assert _rare_color_bbox(grid) != expected
    return color, decoy


def test_rare_color_bbox_fits_every_labeled_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert _rare_color_bbox(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("profile", generator.SCENE_PROFILES)
def test_sampling_alternates_canonical_anchor_and_rare_decoy(band, profile):
    for index in (0, 1):
        grid = generator.generate(817, index, difficulty=band, scene_profile=profile)
        assert generator.self_check(grid) == []
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        if index == 0:
            assert len(_counts(grid)) == 4
            assert _rare_color_bbox(grid) == generator.rule_mirror(grid)
        else:
            _assert_decoy(grid)


def test_semantic_declarations_refute_the_named_shortcut():
    shortcuts = getattr(generator, "CANONICAL_SHORTCUTS", {})
    assert "rarest_color_bbox" in shortcuts, "The canonical-fitting shortcut must be explicit"
    rival = shortcuts["rarest_color_bbox"]
    assert generator.SEMANTIC_RIVALS["rarest_color_bbox"] is rival
    assert generator.LESSON_COMPETITORS["rarest_color_bbox"] is rival
    assert "rarest_color_bbox" in generator.WITNESS_RIVALS["rare_color_decoy"]
    witness = generator.SEMANTIC_WITNESSES["rare_color_decoy"]
    for index in (0, 1):
        grid = generator.generate(19, index)
        assert witness(grid) is bool(index)
        assert rival(grid) == _rare_color_bbox(grid)
        if index:
            assert rival(grid) != generator.rule_mirror(grid)
            assert generator.strict_canonical_like(grid)
        else:
            assert generator.strict_canonical_like(grid) == []


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("start", range(6))
def test_four_pair_windows_teach_the_rival_under_every_query_rotation(band, start):
    assert getattr(generator, "LESSON_SCHEDULE_PERIOD", None) == 6
    assert generator.EXAMPLES_NEEDED == 3
    pairs = []
    for index in range(start, start + 4):
        grid = generator.generate(0, index, difficulty=band)
        branch = "rare_color_decoy" if index % 2 else "canonical_anchor"
        rank = ("low", "interior", "high")[index % 3]
        expected_profile = f"{branch}_source_{rank}"
        assert generator.schedule_profile(0, index, band) == expected_profile
        palette = sorted(color for color in _counts(grid) if color)
        source_color = _source_color(grid)
        observed_rank = ("low" if source_color == palette[0] else
                         "high" if source_color == palette[-1] else "interior")
        assert observed_rank == rank
        pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
    assert sum(len(_counts(pair["input"])) == 5 for pair in pairs) == 2
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert any(_rare_color_bbox(pair["input"]) != pair["output"] for pair in demos)
        for highest in (False, True):
            assert any(_numeric_color_rule(pair["input"], highest) != pair["output"]
                       for pair in demos)
        assert generator.lesson_identifiable(demos, query) == []


def test_anchor_only_demonstrations_do_not_teach_a_decoy_query():
    identify = getattr(generator, "lesson_identifiable", None)
    assert callable(identify), "The lesson hook must actually score surviving rivals"
    demos = []
    for index in (0, 2, 4):
        grid = generator.generate(771, index)
        demos.append({"input": grid, "output": generator.rule_mirror(grid)})
    grid = generator.generate(771, 1)
    query = {"input": grid, "output": generator.rule_mirror(grid)}
    reasons = identify(demos, query)
    assert reasons and any("rarest_color_bbox" in reason for reason in reasons)


def test_generic_fifth_colors_and_incomplete_decoys_are_rejected():
    anchor = generator.generate(27, 0)
    fresh = next(color for color in range(1, 10) if color not in _counts(anchor))
    singleton = [row[:] for row in anchor]
    singleton[0][0] = fresh
    assert generator.self_check(singleton)
    assert generator.observe_overrides(singleton) == {}
    decoy_grid = generator.generate(27, 1)
    _color, decoy = _assert_decoy(decoy_grid)
    for position in ((decoy[0], decoy[1]), (decoy[0] + 1, decoy[1] + 1)):
        broken = [row[:] for row in decoy_grid]
        broken[position[0]][position[1]] = 0 if position == (decoy[0], decoy[1]) else _color
        assert generator.self_check(broken)
        assert generator.observe_overrides(broken) == {}


def test_decoy_generation_preserves_global_rng_and_fresh_returns():
    state = random.getstate()
    first = generator.generate(441, 17, difficulty="hard")
    second = generator.generate(441, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second and first is not second and first[0] is not second[0]
    _assert_decoy(first)
    first[0][0] = (first[0][0] + 1) % 10
    assert second == generator.generate(441, 17, difficulty="hard")


@pytest.mark.parametrize("profile", generator.SCENE_PROFILES)
def test_each_retained_fallback_supports_a_disjoint_decoy(profile):
    add_decoy = getattr(generator, "_add_rare_color_decoy", None)
    assert callable(add_decoy), "A scheduled decoy must also be placed after fallback"
    grid = generator._fallback_scene(profile, 9, 1, 2)
    original = [row[:] for row in grid]
    result = add_decoy(grid, profile, 3, random.Random(9021))
    assert grid == original
    assert generator.self_check(result) == []
    _assert_decoy(result)


@pytest.mark.parametrize("band", ("easy", None, "hard"))
@pytest.mark.parametrize("seed", (True, False, 1.0, 1.75, "1"))
def test_seed_requires_a_python_integer(seed, band):
    with pytest.raises(ValueError, match="seed must be an integer"):
        generator.generate(seed, 0, difficulty=band)


@pytest.mark.parametrize("band", ("easy", None, "hard"))
@pytest.mark.parametrize("sample_index", (True, False, -1))
def test_schedule_requires_a_nonnegative_integer_index(sample_index, band):
    with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
        generator.generate(991, sample_index, difficulty=band)


def test_signed_integer_seeds_remain_supported():
    # The public Catalog generation API permits signed integer seeds, while
    # sample_index alone must be nonnegative.
    first = generator.generate(-1, 0)
    assert generator.self_check(first) == []
    assert first == generator.generate(-1, 0)


def _numeric_color_rule(grid, highest):
    source_color = _source_color(grid)
    palette = sorted(color for color in _counts(grid) if color)
    if source_color == palette[-1 if highest else 0]:
        return _paint_other_slot(grid, source_color)
    return [row[:] for row in grid]


def _recolor_source_to_rank(grid, rank):
    source_color = _source_color(grid)
    palette = sorted(color for color in _counts(grid) if color)
    selected = palette[0 if rank == "low" else -1 if rank == "high" else 1]
    remaining_original = [color for color in palette if color != source_color]
    remaining_new = [color for color in palette if color != selected]
    mapping = {0: 0, source_color: selected, **dict(zip(remaining_original, remaining_new))}
    return [[mapping[value] for value in row] for row in grid]


@pytest.mark.parametrize("band,seed,start,query_index,highest", (
    ("easy", 198416826956592, 33, 0, False),
    ("medium", 162543051128192, 0, 2, True),
    ("hard", 17061489957215, 11, 2, True),
))
def test_retained_numeric_color_rotation_replays_are_refuted(band, seed, start, query_index, highest):
    pairs = []
    for index in range(start, start + 4):
        grid = generator.generate(seed, index, difficulty=band)
        pairs.append({"input": grid, "output": _paint_other_slot(grid, _source_color(grid))})
    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
    assert any(_numeric_color_rule(pair["input"], highest) != pair["output"]
               for pair in demos), "The retained numeric-color rival still fits every demonstration"
    assert generator.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("rank,name", (("low", "first_color_only"), ("high", "last_color_only")))
def test_numeric_rivals_detect_rank_constant_demonstration_ambiguity(rank, name):
    assert name in generator.LESSON_COMPETITORS
    assert name in generator.SEMANTIC_RIVALS
    assert name not in generator.CANONICAL_SHORTCUTS
    demos = []
    for index in (0, 1, 2):
        grid = _recolor_source_to_rank(generator.generate(301, index), rank)
        assert generator.self_check(grid) == []
        demos.append({"input": grid, "output": generator.rule_mirror(grid)})
    grid = _recolor_source_to_rank(generator.generate(301, 3), "interior")
    query = {"input": grid, "output": generator.rule_mirror(grid)}
    assert all(generator.LESSON_COMPETITORS[name](pair["input"]) == pair["output"] for pair in demos)
    assert generator.LESSON_COMPETITORS[name](grid) != query["output"]
    assert any(name in reason for reason in generator.lesson_identifiable(demos, query))
