"""Export names depend only on visible challenge content."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import pytest
from reviewer_support import public_challenge_bytes

SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/prototype.py'
@pytest.fixture(scope='module')
def proto():
    spec = importlib.util.spec_from_file_location('e521d16d403e_public_names', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_name_ignores_private_setting_seed_and_query_answers(proto):
    episode = {'parameters': {'setting': 'a'}, 'seed': 17,
               'train': [{'input': [[2, 3]], 'output': [[3, 2]]}],
               'test': [{'input': [[5, 6]], 'output': [[6, 5]]}]}
    name = proto.public_filename(episode)
    changed = deepcopy(episode)
    changed['parameters'] = {'setting': 'b'}
    changed['seed'] = 99
    changed['test'][0]['output'] = [[5, 6]]
    assert proto.public_filename(changed) == name
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', name)
    changed['train'][0]['output'] = [[2, 3]]
    assert proto.public_filename(changed) != name

def test_real_racket_export_names(proto, tmp_path):
    destination = tmp_path / 'export'
    report = proto.write_evidence([0, 1], out=destination)
    assert len(report['episodes']) == 2
    for row in report['episodes']:
        path = destination / row['public_path']
        episode = json.loads((destination / row['private_path']).read_text())
        assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', path.name)
        assert path.name == proto.public_filename(episode)
        assert json.loads(path.read_text()) == proto.public_challenge(episode)
        raw = path.read_bytes()
        assert path.name == f'challenge-{hashlib.sha256(raw).hexdigest()}.json'
        assert raw == public_challenge_bytes(episode)
