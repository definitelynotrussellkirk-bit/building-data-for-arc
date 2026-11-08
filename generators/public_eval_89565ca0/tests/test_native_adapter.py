import copy
import importlib.util
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rooms_adapter_test', HOME/'workspace/parametric/adapter.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def test_matched_inputs_distinguish_settings_and_exact_default():
    assert A.program({'sort_order':'ascending'}) == (HOME/'reference.rkt').read_text()
    for seed in (0,17,43,2**63-1):
        ascending = A.generate(seed,{'sort_order':'ascending'},2,4)
        descending = A.generate(seed,{'sort_order':'descending'},2,4)
        for split in ('train','test'):
            assert [p['input'] for p in ascending[split]] == [p['input'] for p in descending[split]]
            assert all(a['output'] != d['output'] for a,d in zip(ascending[split],descending[split]))


def test_counts_prefixes_no_aliases_or_global_random_mutation():
    before = random.getstate()
    for order in ('ascending','descending'):
        settings = {'sort_order':order}
        original = copy.deepcopy(settings)
        full = A.generate(17,settings,6,4)
        for demos in range(2,7):
            for queries in range(1,5):
                lesson = A.generate(17,settings,demos,queries)
                assert lesson['train'] == full['train'][:demos]
                assert lesson['test'] == full['test'][:queries]
                assert set(lesson) == {'train','test','program_solution'}
        assert settings == original
        full['train'][0]['input'][0][0] = -7
        assert A.generate(17,settings,6,4)['train'][0]['input'][0][0] >= 0
    assert random.getstate() == before


def test_complete_queries_are_distinct_and_include_substantive_room_limit():
    lesson = A.generate(2**63-1,{'sort_order':'ascending'},6,4)
    pairs = lesson['train'] + lesson['test']
    inputs = [tuple(tuple(row) for row in p['input']) for p in pairs]
    assert len(set(inputs)) == 10
    largest = [p for p in lesson['test'] if len(p['input']) == len(p['input'][0]) == 30]
    assert len(largest) == 1
    assert len(largest[0]['output'][0]) == 30
    info = A.family.analyze(largest[0]['input'])
    assert max(x['rooms'] for x in info['objects']) == 30
    assert len(info['objects']) >= 3


@pytest.mark.parametrize('seed',[True,-1,2**63,0.0,'0',None])
def test_bad_seeds(seed):
    with pytest.raises((ValueError,TypeError)):
        A.generate(seed,{'sort_order':'ascending'},2,4)


@pytest.mark.parametrize('demos,queries',[(True,4),(1,4),(7,4),(2.0,4),(2,True),(2,0),(2,5),(2,4.0)])
def test_bad_counts(demos,queries):
    with pytest.raises((ValueError,TypeError)):
        A.generate(0,{'sort_order':'ascending'},demos,queries)


@pytest.mark.parametrize('setting',[{},None,[],{'sort_order':True},{'sort_order':'ascending','extra':0}])
def test_bad_settings(setting):
    with pytest.raises((ValueError,TypeError)):
        A.generate(0,setting,2,4)
