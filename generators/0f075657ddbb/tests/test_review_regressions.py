"""Task-local, grid-observed regressions; no generated output is trusted as a label."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
sys.path.insert(0, str(ROOT / 'src'))
spec = importlib.util.spec_from_file_location('review_nested_frames', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def canonical():
    for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').open():
        row = json.loads(line)
        if row['task_id'] == '0f075657ddbb':
            return row
    raise AssertionError('canonical task missing')


def boxes(grid):
    """Independent exact-perimeter component extractor, deliberately not gen helpers."""
    todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4}
    result = []
    while todo:
        start = min(todo)
        todo.remove(start)
        cells, fringe = {start}, [start]
        while fringe:
            r, c = fringe.pop()
            for point in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if point in todo:
                    todo.remove(point); cells.add(point); fringe.append(point)
        r0, c0 = min(r for r,c in cells), min(c for r,c in cells)
        r1, c1 = max(r for r,c in cells), max(c for r,c in cells)
        perimeter = {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
                     if r in (r0,r1) or c in (c0,c1)}
        if r1 > r0 and c1 > c0 and cells == perimeter:
            result.append((r0,c0,r1,c1))
    return sorted(result, key=lambda b: (-(b[2]-b[0]+1)*(b[3]-b[1]+1),b[0],b[1]))


@pytest.mark.parametrize('pair', canonical()['train'] + canonical()['test'])
def test_self_check_accepts_every_canonical_input(pair):
    assert gen.self_check(pair['input']) == []


@pytest.mark.parametrize('difficulty', [None,'easy','medium','hard'])
def test_explicit_axes_override_difficulty_and_are_exact(difficulty):
    g = gen.generate(17, 0, difficulty=difficulty, grid_h=29, grid_w=30,
                     n_frames=4, band_gap=3, k_select=0, palette_size=5,
                     position_bias='offset')
    bs = boxes(g)
    assert (len(g),len(g[0])) == (29,30)
    assert len(bs) == 4
    assert sum(v == 2 for v in g[0]) == 0
    assert len({v for row in g for v in row} - {0}) == 5
    gaps = [(b[0]-a[0],b[1]-a[1],a[2]-b[2],a[3]-b[3]) for a,b in zip(bs,bs[1:])]
    assert min(min(x) for x in gaps) == 3
    assert any(len(set(x)) > 1 for x in gaps)
    assert gen.self_check(g) == []


@pytest.mark.parametrize('k', [0,1,2,3,6])
def test_selector_is_never_clamped(k):
    g = gen.generate(2,0,n_frames=2,k_select=k)
    assert sum(v == 2 for v in g[0]) == k
    assert gen.self_check(g) == []


@pytest.mark.parametrize('key,value', [('grid_h',10),('grid_w',31),('n_frames',-1),
    ('n_frames',6),('k_select',-1),('k_select',7),('band_gap',1),
    ('palette_size',1),('grid_h',True),('n_frames',2.5),('grid_w','20'),
    ('position_bias','diagonal'),('texture','invalid'),('typo',2)])
def test_invalid_overrides_fail_loud(key,value):
    with pytest.raises((TypeError,ValueError)):
        gen.generate(0,0,**{key:value})


def test_infeasible_combination_fails_instead_of_falling_back():
    with pytest.raises(ValueError):
        gen.generate(0,0,grid_h=11,grid_w=11,n_frames=5,band_gap=3)


@pytest.mark.parametrize('texture', ['no_frames','no_markers','single_frame'])
def test_documented_lawful_edge_cases(texture):
    g = gen.generate(0,0,texture=texture)
    assert gen.self_check(g) == []
    if texture == 'no_frames': assert boxes(g) == []
    elif texture == 'no_markers': assert 2 not in g[0]
    else: assert len(boxes(g)) == 1


def test_broken_rectangle_is_rejected():
    g = copy.deepcopy(canonical()['train'][0]['input'])
    g[2][6] = 0
    assert gen.self_check(g), 'two yellow components are insufficient: one frame is broken'


@pytest.mark.parametrize('g', [[],[[]],[[0],[0,1]],[[True,0]],[[0,10]],[[0,-1]],[[0,1.5]],None])
def test_malformed_grids_return_reasons_not_exceptions(g):
    assert gen.self_check(g)


def test_live_default_curriculum_varies_and_includes_canonical_noop():
    grids = [gen.generate(seed,i,difficulty=band)
             for band in ('easy','medium','hard') for seed in range(12) for i in range(4)]
    assert all(gen.self_check(g) == [] for g in grids)
    assert any(2 not in g[0] for g in grids)
    assert any(sum(v == 2 for v in g[0]) > 0 for g in grids)
    assert len({json.dumps(g) for g in grids}) > len(grids)*0.95
    assert getattr(gen,'ALLOW_IDENTITY_OUTPUT',False)


def test_seed_and_index_determinism():
    for i in range(16):
        assert gen.generate(17,i) == gen.generate(17,i)
    assert len({json.dumps(gen.generate(17,i)) for i in range(16)}) == 16


@pytest.mark.parametrize('pair', canonical()['train'] + canonical()['test'])
def test_rule_mirror_matches_canonical_pairs(pair):
    assert callable(getattr(gen,'rule_mirror',None))
    before = copy.deepcopy(pair['input'])
    assert gen.rule_mirror(pair['input']) == pair['output']
    assert pair['input'] == before


def test_probe_can_start_from_a_shallow_relocated_directory():
    import shutil
    import subprocess
    import tempfile
    # Real staged workers live directly below /tmp; pytest's tmp_path has
    # extra parents and would conceal an unconditional parents[3] lookup.
    with tempfile.TemporaryDirectory(dir='/tmp',prefix='probe-test-') as directory:
        target = Path(directory) / 'review_probe.py'
        shutil.copyfile(HOME / 'workspace/review_probe.py', target)
        process = subprocess.run([sys.executable,str(target),'--help'],capture_output=True,text=True,timeout=10)
        assert process.returncode == 0, process.stderr


def test_diagonal_callers_cover_every_schedule_profile():
    # A phase=(seed+index)%4 implementation fails when caller uses (i,i).
    observed = {gen.schedule_profile(i,i) for i in range(128)}
    assert observed == set(gen.SCHEDULE_PROFILES)


def test_active_examples_dominate_without_removing_both_noop_branches():
    n = 240
    grids = [gen.generate(10000+i,0,difficulty='medium') for i in range(n)]
    changed = sum(gen.rule_mirror(g) != g for g in grids)
    assert 0.65*n <= changed <= 0.85*n
    assert any(sum(v==2 for v in g[0]) == 0 for g in grids)
    assert any(sum(v==2 for v in g[0]) > len(boxes(g)) for g in grids)


def test_default_scale_mixture_retains_compact_and_large_layouts():
    # New seeds, not the fixed 60-example battery census. This tests a broad
    # mixture, not memorized canonical arrays or a precise sampled frequency.
    grids = [gen.generate(10000+i,0,difficulty='hard') for i in range(240)]
    compact = [g for g in grids if 11<=len(g)<=14 and 12<=len(g[0])<=16
               and 3<=len({v for row in g for v in row})<=4]
    assert len(compact) >= len(grids)*0.40
    assert any(len(g)>20 or len(g[0])>20 for g in grids)
    assert any(len(boxes(g)) >= 4 for g in grids)


@pytest.mark.parametrize('kind',['uniform','singleton','solid_2x2','line'])
def test_no_frame_branch_does_not_admit_one_color_impostors(kind):
    g = [[0]*13 for _ in range(13)]
    if kind=='uniform': g = [[2]*13 for _ in range(13)]
    elif kind=='singleton': g[6][6] = 2
    elif kind=='solid_2x2':
        for r in range(2):
            for c in range(2): g[r][c] = 2
    else:
        for c in range(4): g[6][c] = 2
    assert gen.self_check(g)


@pytest.mark.parametrize('overrides',[
    {'n_frames':5,'grid_h':11},
    {'texture':'no_frames','n_frames':2},
    {'texture':'no_markers','k_select':1},
    {'n_frames':1,'band_gap':2},
])
def test_rejected_combinations_carry_conflicting_axis_names(overrides):
    with pytest.raises(ValueError) as caught:
        gen.generate(0,0,**overrides)
    axes = set(getattr(caught.value,'incompatible_axes',()))
    assert 2 <= len(axes)
    assert axes <= set(overrides)


def test_selected_authority_matches_canonical_exactly():
    source = ROOT/'shared/data/base/solutions/banks/f6c2fd26c5e5/H72__0f075657ddbb.json'
    target = json.loads(source.read_text())['racket_target']
    assert target['target_code'] == canonical()['program_solution']


@pytest.mark.parametrize('index',range(8))
def test_explicit_zero_frames_works_through_every_schedule_profile(index):
    g = gen.generate(17,index,n_frames=0)
    assert boxes(g) == []
    assert gen.self_check(g) == []
    assert gen.rule_mirror(g) == g


def _probe_module():
    spec = importlib.util.spec_from_file_location('review_probe_for_tests',HOME/'workspace/review_probe.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    return probe


def test_probe_normalizes_single_pair_and_digit_rows_without_mutating():
    probe = _probe_module()
    pair={'input':['02','40'],'output':['08','40']}
    before=copy.deepcopy(pair)
    normalize=getattr(probe,'normalize_pairs',None)
    assert callable(normalize)
    assert normalize(pair)==[{'input':[[0,2],[4,0]],'output':[[0,8],[4,0]]}]
    assert pair==before
    assert normalize([pair])==normalize(pair)


def test_serializable_lessons_identify_every_default_query_phase():
    # Regression for the real after-policy limit, not just execution parity.
    assert 2 <= gen.EXAMPLES_NEEDED <= 5
    for seed in range(40):
        for offset in range(4):
            demos=[]
            for i in range(offset,offset+gen.EXAMPLES_NEEDED):
                g=gen.generate(seed,i,difficulty='medium')
                demos.append({'input':g,'output':gen.rule_mirror(g)})
            query=gen.generate(seed,offset+gen.EXAMPLES_NEEDED,difficulty='medium')
            assert gen.lesson_identifiable(demos,{'input':query,'output':gen.rule_mirror(query)}) == []
