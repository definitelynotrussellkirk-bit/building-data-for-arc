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
        return {'files': [], 'task_ids': options['task_ids']}
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


def test_source_drift_after_planning_stops_without_retry_or_canonical_fallback(accepted, tmp_path, monkeypatch):
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
    assert len(failures) == 1 and 'snapshot' in failures[0]['reason']
    assert failures[0]['retryable'] is False
    assert result['attempted_episodes'] == 1
    assert result['stop_reason']['kind'] == 'accepted_parameter_snapshot_invalid'


@pytest.mark.parametrize('change', ['adapter', 'acceptance'])
def test_actual_frozen_source_drift_stops_after_one_attempt(accepted, tmp_path, monkeypatch, change):
    catalog, tid, calls = accepted
    original = datasets.prepare_runtime
    def prepare(*args, **kwargs):
        result = original(*args, **kwargs)
        if change == 'adapter':
            (catalog.root / 'generators' / tid / 'workspace/parametric/adapter.py').write_text('# drift\n')
        else:
            p = catalog.root / 'generators' / tid / 'parametric/accepted.json'
            record = json.loads(p.read_text()); record['reason'] = 'changed acceptance bytes'
            p.write_bytes(raw(record))
        return result
    monkeypatch.setattr(datasets, 'prepare_runtime', prepare)
    result = export(accepted, tmp_path / change, max_attempts=5)
    assert result['status'] == 'incomplete'
    assert result['attempted_episodes'] == 1 and result['accepted_episodes'] == 0
    assert result['stop_reason']['task_id'] == tid and calls == []


def test_bounded_sampler_failure_remains_retryable(accepted, tmp_path, monkeypatch):
    attempts = []
    def exhaust(self, *args, **kwargs):
        attempts.append(kwargs['seed'])
        raise ValueError('bounded candidate budget exhausted')
    monkeypatch.setattr(Catalog, 'generate_parametric', exhaust)
    output = tmp_path / 'bounded'; result = export(accepted, output, max_attempts=3)
    assert len(attempts) == 3 and result['attempted_episodes'] == 3
    assert result['status'] == 'incomplete' and 'stop_reason' not in result
    assert all(row.get('retryable') is not False for row in jsonl(output / 'rejections.jsonl'))


def test_source_stop_retains_completed_rows_and_hashed_partial_manifest(accepted, tmp_path, monkeypatch):
    catalog, tid, calls = accepted; original = Catalog.generate_parametric; attempts = []
    def drift(self, *args, **kwargs):
        attempts.append(kwargs['seed'])
        if len(attempts) == 2:
            (catalog.root / 'generators' / tid / 'workspace/parametric/adapter.py').write_text('# drift\n')
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Catalog, 'generate_parametric', drift)
    output = tmp_path / 'partial'
    result = catalog.export(output, count=3, seed=17, task_ids=[tid], style='episodes',
                            accepted_parameters=True, max_attempts=9)
    assert result['status'] == 'incomplete' and result['accepted_episodes'] == 1
    assert result['attempted_episodes'] == 2 and len(attempts) == 2 and calls == []
    assert len(jsonl(output / 'public.jsonl')) == len(jsonl(output / 'episodes.private.jsonl')) == 1
    assert result['files']['public.jsonl']['sha256'] == datasets.sha256(output / 'public.jsonl')
    assert json.loads((output / 'manifest.json').read_text()) == result


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


def test_parametric_only_pool_implicitly_uses_accepted_programs(accepted, tmp_path):
    catalog, tid, _ = accepted
    output = tmp_path / 'only-parameters'
    result = catalog.export(output, count=1, seed=17, style='episodes',
                            sampling='uniform', parametric_only=True)
    assert result['status'] == 'complete'
    assert result['options']['accepted_parameters'] is True
    assert result['options']['parametric_only'] is True
    pool = json.loads((output / 'pool.private.json').read_text())
    assert [row['id'] for row in pool['generators']] == [tid]
    episode, = jsonl(output / 'episodes.private.jsonl')
    assert episode['parametric']['family'] == tid
    assert len(episode['train']) == 2 and len(episode['test']) == 4
    assert datasets.verify_dataset(output) == result


def test_parametric_only_refuses_explicit_canonical_ids(accepted, tmp_path):
    catalog, tid, _ = accepted
    output = tmp_path / 'canonical-not-requested'
    with pytest.raises(ValueError, match='accepted parametric'):
        catalog.export(output, count=1, task_ids=[tid, 'aaaa00000002'],
                       parametric_only=True)
    assert not output.exists()


