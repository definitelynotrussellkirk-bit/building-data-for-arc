"""Trusted maintainer probe, copied into a fresh read-confined checkout."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def _grid(value):
    return (type(value) is list and 1 <= len(value) <= 30 and type(value[0]) is list
            and 1 <= len(value[0]) <= 30 and all(type(row) is list and len(row) == len(value[0])
            and all(type(x) is int and 0 <= x <= 9 for x in row) for row in value))


def check_episode(episode, task_id, source, demos, queries, *, seed):
    if (episode.get('task_id') != task_id or type(episode.get('seed')) is not int or episode['seed'] != seed
            or episode.get('executed_rule_hash') != source['rule_hash']
            or episode.get('provenance', {}).get('generator_sha256') != source['generator_sha256']
            or len(episode.get('train', [])) != demos or len(episode.get('test', [])) != queries):
        raise ValueError('Generated episode identity or requested counts differ')
    pairs = episode['train'] + episode['test']
    if any(not _grid(p.get('input')) or not _grid(p.get('output')) for p in pairs):
        raise ValueError('Generated grids need exact integer cells and rectangular 1..30 dimensions')
    if len({_json(pair['input']) for pair in pairs}) != len(pairs):
        raise ValueError('Generated episode repeats a visible input')
    return {'demonstrations': demos, 'queries': queries, 'distinct_inputs': len(pairs),
            'generator_sha256': source['generator_sha256'], 'executed_rule_hash': source['rule_hash']}


def main(config_path):
    root = Path(__file__).resolve().parent;config = json.loads(Path(config_path).read_text())
    if Path(sys.prefix).resolve() != root / 'venv' or sys.prefix == sys.base_prefix:
        raise ValueError('The probe must use its own fresh virtual environment')
    checkout = root / 'checkout';work = checkout / 'WORK';repo = work / 'repo'
    sys.path.insert(0, str(root))
    from review_packet_verify_process import run_command
    env = dict(os.environ);fake = root / 'fake-host';fake.mkdir()
    binary = fake / 'racket';binary.write_text('#!/bin/sh\nexit 97\n');binary.chmod(0o755)
    env['PATH'] = str(fake) + os.pathsep + env['PATH']
    records = []
    def run(name, args):
        row = run_command([sys.executable, str(checkout / 'review.py'), *args],
            cwd=checkout, env=env, timeout=config['timeout'], log_root=root / 'logs', name=name)
        records.append(row);(root / 'probe-progress.json').write_text(json.dumps(records, indent=2) + '\n')
        if row['exit_code'] != 0 or row['failure']:
            raise RuntimeError('Packet command failed: ' + name + '; see retained command logs')
        return Path(row['stdout']['path']).read_text()
    run('verify', ['verify'])
    sys.path.insert(0, str(repo / 'src'))
    from arcpuzzles.review_full_draw import draw_main
    manifest = json.loads((work / 'PACKET-MANIFEST.json').read_bytes())
    if hashlib.sha256((work / 'PACKET-MANIFEST.json').read_bytes()).hexdigest() != config['packet_id']:
        raise ValueError('Cold manifest identity differs')
    draw_main(work, hashlib.sha256(('packet-verify:' + str(config['seed'])).encode()).digest())
    run('start', ['start']);run('duties', ['duties'])
    setup = json.loads(run('setup', ['setup']))
    expected_binary = work / '.review/racket-runtime/racket/bin/racket'
    if Path(setup['racket']).resolve() != expected_binary.resolve():
        raise ValueError('The supplied offline Racket must be selected instead of the host runtime')
    version = run('racket-version', ['run', 'racket', '--version']).strip()
    if '8.10' not in version:raise ValueError('Unexpected bundled Racket version')
    stats = json.loads(run('stats', ['run', sys.executable, '-m', 'arcpuzzles', 'stats']))
    executable_count = sum(row.get('job_kind') != 'public_eval_creation' or row.get('catalog_present', False) for row in manifest['generators'].values())
    if stats['generators'] != executable_count:raise ValueError('Cold catalog size differs')
    task_id = config['task_id'];output = work / 'checks/packet-verification';output.mkdir(parents=True);(output / 'private').mkdir();(output / 'public').mkdir()
    args = ['run', sys.executable, '-m', 'arcpuzzles', 'generate', task_id, '--count', '1',
            '--seed', str(config['seed']), '--train', str(config['demos']), '--test', str(config['queries']),
            '--timeout', str(config['timeout']), '--out', '../checks/packet-verification/private/episode.jsonl']
    if config['allow_unapproved']:args.append('--allow-unapproved')
    run('generate', args)
    lines = (output / 'private/episode.jsonl').read_text().splitlines()
    if len(lines) != 1:raise ValueError('Expected exactly one generated episode')
    episode = json.loads(lines[0]);source = manifest['generators'][task_id]
    proof = check_episode(episode, task_id, source, config['demos'], config['queries'], seed=config['seed'])
    pairs = episode['train'] + episode['test']
    (output / 'private/inputs.json').write_text(json.dumps({'inputs': [p['input'] for p in pairs]}))
    run('reference-replay', ['run', sys.executable, '-m', 'arcpuzzles', 'apply', task_id,
        '--input', '../checks/packet-verification/private/inputs.json', '--timeout', str(config['timeout']),
        '--out', '../checks/packet-verification/private/reference.json'])
    reference = json.loads((output / 'private/reference.json').read_text())
    if (reference['generator_sha256'] != source['generator_sha256']
            or reference['executed_rule_hash'] != source['rule_hash']
            or reference['rule_hash_matches_catalog'] is not True or len(reference['results']) != len(pairs)
            or any(r['error'] is not None or r.get('valid_output') is not True or _json(r['output']) != _json(p['output'])
                   for r, p in zip(reference['results'], pairs))):
        raise ValueError('Independent reference API replay disagrees with generated labels')
    # Use the packet's helper, under the same confined, independent environment.
    sys.path.insert(0, str(repo / 'shared/runtime'))
    from reviewer_support import public_challenge_bytes, public_challenge_id
    raw = public_challenge_bytes(episode);public = json.loads(raw)
    if (set(public) != {'train', 'test'} or any(set(p) != {'input', 'output'} for p in public['train'])
            or any(set(p) != {'input'} for p in public['test'])):
        raise ValueError('Public challenge contains private metadata or query answers')
    altered = json.loads(json.dumps(episode));altered['seed'] = 'private';altered['program'] = 'private'
    altered['settings'] = {'hidden': 'changed'};altered['provenance'] = {'private': 'changed'}
    for pair in altered['test']:pair['output'] = [[9]]
    if public_challenge_bytes(altered) != raw or public_challenge_id(episode) != hashlib.sha256(raw).hexdigest():
        raise ValueError('Public identity depends on hidden metadata or differs from exact bytes')
    public_id = hashlib.sha256(raw).hexdigest();(output / 'public' / (public_id + '.json')).write_bytes(raw)
    proof.update(reference_labels_replayed=len(pairs), public_query_answers_omitted=True,
                 visible_only_public_id=public_id, retained_artifacts={'private_episode':'artifacts/private/episode.jsonl', 'reference_replay':'artifacts/private/reference.json', 'public_challenge':'artifacts/public/' + public_id + '.json'})
    accepted = None
    if config['accepted_family']:
        family = config['accepted_family']
        run('accepted-export', ['run', sys.executable, '-m', 'arcpuzzles', 'export', '--approved', '--id', family,
            '--accepted-parameters', '--style', 'episodes', '--sampling', 'uniform', '--count', '2',
            '--seed', str(config['seed']), '--train', str(config['demos']), '--test', str(config['queries']),
            '--timeout', str(config['timeout']), '--out', '../checks/packet-verification/accepted-export'])
        run('accepted-inspect', ['run', sys.executable, '-m', 'arcpuzzles', 'inspect-export',
                                '../checks/packet-verification/accepted-export'])
        rows = [json.loads(line) for line in (output / 'accepted-export/episodes.private.jsonl').read_text().splitlines()]
        if (len(rows) != 2 or any('parametric' not in e or e['task_id'] != family
                or len(e['train']) != config['demos'] or len(e['test']) != config['queries']
                or e.get('training_admitted') is not False for e in rows)):
            raise ValueError('Accepted-family export fell back or its counts/admission metadata differ')
        accepted = {'family': family, 'episodes': 2, 'queries': 2 * config['queries'],
                    'executed_rule_hashes': sorted({e['executed_rule_hash'] for e in rows}),
                    'settings': [e['parametric']['settings'] for e in rows], 'training_admitted': False}
    with expected_binary.open('rb') as f:racket_sha = hashlib.file_digest(f, 'sha256').hexdigest()
    result = {'status': 'passed', 'packet_id': config['packet_id'], 'catalog_generators': stats['generators'],
              'racket': {'version': version, 'binary_sha256': racket_sha, 'bundled_runtime_selected': True},
              'episode': proof, 'accepted_export': accepted, 'commands': records,
              'source_reads_confined': True, 'training_admitted': False,
              'scope': 'One generated episode and reference replay, not all generators or semantic uniqueness.'}
    (root / 'probe-result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
