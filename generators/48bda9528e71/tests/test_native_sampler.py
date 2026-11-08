"""Geometry, color roles and reproducibility of native extent-projection inputs."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
HOME = ROOT / 'generators/48bda9528e71/workspace/parametric'
_spec = importlib.util.spec_from_file_location('_native_projection_sampler_tests', HOME / 'sampler.py')
sampler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sampler)
selected, _, _ = load_selected_generator('48bda9528e71', root=ROOT)


def facts(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color != 8}
    counts = Counter(grid[r][c] for r, c in cells)
    rare_color = min(counts, key=counts.get)
    rare = {p for p in cells if grid[p[0]][p[1]] == rare_color}
    return cells, counts, rare_color, rare


def bbox(cells):
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def rays(cells, n):
    result = set()
    for r in {r for r, _ in cells}:
        cs = [c for rr, c in cells if rr == r]
        result.update((r, c) for c in range(n) if c < min(cs) or c > max(cs))
    for c in {c for _, c in cells}:
        rs = [r for r, cc in cells if cc == c]
        result.update((r, c) for r in range(n) if r < min(rs) or r > max(rs))
    return result


@pytest.mark.parametrize('seed', [0, 1, 17, 2**63 - 1])
def test_every_constructive_role_obeys_shape_color_and_marker_grammar(seed):
    train, test = sampler.sample_inputs(seed, 6, 4)
    assert (len(train), len(test)) == (6, 4)
    for grid in train + test:
        n = len(grid)
        assert type(grid) is list and 5 <= n <= 30
        assert all(type(row) is list and len(row) == n for row in grid)
        assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
        cells, counts, rare_color, rare = facts(grid)
        assert 7 <= len(cells) <= (n * n - 1) // 2
        assert selected._is_connected(cells)
        assert selected._is_orthogonally_convex(cells)
        r0, c0, r1, c1 = bbox(cells)
        assert r1 - r0 >= 2 and c1 - c0 >= 2
        assert len(counts) in (2, 3)
        assert all(counts[rare_color] < count for color, count in counts.items() if color != rare_color)
        assert rare <= selected._interior_cells(cells)
        markers = selected._extent_positions(cells, n, n)
        assert len(markers) >= 4
        assert markers < rays(cells, n)
        assert not (markers & cells)


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_minimum_lesson_exposes_color_frequency_concavity_and_edge_clipping(seed):
    train, _ = sampler.sample_inputs(seed)
    info = [facts(grid) for grid in train]
    assert [len(counts) for _, counts, _, _ in info] == [3, 2, 3]
    assert info[0][2] != 0 and 0 in info[0][1]
    assert info[1][2] == 9 and set(info[1][1]) == {0, 9}
    assert len(info[1][0]) == 16 and info[1][3] == selected._interior_cells(info[1][0])
    assert _color_features(train[1])[0] == {'components': 1, 'interior': 0, 'enclosed': False}
    assert info[2][2] == 0
    assert _color_features(train[2])[9]['enclosed']
    assert len(info[2][3]) == 1 and max(info[2][1], key=info[2][1].get) == 9
    assert len({len(rare) for _, _, _, rare in info}) >= 2
    assert len({len(cells) for cells, _, _, _ in info}) == 3
    assert all(selected._lattice_convex_hull(cells) != cells for cells, _, _, _ in info)
    first_cells, first_counts, rare_color, rare = info[0]
    n = len(train[0])
    r0, c0, r1, c1 = bbox(first_cells)
    assert 0 < r0 <= r1 < n - 1 and 0 < c0 <= c1 < n - 1
    assert train[0][(r0 + r1) // 2][(c0 + c1) // 2] != rare_color
    rare_box = bbox(rare)
    rare_area = (rare_box[2] - rare_box[0] + 1) * (rare_box[3] - rare_box[1] + 1)
    common_boxes = []
    for color in first_counts:
        if color != rare_color:
            positions = {p for p in first_cells if train[0][p[0]][p[1]] == color}
            rb, cb, re, ce = bbox(positions)
            common_boxes.append((re - rb + 1) * (ce - cb + 1))
    assert min(common_boxes) < rare_area
    assert any({p for p in first_cells if train[0][p[0]][p[1]] == color}
               <= selected._interior_cells(first_cells)
               for color in first_counts if color != rare_color)
    second_cells = info[1][0]
    n = len(train[1])
    assert any(r in (0, n - 1) or c in (0, n - 1) for r, c in second_cells)
    # Opposite edges of an internal cross have distinct row and column extents.
    row_extents = {(min(c for rr, c in first_cells if rr == r), max(c for rr, c in first_cells if rr == r))
                   for r in {r for r, _ in first_cells}}
    col_extents = {(min(r for r, cc in first_cells if cc == c), max(r for r, cc in first_cells if cc == c))
                   for c in {c for _, c in first_cells}}
    assert len(row_extents) >= 2 and len(col_extents) >= 2


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_query_boundaries_use_substantial_distinct_shapes(seed):
    _, test = sampler.sample_inputs(seed)
    assert [len(grid) for grid in test] == [5, 16, 24, 30]
    assert len(facts(test[0])[0]) == 12
    assert len(facts(test[2])[0]) >= 180
    largest = facts(test[3])[0]
    assert len(largest) in (275, 371)
    assert bbox(largest) == (0, 0, 29, 29)
    assert len({len(facts(grid)[0]) for grid in test}) == 4


def test_fresh_deterministic_prefixes_leave_global_rng_untouched():
    state = random.getstate()
    full = sampler.sample_inputs(1119, 6, 4)
    assert random.getstate() == state
    assert sampler.sample_inputs(1119, 6, 4) == full
    for demos in (3, 4, 5, 6):
        for queries in (1, 2, 3, 4):
            assert sampler.sample_inputs(1119, demos, queries) == (full[0][:demos], full[1][:queries])
    changed = sampler.sample_inputs(1119)
    changed[0][0][0][0] = 99
    assert sampler.sample_inputs(1119)[0][0][0][0] != 99
    assert sampler.sample_inputs(1120) != sampler.sample_inputs(1119)


def _color_features(grid):
    cells, counts, _, _ = facts(grid)
    interior = selected._interior_cells(cells)
    result = {}
    for color in counts:
        group = {p for p in cells if grid[p[0]][p[1]] == color}
        todo, components = set(group), 0
        while todo:
            components += 1
            frontier = [todo.pop()]
            while frontier:
                r, c = frontier.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = r + dr, c + dc
                    if p in todo:
                        todo.remove(p)
                        frontier.append(p)
        result[color] = {'components': components, 'interior': len(group & interior),
                         'enclosed': group <= interior}
    return result


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
@pytest.mark.parametrize('rival', ['fewest_interior_cells', 'most_components_numeric_tie',
                                  'highest_fully_enclosed', 'lowest_fully_enclosed'])
def test_demonstrations_refute_reviewed_color_shortcuts(seed, rival):
    """Wrong color changes both projection modes because every role has markers."""
    train, _ = sampler.sample_inputs(seed)
    refuted = False
    for grid in train:
        _, _, rare_color, _ = facts(grid)
        data = _color_features(grid)
        keys = {'fewest_interior_cells': lambda c: (data[c]['interior'], c),
                'most_components_numeric_tie': lambda c: (-data[c]['components'], c),
                'highest_fully_enclosed': lambda c: (not data[c]['enclosed'], -c),
                'lowest_fully_enclosed': lambda c: (not data[c]['enclosed'], c)}
        refuted |= min(data, key=keys[rival]) != rare_color
    assert refuted, rival


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
@pytest.mark.parametrize('mode', ['one_step', 'to_boundary'])
def test_demonstrations_require_geometry_from_all_foreground_colors(seed, mode):
    """Regress the protected dominant-color-only projection counterexample."""
    train, _ = sampler.sample_inputs(seed)
    refuted = False
    for grid in train:
        cells, counts, _, _ = facts(grid)
        dominant = max(counts, key=counts.get)
        reduced = {p for p in cells if grid[p[0]][p[1]] == dominant}
        project = (lambda ps: selected._extent_positions(ps, len(grid), len(grid))) if mode == 'one_step' else (lambda ps: rays(ps, len(grid)))
        refuted |= project(cells) != project(reduced)
    assert refuted


_REPAIR_BASELINE = {
    0: {
        'queries': ['83a1296d74e1b1e0c88d2647d89638ffc8bd11ff34a95fc2640b2155dd4f5382',
                    '1d163e249367f5eb8f9389e80ff85418808de0b63a2ca008ce377098eb3b9ab9',
                    'a5f9d3a708c8e18cf307a1c906dbf63740adc9b22d09a866b8105c6ffc7b23bf',
                    '450b9649a0e505881a3512bdac9dbd1d3eb57b5645ddd0c7e7edee0df6961533'],
        'demo0': '26a45da7e1f123babd68a10c572b826948b82ff276b8e422ef8ee25d2640a3b3',
        'demo2_occupied': 'd9f498788cd7f84c194c35f27ffee613caa319f1f51556c397303ec124bb2ac7',
        'demo2_rare_positions': '7c43e73a164e84b1361816bb4486c4b84528058d9eb109a47436582165fc0f6f',
    },
    17: {
        'queries': ['2b5136333c8130482d441f9c110da9bb08bb720be2dd25e53703c791c74f4cd5',
                    '13412dc0460361888c97616f913823bf75654b8389440e272d28e239a9f02f55',
                    '086f25ff392987c8ec2cd0d14458639657d788fb1d2ce18d47054f4035ebfd06',
                    'eb8b2a11b29b3ff1876cef54b588c72381908c89154486ce82cdd0baeb9f096a'],
        'demo0': '00a8fbce06d7bb9acb5b4dfee96b02d7af5d653249368acf63af38dd9648da8c',
        'demo2_occupied': '198a8c3b21ddcf70923d208f84ac5876806002f7b4ba591517cba9674184f29a',
        'demo2_rare_positions': '917459ba56bc2fbd6881ede6b6c5653fe171f225724b2efbeebd68f161ba0517',
    },
    2**63 - 1: {
        'queries': ['e6ec7fe3e69e99b9014f3c628f155699acf5bb565531ab7709ca242cbb354c6d',
                    '805725cc0587427cd7aa6ac150fbfdc0deb194573a14f13c3584da622f1f8e08',
                    'fa6a9aacc50ba842360f9e54e51f04c32231cc4c4b6851dd2988c0998d8cac12',
                    '0f1345e7ddfd21696cd8763d37825dacde674e37038bb302164c1496c94a9372'],
        'demo0': 'de70b568cdcaf74e4adcf7e0588e08ffd6617fc7d37f9e0d8919690592275536',
        'demo2_occupied': '0d816cd117ba66fc0ca97463204a5fdcb55fc001e5983afb2e22d1cc0e0b8638',
        'demo2_rare_positions': '2cdcd781ef622badf7f9a3e0ba8430baaa5f119836d73e8ce7f627593a6db6ca',
    },
}

_GEOMETRY_REPAIR_BASELINE = {
    0: {'demo1': '6307622573b63967ccf51b284bd121254494a5f1acb0f5aea0b31306c5a9095f',
        'previous_rare': [(11, 4), (14, 8), (15, 5), (15, 7), (15, 12)]},
    17: {'demo1': 'c1ec55a626c29eb39a7f485d0722fc0932d58088d7ade3f55fd0a36d42d907e3',
         'previous_rare': [(2, 2), (2, 8), (4, 2), (4, 5), (6, 4)]},
    2**63 - 1: {'demo1': 'fb9da3786ee1157d8c2559667133473067473220c43c2860b389e7ef492ecb60',
               'previous_rare': [(7, 15), (12, 9), (13, 8), (15, 7), (15, 10)]},
}


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_repairs_preserve_queries_and_documented_demonstration_geometry(seed):
    train, queries = sampler.sample_inputs(seed)
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    baseline = _REPAIR_BASELINE[seed]
    assert [digest(grid) for grid in queries] == baseline['queries']
    assert digest(train[0]) == baseline['demo0']
    geometry_baseline = _GEOMETRY_REPAIR_BASELINE[seed]
    assert digest(train[1]) == geometry_baseline['demo1']
    cells, _, _, rare = facts(train[2])
    assert digest(sorted(cells)) == baseline['demo2_occupied']
    previous = set(geometry_baseline['previous_rare'])
    assert digest(sorted(previous)) == baseline['demo2_rare_positions']
    assert len(rare) == 1 and rare <= previous


@pytest.mark.parametrize('seed', [True, False, -1, 2**63, 1.0, '1', None])
def test_invalid_seed(seed):
    with pytest.raises(ValueError):
        sampler.sample_inputs(seed)


@pytest.mark.parametrize('demos', [True, False, 2, 7, 3.0, '3', None])
def test_invalid_demo_count(demos):
    with pytest.raises(ValueError):
        sampler.sample_inputs(0, demos, 4)


@pytest.mark.parametrize('queries', [True, False, 0, 5, 1.0, '1', None])
def test_invalid_query_count(queries):
    with pytest.raises(ValueError):
        sampler.sample_inputs(0, 3, queries)
