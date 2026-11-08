"""Task-local regressions. Run explicitly; the root test config may omit these."""
from pathlib import Path
import copy
import importlib.util
import sys

import pytest

# Locate the task's own runtime without assuming a fixed parent depth.
try:
    from reviewer_support import canonical_path, find_root
except ModuleNotFoundError:
    here = Path(__file__).resolve()
    helper = next(
        (candidate / 'shared/runtime' for candidate in (here.parent, *here.parents)
         if (candidate / 'shared/runtime/reviewer_support.py').is_file()),
        None,
    )
    if helper is None:
        raise
    sys.path.insert(0, str(helper))
    from reviewer_support import canonical_path, find_root

REPO = find_root(__file__)
SOURCE = REPO / 'generators/ffcd7510821d/generator.py'
SPEC = importlib.util.spec_from_file_location('marker_generator', SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def crop(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value and not (r == 0 and value == 9)]
    a, b = min(r for r, c in points), max(r for r, c in points)
    x, y = min(c for r, c in points), max(c for r, c in points)
    return [row[x:y+1] for row in grid[a:b+1]]


def rotations(grid):
    out = []
    for _ in range(4):
        out.append(tuple(map(tuple, grid)))
        grid = [list(row) for row in zip(*grid[::-1])]
    return out


def content_colors(grid):
    return set(v for row in grid for v in row) - {0, 9}


def test_plus_shape_is_not_a_rotation_witness():
    grid = [[0] * 10 for _ in range(8)]
    grid[0][:3] = [9, 9, 9]
    for r, c in [(3, 4), (4, 3), (4, 4), (4, 5), (5, 4)]:
        grid[r][c] = 3
    assert gen.self_check(grid), 'nonrectangular plus has only one distinguishable rotation'


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
def test_default_rotation_witnesses(difficulty):
    for index in range(200):
        grid = gen.generate(0, index, difficulty=difficulty)
        assert not gen.self_check(grid), (index, gen.self_check(grid))
        assert len(set(rotations(crop(grid)))) == 4, index


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
def test_every_four_consecutive_examples_teach_all_turns(difficulty):
    for seed in range(4):
        for start in range(5):
            grids = [gen.generate(seed, start+i, difficulty=difficulty) for i in range(4)]
            assert {g[0].count(9) % 4 for g in grids} == {0, 1, 2, 3}
            assert any(len(content_colors(g)) == 1 for g in grids)
            assert any(len(content_colors(g)) > 1 for g in grids)


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('n_markers', range(5))
def test_explicit_marker_counts(difficulty, n_markers):
    grid = gen.generate(17, 4, difficulty=difficulty, n_markers=n_markers)
    assert grid[0].count(9) == n_markers
    assert not gen.self_check(grid)


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('n_blobs', range(1, 5))
def test_exact_blobs_at_smallest_dimensions(difficulty, n_blobs):
    grid = gen.generate(17, 4, difficulty=difficulty, grid_h=7, grid_w=8, n_blobs=n_blobs)
    assert (len(grid), len(grid[0])) == (7, 8)
    assert len(content_colors(grid)) == n_blobs
    assert not gen.self_check(grid)


@pytest.mark.parametrize('override', [
    {'n_markres': 3}, {'texture': 'nonsense'}, {'density': 'dense'},
    {'palette_size': 1}, {'palette_kind': 'nonsense'}, {'n_markers': 9},
    {'n_blobs': 0}, {'grid_h': True}, {'grid_w': 8.5},
])
def test_bad_or_removed_overrides_are_rejected(override):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize('palette,allowed', [('warm', {2,4,6,7}), ('cool', {1,3,5,8}), ('varied', set(range(1,9)))])
def test_palette_override_changes_actual_colors(palette, allowed):
    grid = gen.generate(7, 3, n_blobs=4, palette_kind=palette)
    assert content_colors(grid) <= allowed


def test_selfcheck_does_not_trust_texture_metadata():
    assert gen.self_check([[]], meta={'texture':'no_markers'})
    bad = [[0] * 10 for _ in range(8)]
    assert gen.self_check(bad, meta={'texture':'four_markers'})


def test_hash_pin_matches_unchanged_authority():
    import hashlib, json
    rows = canonical_path(REPO).read_text().splitlines()
    record = next(json.loads(line) for line in rows if json.loads(line).get('task_id') == gen.TASK_ID)
    expected = hashlib.sha256(' '.join(record['program_solution'].split()).encode()).hexdigest()[:12]
    assert getattr(gen, 'RULE_HASH', None) == expected
    for pair in record['train'] + record['test']:
        assert not gen.self_check(pair['input'])


def test_deterministic_and_no_input_mutation():
    for index in range(20):
        one = gen.generate(71, index)
        assert one == gen.generate(71, index)
        saved = copy.deepcopy(one)
        gen.self_check(one)
        assert one == saved


def test_lesson_hook_rejects_an_unseen_marker_class():
    assert callable(getattr(gen, 'lesson_identifiable', None))
    demo = gen.generate(8, 0, n_markers=1, n_blobs=1)
    query = gen.generate(8, 1, n_markers=2, n_blobs=1)
    answer = lambda g: [list(row) for row in rotations(crop(g))[g[0].count(9) % 4]]
    assert gen.lesson_identifiable([{'input': demo, 'output': answer(demo)}], {'input': query})


def test_complete_lesson_is_identifiable_and_wrong_labels_are_not():
    assert callable(getattr(gen, 'lesson_identifiable', None))
    answer = lambda g: [list(row) for row in rotations(crop(g))[g[0].count(9) % 4]]
    for seed in range(6):
        grids = [gen.generate(seed, index) for index in range(5)]
        demos = [{'input': g, 'output': answer(g)} for g in grids[:4]]
        query = {'input': grids[4]}
        assert not gen.lesson_identifiable(demos, query)
        bad = copy.deepcopy(demos)
        bad[0]['output'] = [[0]]
        assert gen.lesson_identifiable(bad, query)


def test_semantic_hooks_and_mutations_are_executable():
    assert getattr(gen, 'SEMANTIC_RIVALS', None)
    assert getattr(gen, 'SEMANTIC_WITNESSES', None)
    assert callable(getattr(gen, 'mutation_fixtures', None))
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name
    fired = set()
    for index in range(12):
        grid = gen.generate(10, index)
        expected = [list(row) for row in rotations(crop(grid))[grid[0].count(9) % 4]]
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                fired.add(name)
                assert any(gen.SEMANTIC_RIVALS[rival](grid) != expected
                           for rival in gen.WITNESS_RIVALS[name]), name
    assert fired == set(gen.SEMANTIC_WITNESSES)


def test_diagonal_seed_census_does_not_hide_rotation_classes():
    assert {gen.generate(i, i)[0].count(9) % 4 for i in range(16)} == {0, 1, 2, 3}
