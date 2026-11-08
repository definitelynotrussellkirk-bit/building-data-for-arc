import json
from pathlib import Path
from solution import solve

def test_all_visible_demonstrations():
    task=json.loads(Path(__file__).with_name('challenge.json').read_text())
    for i,p in enumerate(task['train']):
        assert solve(p['input'])==p['output'],i
