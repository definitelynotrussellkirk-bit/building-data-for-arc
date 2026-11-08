"""Source-bound public-authoring views; never native qualification or acceptance.

Run from the explicit checkout, for example::

    python workspace/authoring_preview.py --root . export \
      --public-preflight ../checks/TASK/preflight/preflight.json --out NEW

The complete bundle, its listing, all reports and private/ belong to the
controller. Reveal only one public/<visible-sha256>.json at a time. Verification
checks editable receipts and serialization; it neither authenticates hostile
rewrites nor executes Racket or implements a model controller.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


# This generic tool remains usable when copied into another task home.
_OWN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_OWN_ROOT / 'src'))
sys.path.insert(0, str(_OWN_ROOT / 'shared/runtime'))
from arcpuzzles.query_presentation import query_order
from arcpuzzles.review_witness import _public_preflight
from reviewer_support import public_challenge_bytes


SCHEMA = 'arcpuzzles-public-authoring-sequential-projection-v1'
SOURCE_NAMES = ('preflight.json', 'execution.json', 'original-pairs.json')
LIMITS = ('Unapproved authoring projection and finite serialization/mutation checks. '
          'Editable evidence is not independently authenticated. No new Racket replay, '
          'controller, owner qualification, owner acceptance or training admission. '
          'Keep bundle listings, mappings and reports private; reveal one public file at a time.')


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _no_symlinks(path):
    path = Path(path).absolute()
    _require(not any(p.is_symlink() for p in (path, *path.parents)),
             'Paths must contain no symlinks')
    return path


def _regular_bytes(path):
    path = _no_symlinks(path)
    _require(path.is_file(), 'Missing regular file: ' + str(path))
    return path.read_bytes()


def _new(path):
    path = _no_symlinks(path)
    if path.exists():
        raise FileExistsError('Choose a new output path: ' + str(path))
    return path


def _json(raw):
    def unique(items):
        result = {}
        for key, value in items:
            _require(key not in result, 'Duplicate JSON field: ' + key)
            result[key] = value
        return result
    def finite(value):
        raise ValueError('Nonfinite JSON number: ' + value)
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=finite)


def _load_preflight(root, path):
    """Validate the source/evidence closure without treating it as qualification."""
    path = _no_symlinks(path)
    source_bytes = {name: _regular_bytes(path.with_name(name)) for name in SOURCE_NAMES}
    q, execution = _public_preflight(root, path)
    _require(source_bytes == {name: _regular_bytes(path.with_name(name)) for name in SOURCE_NAMES},
             'Source receipt changed during validation')
    return q, execution, source_bytes


def public_view_bytes(episode, query_index=0):
    """Inspect only demonstrations and the selected query's input."""
    queries = episode.get('test')
    _require(type(queries) is list and type(query_index) is int
             and 0 <= query_index < len(queries), 'Select an exact integer query index')
    return public_challenge_bytes({'train': episode.get('train'),
                                  'test': [{'input': queries[query_index]['input']}]})


def _projection(q, execution, source_bytes, source_preflight, presentation_seed):
    _require(type(presentation_seed) is int, 'Presentation seed must be an exact integer')
    views, mappings = {}, []
    _require(bool(execution.get('episodes')), 'Authoring execution has no episodes')
    for index, episode in enumerate(execution['episodes']):
        _require(len(episode['test']) == 4, 'Authoring projection requires a complete four-query bank')
        _require(2 <= len(episode['train']) <= 6, 'Authoring demonstrations must be within 2..6')
        inputs = [_raw(pair['input']) for split in ('train', 'test') for pair in episode[split]]
        _require(len(set(inputs)) == len(inputs), 'Episode inputs must be distinct')
        order = query_order(4, episode['seed'] + presentation_seed)
        identifiers = []
        for source_index in order:
            payload = public_view_bytes(episode, source_index)
            identifier = _sha(payload)
            _require(identifier not in views, 'Duplicate visible query view')
            views[identifier] = payload
            identifiers.append(identifier)
        mappings.append({'episode_index': index, 'source_indices': order, 'view_ids': identifiers})
    manifest = {
        'schema': SCHEMA, 'status': 'authoring_projection', 'task_id': q['task_id'],
        'verification_status': 'authoring_preflight_not_owner_qualification',
        'source_binding': q['source_binding'], 'source_preflight': source_preflight,
        'source_copies': [{'path': name, 'sha256': _sha(source_bytes[name])}
                          for name in SOURCE_NAMES],
        'presentation_seed': presentation_seed, 'episodes': mappings,
        'public_files': [{'path': f'public/{identifier}.json', 'sha256': identifier}
                         for identifier in sorted(views)],
        'racket_replayed': False, 'owner_acceptance': 'not_performed',
        'training_admitted': False, 'limits': LIMITS,
    }
    return views, manifest


