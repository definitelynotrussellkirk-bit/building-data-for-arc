"""Task-local tests, portable into the packet's isolated task runtime."""
import importlib.util
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dihedral_probe',HOME/'workspace'/'probe.py')
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
gen=probe.load_generator()


def test_equal_area_non_equivalent_is_lawful():
    grid=probe.witness_grid()
    assert probe.oracle(grid)==[[8,0,8,0],[0,8,0,8],[8,0,8,0],[0,8,0,8]]
    assert probe.count_only(grid)!=probe.oracle(grid)
    assert gen.self_check(grid)==[]


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_each_three_demo_window_refutes_count_only(band):
    for seed in range(12):
        grids=[gen.generate(seed,si,difficulty=band) for si in range(5)]
        for start in range(3):
            assert any(probe.oracle(g)!=probe.count_only(g) for g in grids[start:start+3]), (band,seed,start)


def test_n_classes_one_is_not_silently_clamped():
    grid=gen.generate(1,0,n_classes=1)
    assert probe.oracle(grid)==[[8]*4 for _ in range(4)]
    assert gen.self_check(grid)==[]


@pytest.mark.parametrize('n',[1,2,3,4])
def test_exact_palette_size(n):
    grid=gen.generate(9,1,palette_size=n)
    assert len(set(sum(grid,[]))-{0})==n


def test_four_nonempty_panels_are_required():
    assert gen.self_check([[0]*9 for _ in range(9)])
    grid=probe.witness_grid()
    for r in range(4):
        for c in range(4):
            grid[r][c]=0
    assert gen.self_check(grid)


def test_exact_controls_have_public_named_draw_provenance():
    from puzzle_generators.base import set_ctx_observer
    seen=[]
    set_ctx_observer(seen.append)
    try:
        grid=gen.generate(0,0,difficulty='easy')
    finally:
        set_ctx_observer(None)
    actual=gen.observe_overrides(grid)
    assert seen
    assert all(seen[-1].recorded_draws().get(k)==actual[k] for k in gen.AXES)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_all_exact_axis_combinations(band):
    for classes in range(1,5):
        for palette in range(1,5):
            grid=gen.generate(0,0,difficulty=band,n_classes=classes,palette_size=palette,grid_h=9,grid_w=9)
            assert gen.self_check(grid)==[]
            assert gen.observe_overrides(grid)==dict(grid_h=9,grid_w=9,n_classes=classes,palette_size=palette)


@pytest.mark.parametrize('kwargs',[{'n_classes':0},{'n_classes':5},{'palette_size':True},{'palette_size':None},
                                    {'grid_h':8},{'texture':'smooth'},{'n_classes':'2'}])
def test_invalid_or_removed_controls_raise(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0,0,**kwargs)


def test_all_declared_rivals_refuted_in_every_default_three_demo_window():
    rivals=dict(gen.CANONICAL_SHORTCUTS)
    rivals.update(gen.LESSON_COMPETITORS)
    assert len(rivals)>=5
    for band in ('easy','medium','hard'):
        for seed in range(6):
            grids=[gen.generate(seed,si,difficulty=band) for si in range(5)]
            for start in range(3):
                for name,rival in rivals.items():
                    assert any(rival(g)!=probe.oracle(g) for g in grids[start:start+3]),(band,seed,start,name)


def test_banks_are_connected_distinct_and_d4_complete():
    for size,shapes in gen._banks().items():
        keys=set()
        for shape in shapes:
            assert len(shape)==size
            assert max(gen._extent(shape))<=4
            todo=[shape[0]]; seen={shape[0]}; occupied=set(shape)
            for r,c in todo:
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    q=(r+dr,c+dc)
                    if q in occupied and q not in seen:
                        seen.add(q); todo.append(q)
            assert len(seen)==size
            assert gen._key(shape) not in keys
            keys.add(gen._key(shape))
            assert all(gen._key(gen._dihedral(shape,t))==shape for t in range(8))


def test_every_canonical_shortcut_fits_every_canonical_pair():
    import json
    pairs=json.loads((Path(__file__).with_name('canonical_examples.json')).read_text())
    assert len(pairs)==5
    assert gen.CANONICAL_SHORTCUTS
    for pair in pairs:
        assert gen.self_check(pair['input'])==[]
        assert probe.oracle(pair['input'])==pair['output']
        assert all(rival(pair['input'])==pair['output'] for rival in gen.CANONICAL_SHORTCUTS.values())


def _lesson_tool():
    spec=importlib.util.spec_from_file_location('public_lesson_probe',HOME/'workspace'/'lesson_probe.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_public_lesson_probe_rejects_no_contract():
    from types import SimpleNamespace
    with pytest.raises(ValueError,match='NO_CONTRACT'):
        _lesson_tool().score_episodes(SimpleNamespace(),[])


def test_public_lesson_probe_detects_survivor_without_query_error():
    grid=gen.generate(0,0,n_classes=1)
    pair={'input':grid,'output':probe.oracle(grid)}
    report=_lesson_tool().score_episodes(gen,[{'seed':0,'train':[pair]*3,'test':[pair]}])
    assert report['survived_demos']['count_only']==1
    assert report['survived_demos_wrong_query']['count_only']==0
    assert report['unique_inputs']==1
    assert report['racket_oracle_mismatches']==[]
