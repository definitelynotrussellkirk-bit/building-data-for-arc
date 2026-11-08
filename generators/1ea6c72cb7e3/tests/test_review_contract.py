"""Task-local regression tests; the original root test is left frozen."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('reviewed_visibility_generator', HOME / 'generator.py')
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


def ray_reference(grid):
    """Independent per-watcher ray accumulation, for tests only (not labels)."""
    seen = [[set() for _ in row] for row in grid]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 5):
                continue
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                y, x = r + dr, c + dc
                while 0 <= y < h and 0 <= x < w and grid[y][x] != 5:
                    if grid[y][x] == 0:
                        seen[y][x].add(color)
                    y, x = y + dr, x + dc
    return [[v if v else (0 if not seen[r][c] else next(iter(seen[r][c]))
                         if len(seen[r][c]) == 1 else 8)
             for c, v in enumerate(row)] for r, row in enumerate(grid)]


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_canonical_profile_floor_in_each_band(band):
    profiles = {(9, 9, 5), (10, 10, 5), (11, 11, 5), (10, 11, 5)}
    hits = 0
    for i in range(20):
        seed = int(hashlib.sha256(f'profile-floor:v1:{G.TASK_ID}:{band}:{i}'.encode()).hexdigest()[:12], 16)
        grid = G.generate(seed, seed % 7919 + i, difficulty=band)
        hits += (len(grid), len(grid[0]), len({v for row in grid for v in row})) in profiles
    assert hits >= 1, f'{band}: {hits}/20 canonical profile hits'


def test_declares_executable_semantic_contract():
    for name in ('strict_canonical_like', 'SEMANTIC_WITNESSES', 'SEMANTIC_RIVALS',
                 'WITNESS_RIVALS', 'CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS',
                 'lesson_identifiable', 'schedule_profile', 'SCHEDULE_PROFILES'):
        assert hasattr(G, name), f'missing semantic hook {name}'


@pytest.mark.parametrize('bad', [None, [], [[]], [[0], [0, 0]], [[[]]], [[{}]], [[None]], [[True]], [['2']], [[-1]], [[10]]])
def test_invalid_values_return_findings_without_crashing(bad):
    assert G.self_check(bad)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_all_cyclic_starts_refute_declared_rivals(band):
    assert hasattr(G, 'LESSON_COMPETITORS'), 'missing lesson competitors'
    for seed in (0, 1, 17, 41):
        grids = [G.generate(seed, i, difficulty=band) for i in range(5)]
        for start in range(3):
            demos = [{'input': g, 'output': ray_reference(g)} for g in grids[start:start+3]]
            assert not G.lesson_identifiable(demos, {'input': grids[-1]})
            for name, rival in {**G.CANONICAL_SHORTCUTS, **G.LESSON_COMPETITORS}.items():
                assert any(rival(p['input']) != p['output'] for p in demos), (seed, start, name)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_exact_override_boundaries_and_contrast_schedule(band):
    for h in (9, 13):
        for w in (9, 14):
            for count in (3, 4):
                for profile in G.SCENE_PROFILES:
                    axes = dict(grid_h=h, grid_w=w, n_watchers=count, scene_profile=profile)
                    for start in range(3):
                        grid = G.generate(771, start, difficulty=band, **axes)
                        assert (len(grid), len(grid[0])) == (h, w)
                        assert not G.self_check(grid, meta={'overrides': axes})
                        assert G.observe_overrides(grid) == {'n_watchers': count, 'scene_profile': profile}
                        if hasattr(G, 'schedule_profile') and G.schedule_profile(771, start, band) == 'contrast':
                            gold = ray_reference(grid)
                            for name, rival in G.LESSON_COMPETITORS.items():
                                assert rival(grid) != gold, (axes, name)


def test_canonical_shortcuts_fit_every_canonical_pair():
    assert hasattr(G, 'CANONICAL_SHORTCUTS'), 'missing canonical shortcuts'
    records = [json.loads(line) for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').open()
               if f'"{G.TASK_ID}"' in line]
    total = 0
    for record in records:
        for split in ('train', 'test'):
            for pair in record[split]:
                total += 1
                assert not G.self_check(pair['input'])
                assert ray_reference(pair['input']) == pair['output']
                for name, rival in G.CANONICAL_SHORTCUTS.items():
                    assert rival(pair['input']) == pair['output'], name
    assert total == 4


def test_determinism_purity_and_fresh_rows():
    state = random.getstate()
    for i in range(6):
        a = G.generate(101, i, difficulty='medium')
        b = G.generate(101, i, difficulty='medium')
        assert a == b and a is not b and all(x is not y for x, y in zip(a, b))
        if hasattr(G, 'LESSON_COMPETITORS'):
            original = copy.deepcopy(a)
            for rival in G.LESSON_COMPETITORS.values():
                rival(a)
                assert a == original
    assert random.getstate() == state


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_default_draw_provenance_matches_returned_axes(monkeypatch, band):
    actual_gen_ctx = G.gen_ctx
    contexts = []
    def capture_context(**kwargs):
        ctx = actual_gen_ctx(**kwargs)
        contexts.append(ctx)
        return ctx
    monkeypatch.setattr(G, 'gen_ctx', capture_context)
    for index in range(3):
        grid = G.generate(0, index, difficulty=band)
        recorded = contexts[-1].drawn_store
        assert recorded['grid_h'] == len(grid)
        assert recorded['grid_w'] == len(grid[0])
        assert recorded['n_watchers'] == G.observe_overrides(grid)['n_watchers']
