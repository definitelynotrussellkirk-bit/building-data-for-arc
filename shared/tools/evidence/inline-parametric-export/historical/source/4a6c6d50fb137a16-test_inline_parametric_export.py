"""Exporter boundaries with synthetic worker evidence; real Racket smoke is separate."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog, datasets, parametric_promotion as promotion
from arcpuzzles.catalog import jsonl
from arcpuzzles.cli import parser


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'


@pytest.fixture
def accepted(library, monkeypatch, tmp_path):
    tid = 'aaaa00000001'; home = library / 'generators' / tid / 'workspace/parametric'
    home.mkdir(parents=True); (home / 'adapter.py').write_text('# synthetic interface fixture\n')
    (home / 'promotion.json').write_bytes(raw({
        'schema': promotion.CONTRACT, 'adapter': f'generators/{tid}/workspace/parametric/adapter.py',
        'parameters': {'side': ['left', 'right']}, 'default': {'side': 'left'},
        'limits': {'demos': [2, 8], 'queries': [1, 8]}}))
    row = Catalog(library).describe(tid); p = home / 'evidence/manifest.json'; p.parent.mkdir()
    p.write_bytes(raw({'task_id': tid, 'generator_sha256': row['generator_sha256'],
        'canonical_rule_hash': row['rule_hash'], 'verification_status': 'reviewer_reported',
        'files': [{'path': (home / 'adapter.py').relative_to(library).as_posix(),
                   'sha256': datasets.sha256(home / 'adapter.py')}]}))

    def execute(catalog, task_id, contract, jobs, timeout):
        episodes, checks = [], []
        for j in jobs:
            program = '(rule! g)' if j['settings']['side'] == 'left' else '(rule! (flip-lr g))'
            pairs = [{'input': [[i % 10, i // 10, j['seed'] % 10]], 'output': [[i % 10]]}
                     for i in range(j['demos'] + j['queries'])]
            episodes.append({'task_id': task_id, 'seed': j['seed'], 'settings': j['settings'],
                'train': pairs[:j['demos']], 'test': pairs[j['demos']:], 'program': program,
                'program_sha256': hashlib.sha256(program.encode()).hexdigest(),
                'reference': 'accepted_parametric'})
            checks.append({'seed': j['seed'], 'settings': j['settings'],
                'counts': {'demos': j['demos'], 'queries': j['queries']},
                'survivors': [j['settings']], 'label_count': len(pairs)})
        return {'episodes': episodes, 'checks': checks, 'racket': {'backend': 'racket', 'protected': True},
                'racket_evaluations': sum(j['demos'] + j['queries'] for j in jobs)}
    monkeypatch.setattr(promotion, '_execute', execute)
    catalog = Catalog(library)
    q = promotion.qualify(catalog, tid, tmp_path / 'qualification')
    promotion.accept(catalog, tid, Path(q['receipt']), reason='Synthetic interface fixture only')

    def prepare(catalog, stage, **options):
        target = stage / 'data/canonical/puzzles.jsonl'; target.parent.mkdir(parents=True)
        target.write_bytes((library / 'shared/data/canonical/puzzles.jsonl').read_bytes())
        return {'files': []}
    monkeypatch.setattr(datasets, 'prepare_runtime', prepare)
    monkeypatch.setattr(datasets, 'demonstration_policy', lambda stage, row, n, **kw: {
        'automatic': n is None, 'declared_minimum': 2, 'resolved_n_train': n or 4})
    calls = []
    def canonical(stage, row, **options):
        calls.append(row['id']); n = options['n_train'] or 4
        pairs = [{'input': [[i]], 'output': [[i]]} for i in range(n + options['n_test'])]
        return [{'task_id': row['id'], 'seed': options['seed'], 'program': '(rule! g)',
                 'train': pairs[:n], 'test': pairs[n:], 'rejections': [],
                 'provenance': {'generator_sha256': row['generator_sha256'], 'approved': True}}]
    monkeypatch.setattr(datasets, 'generate_in_runtime', canonical)
    def render(args, stage, **options):
        request = json.loads((stage / 'export_request.json').read_text()); e = request['episode']
        item = {'episode_id': datasets.public_episode(e)['episode_id'],
                'program': e['program'], 'source_provenance': e['provenance']}
        (stage / 'export_result.json').write_bytes(raw({'rows': [item], 'diagnostics': {}}))
        return {'exit_code': 0, 'timed_out': False}
    monkeypatch.setattr(datasets, 'run_process', render)
    return catalog, tid, calls


def export(accepted, output, **options):
    catalog, tid, _ = accepted
    return catalog.export(output, count=1, seed=17, task_ids=[tid], style='episodes',
                          accepted_parameters=True, **options)


def test_cli_exposes_opt_in_without_changing_default():
    base = ['export', '--count', '1', '--out', 'new-output']
    assert parser().parse_args(base).accepted_parameters is False
    assert parser().parse_args(base + ['--accepted-parameters']).accepted_parameters is True


def test_opt_in_emits_frozen_accepted_episode_with_own_program_identity(accepted, tmp_path):
    output = tmp_path / 'inline'; result = export(accepted, output, n_test=4)
    assert result['status'] == 'complete' and accepted[2] == []
    episode, = jsonl(output / 'episodes.private.jsonl'); public, = jsonl(output / 'public.jsonl')
    assert len(episode['train']) == 2 and len(episode['test']) == 4
    assert episode['parametric']['family'] == accepted[1]
    assert episode['parametric']['source_sha256'] == episode['provenance']['generator_sha256']
    assert episode['executed_rule_hash'] == hashlib.sha256(' '.join(episode['program'].split()).encode()).hexdigest()[:12]
    assert episode['training_admitted'] is False and episode['parametric_accepted'] is True
    assert set(public) == {'episode_id', 'train', 'test'}
    assert all(set(p) == {'input'} for p in public['test'])
    assert public['episode_id'] == episode['episode_id']
    changed = deepcopy(episode); changed['seed'] += 1; changed['parametric']['acceptance_sha256'] = 'private-change'
    changed['test'][0]['output'] = [[9]]; changed['program'] = 'private-program-change'
    assert datasets.public_episode(changed) == public
    assert datasets.verify_dataset(output) == result


def test_default_and_families_without_acceptance_keep_canonical_generation(accepted, tmp_path):
    catalog, tid, calls = accepted
    options = dict(count=1, task_ids=[tid], seed=17, style='episodes', n_train=2, n_test=2)
    catalog.export(tmp_path / 'old', **options)
    catalog.export(tmp_path / 'explicit-false', accepted_parameters=False, **options)
    assert calls == [tid, tid]
    assert (tmp_path / 'old/public.jsonl').read_bytes() == (tmp_path / 'explicit-false/public.jsonl').read_bytes()
    catalog.export(tmp_path / 'no-family', accepted_parameters=True, **dict(options, task_ids=['aaaa00000002']))
    assert calls[-1] == 'aaaa00000002'
    assert 'parametric' not in jsonl(tmp_path / 'no-family/episodes.private.jsonl')[0]


@pytest.mark.parametrize('options', [
    {'accepted_parameters': 1}, {'accepted_parameters': 'yes'},
    {'reference': 'archival', 'allow_unapproved': True}, {'style': 'synthpipe'},
    {'difficulty': 'hard'}, {'n_train': 1}, {'n_test': 9},
])
def test_unsupported_combinations_fail_before_output_creation(accepted, tmp_path, options):
    catalog, tid, _ = accepted; output = tmp_path / 'invalid'
    request = dict(count=1, task_ids=[tid], accepted_parameters=True)
    request.update(options)
    with pytest.raises(ValueError):
        catalog.export(output, **request)
    assert not output.exists()


def test_stale_acceptance_fails_before_output_instead_of_falling_back(accepted, tmp_path):
    catalog, tid, calls = accepted
    (catalog.root / 'generators' / tid / 'workspace/parametric/adapter.py').write_text('# changed\n')
    with pytest.raises(ValueError, match='accepted|changed|stale'):
        export(accepted, tmp_path / 'stale')
    assert not (tmp_path / 'stale').exists() and calls == []


def test_source_drift_after_planning_is_a_rejection_not_canonical_fallback(accepted, tmp_path, monkeypatch):
    original = Catalog.generate_parametric
    def drift(self, *args, **kwargs):
        episodes = original(self, *args, **kwargs)
        episodes[0]['provenance']['parametric_acceptance_sha256'] = 'f' * 64
        return episodes
    monkeypatch.setattr(Catalog, 'generate_parametric', drift)
    output = tmp_path / 'drift'; result = export(accepted, output, max_attempts=2)
    assert result['status'] == 'incomplete' and result['accepted_episodes'] == 0
    assert accepted[2] == [] and not jsonl(output / 'episodes.private.jsonl')
    failures = jsonl(output / 'rejections.jsonl')
    assert len(failures) == 2 and all('snapshot' in row['reason'] for row in failures)


def test_mixed_export_rejects_same_visible_challenge_with_different_private_answers(accepted, tmp_path, monkeypatch):
    catalog, tid, _ = accepted; output = tmp_path / 'visible-conflict'
    def conflicting(stage, row, **options):
        previous, = jsonl(output / 'episodes.private.jsonl')
        result = {key: deepcopy(previous[key]) for key in ('train', 'test', 'program')}
        for pair in result['test']: pair['output'] = [[9]]
        result.update(task_id=row['id'], seed=options['seed'], rejections=[],
                      provenance={'generator_sha256': row['generator_sha256'], 'approved': True})
        return [result]
    monkeypatch.setattr(datasets, 'generate_in_runtime', conflicting)
    # Seed1 selects the accepted family first and canonical peer second.
    result = catalog.export(output, count=2, seed=1, task_ids=[tid, 'aaaa00000002'],
                            style='episodes', sampling='uniform', n_train=2, n_test=4,
                            max_attempts=2, accepted_parameters=True)
    assert result['status'] == 'incomplete' and result['accepted_episodes'] == 1
    assert len(jsonl(output / 'episodes.private.jsonl')) == 1
    assert 'Duplicate' in jsonl(output / 'rejections.jsonl')[-1]['reason']


def resign(output):
    path = output / 'manifest.json'; m = json.loads(path.read_text())
    for name, item in m['files'].items():
        p = output / name; item.update(sha256=datasets.sha256(p), bytes=p.stat().st_size)
    m['dataset_id'] = datasets._identity({k: v for k, v in m.items() if k != 'dataset_id'})
    path.write_bytes(raw(m))


@pytest.mark.parametrize('mutation', ['program', 'executed-hash', 'settings', 'acceptance',
                                     'source', 'boolean-label', 'private-provenance', 'public-query'])
def test_serialized_verifier_rejects_rehashed_binding_tampering(accepted, tmp_path, mutation):
    output = tmp_path / mutation; export(accepted, output, n_test=4)
    path = output / 'episodes.private.jsonl'; e, = jsonl(path)
    if mutation == 'program': e['program'] = '(rule! (flip-ud g))'
    if mutation == 'executed-hash': e['executed_rule_hash'] = 'f' * 12
    if mutation == 'settings': e['parametric']['settings'] = {'side': 'unknown'}
    if mutation == 'acceptance': e['parametric']['acceptance_sha256'] = 'f' * 64
    if mutation == 'source': e['parametric']['source_sha256'] = 'f' * 64
    if mutation == 'boolean-label': e['test'][0]['output'] = [[False]]
    path.write_bytes(raw(e))
    if mutation == 'private-provenance':
        path = output / 'labels.private.jsonl'; row, = jsonl(path); row['provenance']['parametric']['source_sha256'] = 'f' * 64; path.write_bytes(raw(row))
    if mutation == 'public-query':
        path = output / 'public.jsonl'; row, = jsonl(path); row['test'][0]['input'] = [[9]]; path.write_bytes(raw(row))
    resign(output)
    with pytest.raises(ValueError): datasets.verify_dataset(output)


@pytest.mark.parametrize('mutation', ['no-metadata', 'no-episode', 'disabled-option', 'integer-option',
                                     'certificate-seed', 'reference', 'runtime', 'duplicate-input',
                                     'request-counts', 'float-seed', 'top-settings'])
def test_coordinated_tampering_cannot_strip_admission_or_request_contract(accepted, tmp_path, mutation):
    output = tmp_path / mutation; export(accepted, output, n_test=4)
    e, = jsonl(output / 'episodes.private.jsonl')
    if mutation == 'no-metadata': del e['parametric']
    if mutation == 'certificate-seed': e['provenance']['demo_only_certificate']['seed'] += 1
    if mutation == 'reference': e['provenance']['reference'] = 'canonical'
    if mutation == 'runtime': e['provenance']['racket_runtime'] = {'backend': 'test', 'protected': False}
    if mutation == 'float-seed':
        e['seed'] = 1.0; e['provenance']['demo_only_certificate']['seed'] = 1
    if mutation == 'top-settings':
        e['settings']['side'] = 'right' if e['settings']['side'] == 'left' else 'left'
    if mutation == 'duplicate-input': e['test'][0]['input'] = deepcopy(e['train'][0]['input'])
    if mutation == 'request-counts':
        e['test'].pop(); c = e['provenance']['demo_only_certificate']
        c['label_count'] -= 1; c['counts']['queries'] -= 1
    if mutation != 'no-metadata':
        e['episode_id'] = datasets.public_episode(e)['episode_id']
        (output / 'public.jsonl').write_bytes(raw(datasets.public_episode(e)))
    labels, = jsonl(output / 'labels.private.jsonl')
    labels.update(episode_id=e['episode_id'], seed=e['seed'], provenance=e['provenance'],
                  test_outputs=[p['output'] for p in e['test']])
    (output / 'labels.private.jsonl').write_bytes(raw(labels))
    rows = jsonl(output / 'data.private.jsonl')
    for row in rows: row.update(episode_id=e['episode_id'], source_provenance=e['provenance'])
    (output / 'data.private.jsonl').write_bytes(b''.join(raw(row) for row in rows))
    (output / 'episodes.private.jsonl').write_bytes(b'' if mutation == 'no-episode' else raw(e))
    if mutation in {'disabled-option', 'integer-option'}:
        p = output / 'manifest.json'; m = json.loads(p.read_text())
        m['options']['accepted_parameters'] = False if mutation == 'disabled-option' else 1
        p.write_bytes(raw(m))
    resign(output)
    with pytest.raises(ValueError): datasets.verify_dataset(output)
