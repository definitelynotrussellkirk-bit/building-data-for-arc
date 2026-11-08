"""Visible-only regression checks for the blind solve."""
import json
from pathlib import Path
from solution import solve

def test_all_visible_training_pairs():
    challenge=json.loads((Path(__file__).with_name('challenge.json')).read_text())
    for i,pair in enumerate(challenge['train']):
        assert solve(pair['input']) == pair['output'], f'visible training pair {i}'
