"""Native sampler contracts: lawful inputs, deliberate lessons, and seed isolation."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import find_root

HOME = find_root(__file__) / "generators" / "b88894a36787"
SAMPLER = HOME / "workspace" / "parametric" / "sampler.py"


def _sampler():
    assert SAMPLER.exists(), "native sampler.py has not been built"
    spec = importlib.util.spec_from_file_location("native_sampler_under_test", SAMPLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _geometry(grid):
    """Parse the public input independently of the sampler's constructors."""
    h, w = len(grid), len(grid[0])
    assert 8 <= h <= 30 and 8 <= w <= 30
    assert all(type(row) is list and len(row) == w for row in grid)
    assert all(type(x) is int and 0 <= x <= 9 for row in grid for x in row)
    headers = [(c, x) for c, x in enumerate(grid[0]) if x]
    assert 2 <= len(headers) <= min(8, w - 2)
    assert [c for c, _ in headers] == list(range(headers[0][0], headers[-1][0] + 1))
    assert headers[0][0] > 0 and headers[-1][0] < w - 1
    colors = [x for _, x in headers]
    assert len(set(colors)) == len(colors)
    dots = [(r, c, x) for r in range(1, h) for c, x in enumerate(grid[r]) if x]
    assert all(c in (0, w - 1) for _, c, _ in dots)
    entries = []
    for c, color in headers:
        targets = [(r, side) for r, side, x in dots if x == color]
        assert len(targets) <= 1
        entries.append((c, color, targets[0] if targets else None))
    missing = sum(dot is None for _, _, dot in entries)
    assert 0 <= missing <= min(2, len(headers) - 1)
    noise = [(r, c, x) for r, c, x in dots if x not in colors]
    assert len(noise) <= 2
    return entries, noise


def _matched(grid):
    """Occupancy oracle from route coordinates, with canonical left priority."""
    entries, _ = _geometry(grid)
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for col, color, dot in reversed(entries):
        out[0][col] = color
        if dot is not None:
            row, side = dot
            for r in range(row + 1):
                out[r][col] = color
            for c in range(min(col, side), max(col, side) + 1):
                out[row][c] = color
    return out


def _hits(grid):
    rendered = _matched(grid)
    return {c: next((r for r in range(1, len(grid)) if rendered[r][c]), None)
            for c, _, dot in _geometry(grid)[0] if dot is None}


def _fingerprint(grid):
    return json.dumps(grid, separators=(",", ":"))


def _normalized_demos(demos):
    # Both witness layouts share one reflection coin, then are relabelled by
    # canonical header order. Geometry is normalized only for checking roles.
    d1, d2 = demos[:2]
    es, _ = _geometry(d1)
    reflected = es[0][2] is not None and es[0][2][0] != 1
    return ([list(reversed(row)) for row in d1],
            [list(reversed(row)) for row in d2]) if reflected else (d1, d2)


def test_default_lesson_teaches_two_one_and_zero_omissions_with_rendered_hits():
    sampler = _sampler()
    for seed in range(24):
        demos, queries = sampler.sample_inputs(seed)
        assert (len(demos), len(queries)) == (3, 4)
        d1, d2 = _normalized_demos(demos)
        e1, noise1 = _geometry(d1)
        h1, w1 = len(d1), len(d1[0])
        assert h1 >= 11 and w1 >= 13 and len(e1) == 6
        assert [e[2] for e in e1] == [(1, 0), None, (h1 - 2, 0), (h1 - 4, 0), None, (h1 - 2, w1 - 1)]
        assert 1 <= len(noise1) <= 2
        assert _hits(d1) == {e1[1][0]: h1 - 4, e1[4][0]: None}
        # A later hit must exist; first_hit cannot simply use the earliest dot.
        assert _matched(d1)[h1 - 2][e1[1][0]] != 0
        assert _matched(d1)[h1 - 4][e1[2][0]] == e1[2][1]
        e2, noise2 = _geometry(d2)
        h2, w2 = len(d2), len(d2[0])
        assert h2 >= 9 and w2 >= 11 and len(e2) == 4
        assert [e[2] for e in e2] == [(h2 - 1, w2 - 1), (3, 0), (1, w2 - 1), None]
        assert len(noise2) == 1
        assert _hits(d2) == {e2[3][0]: 1}
        e3, noise3 = _geometry(demos[2])
        assert 11 <= len(demos[2]) <= 15 and 11 <= len(demos[2][0]) <= 15
        assert len(e3) == 4 and not noise3
        assert [e[2][0] for e in e3] == [2, 5, 5, 2]
        assert [e[2][1] for e in e3] == [0, 0, len(demos[2][0]) - 1, len(demos[2][0]) - 1]


def test_default_demonstrations_stop_missing_columns_in_both_canvas_halves():
    sampler = _sampler()
    for seed in (0, 17, 19, 2**63 - 1, *range(32)):
        demos, _ = sampler.sample_inputs(seed)
        sides = []
        for grid in demos[:2]:
            actual_hits = [(col, row) for col, row in _hits(grid).items() if row is not None]
            assert len(actual_hits) == 1
            col, _ = actual_hits[0]
            # Strict center separation also survives the common reflection.
            assert 2 * col != len(grid[0]) - 1
            sides.append(2 * col < len(grid[0]) - 1)
        assert set(sides) == {False, True}


def test_first_demonstration_has_a_lower_half_hit_and_a_later_blocker():
    sampler = _sampler()
    for seed in (0, 17, 19, 2**63 - 1, *range(32)):
        demos, _ = sampler.sample_inputs(seed)
        grid = demos[0]
        hits = [(col, row) for col, row in _hits(grid).items() if row is not None]
        assert len(hits) == 1
        col, row = hits[0]
        assert 2 * row >= len(grid)
        assert row == len(grid) - 4
        assert _matched(grid)[len(grid) - 2][col] != 0


