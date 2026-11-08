"""Native adapter counts, matched settings and query-prefix contract."""
import importlib.util
from pathlib import Path
import pytest
KEY = 'path_tiebreak'
VALUES = ['canonical_udlr', 'horizontal_first']

def adapter():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("_owner_adapter_d3ae93aa8d37", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_counts_and_prefix_are_independent():
    a = adapter(); setting = {KEY: VALUES[0]}
    small = a.generate(17, setting, 2, 1)
    large = a.generate(17, setting, 6, 4)
    assert (len(small['train']), len(small['test'])) == (2, 1)
    assert (len(large['train']), len(large['test'])) == (6, 4)
    assert small['train'] == large['train'][:2]
    assert small['test'] == large['test'][:1]
    inputs = [pair['input'] for split in ('train','test') for pair in large[split]]
    assert len({str(grid) for grid in inputs}) == len(inputs)

def test_settings_share_inputs_but_change_labels():
    a = adapter()
    left = a.generate(0, {KEY: VALUES[0]}, 3, 4)
    right = a.generate(0, {KEY: VALUES[1]}, 3, 4)
    for split in ('train', 'test'):
        assert [p['input'] for p in left[split]] == [p['input'] for p in right[split]]
    assert any(x['output'] != y['output'] for x,y in zip(left['train'],right['train']))
    assert left['program_solution'] != right['program_solution']

@pytest.mark.parametrize('demos,queries', [(True,4),(3,False),(1,4),(7,4),(3,0),(3,5),(3,1.0)])
def test_invalid_counts_fail(demos,queries):
    with pytest.raises((ValueError,TypeError)):
        adapter().generate(0, {KEY: VALUES[0]}, demos, queries)

def test_unknown_settings_fail():
    with pytest.raises((ValueError,TypeError)):
        adapter().program({KEY: VALUES[0], 'unknown': 1})
