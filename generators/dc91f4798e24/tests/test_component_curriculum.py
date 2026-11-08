"""Task-local regression contract; executable in source and staged layouts."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/runtime').is_dir() or (p / 'arc_repl').is_dir())
if (ROOT / 'shared/runtime').exists():
    sys.path.insert(0, str(ROOT / 'shared/runtime'))
else:
    sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('component_generator', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def component_sizes(grid, color, diagonal=False):
    """Independent set flood fill (not the generator's implementation)."""
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    sizes = []
    moves = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    while pending:
        pending.remove(start := min(pending))
        queue = [start]
        size = 0
        while queue:
            r, c = queue.pop()
            size += 1
            for dr, dc in moves:
                q = (r + dr, c + dc)
                if q in pending:
                    pending.remove(q)
                    queue.append(q)
        sizes.append(size)
    return sizes


def canonical_pairs():
    path = ROOT / ('shared/data/canonical/puzzles.jsonl' if (ROOT / 'shared').exists()
                   else 'data/canonical/puzzles.jsonl')
    task = next(json.loads(x) for x in path.read_text().splitlines()
                if json.loads(x).get('task_id') == gen.TASK_ID)
    return task['train'] + task['test']


def test_accepts_all_five_canonical_inputs():
    failures = [gen.self_check(p['input']) for p in canonical_pairs()]
    assert failures == [[]] * 5


@pytest.mark.parametrize('difficulty', [None, 'easy', 'medium', 'hard'])
def test_curriculum_teaches_components_not_pixels(difficulty):
    for seed in range(30):
        grid = gen.generate(seed, seed % 7, difficulty=difficulty)
        assert not gen.self_check(grid)
        assert any(max(component_sizes(grid, color), default=0) > 1 for color in (1, 2, 3))
        assert grid == gen.generate(seed, seed % 7, difficulty=difficulty)


@pytest.mark.parametrize('difficulty', [None, 'easy', 'medium', 'hard'])
def test_default_supports_noise_diagonal_contacts_and_boundaries(difficulty):
    corpus = [gen.generate(seed, 0, difficulty=difficulty) for seed in range(100)]
    assert any(any(v >= 4 for row in g for v in row) for g in corpus)
    assert any(any(len(component_sizes(g, c)) != len(component_sizes(g, c, True))
                   for c in (1, 2, 3)) for g in corpus)
    assert any(any(v in (1, 2, 3) for v in g[0]) for g in corpus)
    assert any(any(v in (1, 2, 3) for v in g[-1]) for g in corpus)
    assert any(any(row[0] in (1, 2, 3) for row in g) for g in corpus)
    assert any(any(row[-1] in (1, 2, 3) for row in g) for g in corpus)


@pytest.mark.parametrize('difficulty', [None, 'easy', 'medium', 'hard'])
@pytest.mark.parametrize('shape', [(7, 8), (7, 22), (18, 8), (18, 22)])
def test_dimension_overrides_work_in_every_band(difficulty, shape):
    h, w = shape
    grid = gen.generate(7, 3, difficulty=difficulty, grid_h=h, grid_w=w)
    assert (len(grid), len(grid[0])) == shape
    assert not gen.self_check(grid)


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match='[Uu]nknown'):
        gen.generate(0, 0, definitely_a_typo=3)


@pytest.mark.parametrize('bad', [[], [[]], [[0, 1], [2]], [[-1]], [[10]], [['x']], [[True]]])
def test_invalid_grid_returns_errors_not_exception(bad):
    assert gen.self_check(bad)


def test_diagonal_profile_is_an_explicit_four_versus_eight_witness():
    for seed in range(30):
        g = gen.generate(seed, 0, texture='diagonal')
        assert not gen.self_check(g)
        assert any(len(component_sizes(g, c)) != len(component_sizes(g, c, True)) for c in (1, 2, 3))


@pytest.mark.parametrize('mode', ['equal_counts', 'missing_color', 'no_components'])
def test_degenerates_stay_explicit_and_honor_dimensions(mode):
    g = gen.generate(8, 1, texture=mode, grid_h=7, grid_w=8)
    assert (len(g), len(g[0])) == (7, 8)
    assert gen.self_check(g)


def test_semantic_rivals_fit_canonical_and_witnesses_refute_them():
    assert 'eight_connected' in getattr(gen, 'CANONICAL_SHORTCUTS', {})
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(p['input']) == p['output'] for p in canonical_pairs())
    fired = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for seed in range(60):
        g = gen.generate(seed, 0)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            if witness(g):
                fired[name] += 1
                assert any(gen.SEMANTIC_RIVALS[rival](g) != gen._histogram(g)
                           for rival in gen.WITNESS_RIVALS[name])
    assert all(fired.values())


@pytest.mark.parametrize('difficulty', [None, 'easy', 'medium', 'hard'])
def test_canonical_scale_and_distractors_remain_supported_in_every_band(difficulty):
    signatures = {(len(p['input']), len(p['input'][0]), len({v for row in p['input'] for v in row}))
                  for p in canonical_pairs()}
    hits = 0
    for seed in range(100):
        g = gen.generate(seed, seed % 16, difficulty=difficulty)
        hits += (len(g), len(g[0]), len({v for row in g for v in row})) in signatures
    assert hits >= 20, (difficulty, hits)


def test_independent_probe_has_known_four_vs_eight_and_binary_results():
    probe_spec = importlib.util.spec_from_file_location('component_probe', HOME / 'workspace/review_probe.py')
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    g = [[1, 2, 1], [0, 1, 0], [3, 0, 0]]
    assert probe.histogram(g) == [[1, 1, 1], [2, 0, 0], [3, 0, 0]]
    assert probe.histogram(g, 8) == [[1], [2], [3]]
    assert probe.binary_rival(g) == [[1], [2], [3]]
