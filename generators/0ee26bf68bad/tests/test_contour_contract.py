"""Source-bound behavioral regressions for the largest-component contour task."""
from __future__ import annotations

from copy import deepcopy
from itertools import product

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0ee26bf68bad"
TEXTURES = ("rectangle", "joint")
BANDS = (None, "easy", "medium", "hard")
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


@pytest.fixture(scope="module")
def gen():
    module, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    return module


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _objects(grid, *, diagonal=False):
    """Independently enumerate monochromatic cardinal components in scan order."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    directions = DIRS4 + (((-1, -1), (-1, 1), (1, -1), (1, 1)) if diagonal else ())
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        cells, pending = {start}, [start]
        unseen.remove(start)
        while pending:
            row, col = pending.pop()
            for dr, dc in directions:
                point = row + dr, col + dc
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    pending.append(point)
        result.append((color, frozenset(cells)))
    return result


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _area(cells):
    top, left, bottom, right = _bbox(cells)
    return (bottom - top + 1) * (right - left + 1)


def _winner(grid, *, diagonal=False):
    objects = _objects(grid, diagonal=diagonal)
    return min(objects, key=lambda obj: (-len(obj[1]), *_bbox(obj[1])[:2]))


def _contour_oracle(grid, *, diagonal=False):
    color, cells = _winner(grid)
    top, left, bottom, right = _bbox(cells)
    directions = DIRS4 + (((-1, -1), (-1, 1), (1, -1), (1, 1)) if diagonal else ())
    return [
        [color if (r, c) in cells and any((r + dr, c + dc) not in cells
                                        for dr, dc in directions) else 0
         for c in range(left, right + 1)]
        for r in range(top, bottom + 1)
    ]


def _has_enclosed_hole(cells):
    top, left, bottom, right = _bbox(cells)
    absent = {(r, c) for r in range(top, bottom + 1)
              for c in range(left, right + 1) if (r, c) not in cells}
    outside = {p for p in absent if p[0] in (top, bottom) or p[1] in (left, right)}
    pending = list(outside)
    while pending:
        row, col = pending.pop()
        for dr, dc in DIRS4:
            point = row + dr, col + dc
            if point in absent and point not in outside:
                outside.add(point)
                pending.append(point)
    return bool(absent - outside)


def _assert_scene(grid):
    assert isinstance(grid, list) and grid and grid[0]
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    objects = _objects(grid)
    assert len(objects) == 3
    sizes = sorted((len(cells) for _, cells in objects), reverse=True)
    assert sizes[0] > sizes[1]
    return objects


def _assert_texture(grid, texture):
    objects = _assert_scene(grid)
    winner_color, winner = _winner(grid)
    distractors = [obj for obj in objects if obj != (winner_color, winner)]
    if texture == "rectangle":
        assert len(winner) == _area(winner)
        assert len({color for color, _ in objects}) == 3
    else:
        assert texture == "joint"
        assert len(winner) < _area(winner)
        assert _has_enclosed_hole(winner)
        assert _contour_oracle(grid) != _contour_oracle(grid, diagonal=True)
        assert distractors[0][0] == distractors[1][0] != winner_color
        assert sum(len(cells) for _, cells in distractors) > len(winner)
        assert any(_area(cells) > _area(winner) for _, cells in distractors)
        assert len(_objects(grid, diagonal=True)) == 2
        assert _winner(grid, diagonal=True)[0] != winner_color
        top, left, bottom, right = _bbox(winner)
        bbox_frame = [[winner_color if r in (top, bottom) or c in (left, right) else 0
                       for c in range(left, right + 1)]
                      for r in range(top, bottom + 1)]
        bbox_strip = [[winner_color if (r, c) in winner
                       and (r in (top, bottom) or c in (left, right)) else 0
                       for c in range(left, right + 1)]
                      for r in range(top, bottom + 1)]
        assert _contour_oracle(grid) != bbox_frame
        assert _contour_oracle(grid) != bbox_strip


def test_canonical_acceptance_and_independent_contour_labels(gen, canonical):
    assert len(canonical) == 4
    assert callable(getattr(gen, "rule_mirror", None)), "declare the selected-rule mirror"
    assert callable(getattr(gen, "strict_canonical_like", None))
    for pair in canonical:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _contour_oracle(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("grid", [
    [[2, 2, 0, 3, 3, 3, 0, 2, 2]],
    [[2, 2, 3, 3, 3, 4, 4, 0]],
])
def test_lawful_repeated_colors_touching_colors_and_distractor_ties(gen, grid):
    assert gen.self_check(grid) == []
    assert callable(getattr(gen, "rule_mirror", None))
    assert gen.rule_mirror(grid) == [[3, 3, 3]]


@pytest.mark.parametrize("grid", [
    None, [], [[]], "123", [0], [[0], [0, 0]],
    [[True, 0, 2, 2, 0, 3]], [[1.0, 0, 2, 2, 0, 3]],
    [["1", 0, 2, 2, 0, 3]], [[-1, 0, 2, 2, 0, 3]],
    [[10, 0, 2, 2, 0, 3]], [[0, 0, 0]],
    [[2, 2, 0, 3, 3, 0, 4]],  # Tied largest components.
    [[2, 0, 3, 3]],  # Two components.
    [[1, 0, 2, 2, 0, 3, 0, 4]],  # Four components.
])
def test_self_check_rejects_malformed_or_out_of_domain_inputs_without_raising(gen, grid):
    reasons = gen.self_check(grid)
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) for reason in reasons)


@pytest.mark.parametrize("options", [
    {"unknown_axis": 1}, {"grid_h": 6}, {"grid_h": 15},
    {"grid_w": 8}, {"grid_w": 15}, {"winner_color": 0}, {"winner_color": 10},
    {"texture": "unknown"}, {"texture": 1},
    *[{axis: value} for axis in ("grid_h", "grid_w", "winner_color")
      for value in (True, 6.0, "6", -1)],
])
def test_unknown_out_of_range_and_noninteger_overrides_reject(gen, options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(31, 5, **options)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("texture", TEXTURES)
def test_exact_controls_and_teaching_textures_at_every_crossband_boundary(gen, band, texture):
    assert callable(getattr(gen, "observe_overrides", None))
    assert callable(getattr(gen, "rule_mirror", None))
    for height, width, color in product((7, 14), (9, 14), (1, 9)):
        options = {"grid_h": height, "grid_w": width, "winner_color": color, "texture": texture}
        grid = gen.generate(731, 9, difficulty=band, **options)
        assert (len(grid), len(grid[0]), _winner(grid)[0]) == (height, width, color)
        assert gen.observe_overrides(grid) == options
        assert gen.self_check(grid) == []
        _assert_texture(grid, texture)
        assert gen.rule_mirror(grid) == _contour_oracle(grid)


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_alternates_two_realized_textures_and_is_deterministic(gen, band):
    assert callable(getattr(gen, "observe_overrides", None))
    seen = []
    for index in range(4):
        grid = gen.generate(2**40 + 73, index, difficulty=band)
        assert grid == gen.generate(2**40 + 73, index, difficulty=band)
        texture = gen.observe_overrides(grid)["texture"]
        seen.append(texture)
        _assert_texture(grid, texture)
    assert set(seen[:2]) == set(TEXTURES)
    assert seen[:2] == seen[2:]


def test_canonical_shortcuts_fit_source_and_have_generated_counterexamples(gen, canonical):
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", None)
    rivals = getattr(gen, "SEMANTIC_RIVALS", None)
    assert isinstance(shortcuts, dict) and shortcuts
    assert isinstance(rivals, dict) and rivals
    assert set(shortcuts) <= set(rivals)
    assert callable(getattr(gen, "lesson_identifiable", None))
    generated = [gen.generate(510, index) for index in range(4)]
    for name, rival in shortcuts.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical), name
        counterexamples = [grid for grid in generated if rival(grid) != _contour_oracle(grid)]
        assert counterexamples, name
        query = {"input": counterexamples[0], "output": _contour_oracle(counterexamples[0])}
        assert gen.lesson_identifiable(canonical, query), name


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_four_pair_period_windows_remain_identifiable_after_every_query_rotation(gen, band):
    assert getattr(gen, "EXAMPLES_NEEDED", None) == 3
    assert getattr(gen, "LESSON_SCHEDULE_PERIOD", None) == 2
    assert callable(getattr(gen, "lesson_identifiable", None))
    rivals = getattr(gen, "SEMANTIC_RIVALS", None)
    assert isinstance(rivals, dict) and rivals
    for start in range(2):
        pairs = []
        for index in range(start, start + 4):
            grid = gen.generate(812, index, difficulty=band)
            pairs.append({"input": grid, "output": _contour_oracle(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)
            for name, rival in rivals.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    assert rival(query["input"]) == query["output"], (name, start, query_index)


@pytest.mark.parametrize("convert", (bool, float))
def test_invalid_label_scalar_types_cannot_pass_by_python_numeric_equality(gen, convert):
    grid = gen.generate(21, 1, winner_color=1, texture="joint")
    output = [[convert(value) for value in row] for row in gen.rule_mirror(grid)]
    pair = {"input": grid, "output": output}
    assert gen.lesson_identifiable([pair], pair)


@pytest.mark.parametrize("seed", (True, False, 1.0, 1.75, "1"))
def test_seed_rejects_numerically_coercible_nonintegers(gen, seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


def test_signed_and_large_integer_seeds_remain_supported(gen):
    for seed in (-17, 0, 2**63 + 19):
        assert gen.self_check(gen.generate(seed, 0)) == []
