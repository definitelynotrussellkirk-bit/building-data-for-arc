"""Recheck saved public/private episodes and exercise two corruption failures.

Run via the packet wrapper: python verify_saved_export.py REPO_ROOT EXPORT_DIR
This checks stored labels with the Python mirror. The separate export receipt
records the actual Racket executions; this script does not claim new Racket runs.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

repo = Path(sys.argv[1]).resolve()
batch = Path(sys.argv[2]).resolve()
source = repo / 'generators/061566027b67/workspace/parametric/rectangle_modes.py'
spec = importlib.util.spec_from_file_location('saved_export_rectangle_modes', source)
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def verify(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    require(manifest['schema'] == 'rectangle-modes-public-batch-v1', 'manifest schema')
    entries = manifest['public']
    identifiers = [row['id'] for row in entries]
    require(identifiers == sorted(set(identifiers)), 'ids must be sorted and unique')
    expected_names = {identifier + '.json' for identifier in identifiers}
    for area in ('public', 'private'):
        files = list((directory / area).iterdir())
        require({f.name for f in files} == expected_names, area + ' file inventory')
        require(all(f.is_file() and not f.is_symlink() for f in files), area + ' ordinary files')
    pairs = queries = 0
    settings = set()
    for entry in entries:
        identifier = entry['id']
        require(len(identifier) == 64 and all(c in '0123456789abcdef' for c in identifier), 'id format')
        require(entry['path'] == 'public/' + identifier + '.json', 'public path')
        public = (directory / entry['path']).read_bytes()
        episode = json.loads((directory / 'private' / (identifier + '.json')).read_text())
        require(hashlib.sha256(public).hexdigest() == identifier, 'public byte hash')
        require(public == p.public_challenge_bytes(episode), 'public projection')
        params = p.Parameters(**episode['parameters'])
        settings.add((params.shape_mode, params.paint_color))
        require(episode['program'] == p.materialize_program(params), 'program settings')
        require(hashlib.sha256(episode['program'].encode()).hexdigest() == episode['program_sha256'], 'program hash')
        require(episode['source_hashes'] == p._source_hashes(), 'source hashes')
        require(2 <= len(episode['train']) <= 16 and 1 <= len(episode['test']) <= 16, 'counts')
        all_pairs = episode['train'] + episode['test']
        inputs = [json.dumps(pair['input']) for pair in all_pairs]
        require(len(set(inputs)) == len(inputs), 'distinct demo and query inputs')
        for pair in all_pairs:
            require(pair['output'] == p.solve_python(pair['input'], params), 'stored label differs from mirror')
        certificate = p.demo_certificate(episode['train'], [v['input'] for v in episode['test']], params)
        require(certificate == episode['certificate'], 'stored certificate')
        require(all(v['identified'] for v in certificate['per_query']), 'query identifiability')
        pairs += len(all_pairs)
        queries += len(episode['test'])
    return {'episodes': len(entries), 'pairs': pairs, 'queries': queries, 'settings': len(settings)}

result = verify(batch)
require(result == {'episodes': 20, 'pairs': 140, 'queries': 80, 'settings': 20}, 'expected all-settings evidence')
tamper_rejections = []
with tempfile.TemporaryDirectory(prefix='saved-export-tamper-', dir=batch.parent) as temporary:
    target = Path(temporary) / 'copy'
    shutil.copytree(batch, target)
    manifest = json.loads((target / 'manifest.json').read_text())
    identifier = manifest['public'][0]['id']
    private_path = target / 'private' / (identifier + '.json')
    original = private_path.read_bytes()
    altered = json.loads(original)
    altered['test'][0]['output'][0][0] = (altered['test'][0]['output'][0][0] + 1) % 10
    private_path.write_text(json.dumps(altered))
    try:
        verify(target)
    except ValueError as exc:
        require(str(exc) == 'stored label differs from mirror', 'specific private-label rejection')
        tamper_rejections.append('private_query_label')
    else:
        raise AssertionError('private query-label corruption was accepted')
    private_path.write_bytes(original)
    public_path = target / 'public' / (identifier + '.json')
    altered = json.loads(public_path.read_bytes())
    altered['seed'] = 42
    public_path.write_text(json.dumps(altered))
    try:
        verify(target)
    except ValueError as exc:
        require(str(exc) == 'public byte hash', 'specific public-byte rejection')
        tamper_rejections.append('public_metadata_injection')
    else:
        raise AssertionError('public metadata injection was accepted')
print(json.dumps({'status': 'passed', **result, 'tamper_rejections': tamper_rejections,
                  'real_racket_executed': False, 'stored_labels_rechecked_with': 'python_mirror',
                  'prototype_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}, sort_keys=True))
