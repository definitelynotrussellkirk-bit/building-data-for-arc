"""Task-local regression tests, runnable directly from the extracted repo."""
from __future__ import annotations

import importlib.util
import itertools
import json
import random
import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location("palette_generator_under_test", HOME / "generator.py")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def components(grid):
    """Independent flood fill: do not validate the implementation with itself."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        stack, cells = [start], {start}
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        result.append({"color": color, "cells": cells,
                       "left": min(c for r, c in cells), "top": min(r for r, c in cells),
                       "right": max(c for r, c in cells)})
    return sorted(result, key=lambda obj: (obj["left"], obj["top"]))


def answer(grid):
    return [[obj["color"] for obj in components(grid)]]


def canonical_pairs():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row["task_id"] == "7b6758552009":
            return row["train"] + row["test"]
    raise AssertionError("missing canonical task")


def test_normal_distribution_contains_repeated_colors():
    grids = [gen.generate(928, i) for i in range(80)]
    assert any(len(components(g)) > len({v for row in g for v in row if v}) for g in grids)


def test_normal_distribution_is_not_fixed_to_left_edge_anchors():
    grids = [gen.generate(928, i) for i in range(80)]
    assert any(g[1][0] == 0 or g[-2][0] == 0 for g in grids)
    tied = [components(g) for g in grids if len({o['left'] for o in components(g)}) < len(components(g))]
    assert any(min(o['left'] for o in cs) > 0 for cs in tied)
    assert any(any(len(o['cells']) > 1 for o in cs if sum(p['left'] == o['left'] for p in cs) > 1) for cs in tied)


def test_two_component_canonical_branch_is_supported():
    grid = gen.generate(92, 0, difficulty="easy", components=2)
    assert len(components(grid)) == 2


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_documented_override_boundaries_have_observable_effects(difficulty):
    for h, w, count, color, layout in itertools.product(
        (6, 12), (10, 18), (2, 5), ("distinct", "repeated"), ("separated", "tied", "crossing")
    ):
        requested = dict(grid_h=h, grid_w=w, components=count, color_policy=color, layout=layout)
        grid = gen.generate(707, 11, difficulty=difficulty, **requested)
        assert len(grid) == h and all(len(row) == w for row in grid)
        cs = components(grid)
        assert len(cs) == count
        assert (len({o['color'] for o in cs}) == count) == (color == "distinct")
        assert gen.observe_overrides(grid) == requested
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == answer(grid)
        for a, b in itertools.combinations(cs, 2):
            assert all(max(abs(r - rr), abs(c - cc)) > 1 for r, c in a['cells'] for rr, cc in b['cells'])


@pytest.mark.parametrize("kw", [
    {"bogus_axis": 3}, {"palette_kind": "warm"}, {"grid_h": 5}, {"grid_h": 13},
    {"grid_w": 9}, {"grid_w": 19}, {"components": 1}, {"components": 6},
    {"grid_h": True}, {"grid_h": 6.5}, {"grid_w": "10"},
    {"layout": "diagonal"}, {"color_policy": "warm"},
])
def test_invalid_and_retired_overrides_fail_loudly(kw):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kw)


@pytest.mark.parametrize("bad", [
    [], [[]], [[0] * 10 for _ in range(6)], [[3] * 10 for _ in range(6)],
    [[0, 3, 3, 0]], [[0, 1], [0]], [[0, 1, 0, True]],
    [[0, 1, 0, 10]], [[0, 1, 0, -1]], [[0, 1, 0, 2.0]],
    [[0, 1, 2, 0]], [[0, 1, 0], [0, 0, 2]],
])
def test_selfcheck_rejects_invalid_scenes(bad):
    assert gen.self_check(bad)


def test_same_color_disconnected_components_are_not_rejected_or_deduplicated():
    grid = [[0] * 10 for _ in range(6)]
    grid[1][1] = grid[1][7] = 4
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == [[4, 4]]


def test_all_canonical_inputs_remain_lawful_and_match_independent_oracle():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair['input']) == []
        assert gen.strict_canonical_like(pair['input']) == []
        assert gen.rule_mirror(pair['input']) == answer(pair['input']) == pair['output']


def test_declared_shortcuts_really_fit_every_canonical_pair():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in canonical_pairs()), name


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_four_draw_lesson_counters_all_declared_rivals(difficulty):
    for seed in range(16):
        for start in (0, 1, 7):
            grids = [gen.generate(seed, i, difficulty=difficulty) for i in range(start, start + 5)]
            demos = [{'input': g, 'output': answer(g)} for g in grids[:4]]
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert any(rival(d['input']) != d['output'] for d in demos), (seed, start, name)
            assert gen.lesson_identifiable(demos, {'input': grids[4]}) == []
            assert {gen.schedule_profile(seed, i, difficulty) for i in range(start, start + 4)} == set(gen.SCHEDULE_PROFILES)


def test_replay_global_rng_purity_and_fresh_return():
    random.seed(101)
    before = random.getstate()
    a, b = gen.generate(83, 7), gen.generate(83, 7)
    assert a == b and a is not b
    assert all(x is not y for x, y in zip(a, b))
    assert random.getstate() == before
    a[0][0] = (a[0][0] + 1) % 10
    assert a != b


def test_default_census_has_no_duplicate_input_contradictions():
    seen = {}
    for index in range(600):
        grid = gen.generate(2053, index)
        assert gen.self_check(grid) == []
        key = tuple(map(tuple, grid))
        assert seen.setdefault(key, answer(grid)) == gen.rule_mirror(grid)
    assert len(seen) > 590


def test_lesson_hook_exposes_surviving_shortcut_without_query_label():
    pair = canonical_pairs()[0]
    query = gen.generate(0, 1)  # repeated-color scheduled profile
    reasons = gen.lesson_identifiable([pair], {'input': query})
    assert any('unique_colors' in reason for reason in reasons)
    assert gen.lesson_identifiable([{'input': pair['input'], 'output': [[9]]}], {'input': query})


def test_common_seed_equals_index_probe_does_not_alias_away_profiles():
    assert {gen.schedule_profile(i, i) for i in range(1, 41)} == set(gen.SCHEDULE_PROFILES)


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
def test_canonical_profile_retains_demonstrated_scale_without_replaying_grids(difficulty):
    scales = {(6, 11, 2), (7, 10, 3), (8, 12, 3), (9, 13, 4)}
    distinct_grids = set()
    for seed in range(24):
        index = next(i for i in range(4) if gen.schedule_profile(seed, i) == 'canonical')
        grid = gen.generate(seed, index, difficulty=difficulty)
        assert (len(grid), len(grid[0]), len(components(grid))) in scales
        assert len({o['color'] for o in components(grid)}) == len(components(grid))
        distinct_grids.add(tuple(map(tuple, grid)))
    assert len(distinct_grids) == 24


def test_probe_has_an_offline_help_command_and_rejects_zero_samples():
    import subprocess
    script = HOME / 'workspace/probe_palette.py'
    help_run = subprocess.run([sys.executable, str(script), '--help'], capture_output=True, text=True)
    assert help_run.returncode == 0
    bad = subprocess.run([sys.executable, str(script), '--samples', '0', '--out', 'unused'], capture_output=True, text=True)
    assert bad.returncode != 0 and 'positive' in bad.stderr


def test_canonical_scale_does_not_replay_identical_scenes_across_bands():
    scenes = [gen.generate(seed, index, difficulty=band)
              for seed in range(32) for index in (0,)
              for band in ('easy', 'medium', 'hard')]
    assert len({tuple(map(tuple, grid)) for grid in scenes}) >= 94
