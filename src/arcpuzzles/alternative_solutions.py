"""Hash-bound auxiliary tasks: one demo-consistent answer is given; find another.

Programs and certificates stay controller-side. This does not admit a generator
or claim that a shortcut remains valid after its lesson has been repaired.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

from .parametric_worker import _grid
from .runtime import run_process

CANDIDATE = 'arcpuzzles-alternative-solution-candidate-v1'
STREAM = 'arcpuzzles-alternative-solutions-v1'


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode() + b'\n'


def digest(value):
    return hashlib.sha256(raw(value)).hexdigest()


def file_hash(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def _local(root, name):
    if (type(name) is not str or not name or '\\' in name
            or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts):
        raise ValueError('Unsafe source path')
    path = root / name
    if path.resolve() != path.absolute() or not path.is_file():
        raise ValueError('Missing or symlinked source path: ' + name)
    return path


def validate(candidate, root=None):
    if not isinstance(candidate, dict) or candidate.get('schema') != CANDIDATE:
        raise ValueError('Unknown candidate schema')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', candidate.get('generator_id', '')):
        raise ValueError('Invalid generator identity')
    train = candidate.get('train')
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError('Candidate needs 2..6 exact demonstrations')
    seen = set()
    for pair in train:
        if not isinstance(pair, dict) or set(pair) != {'input', 'output'}:
            raise ValueError('Demonstration must contain input/output only')
        _grid(pair['input']); _grid(pair['output'])
        key = digest(pair['input'])
        if key in seen: raise ValueError('Repeated demonstration input')
        seen.add(key)
    query = candidate.get('query')
    if not isinstance(query, dict) or set(query) != {'input'}:
        raise ValueError('Query must contain input only')
    _grid(query['input'])
    if digest(query['input']) in seen: raise ValueError('Query repeats a demonstration')
    hypotheses = candidate.get('hypotheses')
    if type(hypotheses) is not list or not 2 <= len(hypotheses) <= 16:
        raise ValueError('Candidate needs 2..16 executable hypotheses')
    for hypothesis in hypotheses:
        for field in ('name', 'description', 'program'):
            value = hypothesis.get(field)
            if type(value) is not str or not value.strip() or len(value.encode()) > 100000:
                raise ValueError('Invalid hypothesis ' + field)
    evidence = candidate.get('source_evidence')
    if type(evidence) is not list or not evidence:
        raise ValueError('Source evidence is required')
    if root is not None:
        for row in evidence:
            path = _local(Path(root), row['path'])
            if file_hash(path) != row.get('sha256'):
                raise ValueError('Changed source evidence: ' + row['path'])
    return candidate


def _evaluate(root, candidate):
    """Child-only execution through the same-checkout protected Racket bridge."""
    from .parametric_worker import _local_imports, _real_evaluator
    validate(candidate, root)
    runtime = root / 'shared/runtime'
    with _local_imports(runtime, runtime):
        from arc_repl.parser import parse_all, Symbol
        for h in candidate['hypotheses']:
            forms = parse_all(h['program'])
            if (len(forms) != 1 or not isinstance(forms[0], list) or not forms[0]
                    or forms[0][0] not in (Symbol('rule!'), Symbol('lambda'))):
                raise ValueError('Program needs one complete rule! or lambda expression')
        apply, identity, bridge = _real_evaluator(runtime)
        results = []
        try:
            for h in candidate['hypotheses']:
                outputs = [_grid(apply(h['program'], pair['input'])) for pair in candidate['train']]
                if outputs != [pair['output'] for pair in candidate['train']]:
                    raise ValueError('Hypothesis breaks a visible demonstration: ' + h['name'])
                results.append({'program_sha256': hashlib.sha256(h['program'].encode()).hexdigest(),
                                'train_outputs': outputs,
                                'query_output': _grid(apply(h['program'], candidate['query']['input']))})
        finally:
            bridge.close()
    return {'status': 'verified', 'candidate_sha256': digest(candidate), 'racket': identity,
            'verifier_sha256': file_hash(Path(__file__).resolve()),
            'evaluations': len(results) * (len(candidate['train']) + 1), 'hypotheses': results}


def certify(root, candidate):
    validate(candidate, root)
    with tempfile.TemporaryDirectory(prefix='arc-alternative-replay-') as folder:
        request = Path(folder) / 'request.json'
        request.write_bytes(raw({'root': str(root), 'candidate': candidate}))
        result = run_process([sys.executable, '-m', 'arcpuzzles.alternative_solutions',
                              '_verify', str(request)], root, timeout=60,
                             extra_env={'PYTHONPATH': str(Path(__file__).resolve().parents[1]),
                                        'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
    if result['timed_out'] or result['exit_code'] != 0:
        raise ValueError('Protected replay failed: ' + result['stdout'][-1000:] + result['stderr'][-1000:])
    return json.loads(result['stdout'])


def examples(candidate, certificate):
    validate(candidate)
    if (certificate.get('status') != 'verified' or certificate.get('candidate_sha256') != digest(candidate)
            or certificate.get('racket', {}).get('backend') != 'racket'
            or certificate.get('racket', {}).get('protected') is not True):
        raise ValueError('Certificate is unprotected or bound to different candidate bytes')
    hypotheses = candidate['hypotheses']; checked = certificate.get('hypotheses')
    if type(checked) is not list or len(checked) != len(hypotheses):
        raise ValueError('Certificate hypothesis inventory differs')
    gold = [p['output'] for p in candidate['train']]
    for h, result in zip(hypotheses, checked):
        if result.get('program_sha256') != hashlib.sha256(h['program'].encode()).hexdigest():
            raise ValueError('Certificate program hash differs')
        for output in result.get('train_outputs', []): _grid(output)
        if raw(result.get('train_outputs')) != raw(gold):
            raise ValueError('Hypothesis breaks a visible demonstration')
        _grid(result['query_output'])
    base = {'train': candidate['train'], 'test': [candidate['query']]}
    rows = []
    for i, j in itertools.permutations(range(len(hypotheses)), 2):
        if checked[i]['query_output'] == checked[j]['query_output']: continue
        prompt = {**base, 'task_type': 'find_alternative_solution',
                  'instruction': 'The given rule fits every demonstration. Find a different rule '
                                 'that also fits every demonstration but gives a different answer '
                                 'for the test input. Return that other output grid.',
                  'given_solution': {'rule': hypotheses[i]['description'],
                                     'output': checked[i]['query_output']}}
        rows.append({'prompt_id': digest(prompt), 'group_id': digest(base), 'prompt': prompt,
                     'target': checked[j]['query_output'], 'target_rule': hypotheses[j]['description'],
                     'target_program_sha256': checked[j]['program_sha256'],
                     'proof': {'candidate_sha256': digest(candidate),
                               'certificate_sha256': digest(certificate),
                               'given_hypothesis': i, 'target_hypothesis': j,
                               'generator_id': candidate['generator_id'],
                               'lineage': candidate.get('lineage', {})}})
    if not rows: raise ValueError('No different query answers: not an alternative-answer task')
    return rows


def combine(examples_):
    prompts = {}; targets = {}
    for row in examples_:
        pid = row['prompt_id']
        if digest(row['prompt']) != pid: raise ValueError('Public prompt identity differs')
        if pid in prompts and raw(prompts[pid]) != raw(row['prompt']): raise ValueError('Prompt collision')
        prompts[pid] = row['prompt']
        key = (pid, digest(row['target']))
        target = targets.setdefault(key, {'output': row['target'], 'rule': row['target_rule'],
                                        'program_sha256': row['target_program_sha256'],
                                        'group_id': row['group_id'], 'proofs': []})
        if row['proof'] not in target['proofs']: target['proofs'].append(row['proof'])
    public = []; private = []; train = []
    for pid in sorted(prompts):
        choices = [v for (p, _), v in sorted(targets.items()) if p == pid]
        public.append({'id': pid, 'challenge': prompts[pid]})
        private.append({'prompt_id': pid, 'group_id': choices[0]['group_id'], 'acceptable_targets': choices})
        for choice in choices:
            train.append({'unit_id': digest({'prompt_id': pid, 'target': choice['output']}),
                          'prompt_id': pid, 'group_id': choice['group_id'], 'prompt': prompts[pid],
                          'target': choice['output'], 'target_rule': choice['rule'],
                          'provenance': choice['proofs']})
    return public, private, train


def publish(directory, rows, certificates, quarantined):
    public, private, train = combine(rows)
    if not train: raise ValueError('No verified alternative-answer tasks to publish')
    payloads = {name: b''.join(raw(row) for row in values) for name, values in
                [('public.jsonl', public), ('private.jsonl', private), ('train.jsonl', train),
                 ('certificates.jsonl', certificates)]}
    manifest = {'schema': STREAM, 'files': {n: hashlib.sha256(b).hexdigest() for n, b in payloads.items()},
                'exporter_source': {'path': 'src/arcpuzzles/alternative_solutions.py',
                                    'sha256': file_hash(Path(__file__).resolve())},
                'counts': {'source_candidates': len(certificates), 'public_prompts': len(public),
                           'training_units': len(train), 'lesson_groups': len({r['group_id'] for r in train}),
                           'quarantined': len(quarantined)}, 'quarantined': quarantined,
                'semantics': 'Explicit alternative-answer auxiliary mode; both programs fit exact demos; '
                             'targets differ from the given answer. Not real-model repair trajectories.',
                'split_policy': 'Keep each lesson group and its source family together.',
                'training_admitted': False}
    snapshot = digest(manifest); directory = Path(directory).absolute()
    if directory.resolve() != directory: raise ValueError('Stream directory must not traverse symlinks')
    directory.mkdir(parents=True, exist_ok=True); snapshots = directory / 'snapshots'
    snapshots.mkdir(exist_ok=True)
    if snapshots.is_symlink(): raise ValueError('Snapshot directory must be local')
    final = snapshots / snapshot
    payloads['manifest.json'] = raw(manifest)
    if final.exists():
        for name, data in payloads.items():
            if _local(final, name).read_bytes() != data: raise ValueError('Existing snapshot hash/content differs')
    else:
        stage = Path(tempfile.mkdtemp(prefix='.building-', dir=snapshots))
        try:
            for name, data in payloads.items(): (stage / name).write_bytes(data)
            os.rename(stage, final)
        finally:
            if stage.exists(): shutil.rmtree(stage)
    pointer = {'schema': STREAM, 'snapshot_id': snapshot, 'manifest_sha256': digest(manifest),
               'counts': manifest['counts']}
    fd, name = tempfile.mkstemp(prefix='.CURRENT-', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as handle: handle.write(raw(pointer))
        os.replace(name, directory / 'CURRENT.json')
    finally:
        if os.path.exists(name): os.unlink(name)
    return pointer


def iter_training_rows(directory):
    """Read the current immutable snapshot; verify bytes before yielding any row."""
    directory = Path(directory).resolve(); pointer = json.loads(_local(directory, 'CURRENT.json').read_bytes())
    snapshot = pointer.get('snapshot_id', '')
    if not re.fullmatch(r'[0-9a-f]{64}', snapshot): raise ValueError('Invalid snapshot identity')
    base = directory / 'snapshots' / snapshot
    manifest_path = _local(base, 'manifest.json')
    if file_hash(manifest_path) != pointer.get('manifest_sha256'): raise ValueError('Manifest hash differs')
    manifest = json.loads(manifest_path.read_bytes())
    if manifest.get('schema') != STREAM or digest(manifest) != snapshot: raise ValueError('Snapshot hash differs')
    expected = {'public.jsonl', 'private.jsonl', 'train.jsonl', 'certificates.jsonl'}
    if set(manifest.get('files', {})) != expected: raise ValueError('Snapshot inventory differs')
    for name, sha in manifest['files'].items():
        if file_hash(_local(base, name)) != sha: raise ValueError('Artifact hash differs: ' + name)
    for line in _local(base, 'train.jsonl').read_bytes().splitlines():
        row = json.loads(line); _grid(row['target'])
        if (digest(row['prompt']) != row['prompt_id']
                or digest({'prompt_id': row['prompt_id'], 'target': row['target']}) != row['unit_id']):
            raise ValueError('Training identity differs')
        yield row


def refresh(root, directory):
    root = Path(root).resolve(); rows = []; certificates = []; quarantined = []
    paths = set()
    for pattern in ('generators/*/evidence/alternative-solutions/*.json',
                    'generators/*/workspace/parametric/evidence/alternative-solutions/*.json',
                    'generators/*/counterexamples/alternative-solutions/*.json'):
        paths.update(root.glob(pattern))
    for path in sorted(paths):
        try:
            candidate = json.loads(path.read_bytes())
            if not isinstance(candidate, dict) or candidate.get('schema') != CANDIDATE: continue
            certificate = certify(root, candidate)
            rows.extend(examples(candidate, certificate))
            certificates.append({'path': path.relative_to(root).as_posix(),
                                 'file_sha256': file_hash(path), 'candidate': candidate,
                                 'certificate': certificate})
        except (ValueError, KeyError, OSError, TypeError, AttributeError) as exc:
            quarantined.append({'path': path.relative_to(root).as_posix(), 'error': str(exc)})
    return publish(directory, rows, certificates, quarantined)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == '_verify':
        try:
            request = json.loads(Path(args[1]).read_bytes())
            print(json.dumps(_evaluate(Path(request['root']), request['candidate']), sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({'error': type(exc).__name__, 'message': str(exc)})); return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['refresh', 'inspect'])
    parser.add_argument('--library', type=Path, default=Path.cwd())
    parser.add_argument('--out', type=Path, default=Path('var/datasets/alternative-solutions'))
    options = parser.parse_args(args)
    if options.action == 'refresh': result = refresh(options.library, options.out)
    else: result = {'verified_training_units': sum(1 for _ in iter_training_rows(options.out))}
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == '__main__':
    raise SystemExit(main())