def _source_path(root, relative):
    _require(type(relative) is str and not Path(relative).is_absolute()
             and '\\' not in relative and '\0' not in relative,
             'Source preflight must be a relative same-workspace path')
    path = _no_symlinks(root / relative)
    _require(path.resolve().is_relative_to(root.parent),
             'Source preflight must remain inside the explicit workspace')
    _require(path.name == 'preflight.json', 'Source receipt must be named preflight.json')
    return path


def _inventory(bundle):
    _no_symlinks(bundle)
    _require(bundle.is_dir(), 'Bundle must be a directory')
    files, directories = set(), set()
    for path in bundle.rglob('*'):
        _no_symlinks(path)
        relative = path.relative_to(bundle).as_posix()
        if path.is_file():
            files.add(relative)
        elif path.is_dir():
            directories.add(relative)
        else:
            raise ValueError('Unexpected special bundle member: ' + relative)
    return files, directories


def _verify(root, bundle):
    root = _no_symlinks(root).resolve()
    bundle = _no_symlinks(bundle)
    files, directories = _inventory(bundle)
    manifest_raw = _regular_bytes(bundle / 'private/manifest.json')
    saved = _json(manifest_raw)
    _require(saved.get('schema') == SCHEMA, 'Unsupported authoring projection schema')
    original = _source_path(root, saved.get('source_preflight'))
    current = _load_preflight(root, original)
    copied = _load_preflight(root, bundle / 'private/preflight.json')
    _require(current == copied, 'Original source receipt and private source copies differ')
    views, manifest = _projection(*copied, saved['source_preflight'], saved.get('presentation_seed'))
    expected = {'private/manifest.json', *('private/' + name for name in SOURCE_NAMES)}
    expected.update(row['path'] for row in manifest['public_files'])
    _require(files == expected and directories == {'private', 'public'},
             'Bundle file inventory differs')
    _require(manifest_raw == _raw(manifest), 'Private metadata or presentation mapping differs')
    for identifier, payload in views.items():
        _require(_regular_bytes(bundle / 'public' / f'{identifier}.json') == payload,
                 'Public view differs from exact source-bound visible bytes/hash')
    _require(_load_preflight(root, original) == current,
             'Source receipt changed during bundle verification')
    return current, manifest, views


def verify(root, bundle):
    """Check current source, original/copy receipts, exact inventory and projection."""
    _, manifest, views = _verify(Path(root), Path(bundle))
    return {'status': 'verified_authoring_projection', 'task_id': manifest['task_id'],
            'episodes': len(manifest['episodes']), 'views': len(views),
            'owner_acceptance': 'not_performed', 'training_admitted': False,
            'racket_replayed': False, 'limits': LIMITS}