@pytest.mark.parametrize("seed,query_sha256", [
    (0, "95dff783ca7e03ee952604e0d41ec5233a6f50e2e1b26b1df8ba6f3905bc4a4f"),
    (17, "dec02357afed86623486189fded33b8ad646527d740393f392a668171f445fd4"),
    (19, "cb3518d202d6d22e62e54d75efea167e1117fd5b1ea58e6266f69fede4c89c6c"),
    (2**63 - 1, "5d781492b5fef0343eeebf5e133b8e196ffcc67b14eb0509ca9bb7f64c3a7cdf"),
])
def test_teaching_repair_preserves_original_four_query_inputs(seed, query_sha256):
    sampler = _sampler()
    # Digests are from the retained pre-repair source snapshot, covering all
    # four ordered query inputs byte-for-byte in compact JSON serialization.
    _, queries = sampler.sample_inputs(seed)
    assert hashlib.sha256(_fingerprint(queries).encode()).hexdigest() == query_sha256


def test_query_bank_contains_real_minimum_complete_large_and_full_scale_content():
    sampler = _sampler()
    for seed in range(24):
        demos, queries = sampler.sample_inputs(seed, demos=6)
        by_shape = {(len(g), len(g[0])): g for g in queries}
        assert set(by_shape) == {(8, 8), (17, 21), (24, 26), (30, 30)}
        small = by_shape[(8, 8)]
        assert len(_geometry(small)[0]) == 3
        assert len(_hits(small)) == 1 and None not in _hits(small).values()
        complete = _geometry(by_shape[(17, 21)])[0]
        assert len(complete) == 5 and all(e[2] is not None for e in complete)
        large = _geometry(by_shape[(24, 26)])[0]
        assert len(large) == 7 and 1 <= sum(e[2] is None for e in large) <= 2
        full = by_shape[(30, 30)]
        entries, _ = _geometry(full)
        assert len(entries) == 8 and sum(e[2] is None for e in entries) == 2
        endpoints = [e[2] for e in entries if e[2] is not None]
        assert all(r >= 17 for r, _ in endpoints) and any(r == 29 for r, _ in endpoints)
        assert {c for _, c in endpoints} == {0, 29}
        rendered = _matched(full)
        assert sum(bool(x) for row in rendered for x in row) >= 150
        assert any(rendered[29]) and any(row[0] for row in rendered) and any(row[-1] for row in rendered)
        assert len({_fingerprint(g) for g in demos + queries}) == 10


def test_all_count_prefixes_retain_independent_query_bank_and_fresh_grids():
    sampler = _sampler()
    for seed in (0, 1, 37, 2**63 - 1):
        full_demos, full_queries = sampler.sample_inputs(seed, demos=6, queries=4)
        for demo_count in range(3, 7):
            for query_count in range(1, 5):
                demos, queries = sampler.sample_inputs(seed, demos=demo_count, queries=query_count)
                assert demos == full_demos[:demo_count]
                assert queries == full_queries[:query_count]
                assert demos is not full_demos and queries is not full_queries
                assert demos[0] is not full_demos[0] and demos[0][0] is not full_demos[0][0]
        demos, queries = sampler.sample_inputs(seed)
        demos[0][0][0] = 9
        queries[0][0][0] = 9
        assert sampler.sample_inputs(seed, demos=6) == (full_demos, full_queries)


def test_rng_is_local_reproducible_and_has_palette_offset_and_order_variety():
    sampler = _sampler()
    before = random.getstate()
    banks = [sampler.sample_inputs(seed, demos=6) for seed in range(32)]
    assert random.getstate() == before
    palettes, starts, shapes = set(), set(), set()
    for demos, queries in banks:
        for grid in demos + queries:
            _geometry(grid)
        palettes.add(tuple(x for x in demos[0][0] if x))
        starts.add(next(c for c, x in enumerate(demos[0][0]) if x))
        shapes.add(tuple((len(g), len(g[0])) for g in queries))
    assert len(palettes) >= 16 and len(starts) >= 3 and len(shapes) >= 8
    assert all(banks[i] == sampler.sample_inputs(i, demos=6) for i in range(32))


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, [], {}])
def test_seed_requires_exact_integer(bad):
    sampler = _sampler()
    with pytest.raises(TypeError):
        sampler.sample_inputs(bad)


@pytest.mark.parametrize("bad", [-1, 2**63])
def test_seed_range_is_bounded(bad):
    sampler = _sampler()
    with pytest.raises(ValueError):
        sampler.sample_inputs(bad)


@pytest.mark.parametrize("control,bad", [(key, value) for key in ("demos", "queries") for value in (True, 3.0, "3", None)])
def test_counts_require_exact_integers(control, bad):
    sampler = _sampler()
    with pytest.raises(TypeError):
        sampler.sample_inputs(0, **{control: bad})


@pytest.mark.parametrize("control,bad", [("demos", 2), ("demos", 7), ("queries", 0), ("queries", 5)])
def test_count_ranges_are_bounded(control, bad):
    sampler = _sampler()
    with pytest.raises(ValueError):
        sampler.sample_inputs(0, **{control: bad})


def test_inputs_have_no_setting_or_unknown_control():
    sampler = _sampler()
    for kwargs in ({"settings": {"missing_extension": "bottom"}}, {"mode": "first_hit"}, {"other": 2}):
        with pytest.raises(TypeError):
            sampler.sample_inputs(0, **kwargs)
