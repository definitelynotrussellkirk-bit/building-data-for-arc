"""Public export identifiers depend only on visible puzzle content."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/prototype.py'
@pytest.fixture(scope='module')
def proto():
    spec = importlib.util.spec_from_file_location('5dc10de63325_public_names', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_name_ignores_private_setting_seed_and_query_answers(proto):
    ep = {'parameter': {'marker_order': 'near_to_far'}, 'seed': 19,
          'train': [{'input': [[2, 3]], 'output': [[3, 2]]}],
          'test': [{'input': [[5, 6]], 'output': [[6, 5]]}]}
    name = proto.public_filename(ep)
    changed = deepcopy(ep)
    changed['parameter'] = {'marker_order': 'far_to_near'}
    changed['seed'] = 101
    changed['test'][0]['output'] = [[5, 6]]
    assert proto.public_filename(changed) == name
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', name)
    changed['train'][0]['output'] = [[2, 3]]
    assert proto.public_filename(changed) != name

def test_actual_racket_export_uses_opaque_names(proto, tmp_path):
    out = tmp_path / 'export'
    summary = proto.build_evidence(out)
    assert summary['passed'] and len(summary['episodes']) == 3
    files = list((out/'public').iterdir())
    assert len(files) == 3
    assert all(re.fullmatch(r'challenge-[0-9a-f]{64}\.json', p.name) for p in files)
    for row in summary['episodes']:
        private = json.loads((out/row['private_evidence']).read_text())
        public = out/row['public_challenge']
        assert public.parent == out/'public'
        assert public.name == proto.public_filename(private['episode'])
        assert json.loads(public.read_text()) == proto.public_challenge(private['episode'])
