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
    spec = importlib.util.spec_from_file_location('mark_action_public_names', SOURCE)
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

def test_real_racket_cli_all_settings_preserves_both_challenges(proto, tmp_path, monkeypatch):
    destination = tmp_path / 'export'
    monkeypatch.setattr(sys, 'argv', [str(SOURCE), '--seed', '17', '--all-settings', '--out', str(destination)])
    proto.main()
    manifest = json.loads((destination / 'manifest.json').read_text())
    assert len(manifest['episodes']) == 2
    names = []
    for row in manifest['episodes']:
        public = destination / row['public_path']
        private = json.loads((destination / row['private_path']).read_text())
        assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', public.name)
        assert public.name == proto.public_filename(private)
        challenge = json.loads(public.read_text())
        assert challenge == proto.public_challenge(private)
        assert all(set(pair) == {'input'} for pair in challenge['test'])
        names.append(public.name)
    assert len(set(names)) == 2
