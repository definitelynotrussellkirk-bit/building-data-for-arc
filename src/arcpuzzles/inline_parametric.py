"""Accepted-family draws in the standard dataset format; no training admission."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

from .catalog import local_path, sha256, jsonl
from .runtime import validate_grid
from .query_presentation import SCHEMA as PRESENTATION_SCHEMA, present_queries, verify_presentation
from . import parametric_promotion as promotion


class AcceptedSnapshotError(ValueError):
    """The frozen accepted-family plan cannot be used for another draw."""


def _key(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def public_identity(episode):
    # Same exact canonical challenge bytes as the opt-in standalone exporter.
    return promotion._hash(promotion._public(episode))


def _demo_count(limits, requested, *, parametric_only=False):
    count = limits['demos'][0] if requested is None else requested
    if parametric_only and requested is None:
        count = max(2, count)
    if type(count) is not int:
        raise ValueError('Demonstration count must be an integer')
    if parametric_only and not 2 <= count <= 6:
        raise ValueError('Parametric-only exports require 2 to 6 demonstrations')
    if not limits['demos'][0] <= count <= limits['demos'][1]:
        raise ValueError('Demonstration count is outside the accepted parameter limits')
    return count


def _record(record, tid):
    """Validate a frozen declaration; this does not establish current source."""
    if (type(record) is not dict or record.get('schema') != promotion.ACCEPTANCE
            or record.get('status') != 'accepted' or record.get('task_id') != tid
            or record.get('training_admitted') is not False):
        raise ValueError('Invalid frozen parameter acceptance record')
    try:
        settings = promotion.settings_space(record)
        if (set(record['programs']) != {_key(setting) for setting in settings}
                or record['source_binding']['task_id'] != tid
                or record['programs'][_key(record['default'])] != record['source_binding']['canonical_program_sha256']
                or any(type(h) is not str or len(h) != 64 or set(h) - set('0123456789abcdef')
                       for h in record['programs'].values())):
            raise ValueError('Frozen parameter declaration/program inventory differs')
        limits = record['limits']
        if (not {'demos', 'queries'} <= set(limits)
                or any(type(bounds) is not list or len(bounds) != 2
                       or any(type(n) is not int for n in bounds)
                       or not 1 <= bounds[0] <= bounds[1] <= 32
                       for bounds in (limits['demos'], limits['queries']))):
            raise ValueError('Invalid frozen parameter count limits')
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Invalid frozen parameter acceptance inventory') from error
    return record


def plan(catalog, pool, demos, queries, difficulty, *, parametric_only=False, check_ids=None):
    result = {}
    for row in pool:
        source = promotion._acceptance_path(catalog, row['id'])
        if not source.exists() and not source.is_symlink():
            if parametric_only:
                raise ValueError('Accepted parameter acceptance disappeared before snapshot freezing')
            continue  # A proposed/missing family remains a canonical draw.
        source = local_path(catalog.root, source.relative_to(catalog.root).as_posix())
        if source.is_symlink() or not source.is_file():
            raise ValueError('Acceptance must be a local regular file')
        accepted = None
        if check_ids is None or row['id'] in check_ids:
            accepted = promotion.status(catalog, row['id'])
            if accepted['status'] != 'accepted':
                raise ValueError(f"{row['id']}: accepted parameter family is stale or unavailable: {accepted.get('reason')}")
        if difficulty is not None:
            raise ValueError('Accepted parameter adapters have no difficulty control; omit draw-difficulty')
        raw = source.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if accepted is not None and digest != accepted['acceptance_sha256']:
            raise ValueError('Accepted parameter source changed during export planning')
        record = _record(json.loads(raw), row['id'])
        limits = record['limits']
        count = _demo_count(limits, demos, parametric_only=parametric_only)
        if not limits['queries'][0] <= queries <= limits['queries'][1]:
            raise ValueError('Query count is outside the accepted parameter limits')
        result[row['id']] = {'record': record, 'raw': raw, 'sha256': digest, 'demos': count,
                            'automatic_demos': demos is None,
                            'path': f'parametric-{digest}.private.json'}
    return result


def snapshot(plans, output):
    families = {}
    for tid, item in plans.items():
        (output / item['path']).write_bytes(item['raw'])
        families[tid] = {key: item[key] for key in ('path', 'sha256')}
    (output / 'parametric.private.json').write_bytes(promotion._raw({
        'schema': 'arcpuzzles-inline-acceptances-v1', 'families': families}))


def generate(catalog, row, item, *, seed, queries, timeout):
    bank_count = max(queries, min(4, item['record']['limits']['queries'][1]))
    try:
        episode, = catalog.generate_parametric(row['id'], count=1, seed=seed,
                                               demos=item['demos'], queries=bank_count, timeout=timeout)
    except (ValueError, RuntimeError) as error:
        # A bounded sampler failure can be retried. Source/acceptance drift
        # cannot be repaired by drawing another seed from the frozen plan.
        current = promotion.status(catalog, row['id'])
        if (current.get('status') != 'accepted'
                or current.get('acceptance_sha256') != item['sha256']):
            raise AcceptedSnapshotError('Accepted parameter snapshot is no longer current: '
                                        + str(current.get('reason', current.get('status')))) from error
        raise
    prior = episode['provenance']
    if (prior.get('parametric_acceptance_sha256') != item['sha256']
            or prior.get('generator_sha256') != row['generator_sha256']):
        raise AcceptedSnapshotError('Accepted parameter source changed after the export snapshot')
    meta = {'family': row['id'], 'settings': deepcopy(episode['settings']),
            'acceptance_sha256': item['sha256'], 'source_sha256': row['generator_sha256']}
    program = episode['program']
    digest = hashlib.sha256(program.encode()).hexdigest()
    if item['record']['programs'].get(_key(meta['settings'])) != digest:
        raise AcceptedSnapshotError('Parameter program differs from the frozen acceptance')
    executed = hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12]
    certificate = prior['demo_only_certificate']
    policy = {'automatic': item['automatic_demos'], 'declared_minimum': item['record']['limits']['demos'][0],
              'resolved_n_train': item['demos'], 'basis': 'accepted_parametric_contract'}
    lesson = {'status': 'passed', 'basis': 'demonstration_only_declared_settings',
              'survivors': deepcopy(certificate['survivors']), 'universal_identifiability': False}
    episode.update(parametric=meta, executed_rule_hash=executed, generator_version=row.get('version'),
                   sample_index=0, episode_index=0, rejections=[], lesson_check=lesson,
                   provenance={**prior, 'schema': 'arcpuzzles-generation-v1',
                       'rule_hash': executed, 'catalog_rule_hash': row['rule_hash'],
                       'reference': 'accepted_parametric', 'family': row['family'], 'split': row['split'],
                       'difficulty': None, 'overrides': {}, 'demonstration_policy': policy,
                       'lesson_check': lesson, 'approved': True, 'train_safety': 'reviewed_safe',
                       'catalog_approved': row['approved'], 'catalog_train_safety': row['train_safety'],
                       'approval_basis': 'accepted_parametric_family', 'training_admitted': False,
                       'parametric': deepcopy(meta)})
    episode['episode_id'] = public_identity(episode)
    episode = present_queries(episode, seed=seed, count=queries)
    episode['episode_id'] = public_identity(episode)
    return episode


def verify(output, public, labels, options):
    """Frozen record/serialization consistency, not new Racket or owner approval."""
    presentation_schema = options.get('query_presentation_schema')
    if presentation_schema not in (None, PRESENTATION_SCHEMA):
        raise ValueError('Unknown private query presentation schema')
    index = json.loads((output / 'parametric.private.json').read_bytes())
    if index.get('schema') != 'arcpuzzles-inline-acceptances-v1' or type(index.get('families')) is not dict:
        raise ValueError('Invalid frozen parameter acceptance index')
    accepted = {}
    for tid, item in index['families'].items():
        path = local_path(output, item['path'])
        if sha256(path) != item['sha256']:
            raise ValueError('Frozen parameter acceptance bytes changed')
        record = _record(json.loads(path.read_bytes()), tid)
        accepted[tid] = (record, item['sha256'])
    episodes = jsonl(output / 'episodes.private.jsonl')
    parameter_episodes = {}
    visible_ids = set()
    for episode in episodes:
        visible_id = public_identity(episode)
        if visible_id in visible_ids:
            raise ValueError('Duplicate visible challenge in retained inline episodes')
        visible_ids.add(visible_id)
        if 'parametric' not in episode:
            if episode.get('task_id') in accepted:
                raise ValueError('Inline accepted-family episode lost its parameter metadata')
            continue
        meta = episode['parametric']; tid = episode['task_id']
        if (type(meta) is not dict or set(meta) != {'family', 'settings', 'acceptance_sha256', 'source_sha256'}
                or tid not in accepted or meta['family'] != tid):
            raise ValueError('Invalid inline parameter family binding')
        record, digest = accepted[tid]; binding = record['source_binding']
        promotion._setting(record, meta['settings'])
        program = episode.get('program')
        if (not isinstance(program, str) or meta['acceptance_sha256'] != digest
                or type(episode.get('seed')) is not int or not 0 <= episode['seed'] <= 2**63 - 1
                or _key(episode.get('settings')) != _key(meta['settings'])
                or meta['source_sha256'] != binding['generator_sha256']
                or record['programs'].get(_key(meta['settings'])) != hashlib.sha256(program.encode()).hexdigest()
                or episode.get('program_sha256') != hashlib.sha256(program.encode()).hexdigest()
                or episode.get('executed_rule_hash') != hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12]
                or episode.get('parametric_accepted') is not True or episode.get('training_admitted') is not False
                or episode.get('reference') != 'accepted_parametric'):
            raise ValueError('Inline parameter program/source/acceptance binding differs')
        if ((presentation_schema == PRESENTATION_SCHEMA) != ('query_presentation' in episode)
                or ('query_presentation' in episode and episode['query_presentation'] is None)):
            raise ValueError('Required private query presentation record differs')
        bank = verify_presentation(episode)
        if 'query_presentation' in episode:
            source = {**episode, 'test': bank}
            if (episode['query_presentation']['source_episode_id'] != public_identity(source)
                    or len(bank) != max(options['n_test'], min(4, record['limits']['queries'][1]))):
                raise ValueError('Source query bank identity or count differs')
        for split in ('train', 'test'):
            if not episode.get(split):
                raise ValueError('Inline parameter episode has empty pairs')
            for pair in episode[split]:
                validate_grid(pair['input']); validate_grid(pair['output'])
        demos = _demo_count(record['limits'], options['n_train'],
                            parametric_only=options.get('parametric_only') is True)
        if (type(options['n_test']) is not int or type(demos) is not int
                or len(episode['train']) != demos or len(episode['test']) != options['n_test']):
            raise ValueError('Inline parameter counts differ from the export request')
        for pair in bank:
            validate_grid(pair['input']); validate_grid(pair['output'])
        inputs = [_key(pair['input']) for pair in episode['train'] + bank]
        if len(inputs) != len(set(inputs)):
            raise ValueError('Inline parameter inputs are not distinct')
        provenance = episode['provenance']; certificate = provenance.get('demo_only_certificate', {})
        if (provenance.get('approved') is not True or provenance.get('training_admitted') is not False
                or provenance.get('generator_sha256') != meta['source_sha256']
                or provenance.get('catalog_rule_hash') != binding['rule_hash']
                or provenance.get('rule_hash') != episode['executed_rule_hash']
                or provenance.get('reference') != 'accepted_parametric'
                or provenance.get('approval_basis') != 'accepted_parametric_family'
                or provenance.get('parametric_acceptance_sha256') != digest
                or provenance.get('racket_runtime', {}).get('backend') != 'racket'
                or provenance.get('racket_runtime', {}).get('protected') is not True
                or _key(provenance.get('parametric')) != _key(meta)
                or type(certificate.get('seed')) is not int or certificate['seed'] != episode['seed']
                or _key(certificate.get('settings')) != _key(meta['settings'])
                or _key(certificate.get('counts')) != _key({'demos': demos, 'queries': len(bank)})
                or _key(certificate.get('survivors')) != _key([meta['settings']])
                or type(certificate.get('label_count')) is not int
                or certificate['label_count'] != len(episode['train']) + len(bank)):
            raise ValueError('Inline parameter execution provenance differs')
        if episode['episode_id'] != public_identity(episode):
            raise ValueError('Inline parameter visible identity differs')
        parameter_episodes[episode['episode_id']] = episode
    for visible, hidden in zip(public, labels):
        episode = parameter_episodes.get(visible['episode_id'])
        if episode is None:
            if hidden.get('task_id') in accepted:
                raise ValueError('Accepted-family labels lost their private episode binding')
            continue
        expected = {'episode_id': episode['episode_id'], **promotion._public(episode)}
        if (_key(visible) != _key(expected)
                or _key(hidden['test_outputs']) != _key([p['output'] for p in episode['test']])
                or _key(hidden['provenance']) != _key(episode['provenance'])
                or hidden['task_id'] != episode['task_id'] or _key(hidden['seed']) != _key(episode['seed'])):
            raise ValueError('Inline parameter public/private projection differs')
    for row in jsonl(output / 'data.private.jsonl'):
        episode = parameter_episodes.get(row.get('episode_id'))
        if episode is not None and _key(row.get('source_provenance')) != _key(episode['provenance']):
            raise ValueError('Inline parameter rendered provenance differs')
