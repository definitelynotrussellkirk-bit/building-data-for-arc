"""Proposed-family transport only: protected labels, opaque public challenges.

Four-query public containers are controller data. Use one_query_bytes() for
one visible query at a time; it carries no turn/count/future-query metadata.
This writer grants no approval, acceptance or training admission.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]
from reviewer_support import public_challenge_bytes
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode()


def one_query_bytes(episode, index):
    """Visible demonstrations plus exactly one query, independent of its ordinal."""
    if type(index) is not int or not 0 <= index < len(episode['test']):
        raise ValueError('query index is outside this private episode')
    return public_challenge_bytes({'train': episode['train'], 'test': [episode['test'][index]]})


def plan_records(episodes):
    """Validate grids and reject duplicate public payloads before publication."""
    if not isinstance(episodes, list) or not episodes:
        raise ValueError('at least one episode is required')
    records = []
    for episode in copy.deepcopy(episodes):
        payload = public_challenge_bytes(episode)
        for split in ('train', 'test'):
            for pair in episode[split]:
                _grid(pair['input'])
                _grid(pair['output'])
        records.append((hashlib.sha256(payload).hexdigest(), payload, episode))
    if len({record[0] for record in records}) != len(records):
        raise ValueError('duplicate visible challenge')
    return sorted(records, key=lambda record: record[0])


def export_episodes(episodes, output):
    """Re-execute all claimed labels before writing a new proposed export."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    records = plan_records(episodes)
    with _local_imports(ROOT / 'shared/runtime', Path(__file__).parent):
        apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
        count = 0
        try:
            for _, _, episode in records:
                program = episode.get('program_solution')
                if type(program) is not str or not program.strip():
                    raise ValueError('an exact Racket program is required')
                for split in ('train', 'test'):
                    for pair in episode[split]:
                        actual = _grid(apply(program, pair['input']))
                        count += 1
                        if actual != pair['output']:
                            raise ValueError('Racket label differs from claimed output')
        finally:
            bridge.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.parametric-export-', dir=output.parent) as temporary:
        stage = Path(temporary)
        (stage / 'public').mkdir()
        visible, private = [], []
        for identifier, payload, episode in records:
            (stage / 'public' / (identifier + '.json')).write_bytes(payload)
            visible.append(json_bytes({'episode_id': identifier, **json.loads(payload)}))
            private.append(json_bytes({'episode_id': identifier, **episode}))
        (stage / 'public.jsonl').write_bytes(b''.join(visible))
        (stage / 'private.jsonl').write_bytes(b''.join(private))
        manifest = {'schema': '4512012999bb-prototype-export-v1', 'status': 'complete',
                    'variant_status': 'proposed', 'training_admitted': False,
                    'episodes': len(records), 'label_count': count, 'racket': identity,
                    'files': [{'path': path.relative_to(stage).as_posix(),
                               'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                              for path in sorted(stage.rglob('*')) if path.is_file()]}
        (stage / 'manifest.json').write_bytes(json_bytes(manifest))
        output.mkdir(exist_ok=False)
        for name in ('public', 'public.jsonl', 'private.jsonl', 'manifest.json'):
            os.replace(stage / name, output / name)
    return verify_export(output)


def verify_export(output):
    """Verify serialized bytes and projection; this does not replay Racket."""
    output = Path(output)
    manifest = json.loads((output / 'manifest.json').read_bytes())
    if (manifest.get('schema') != '4512012999bb-prototype-export-v1'
            or manifest.get('status') != 'complete'):
        raise ValueError('incomplete proposed export')
    actual = {path.relative_to(output).as_posix() for path in output.rglob('*')
              if path.is_file() and path != output / 'manifest.json'}
    files = manifest.get('files', [])
    if (len(files) != len(actual) or {row['path'] for row in files} != actual
            or not {'public.jsonl', 'private.jsonl'} <= actual):
        raise ValueError('export inventory differs')
    for row in files:
        path = output / row['path']
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('export bytes differ')
    public = [json.loads(line) for line in (output / 'public.jsonl').read_bytes().splitlines()]
    private = [json.loads(line) for line in (output / 'private.jsonl').read_bytes().splitlines()]
    records = plan_records(private)
    if len(public) != manifest['episodes'] or len(private) != len(public):
        raise ValueError('export count differs')
    expected_files = {'public.jsonl', 'private.jsonl'}
    for visible, hidden, (identifier, payload, _) in zip(public, private, records):
        name = 'public/' + identifier + '.json'
        expected_files.add(name)
        if (hidden.get('episode_id') != identifier
                or visible != {'episode_id': identifier, **json.loads(payload)}
                or public_challenge_bytes(visible) != payload
                or (output / name).read_bytes() != payload):
            raise ValueError('public/private projection differs')
    if actual != expected_files:
        raise ValueError('unexpected export files')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--demos', type=int, choices=range(3, 7), default=3)
    parser.add_argument('--queries', type=int, choices=range(1, 5), default=4)
    parser.add_argument('--alignment', choices=('match', 'contrast', 'both'), default='both')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if not 0 <= args.seed < 2**63:
        parser.error('--seed must be in 0..2**63-1')
    path = Path(__file__).with_name('adapter.py')
    spec = importlib.util.spec_from_file_location('_4512012999bb_export_adapter', path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    settings = ('match', 'contrast') if args.alignment == 'both' else (args.alignment,)
    episodes = []
    for alignment in settings:
        setting = {'alignment': alignment}
        episode = adapter.generate(args.seed, setting, args.demos, args.queries)
        if episode.get('program_solution') != adapter.program(setting):
            raise ValueError('generated program differs from declared setting')
        episodes.append({**episode, 'settings': setting, 'seed': args.seed})
    manifest = export_episodes(episodes, args.out)
    print(json.dumps({'status': 'proposed', 'episodes': manifest['episodes'],
                      'label_count': manifest['label_count'], 'output': str(args.out)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
