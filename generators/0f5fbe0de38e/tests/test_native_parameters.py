"""Native contract regressions: counts, masking, geometry, and executed rules."""
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]

def module():
    path = HOME / 'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter missing'
    spec = importlib.util.spec_from_file_location('native_stamp_adapter_test', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def test_native_counts_prefixes_and_private_masking():
    m = module()
    full = m.generate(17, {'stamp_mask': 'template_holes'}, 6, 4)
    for demos in range(2, 7):
        for queries in range(1, 5):
            ep = m.generate(17, {'stamp_mask': 'template_holes'}, demos, queries)
            assert ep['train'] == full['train'][:demos]
            assert ep['test'] == full['test'][:queries]
            assert len({json.dumps(p['input']) for p in ep['train'] + ep['test']}) == demos + queries
    view = m.public_turn(full, 0)
    assert set(view) == {'train', 'test'}
    assert view['test'] == [{'input': full['test'][0]['input']}]
    view['train'][0]['input'][0][0] = -1
    assert full['train'][0]['input'][0][0] >= 0

def test_settings_match_inputs_and_canonical_bytes():
    m = module()
    a = m.generate(0, {'stamp_mask': 'fill_cells'}, 2, 4)
    b = m.generate(0, {'stamp_mask': 'template_holes'}, 2, 4)
    assert m.program({'stamp_mask':'fill_cells'}) == (HOME/'workspace/parametric/rules/stamp-mask-fill_cells.rkt').read_text()
    assert [p['input'] for p in a['train']+a['test']] == [p['input'] for p in b['train']+b['test']]
    assert all(x['output'] != y['output'] for x,y in zip(a['train'], b['train']))

@pytest.mark.parametrize('demos,queries', [(1,4),(7,4),(2,0),(2,5),(True,4),(2,True),(2,1.0)])
def test_invalid_counts_rejected(demos,queries):
    with pytest.raises(ValueError): module().generate(0, {'stamp_mask':'fill_cells'}, demos, queries)

@pytest.mark.parametrize('settings', [{}, {'stamp_mask':'bad'}, {'stamp_mask':'fill_cells','extra':1}, None])
def test_invalid_settings_rejected(settings):
    with pytest.raises(ValueError): module().generate(0, settings, 2, 4)

def test_stress_is_real_content_and_queries_are_privately_shuffled():
    m = module(); firsts = set()
    for seed in range(10):
        ep = m.generate(seed, {'stamp_mask':'template_holes'}, 2, 4)
        firsts.add(ep['query_source_indices'][0])
        stress = next(p for p in ep['test'] if len(p['input']) == 30 and len(p['input'][0]) == 30)
        info = m.inspect(stress['input'])
        assert sorted(info['scales']) == [1,2,3]
        bg = info['bg_color']; points = [(r,c) for r,row in enumerate(stress['input']) for c,v in enumerate(row) if v != bg]
        assert min(r for r,c in points)==min(c for r,c in points)==0
        assert max(r for r,c in points)==max(c for r,c in points)==29
        assert len({(r>=15,c>=15) for r,c in points})==4
    assert len(firsts)>1

def test_native_racket_parity_and_rivals(tmp_path):
    m = module(); report = m.audit(tmp_path, seeds=2, execute=True)
    assert report['failures']==[]
    assert report['racket_evaluations']>0
    assert all(r['demo_distinguished'] for r in report['rivals'])
