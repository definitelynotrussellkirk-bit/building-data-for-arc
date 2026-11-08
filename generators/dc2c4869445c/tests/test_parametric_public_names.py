"""Public challenge names exclude hidden settings, seeds and query answers."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
import pytest
SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/gap_variant.py'
@pytest.fixture(scope='module')
def proto():
    spec = importlib.util.spec_from_file_location('dc2c4869445c_public_names', SOURCE)
    module = importlib.util.module_from_spec(spec);sys.modules[spec.name] = module;spec.loader.exec_module(module)
    return module

def test_name_depends_only_on_visible_puzzle(proto):
    value = {'seed': 0, 'parameter': {'setting': 0}, 'train': [{'input': [[1]], 'output': [[2]]}], 'test': [{'input': [[3]], 'output': [[4]]}]}
    name = proto.public_filename(value)
    changed = deepcopy(value);changed['seed'] = 123;changed['parameter'] = {'setting': 2};changed['test'][0]['output'] = [[9]]
    assert proto.public_filename(changed) == name
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', name)
    changed['train'][0]['output'] = [[8]]
    assert proto.public_filename(changed) != name

def test_actual_racket_writer_uses_opaque_public_files(proto, tmp_path):
    out = tmp_path/'export'
    proto.write_evidence(out, gap='all')
    files = list((out/'public').rglob('*.json'))
    assert len(files) == 3
    assert all(re.fullmatch(r'challenge-[0-9a-f]{64}\.json', p.name) for p in files)
    for p in files:
        public = json.loads(p.read_text())
        assert proto.public_filename(public) == p.name
        assert all(set(pair) == {'input'} for pair in public['test'])