@pytest.mark.parametrize('mutation', ['missing', 'stale'])
def test_parametric_only_cannot_fall_back_when_acceptance_is_unavailable(accepted, tmp_path, mutation):
    catalog, tid, _ = accepted
    if mutation == 'missing':
        (catalog.root / 'generators' / tid / 'parametric/accepted.json').unlink()
    else:
        (catalog.root / 'generators' / tid / 'workspace/parametric/adapter.py').write_text('# changed\n')
    output = tmp_path / 'unavailable'
    with pytest.raises(ValueError, match='accepted parametric|accepted parameter'):
        catalog.export(output, count=1, parametric_only=True)
    assert not output.exists()


@pytest.mark.parametrize('value', [1, 'yes'])
def test_parametric_only_requires_a_boolean(accepted, tmp_path, value):
    output = tmp_path / 'invalid-only-option'
    with pytest.raises(ValueError, match='parametric_only'):
        accepted[0].export(output, count=1, parametric_only=value)
    assert not output.exists()


@pytest.mark.parametrize('claimed', [True, 1, 'yes'])
def test_verifier_refuses_rehashed_canonical_export_claiming_parametric_only(accepted, tmp_path, claimed):
    output = tmp_path / 'forged-only-option'
    accepted[0].export(output, count=1, seed=17, task_ids=['aaaa00000002'],
                       accepted_parameters=True)
    path = output / 'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['options']['parametric_only'] = claimed
    path.write_bytes(raw(manifest))
    resign(output)
    with pytest.raises(ValueError, match='parametric.only|canonical.only'):
        datasets.verify_dataset(output)


def test_cli_parametric_only_exports_the_accepted_pool(accepted, tmp_path):
    from arcpuzzles.cli import main
    output = tmp_path / 'cli-accepted-only'
    result = main(['--library', str(accepted[0].root), 'export', '--count', '1',
                   '--parametric-only', '--out', str(output)])
    assert result == 0
    episode, = jsonl(output / 'episodes.private.jsonl')
    assert episode['parametric']['family'] == accepted[1]
    assert len(episode['test']) == 4


def test_parametric_only_uses_two_demos_for_a_legacy_one_demo_contract(accepted, tmp_path):
    catalog, tid, _ = accepted
    path = catalog.root / 'generators' / tid / 'workspace/parametric/promotion.json'
    contract = json.loads(path.read_text())
    contract['limits']['demos'][0] = 1
    path.write_bytes(raw(contract))
    qualification = promotion.qualify(catalog, tid, tmp_path / 'one-demo-qualification')
    promotion.accept(catalog, tid, Path(qualification['receipt']), reason='Synthetic legacy minimum fixture')
    output = tmp_path / 'legacy-minimum'
    catalog.export(output, count=1, task_ids=[tid], parametric_only=True)
    episode, = jsonl(output / 'episodes.private.jsonl')
    assert len(episode['train']) == 2
    assert len(episode['test']) == 4
    assert datasets.verify_dataset(output)['status'] == 'complete'


@pytest.mark.parametrize('count', [1, 7])
def test_parametric_only_training_context_rejects_out_of_policy_demo_count(accepted, tmp_path, count):
    output = tmp_path / 'wrong-demo-count'
    with pytest.raises(ValueError, match='2.*6'):
        accepted[0].export(output, count=1, parametric_only=True, n_train=count)
    assert not output.exists()


@pytest.mark.parametrize('mixed', [False, True])
def test_only_mode_requires_every_published_episode_to_have_parameter_evidence(accepted, tmp_path, mixed):
    catalog, tid, _ = accepted
    output = tmp_path / 'hidden-canonical-episode'
    ids = [tid, 'aaaa00000002'] if mixed else ['aaaa00000002']
    result = catalog.export(output, count=2 if mixed else 1, seed=1,
                            task_ids=ids, style='episodes', sampling='uniform',
                            n_train=2, n_test=4, accepted_parameters=True)
    assert result['status'] == 'complete'
    published = jsonl(output / 'labels.private.jsonl')
    assert 'aaaa00000002' in {row['task_id'] for row in published}
    episodes = [row for row in jsonl(output / 'episodes.private.jsonl') if 'parametric' in row]
    assert bool(episodes) is mixed
    (output / 'episodes.private.jsonl').write_bytes(b''.join(raw(row) for row in episodes))
    path = output / 'pool.private.json'
    pool = json.loads(path.read_text())
    pool['generators'] = [row for row in pool['generators'] if row['id'] == tid]
    path.write_bytes(raw(pool))
    path = output / 'manifest.json'
    manifest = json.loads(path.read_text()); manifest['options']['parametric_only'] = True
    path.write_bytes(raw(manifest)); resign(output)
    with pytest.raises(ValueError, match='Parametric-only|parametric.only'):
        datasets.verify_dataset(output)


