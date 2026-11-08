"""Regression checks for the reviewed-rule/sampler union."""
from pathlib import Path
import importlib.util, hashlib, json
HOME=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('_union_test_'+HOME.name, HOME/'workspace/parametric/union.py')
U=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(U)

def test_accepted_program_preservation():
    record=json.loads((HOME/'workspace/parametric/evidence/union-current/self-review.json').read_text())
    for settings,expected in record['accepted_programs_preserved'].items():
        assert hashlib.sha256(U.program(json.loads(settings)).encode()).hexdigest()==expected

def test_matched_teachable_prefixes_and_private_queries():
    for seed in (0,1,10,12,17):
        baseline=None
        for mode in U.VALUES:
            settings={U.KEY:mode};ep=U.generate(seed,settings,6,4)
            grids=[p['input'] for p in ep['train']+ep['test']]
            if baseline is None:baseline=grids
            assert grids==baseline and len({repr(g) for g in grids})==10
            survivors=[v for v in U.VALUES if all(U.predict(p['input'],v)==p['output'] for p in ep['train'][:5])]
            assert survivors==[mode]
            for d in (5,6):
                small=U.generate(seed,settings,d,4)
                assert small['train']==ep['train'][:d] and small['test']==ep['test']
            for q in (1,2,4):assert U.generate(seed,settings,5,q)['test']==ep['test'][:q]
            for i in range(4):assert U.public_view(ep,i)=={'train':ep['train'],'test':[{'input':ep['test'][i]['input']}]}


def test_four_demo_prefix_is_outside_supported_contract():
    import pytest
    with pytest.raises(ValueError):
        U.generate(10, {"projection":"largest_component_bbox"}, 4, 4)
