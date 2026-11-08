"""Observable contracts for local object transpose; run through review.py run.

Canonical answers use portable reviewer_support. Reference execution uses the
public Catalog.apply API, never a Python imitation as the source of labels.
"""
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = '7071285d78ce'
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location('transpose_generator_under_test', HOME / 'generator.py')
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def objects(grid):
    """Independent row-major four-neighbor same-color components."""
    seen = set()
    result = []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr,nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr,nc))
                        todo.append((nr,nc))
            result.append((color, cells))
    return result


def destinations(grid):
    result = []
    for color, cells in objects(grid):
        r1 = min(r for r,c in cells)
        c1 = min(c for r,c in cells)
        result.append((color, {(r1+c-c1,c1+r-r1) for r,c in cells}))
    return result


def foreground_counts(grid):
    return Counter(v for row in grid for v in row if v)


def assert_count(grid, count):
    assert len(objects(grid)) == count
    assert len(foreground_counts(grid)) == count
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize('axis', ['n_blobs','palette_size','n_distinct_colors'])
@pytest.mark.parametrize('count', [2,3,4])
def test_each_exact_count_axis(axis, count):
    assert_count(GEN.generate(0,0,**{axis:count}), count)


@pytest.mark.parametrize('axes', [
    {'n_blobs':2,'palette_size':2},
    {'palette_size':3,'n_distinct_colors':3},
    {'n_blobs':4,'palette_size':4,'n_distinct_colors':4},
])
def test_matching_count_aliases(axes):
    assert_count(GEN.generate(0,0,**axes), next(iter(axes.values())))


@pytest.mark.parametrize('axes', [
    {'n_blobs':2,'palette_size':3},
    {'n_blobs':3,'n_distinct_colors':2},
    {'palette_size':2,'n_distinct_colors':4},
])
def test_conflicting_count_aliases_reject(axes):
    with pytest.raises(ValueError) as exc:
        GEN.generate(0,0,**axes)
    assert set(exc.value.incompatible_axes) == set(axes)
    assert str(exc.value).strip()


@pytest.mark.parametrize('difficulty', [None,'easy','medium','hard'])
@pytest.mark.parametrize('shape', [(8,8),(14,14),(8,14),(14,8)])
def test_dimension_validity_is_independent_of_difficulty_defaults(difficulty, shape):
    h,w = shape
    grid=GEN.generate(0,0,difficulty=difficulty,grid_h=h,grid_w=w,n_blobs=4)
    assert (len(grid),len(grid[0])) == shape
    assert_count(grid,4)


@pytest.mark.parametrize('axis', ['grid_h','grid_w','n_blobs','palette_size','n_distinct_colors'])
@pytest.mark.parametrize('value', [True,2.0,'2'])
def test_exact_integer_controls_reject_coercion(axis,value):
    with pytest.raises((TypeError,ValueError)):
        GEN.generate(0,0,**{axis:value})


@pytest.mark.parametrize('axes', [
    {'grid_h':7},{'grid_w':15},{'n_blobs':1},{'n_blobs':5},
    {'palette_size':1},{'palette_size':9},{'n_distinct_colors':1},{'n_distinct_colors':9},
    {'not_an_axis':2},{'position_bias':'unsupported'},{'density':'dense'},
    {'palette_kind':'unsupported'},{'texture':'unsupported'},
])
def test_unsupported_controls_reject_explicitly(axes):
    with pytest.raises((TypeError,ValueError)):
        GEN.generate(0,0,**axes)


@pytest.mark.parametrize('axes', [
    {'palette_kind':'warm','texture':'cool'},
    {'palette_kind':'default','texture':'varied'},
])
def test_conflicting_palette_aliases_reject(axes):
    with pytest.raises(ValueError) as exc:
        GEN.generate(0,0,**axes)
    assert set(exc.value.incompatible_axes) == set(axes)
    assert str(exc.value).strip()


@pytest.mark.parametrize('kind', ['default','warm','cool','varied'])
def test_texture_is_exact_palette_alias(kind):
    assert GEN.generate(7,2,palette_kind=kind) == GEN.generate(7,2,texture=kind)


@pytest.mark.parametrize('grid', [[],[[]],[[0,0],[0]],[[0,10],[0,0]],[[False,0],[0,0]],[[0,'2'],[0,0]]])
def test_self_check_reports_malformed_grid_without_crashing(grid):
    messages=GEN.self_check(grid)
    assert isinstance(messages,list) and messages


@pytest.fixture(scope='module')
def retained_witnesses():
    report=json.loads((HOME/'counterexamples/current_review/finite-probe.json').read_text())
    return {k:v['input'] for k,v in report['first_witnesses'].items()}


def test_self_check_rejects_retained_destination_collision(retained_witnesses):
    grid=retained_witnesses['target_collisions']
    targets=destinations(grid)
    assert any(a & b for i,(_,a) in enumerate(targets) for _,b in targets[i+1:])
    assert GEN.self_check(grid), 'Accepted overlapping transpose destinations lose object cells'