def test_only_mode_keeps_valid_generation_evidence_after_a_failed_render(accepted, tmp_path, monkeypatch):
    catalog, tid, _ = accepted
    original = datasets.run_process
    first = True
    def fail_first_render(*args, **kwargs):
        nonlocal first
        if first:
            first = False
            return {'exit_code': 1, 'timed_out': False, 'stdout': '',
                    'stderr': 'synthetic render interruption'}
        return original(*args, **kwargs)
    monkeypatch.setattr(datasets, 'run_process', fail_first_render)
    output = tmp_path / 'retried-render'
    result = catalog.export(output, count=1, seed=17, task_ids=[tid],
                            style='episodes', parametric_only=True, max_attempts=4)
    assert result['status'] == 'complete'
    assert len(jsonl(output / 'episodes.private.jsonl')) > len(jsonl(output / 'public.jsonl'))
    assert datasets.verify_dataset(output) == result


@pytest.fixture
def two_accepted(accepted, tmp_path):
    """Two real acceptance records, using the fixture's synthetic worker only."""
    import shutil
    catalog, first, _ = accepted
    second = 'aaaa00000002'
    base = catalog.root / 'generators'
    home = base / second / 'workspace/parametric'
    shutil.copytree(base / first / 'workspace/parametric', home)
    path = home / 'promotion.json'; contract = json.loads(path.read_text())
    contract['adapter'] = f'generators/{second}/workspace/parametric/adapter.py'
    path.write_bytes(raw(contract))
    path = home / 'evidence/manifest.json'; manifest = json.loads(path.read_text())
    manifest.update(task_id=second, generator_sha256=catalog.describe(second)['generator_sha256'])
    manifest['files'] = [{'path': contract['adapter'], 'sha256': datasets.sha256(home / 'adapter.py')}]
    path.write_bytes(raw(manifest))
    result = promotion.qualify(catalog, second, tmp_path / 'second-qualification')
    promotion.accept(catalog, second, Path(result['receipt']), reason='Synthetic second-family fixture')
    return catalog, first, second


def test_only_mode_checks_draw_reachable_sources_without_blocking_on_unused_stale_candidates(two_accepted, tmp_path):
    catalog, first, second = two_accepted
    (catalog.root / f'generators/{second}/workspace/parametric/adapter.py').write_text('# stale\n')
    output = tmp_path / 'bounded-plan'
    result = catalog.export(output, count=1, max_attempts=1, seed=1,
                            parametric_only=True, style='episodes', sampling='uniform')
    assert result['status'] == 'complete'
    assert [e['task_id'] for e in jsonl(output / 'episodes.private.jsonl')] == [first]
    pool = json.loads((output / 'pool.private.json').read_text())['generators']
    assert {row['id'] for row in pool} == {first, second}
    scope = result['options']['parametric_preflight']
    assert scope['checked_tasks'] == scope['runtime_tasks'] == [first]
    assert datasets.verify_dataset(output) == result


def test_only_mode_checks_every_explicit_source_even_when_not_drawn(two_accepted, tmp_path):
    catalog, first, second = two_accepted
    (catalog.root / f'generators/{second}/workspace/parametric/adapter.py').write_text('# stale\n')
    output = tmp_path / 'explicit-stale'
    with pytest.raises(ValueError, match='stale|unavailable'):
        catalog.export(output, count=1, max_attempts=1, seed=1, task_ids=[first, second],
                       parametric_only=True, sampling='uniform')
    assert not output.exists()


def test_only_mode_refuses_acceptance_disappearing_between_discovery_and_freeze(accepted, tmp_path, monkeypatch):
    from arcpuzzles import inline_parametric
    catalog, tid, calls = accepted
    original = inline_parametric.plan
    def remove_acceptance(*args, **kwargs):
        promotion._acceptance_path(catalog, tid).unlink()
        return original(*args, **kwargs)
    monkeypatch.setattr(inline_parametric, 'plan', remove_acceptance)
    output = tmp_path / 'disappeared-acceptance'
    with pytest.raises(ValueError, match='acceptance|snapshot'):
        catalog.export(output, count=1, parametric_only=True)
    assert not output.exists() and calls == []


