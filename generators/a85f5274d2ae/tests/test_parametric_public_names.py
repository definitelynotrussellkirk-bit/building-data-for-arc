"""Export names depend only on visible challenge content."""
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
    spec = importlib.util.spec_from_file_location('axis_tolerance_public_names', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_name_ignores_private_setting_seed_and_query_answers(proto):
    episode = {'parameters': {'mark_action': 'half_swap'}, 'seed': 17,
               'train': [{'input': [[2, 3]], 'output': [[3, 2]]}],
               'test': [{'input': [[5, 6]], 'output': [[6, 5]]}]}
    name = proto.public_filename(episode)
    changed = deepcopy(episode)
    changed['parameters'] = {'mark_action': 'reflection'}
    changed['seed'] = 99
    changed['test'][0]['output'] = [[5, 6]]
    assert proto.public_filename(changed) == name
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', name)
    changed['train'][0]['output'] = [[2, 3]]
    assert proto.public_filename(changed) != name

def test_real_racket_export_has_separate_opaque_public_files(proto, tmp_path):
    from reviewer_support import find_root
    destination = tmp_path / 'export'
    report = proto.collect_evidence(destination, root=Path(find_root(__file__)))
    assert len(report['episodes']) == 3
    public_files = list((destination / 'public').glob('*.json'))
    assert len(public_files) == 3
    for row in report['episodes']:
        private = json.loads((destination / row['path'] / 'private.json').read_text())
        path = destination / row['public_path']
        assert path.parent == destination / 'public'
        assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', path.name)
        assert path.name == proto.public_filename(private)
        assert json.loads(path.read_text()) == proto._public_episode(private)
        assert all(set(pair) == {'input'} for pair in json.loads(path.read_text())['test'])
