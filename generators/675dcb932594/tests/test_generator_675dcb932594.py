"""Focused authoring regressions for the shortest-path union curriculum.

The independent predecessor-frontier oracle is only a test assertion: no
reference labels or generated examples are written to training data.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest

# Bootstrap the public helper from this file's own library or copied runtime.
for ancestor in Path(__file__).resolve().parents:
    support = next((p for p in (ancestor / 'reviewer_support.py',
                               ancestor / 'shared/runtime/reviewer_support.py')
                    if p.is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support.parent))
        break
else:
    raise ImportError('No local reviewer_support.py')

from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
TASK_ID = '675dcb932594'
GENERATOR_PATH = next(p for p in (
    ROOT / 'generators' / TASK_ID / 'generator.py',
    ROOT / 'puzzle_generators/per_puzzle' / TASK_ID / 'generator.py',
) if p.is_file())
SPEC = spec_from_file_location('_regression_675dcb932594', GENERATOR_PATH)
GEN = module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, 'easy', 'medium', 'hard')
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))
RICH = [[int(c) for c in row] for row in
        ('555555', '500005', '502505', '505505', '500035', '555555')]
RICH_OUTPUT = [[int(c) for c in row] for row in
               ('555555', '508885', '582585', '585585', '588835', '555555')]


def shortest_frontier(grid):
    """Collect all equal-distance predecessors, then backtrack their union."""
    start, goal = (next((r, c) for r, row in enumerate(grid)
                        for c, value in enumerate(row) if value == marker)
                   for marker in (2, 3))
    distances, parents = {start: 0}, {start: []}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIRECTIONS:
            cell = r + dr, c + dc
            if not (0 <= cell[0] < len(grid) and 0 <= cell[1] < len(grid[0])):
                continue
            if grid[cell[0]][cell[1]] == 5:
                continue
            distance = distances[r, c] + 1
            if cell not in distances:
                distances[cell] = distance
                parents[cell] = [(r, c)]
                queue.append(cell)
            elif distances[cell] == distance:
                parents[cell].append((r, c))
    output = deepcopy(grid)
    union = set()
    pending = [goal] if goal in distances else []
    while pending:
        cell = pending.pop()
        if cell not in union:
            union.add(cell)
            pending.extend(parents[cell])
            r, c = cell
            if grid[r][c] == 0:
                output[r][c] = 8
    # Count all shortest routes and their vertical-move counts on the DAG.
    paths, vertical_counts = {start: 1}, {start: {0}}
    for cell in sorted(distances, key=distances.get):
        if cell == start:
            continue
        paths[cell] = sum(paths[p] for p in parents[cell])
        vertical_counts[cell] = {
            n + (cell[0] != parent[0])
            for parent in parents[cell] for n in vertical_counts[parent]
        }
    return output, distances.get(goal), paths.get(goal, 0), vertical_counts.get(goal, set())


def declared_rivals():
    rivals = {}
    for attribute in ('LESSON_COMPETITORS', 'CANONICAL_SHORTCUTS'):
        declaration = getattr(GEN, attribute, None)
        assert isinstance(declaration, dict) and declaration, attribute
        assert all(isinstance(name, str) and callable(fn)
                   for name, fn in declaration.items()), attribute
        rivals.update({f'{attribute}:{name}': fn
                       for name, fn in declaration.items()})
    return rivals


def test_metadata_and_exact_axes():
    assert GEN.VERSION == '2.0.0'
    assert GEN.RULE_HASH == '1e4fa5a56660'
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.AXES) == {'grid_h', 'grid_w'}
    assert GEN.LESSON_SCHEDULE_PERIOD == 2
    assert set(GEN.SCHEDULE_PROFILES) == {'tradeoff', 'maze'}


@pytest.mark.parametrize('band', BANDS)
@pytest.mark.parametrize('shape', [(5, 5), (5, 24), (24, 5), (24, 24),
                                   (6, 6), (7, 11), (11, 7), (12, 19), (19, 12)])
@pytest.mark.parametrize('index', [0, 1])
def test_dimension_overrides_are_exact_across_all_bands(band, shape, index):
    h, w = shape
    grid = GEN.generate(4097, index, difficulty=band, grid_h=h, grid_w=w)
    assert (len(grid), {len(row) for row in grid}) == (h, {w})
    assert GEN.self_check(grid, difficulty=band) == []
    assert shortest_frontier(grid)[1] >= 2


@pytest.mark.parametrize('axis', ['grid_h', 'grid_w'])
@pytest.mark.parametrize('value', [True, False, 8.0, 8.25, '8', 4, 25])
@pytest.mark.parametrize('band', BANDS)
def test_bad_dimension_controls_reject(axis, value, band):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(173, 0, difficulty=band, **{axis: value})


@pytest.mark.parametrize('overrides', [
    {'palette_kind': 'warm'}, {'anchor_corner': True},
    {'asymmetry_force': True}, {'palette_size': 3},
    {'position_bias': 'random'}, {'n_distinct_colors': 3},
    {'texture': 'warm'}, {'texture': 'no_corridor'},
    {'texture': 'no_endpoints'}, {'texture': 'full_grid'}, {'typo': 7},
])
def test_removed_or_unknown_controls_reject(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(173, 0, **overrides)


def modified_rich(row, col, value):
    grid = deepcopy(RICH)
    grid[row][col] = value
    return grid


BAD_GRIDS = [
    ('empty', []), ('none', None), ('scalar', 7), ('scalar_row', [5, 5]),
    ('empty_row', [[]]), ('ragged', [[5, 5], [5]]),
    ('illegal_8', modified_rich(1, 1, 8)),
    ('illegal_negative', modified_rich(1, 1, -1)),
    ('float_color', modified_rich(1, 1, 0.0)),
    ('bool_color', modified_rich(1, 1, False)),
    ('string_color', modified_rich(1, 1, '0')),
    ('repeated_start', modified_rich(1, 1, 2)),
    ('repeated_goal', modified_rich(1, 1, 3)),
    ('missing_start', modified_rich(2, 2, 0)),
    ('missing_goal', modified_rich(4, 4, 0)),
    ('missing_walls', [[0 if v == 5 else v for v in row] for row in RICH]),
    ('missing_zeros', [[5 if v == 0 else v for v in row] for row in RICH]),
    ('wall_frame_gap', modified_rich(0, 2, 0)),
    ('disconnected', [[int(c) for c in row] for row in
                       ('55555', '52055', '55555', '55035', '55555')]),
    ('adjacent', [[int(c) for c in row] for row in
                   ('55555', '52305', '55555', '55555', '55555')]),
]


@pytest.mark.parametrize('case,grid', BAD_GRIDS, ids=[name for name, _ in BAD_GRIDS])
def test_self_check_reports_invalid_inputs_without_crashing(case, grid):
    original = deepcopy(grid)
    reasons = GEN.self_check(grid)
    assert isinstance(reasons, list) and reasons, case
    assert all(isinstance(reason, str) and reason for reason in reasons)
    assert grid == original
    # Old texture metadata must never disable the validator.
    assert GEN.self_check(grid, meta={'texture': 'no_corridor'}), case


def test_lawful_disconnected_zero_distractor_and_canonical_inputs():
    grid = [[int(c) for c in row] for row in
            ('5555555', '5200355', '5555555', '5555505', '5555555')]
    assert GEN.self_check(grid) == []
    for pair in PAIRS:
        original = deepcopy(pair['input'])
        assert GEN.self_check(pair['input']) == [], pair
        assert pair['input'] == original


def test_independent_mirror_agrees_with_all_canonical_labels_and_rich_witness():
    assert PAIRS
    for pair in PAIRS:
        assert shortest_frontier(pair['input'])[0] == pair['output'], pair
    assert shortest_frontier(RICH) == (RICH_OUTPUT, 6, 2, {2, 4})
    assert GEN.self_check(RICH) == []


def test_every_declared_canonical_shortcut_reproduces_every_usable_pair():
    shortcuts = getattr(GEN, 'CANONICAL_SHORTCUTS', None)
    assert isinstance(shortcuts, dict) and len(shortcuts) >= 4
    for name, rival in shortcuts.items():
        assert callable(rival), name
        for pair in PAIRS:
            original = deepcopy(pair['input'])
            assert rival(deepcopy(original)) == pair['output'], (name, pair)


@pytest.mark.parametrize('band', BANDS)
def test_default_even_draws_are_rich_tradeoffs_and_dimensions_vary(band):
    rivals = declared_rivals()
    shapes, starts = set(), set()
    for index in range(0, 16, 2):
        grid = GEN.generate(81029, index, difficulty=band)
        assert GEN.schedule_profile(81029, index, difficulty=band) == 'tradeoff'
        assert min(len(grid), len(grid[0])) >= 6
        assert GEN.self_check(grid, difficulty=band) == []
        output, distance, paths, vertical_counts = shortest_frontier(grid)
        assert paths == 2 and len(vertical_counts) == 2, (band, index)
        assert distance > 0 and sum(v == 0 for row in output for v in row) >= 1
        shapes.add((len(grid), len(grid[0])))
        starts.add(next((r, c) for r, row in enumerate(grid)
                        for c, value in enumerate(row) if value == 2))
        for name, rival in rivals.items():
            assert rival(deepcopy(grid)) != output, (band, index, name)
    assert len(shapes) >= 2
    assert len(starts) >= 2
    for index in (1, 3, 5):
        assert GEN.schedule_profile(81029, index, difficulty=band) == 'maze'
        assert GEN.self_check(GEN.generate(81029, index, difficulty=band)) == []


@pytest.mark.parametrize('band', BANDS)
@pytest.mark.parametrize('start', [0, 1, 4, 5])
def test_four_demo_lessons_refute_actual_declarations_after_every_query_rotation(band, start):
    rivals = declared_rivals()
    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(30073, start + offset, difficulty=band)
        pairs.append({'input': grid, 'output': shortest_frontier(grid)[0]})
    for held_out in range(len(pairs)):
        demos = [pair for index, pair in enumerate(pairs) if index != held_out]
        assert len(demos) == 4
        for name, rival in rivals.items():
            assert any(rival(deepcopy(pair['input'])) != pair['output']
                       for pair in demos), (band, start, held_out, name)


def test_generation_is_deterministic_under_reordered_calls_and_external_mutation():
    requests = [(17893, i, band) for band in BANDS for i in (0, 1, 6)]
    expected = {(seed, index, band): GEN.generate(seed, index, difficulty=band)
                for seed, index, band in requests}
    for seed, index, band in reversed(requests):
        actual = GEN.generate(seed, index, difficulty=band)
        assert actual == expected[seed, index, band]
        actual[0][0] = 9
        GEN.generate(97831, 37, difficulty='hard')
        assert GEN.generate(seed, index, difficulty=band) == expected[seed, index, band]


@pytest.mark.parametrize('band', BANDS)
def test_three_cell_component_does_not_choose_an_adjacent_only_start(band):
    # Seed 93 selected the middle of a three-cell component, leaving no legal
    # nonadjacent goal. A constructive sampler must choose a viable endpoint.
    grid = GEN.generate(93, 1, difficulty=band, grid_h=5, grid_w=5)
    assert GEN.self_check(grid) == []
    assert shortest_frontier(grid)[1] >= 2