@pytest.mark.parametrize('mutation', ['missing-draw', 'invented-source', 'wrong-seed', 'runtime-scope'])
def test_only_mode_rejects_rehashed_preflight_scope_or_draw_tampering(two_accepted, tmp_path, mutation):
    catalog, _, _ = two_accepted
    output = tmp_path / mutation
    catalog.export(output, count=1, max_attempts=1, seed=1, parametric_only=True, sampling='uniform')
    path = output / 'manifest.json'; manifest = json.loads(path.read_text())
    scope = manifest['options']['parametric_preflight']
    if mutation == 'missing-draw': scope['checked_tasks'] = []
    if mutation == 'invented-source': scope['checked_tasks'].append('not-in-pool')
    if mutation == 'runtime-scope': scope['runtime_tasks'] = []
    if mutation == 'wrong-seed':
        draws = jsonl(output / 'draws.private.jsonl'); draws[0]['seed'] += 1
        (output / 'draws.private.jsonl').write_bytes(b''.join(raw(row) for row in draws))
    path.write_bytes(raw(manifest)); resign(output)
    with pytest.raises(ValueError, match='preflight|draw'):
        datasets.verify_dataset(output)


def test_query_presentation_materializes_bank_before_selecting_prefix(accepted, tmp_path):
    """Generating only one source query would change this prompt or its receipt."""
    one, four = tmp_path / 'one-query', tmp_path / 'four-queries'
    export(accepted, one, n_test=1)
    export(accepted, four, n_test=4)
    short = jsonl(one / 'episodes.private.jsonl')[0]
    full = jsonl(four / 'episodes.private.jsonl')[0]
    assert short['query_presentation']['source_queries'] == full['query_presentation']['source_queries']
    assert len(short['query_presentation']['source_queries']) == 4
    assert short['test'] == full['test'][:1]
    assert short['provenance']['demo_only_certificate']['counts']['queries'] == 4
    from arcpuzzles.query_presentation import iter_public_turns
    assert list(iter_public_turns(short)) == list(iter_public_turns(full, limit=1))
    order = full['query_presentation']['source_indices']
    assert sorted(order) == [0, 1, 2, 3]
    assert full['test'] == [full['query_presentation']['source_queries'][i] for i in order]
    assert jsonl(four / 'labels.private.jsonl')[0]['test_outputs'] == [p['output'] for p in full['test']]
    assert datasets.verify_dataset(one)['status'] == 'complete'
    assert datasets.verify_dataset(four)['status'] == 'complete'


@pytest.mark.parametrize('field', ['source_indices', 'source_queries', 'selected_count', 'seed', 'source_episode_id'])
def test_rehashed_presentation_tampering_is_rejected(accepted, tmp_path, field):
    output = tmp_path / field
    export(accepted, output, n_test=1)
    episode = jsonl(output / 'episodes.private.jsonl')[0]
    record = episode['query_presentation']
    if field == 'source_indices': record[field].reverse()
    if field == 'source_queries': record[field][-1]['input'] = [[9, 9]]
    if field == 'selected_count': record[field] = 2
    if field == 'seed': record[field] += 1
    if field == 'source_episode_id': record[field] = '0' * 64
    (output / 'episodes.private.jsonl').write_bytes(raw(episode))
    resign(output)
    with pytest.raises(ValueError):
        datasets.verify_dataset(output)


def test_legacy_inline_episode_without_presentation_remains_readable(accepted, tmp_path):
    output = tmp_path / 'legacy-inline'
    export(accepted, output, n_test=4)
    manifest = json.loads((output / 'manifest.json').read_bytes())
    del manifest['options']['query_presentation_schema']
    (output / 'manifest.json').write_bytes(raw(manifest))
    (output / 'plan.json').write_bytes(raw(manifest['options']))
    episode = jsonl(output / 'episodes.private.jsonl')[0]
    episode['test'] = episode.pop('query_presentation')['source_queries']
    episode['episode_id'] = datasets.public_episode(episode)['episode_id']
    (output / 'episodes.private.jsonl').write_bytes(raw(episode))
    (output / 'public.jsonl').write_bytes(raw(datasets.public_episode(episode)))
    for name in ('labels.private.jsonl', 'lineage.private.jsonl', 'data.private.jsonl'):
        rows = jsonl(output / name)
        for row in rows:
            row['episode_id'] = episode['episode_id']
            if name == 'labels.private.jsonl':
                row['test_outputs'] = [pair['output'] for pair in episode['test']]
        (output / name).write_bytes(b''.join(raw(row) for row in rows))
    resign(output)
    assert datasets.verify_dataset(output)['status'] == 'complete'


def test_new_four_query_export_cannot_drop_presentation_record(accepted, tmp_path):
    output = tmp_path / 'missing-presentation'
    export(accepted, output, n_test=4)
    episode = jsonl(output / 'episodes.private.jsonl')[0]
    del episode['query_presentation']
    (output / 'episodes.private.jsonl').write_bytes(raw(episode))
    resign(output)
    with pytest.raises(ValueError, match='presentation'):
        datasets.verify_dataset(output)
