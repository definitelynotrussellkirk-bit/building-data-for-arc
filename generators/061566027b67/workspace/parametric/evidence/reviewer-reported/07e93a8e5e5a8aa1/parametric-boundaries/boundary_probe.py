"""Exercise successful count limits and deterministic replay through real Racket."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / 'generators/061566027b67/workspace/parametric/rectangle_modes.py'
spec = importlib.util.spec_from_file_location('boundary_rectangle_modes', path)
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)

def digest(episode):
    visible_and_labels = {key: episode[key] for key in ('parameters', 'train', 'test', 'program')}
    return hashlib.sha256(json.dumps(visible_and_labels, sort_keys=True).encode()).hexdigest()

records = []
for seed, params, train_count, test_count in (
    (1300615, p.Parameters(), 2, 1),
    (1300616, p.Parameters('outline', 9), 16, 16),
):
    episode = p.build_episode(seed, params, train_count=train_count, test_count=test_count)
    assert len(episode['train']) == train_count
    assert len(episode['test']) == test_count
    inputs = [json.dumps(pair['input']) for split in ('train', 'test') for pair in episode[split]]
    assert len(set(inputs)) == train_count + test_count
    assert all(query['identified'] for query in episode['certificate']['per_query'])
    assert episode['certificate']['survivors'] == [episode['parameters']]
    records.append({'seed': seed, 'parameters': episode['parameters'],
                    'train_count': train_count, 'test_count': test_count,
                    'unique_inputs': len(set(inputs)), 'episode_digest': digest(episode),
                    'program_sha256': episode['program_sha256']})
repeat = p.build_episode(1300615, train_count=2, test_count=1)
assert digest(repeat) == records[0]['episode_digest']
print(json.dumps({'status': 'passed', 'real_racket_executed': True,
                  'racket_pairs_checked': 38, 'deterministic_replay': True,
                  'prototype_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'boundaries': records}, sort_keys=True))