def test_source_destination_overlap_alone_remains_lawful(retained_witnesses):
    # Seed26 is valid under the blank-output authority; source erasure order is
    # not a domain restriction. It contains no destination-destination collision.
    grid=retained_witnesses['target_source_intersections']
    targets=destinations(grid)
    assert all(not (a & b) for i,(_,a) in enumerate(targets) for _,b in targets[i+1:])
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize('seed',[0,26,31,72,128])
def test_generated_destinations_preserve_every_object(seed):
    grid=GEN.generate(seed,0)
    owner={}
    for color,cells in destinations(grid):
        for cell in cells:
            assert cell not in owner, f'seed {seed}: colors {owner.get(cell)} and {color} collide at {cell}'
            owner[cell]=color


def test_canonical_inputs_remain_in_domain():
    pairs=canonical_pairs(TASK,root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair['input']) == [], (pair['split'],pair['pair_index'])


def test_real_reference_preserves_generated_objects_and_canonical_labels(retained_witnesses):
    pairs=canonical_pairs(TASK,root=ROOT)
    generated=[GEN.generate(seed,0) for seed in (0,26,31)]
    lawful_overlap=retained_witnesses['target_source_intersections']
    grids=[p['input'] for p in pairs]+generated+[lawful_overlap]
    report=Catalog(ROOT).apply(TASK,grids,timeout=60)
    assert report['rule_hash_matches_catalog']
    rows=report['results']
    assert len(rows) == len(grids)
    for pair,row in zip(pairs,rows):
        assert row['error'] is None and row['valid_output']
        assert row['output'] == pair['output']
    for grid,row in zip(generated,rows[len(pairs):len(pairs)+len(generated)]):
        assert row['error'] is None and row['valid_output']
        assert foreground_counts(row['output']) == foreground_counts(grid)
        for color,cells in destinations(grid):
            assert all(row['output'][r][c] == color for r,c in cells)
    # Explicit erase-order witness: authority paints into a blank output grid.
    assert rows[-1]['output'][5][4] == 8
    assert foreground_counts(rows[-1]['output']) == foreground_counts(lawful_overlap)


def test_finite_defaults_cover_canonical_object_shapes():
    """Finite distribution regression, not proof of every seed's coverage."""
    def shape(cells):
        r1=min(r for r,c in cells)
        c1=min(c for r,c in cells)
        return tuple(sorted((r-r1,c-c1) for r,c in cells))
    canonical={shape(cells) for pair in canonical_pairs(TASK,root=ROOT)
               for _,cells in objects(pair['input'])}
    generated={shape(cells) for seed in range(256)
               for _,cells in objects(GEN.generate(seed,0))}
    assert canonical <= generated, f'canonical object shapes missing in 256 seeds: {canonical-generated}'


@pytest.mark.parametrize('bad_color',[10,-1,True,'2',2.0])
def test_self_check_rejects_invalid_color_inside_otherwise_lawful_input(bad_color):
    grid=[row[:] for row in canonical_pairs(TASK,root=ROOT)[0]['input']]
    color=next(v for row in grid for v in row if v)
    for row in grid:
        for c,value in enumerate(row):
            if value == color:
                row[c]=bad_color
    assert GEN.self_check(grid)


def test_self_check_rejects_touching_input_objects_with_disjoint_destinations():
    grid=[[0]*9 for _ in range(9)]
    for color,top in ((2,1),(3,4)):
        for dr,dc in ((0,0),(1,0),(1,1),(2,0)):
            grid[top+dr][1+dc]=color
    targets=destinations(grid)
    assert not (targets[0][1] & targets[1][1])
    assert GEN.self_check(grid)


@pytest.mark.parametrize('kind',['default','warm','cool','varied'])
@pytest.mark.parametrize('count',[2,3,4])
def test_palette_classes_are_observable(kind,count):
    warm={2,4,6,7,9}
    cool={1,3,5,8}
    grid=GEN.generate(0,0,palette_kind=kind,n_blobs=count)
    colors=set(foreground_counts(grid))
    assert_count(grid,count)
    if kind == 'default':
        assert colors == set(range(1,count+1))
    elif kind == 'warm':
        assert colors <= warm
    elif kind == 'cool':
        assert colors <= cool
    else:
        assert colors & warm and colors & cool
        assert colors != set(range(1,count+1))


@pytest.mark.parametrize('texture',['no_blobs','all_solid_squares','single_cell_blobs'])
def test_diagnostic_degenerate_fixtures_are_not_accepted_domain(texture):
    assert texture not in GEN.AXES[GEN.AXIS_ALIASES.get('texture', 'texture')]['valid'].split('|')
    assert GEN.self_check(GEN.generate(0,0,texture=texture))
