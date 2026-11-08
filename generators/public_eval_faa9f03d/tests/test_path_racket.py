from pathlib import Path
import json
import pytest
HOME=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator
    root=next(p for p in HOME.parents if (p/'shared/runtime').is_dir())
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    yield apply
    bridge.close()


@pytest.mark.parametrize('split,index',[('train',0),('train',1),('train',2),('test',0),('test',1)])
def test_official_labels_execute_in_racket(evaluator,split,index):
    path=HOME/'reference.rkt'
    assert path.is_file(), 'Missing general Racket reference'
    p=json.loads((HOME/'tests/fixtures/original-pairs.json').read_text())[split][index]
    assert evaluator(path.read_text(),p['input'])==p['output']


def test_retained_numeric_shortcut_and_repaired_teaching(evaluator):
    record=json.loads((HOME/'tests/fixtures/numeric-order-counterexample.json').read_text())
    for pair in record['train']:
        assert evaluator(record['program'],pair['input'])==pair['output']
        assert evaluator(record['rival_program'],pair['input'])==pair['output']
    q=record['query']
    assert evaluator(record['program'],q['input'])==q['output']
    assert evaluator(record['rival_program'],q['input'])==q['rival_output']!=q['output']
    import importlib.util,sys
    p=HOME/'workspace/parametric/adapter.py';spec=importlib.util.spec_from_file_location('_faa_repaired',p)
    a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
    ep=a.generate(1,record['settings'],2,4)
    assert any(evaluator(record['rival_program'],p['input'])!=p['output']for p in ep['train'])


def test_generated_small_and_30_by_30_labels(evaluator):
    import importlib.util,sys
    path=HOME/'workspace/parametric/adapter.py';spec=importlib.util.spec_from_file_location('_faa_boundary',path)
    a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
    for mode in a.MODES:
        ep=a.generate(43,{'crossing_policy':mode},2,4)
        for p in ep['train']+[ep['test'][3]]:
            assert evaluator(ep['program_solution'],p['input'])==p['output']
