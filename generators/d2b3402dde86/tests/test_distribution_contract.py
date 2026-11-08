"""Behavioral regressions for the content-relative, floor-half curriculum.

These tests use the selected implementation and portable canonical authoring
data. Reference-runtime parity is checked separately by the review tools.
"""
from copy import deepcopy
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "d2b3402dde86"
BANDS = ("easy", "medium", "hard")
EXTENTS = ("canonical", "even", "odd")
SCENES = tuple(f"bbox_r{r}_c{c}" for r in (1, 2, 3) for c in (1, 2, 3))


@pytest.fixture(scope="module")
def generator():
    root = find_root(__file__)
    candidates = (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("distribution_contract_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def content_box(grid):
    """Independent geometric observation; no generator helper is consulted."""
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    bottom = max(r for r, _ in cells)
    right = max(c for _, c in cells)
    return top, left, bottom - top + 1, right - left + 1


def floor_answer(grid):
    top, left, height, width = content_box(grid)
    return [row[left:left + width // 2] for row in grid[top:top + height // 2]]


def pair(generator, seed, index, **kwargs):
    grid = generator.generate(seed, index, **kwargs)
    return {"input": grid, "output": floor_answer(grid)}


def test_canonical_labels_and_profile_acceptance_are_preserved(generator, canonical):
    # Catches excluding sparse canonical support or changing crop semantics.
    assert len(canonical) == 3
    for example in canonical:
        assert generator.rule_mirror(example["input"]) == example["output"]
        assert generator.self_check(example["input"]) == []
        assert generator.strict_canonical_like(example["input"]) == []


@pytest.mark.parametrize("height,width,want", [
    (4, 4, [[1, 2], [5, 6]]),
    (4, 6, [[1, 2, 3], [7, 8, 9]]),
    (6, 4, [[1, 2], [5, 6], [9, 1]]),
    (5, 7, [[1, 2, 3], [8, 9, 1]]),
])
def test_mirror_halves_each_axis_and_floors_odd_extents(generator, height, width, want):
    # Catches fixed 3x3, swapped axes, and ceil rather than floor division.
    grid = [[0] * (width + 2) for _ in range(height + 2)]
    for r in range(height):
        for c in range(width):
            grid[r + 1][c + 1] = 1 + (r * width + c) % 9
    original = deepcopy(grid)
    assert generator.rule_mirror(grid) == want
    assert grid == original


@pytest.mark.parametrize("bad", [
    [], [[]], [[0, 1], [2]], [[False, 1]], [[1.0, 2]],
    [[-1, 2]], [[10, 2]], [["1", 2]], [[0, 0], [0, 0]],
])
def test_malformed_and_empty_content_grids_are_rejected(generator, bad):
    # Catches weakened ARC validation and accidental empty-content acceptance.
    assert generator.self_check(bad)
    with pytest.raises(ValueError):
        generator.rule_mirror(bad)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("extent", EXTENTS)
@pytest.mark.parametrize("scene", SCENES)
def test_joint_overrides_are_visible_and_lawful(generator, band, extent, scene):
    # Catches inert overrides, malformed boxes, and color loss on small scenes.
    kwargs = {"difficulty": band, "scene_profile": scene, "extent_profile": extent}
    grid = generator.generate(29, 7, **kwargs)
    before = deepcopy(grid)
    assert grid == generator.generate(29, 7, **kwargs)
    top, left, height, width = content_box(grid)
    assert (top, left) == (int(scene[6]), int(scene[9]))
    if extent == "canonical":
        assert (height, width) == (6, 6)
        assert (len(grid), len(grid[0])) == (10, 10)
        assert generator.strict_canonical_like(grid) == []
    elif extent == "even":
        assert height in (4, 6, 8) and width in (4, 6, 8)
        assert (height, width) != (6, 6)
    else:
        assert height in (5, 7, 9) and width in (5, 7, 9)
    assert top >= 1 and left >= 1
    assert top + height < len(grid) and left + width < len(grid[0])
    assert generator.observe_overrides(grid) == {"scene_profile": scene, "extent_profile": extent}
    assert generator.self_check(grid, difficulty=band) == []
    assert generator.rule_mirror(grid) == floor_answer(grid)
    assert grid == before
    assert len({value for row in grid for value in row if value}) == {"easy": 3, "medium": 4, "hard": 5}[band]


def test_extent_population_reaches_rectangles_and_both_axis_sizes(generator):
    # Catches sampling only square extents despite a declared rectangular domain.
    for extent, sizes in (("even", {4, 6, 8}), ("odd", {5, 7, 9})):
        observed = {content_box(generator.generate(seed, 0, extent_profile=extent))[2:]
                    for seed in range(64)}
        assert {h for h, _ in observed} == sizes
        assert {w for _, w in observed} == sizes
        assert any(h != w for h, w in observed)


def test_canonical_fitting_dimension_rivals_are_actually_declared(generator, canonical):
    # Catches declaring only competitors already refuted by canonical examples.
    even = pair(generator, 0, 0, extent_profile="even")
    odd = pair(generator, 0, 0, extent_profile="odd")
    fitting = [fn for fn in generator.LESSON_COMPETITORS.values()
               if all(fn(p["input"]) == p["output"] for p in canonical)]
    assert any(fn(even["input"]) != even["output"] for fn in fitting)
    assert any(fn(even["input"]) == even["output"] and fn(odd["input"]) != odd["output"]
               for fn in fitting)


@pytest.mark.parametrize("band", BANDS)
def test_every_four_pair_window_remains_dimension_teaching_under_query_rotation(generator, band):
    # Catches schedule holes leaving fixed-size or ceil rivals unrefuted in demos.
    for seed in (0, 1, 17):
        population = [pair(generator, seed, index, difficulty=band) for index in range(11)]
        for start in range(8):
            window = population[start:start + 4]
            boxes = [content_box(p["input"])[2:] for p in window]
            assert sum(h % 2 and w % 2 for h, w in boxes) == 2
            assert sum((h, w) != (6, 6) for h, w in boxes) >= 2
            for query_index, query in enumerate(window):
                demos = [p for i, p in enumerate(window) if i != query_index]
                assert generator.lesson_identifiable(demos, query) == []
                for rival in generator.LESSON_COMPETITORS.values():
                    if all(rival(p["input"]) == p["output"] for p in demos):
                        assert rival(query["input"]) == query["output"]


def test_equivalent_rival_survival_does_not_reject_a_lesson(generator, canonical):
    # Catches treating answer-equivalent hypotheses as a query ambiguity.
    query = pair(generator, 11, 2, extent_profile="canonical")
    survivors = [fn for fn in generator.LESSON_COMPETITORS.values()
                 if all(fn(p["input"]) == p["output"] for p in canonical)]
    assert survivors
    assert all(fn(query["input"]) == query["output"] for fn in survivors)
    assert generator.lesson_identifiable(canonical, query) == []


def test_canonical_train_demos_expose_answer_trimming_query_ambiguity(generator, canonical):
    # Catches silently trimming a blank output border that both demos preserve.
    demos = [p for p in canonical if p["split"] == "train"]
    query = next(p for p in canonical if p["split"] == "test")
    trimming = generator.LESSON_COMPETITORS["trim_answer_background"]
    assert all(trimming(p["input"]) == p["output"] for p in demos)
    assert query["output"] == [[0, 0, 0], [0, 4, 4], [8, 8, 3]]
    assert trimming(query["input"]) == [[0, 4, 4], [8, 8, 3]]
    assert generator.lesson_identifiable(demos, query)


def test_canonical_demos_do_reject_a_dimension_ambiguous_query(generator, canonical):
    # Catches ignoring the surviving fixed-three rival on a noncanonical query.
    query = pair(generator, 3, 0, extent_profile="even")
    assert generator.lesson_identifiable(canonical[:2], query)


@pytest.mark.parametrize("band", BANDS)
def test_canonical_output_can_have_blank_top_row_and_blank_left_column(generator, band):
    # Catches per-quadrant edge forcing that excludes the canonical test endpoint.
    answers = [floor_answer(generator.generate(seed, 0, difficulty=band, extent_profile="canonical"))
               for seed in range(128)]
    assert any(not any(answer[0]) for answer in answers)
    assert any(not any(row[0] for row in answer) for answer in answers)


@pytest.mark.parametrize("overrides", [
    {"extent_profile": "invalid"}, {"extent_profile": False},
    {"scene_profile": "invalid"}, {"unknown_axis": 1},
])
def test_invalid_overrides_are_rejected_instead_of_silently_ignored(generator, overrides):
    with pytest.raises(ValueError):
        generator.generate(0, 0, **overrides)
