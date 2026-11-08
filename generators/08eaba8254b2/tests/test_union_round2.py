"""The improved tie bank must preserve the retained component rule's all-ties semantics."""
from pathlib import Path
import importlib.util,json,hashlib
HOME=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('_union_round2_test',HOME/'workspace/parametric/union.py')
U=importlib.util.module_from_spec(spec);spec.loader.exec_module(U)

def test_all_accepted_programs_and_equal_largest_tie_survive_rebase():
    for settings,sha in json.loads((HOME/'parametric/accepted.json').read_text())['programs'].items():
        assert hashlib.sha256(U.program(json.loads(settings)).encode()).hexdigest()==sha
    seed=next(seed for seed in range(16) if U._rng(seed,'query-bank').randrange(3)==0)
    ep=U.generate(seed,{'projection':'largest_xor_component'},6,4)
    tied=[]
    for pair in ep['test']:
        groups=U.OLD._components(U.OLD.xor_mask(pair['input']))
        largest=max(map(len,groups));winners=[g for g in groups if len(g)==largest]
        if len(winners)>1:
            expected=set().union(*winners)
            actual={(r,c) for r,row in enumerate(pair['output']) for c,v in enumerate(row) if v}
            assert actual==expected
            assert pair['output']!=U.predict(pair['input'],'largest_component_bbox')
            tied.append(pair)
    assert tied