def export(root, preflight, output, *, presentation_seed=0):
    root = _no_symlinks(root).resolve()
    preflight = _no_symlinks(preflight).resolve()
    output = _new(output)
    source_preflight = os.path.relpath(preflight, root)
    _source_path(root, source_preflight)
    values = _load_preflight(root, preflight)
    views, manifest = _projection(*values, source_preflight, presentation_seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.authoring-preview-', dir=output.parent) as directory:
        stage = Path(directory)
        (stage / 'public').mkdir()
        (stage / 'private').mkdir(mode=0o700)
        for identifier, payload in views.items():
            (stage / 'public' / f'{identifier}.json').write_bytes(payload)
        for name, raw in values[2].items():
            (stage / 'private' / name).write_bytes(raw)
        (stage / 'private/manifest.json').write_bytes(_raw(manifest))
        _require(_load_preflight(root, preflight) == values,
                 'Source receipt changed during projection')
        verify(root, stage)
        output.mkdir(exist_ok=False)
        (stage / 'public').rename(output / 'public')
        (stage / 'private').rename(output / 'private')
    return {'status': 'authoring_projection', 'task_id': manifest['task_id'],
            'episodes': len(manifest['episodes']), 'views': len(views),
            'owner_acceptance': 'not_performed', 'training_admitted': False,
            'racket_replayed': False, 'limits': LIMITS}


def _variants(episode):
    yield 'single_query_only', {'train': deepcopy(episode['train']),
                               'test': [{'input': deepcopy(episode['test'][0]['input'])}]}
    metadata = deepcopy(episode)
    for name in tuple(metadata):
        if name not in {'train', 'test'}:
            metadata[name] = {'private_mutation': name}
    metadata['extra_private_metadata'] = {'seed': -1, 'program': 'not a program'}
    for split in ('train', 'test'):
        for pair in metadata[split]:
            pair['extra_private_metadata'] = {'hidden': True}
    yield 'private_metadata_rewritten', metadata
    answers = deepcopy(episode)
    for pair in answers['test']:
        pair['output'] = {'invalid_private_grid': True}
    yield 'query_answers_rewritten', answers
    absent = deepcopy(episode)
    for pair in absent['test']:
        pair.pop('output', None)
    yield 'query_answers_removed', absent
    future = deepcopy(episode)
    future['test'] = [future['test'][0], {'private_future_query': True},
                      {'input': 'not a visible grid', 'output': None}, {}]
    yield 'future_queries_replaced', future
    reordered = deepcopy(episode)
    reordered['test'] = [reordered['test'][0], *reversed(reordered['test'][1:]),
                         {'input': [[9]], 'output': [[8]]}]
    yield 'future_queries_reordered_and_extended', reordered


def _negative_checks(root, bundle):
    results = []
    for name in ('answer_leakage', 'altered_bytes', 'wrong_filename_hash',
                 'missing_file', 'metadata_tamper', 'permutation_tamper'):
        with tempfile.TemporaryDirectory(prefix='authoring-negative-') as directory:
            copy = Path(directory) / 'bundle'
            shutil.copytree(bundle, copy)
            public = next(iter(sorted((copy / 'public').iterdir())))
            if name == 'answer_leakage':
                value = _json(public.read_bytes())
                value['test'][0]['output'] = [[9]]
                leaked = _raw(value)
                old_id, new_id = public.stem, _sha(leaked)
                public.unlink()
                public.with_name(new_id + '.json').write_bytes(leaked)
                # Recompute every claimed visible hash/mapping, so rejection
                # must still follow from projection against source evidence.
                manifest_path = copy / 'private/manifest.json'
                metadata = _json(manifest_path.read_bytes())
                for row in metadata['public_files']:
                    if row['sha256'] == old_id:
                        row.update(path='public/' + new_id + '.json', sha256=new_id)
                metadata['public_files'].sort(key=lambda row: row['path'])
                for episode in metadata['episodes']:
                    episode['view_ids'] = [new_id if identifier == old_id else identifier
                                           for identifier in episode['view_ids']]
                manifest_path.write_bytes(_raw(metadata))
            elif name == 'altered_bytes':
                public.write_bytes(public.read_bytes() + b' ')
            elif name == 'wrong_filename_hash':
                public.rename(public.with_name('0' * 64 + '.json'))
            elif name == 'missing_file':
                public.unlink()
            else:
                path = copy / 'private/manifest.json'
                value = _json(path.read_bytes())
                if name == 'metadata_tamper':
                    value['owner_acceptance'] = 'accepted'
                else:
                    indices = value['episodes'][0]['source_indices']
                    indices[0], indices[1] = indices[1], indices[0]
                path.write_bytes(_raw(value))
            try:
                verify(root, copy)
            except (ValueError, OSError, KeyError, TypeError) as error:
                result = {'name': name, 'status': 'rejected', 'reason': str(error)}
                if name == 'answer_leakage':
                    result['content_hash_recomputed'] = True
                results.append(result)
            else:
                raise ValueError('Negative verifier control was accepted: ' + name)
    return results


def self_check(root, bundle, output):
    """Write a private report only after invariance and tamper controls pass."""
    root, bundle = Path(root), Path(bundle)
    output = _new(output)
    _require(not output.resolve().is_relative_to(bundle.resolve()),
             'Self-check report must remain outside the bundle')
    values, manifest, _ = _verify(root, bundle)
    before = {p.relative_to(bundle).as_posix(): _sha(p.read_bytes())
              for p in bundle.rglob('*') if p.is_file()}
    cases = []
    for mapping, episode in zip(manifest['episodes'], values[1]['episodes']):
        presented = deepcopy(episode)
        presented['test'] = [deepcopy(episode['test'][i]) for i in mapping['source_indices']]
        first = public_view_bytes(presented)
        names = []
        for name, variant in _variants(presented):
            _require(public_view_bytes(variant) == first,
                     'First-turn private-field invariance failed: ' + name)
            names.append(name)
        changed = deepcopy(presented)
        changed['test'][0]['input'][0][0] = (changed['test'][0]['input'][0][0] + 1) % 10
        _require(public_view_bytes(changed) != first, 'Visible-cell positive control failed')
        cases.append({'episode_index': mapping['episode_index'],
                      'first_source_query_index': mapping['source_indices'][0],
                      'first_view_sha256': _sha(first), 'invariance_checks': names,
                      'visible_change_positive_control': 'passed'})
    negatives = _negative_checks(root, bundle)
    verify(root, bundle)
    after = {p.relative_to(bundle).as_posix(): _sha(p.read_bytes())
             for p in bundle.rglob('*') if p.is_file()}
    _require(before == after, 'Original bundle changed during self-check')
    report = {'schema': 'arcpuzzles-public-authoring-first-turn-check-v1', 'status': 'passed',
              'task_id': manifest['task_id'], 'manifest_sha256': before['private/manifest.json'],
              'source_binding': manifest['source_binding'],
              'first_turns_checked': len(cases), 'cases': cases,
              'invariance_checks': sum(len(case['invariance_checks']) for case in cases),
              'positive_controls': len(cases), 'negative_verifier_checks': negatives,
              'racket_replayed': False, 'owner_acceptance': 'not_performed',
              'training_admitted': False, 'limits': LIMITS}
    output.parent.mkdir(parents=True, exist_ok=True)
    _new(output)
    with output.open('xb') as handle:
        handle.write(_raw(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Explicit same-checkout repository')
    commands = parser.add_subparsers(dest='command', required=True)
    write = commands.add_parser('export')
    write.add_argument('--public-preflight', type=Path, required=True)
    write.add_argument('--out', type=Path, required=True)
    write.add_argument('--presentation-seed', type=int, default=0)
    read = commands.add_parser('verify')
    read.add_argument('--bundle', type=Path, required=True)
    check = commands.add_parser('self-check')
    check.add_argument('--bundle', type=Path, required=True)
    check.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'export':
            report = export(args.root, args.public_preflight, args.out,
                            presentation_seed=args.presentation_seed)
        elif args.command == 'verify':
            report = verify(args.root, args.bundle)
        else:
            report = self_check(args.root, args.bundle, args.out)
        print(json.dumps({key: value for key, value in report.items()
                          if key not in {'source_binding', 'cases', 'negative_verifier_checks'}},
                         sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('authoring-preview: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
