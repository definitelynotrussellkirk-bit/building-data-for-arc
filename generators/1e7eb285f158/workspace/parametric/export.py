#!/usr/bin/env python3
"""Opt-in export for the proposed inset/tie-policy prototype.

The writer only packages supplied claims. The CLI separately executes every
label and demonstration-only rival fit through this checkout's protected Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = '1e7eb285f158'
ROOT = Path(__file__).resolve().parents[4]
RUNTIME = ROOT / 'shared/runtime'


def _load_path(path, purpose):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.resolve() != path:
        raise ValueError(f'{purpose} must be a regular adjacent same-checkout file: {path}')
    name = '_arc_' + purpose + '_' + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot load {path}')
    module = importlib.util.module_from_spec(spec)
    # Dataclasses may need the exact module's registry entry while executing.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _load_prototype():
    """Never resolve the common name 'prototype' through the global import cache."""
    return _load_path(Path(__file__).resolve().with_name('prototype.py'), 'prototype')


def _support():
    return _load_path(RUNTIME / 'reviewer_support.py', 'reviewer_support')


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + '\n').encode('utf-8')


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError('grid must have 1..30 rows and columns')
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError('grid must be rectangular with exact integer colors 0..9')
    return value


def _validate_episode(episode):
    if type(episode) is not dict:
        raise ValueError('private episode must be a dictionary')
    seen = set()
    for split in ('train', 'test'):
        pairs = episode.get(split)
        if type(pairs) is not list or not pairs:
            raise ValueError(f'{split} must contain labeled pairs')
        for pair in pairs:
            if type(pair) is not dict or 'input' not in pair or 'output' not in pair:
                raise ValueError('private pairs require input and output grids')
            grid = _grid(pair['input'])
            _grid(pair['output'])
            key = tuple(tuple(row) for row in grid)
            if key in seen:
                raise ValueError('duplicate input across demonstrations/queries')
            seen.add(key)
    if type(episode.get('program_solution')) is not str or not episode['program_solution']:
        raise ValueError('private episode requires reference program text')


def write_export(episodes, out, report=None):
    """Write opaque public projections and separately retain all private data.

    All validation, duplicate checks, and serialization precede destination
    creation. This function does not execute or verify reference programs.
    Return the same manifest that is written to manifest.json.
    """
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f'Refusing existing export destination: {out}')
    episodes = copy.deepcopy(list(episodes))
    if not episodes:
        raise ValueError('an export requires at least one episode')
    support = _support()
    records = []
    ids = set()
    for episode in episodes:
        _validate_episode(episode)
        public_bytes = support.public_challenge_bytes(episode)
        public_id = support.public_challenge_id(episode)
        if public_id != _digest(public_bytes):
            raise ValueError('public projection hash disagrees with exact bytes')
        if public_id in ids:
            raise ValueError('duplicate visible episode projection')
        ids.add(public_id)
        records.append((public_id, public_bytes, episode))
    records.sort(key=lambda item: item[0])
    files = {}
    private = []
    public_records = []
    for public_id, payload, episode in records:
        path = f'public/{public_id}.json'
        files[path] = payload
        public_records.append({'public_id': public_id, 'path': path})
        program_bytes = episode['program_solution'].encode('utf-8')
        program_path = f'private/programs/{_digest(program_bytes)}.rkt'
        files[program_path] = program_bytes
        private.append({'public_id': public_id, 'program_path': program_path, 'episode': episode})
    files['private/episodes.json'] = _json_bytes(private)
    private_report = {'racket_verification': 'not_run'} if report is None else copy.deepcopy(report)
    private_report['writer_verification'] = 'not_performed; packaging only'
    files['private/report.json'] = _json_bytes(private_report)
    manifest = {'schema': 'task-local-parametric-export-v1', 'episodes': public_records,
                'files': [{'path': path, 'sha256': _digest(payload)}
                          for path, payload in sorted(files.items())]}
    manifest_bytes = _json_bytes(manifest)
    out.mkdir(parents=True, exist_ok=False)
    for path, payload in sorted(files.items()):
        destination = out / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    (out / 'manifest.json').write_bytes(manifest_bytes)
    return manifest


def _canonical_program(support):
    root = support.find_root(__file__)
    path = support.canonical_path(root)
    with path.open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    matches = [row for row in rows if row.get('task_id') == TASK_ID]
    if len(matches) != 1 or type(matches[0].get('program_solution')) is not str:
        raise ValueError('expected exactly one selected canonical program record')
    return matches[0]['program_solution'], path


def verified_episodes(seeds, demos=3, queries=4):
    """Generate and independently execute labels and all demo-only rival fits."""
    core = _load_prototype()
    support = _support()
    canonical, ledger = _canonical_program(support)
    if core.program(core.DEFAULT) != canonical:
        raise ValueError('prototype default is not byte-for-byte selected canonical text')
    # Import the same-checkout packages used by the protected qualification path.
    sys.path.insert(0, str(RUNTIME))
    bridge_module = importlib.import_module('arc_repl.racket_bridge')
    wrap_module = importlib.import_module('puzzle_generators.rule_wrap')
    for module in (bridge_module, wrap_module):
        if not Path(module.__file__).resolve().is_relative_to(RUNTIME):
            raise ValueError('reference modules must come from this checkout')
    episodes = []
    fits = []
    counts = {'label_requests': 0, 'label_executions': 0, 'fit_requests': 0,
              'fit_executions': 0, 'cache_hits': 0}
    cache = {}
    wrapped = {}
    with bridge_module.RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get('backend') != 'racket' or identity.get('protected') is not True:
            raise ValueError('export requires a live protected Racket backend')
        for key in ('bridge_path', 'prelude_path'):
            if not Path(identity[key]).resolve().is_relative_to(RUNTIME):
                raise ValueError('protected runtime escaped this checkout')

        def apply(program, grid, phase):
            _grid(grid)
            counts[phase + '_requests'] += 1
            key = (program, tuple(tuple(row) for row in grid))
            if key in cache:
                counts['cache_hits'] += 1
                return copy.deepcopy(cache[key])
            if program not in wrapped:
                wrapped[program] = wrap_module.wrap_rule(program)
            literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
            result = bridge.eval_text(f'({wrapped[program]} {literal})')
            _grid(result)
            counts[phase + '_executions'] += 1
            cache[key] = copy.deepcopy(result)
            return result

        for seed in seeds:
            for setting in core.SETTINGS:
                episode = core.generate(seed, dict(setting), demos=demos, queries=queries)
                _validate_episode(episode)
                if len(episode['train']) != demos or len(episode['test']) != queries:
                    raise ValueError('generator returned fewer/more pairs than requested')
                if episode.get('settings') != setting or episode.get('seed') != seed:
                    raise ValueError('generator returned mismatched seed/settings')
                program = core.program(setting)
                if episode['program_solution'] != program:
                    raise ValueError('episode program does not match declared setting')
                for split in ('train', 'test'):
                    for index, pair in enumerate(episode[split]):
                        actual = apply(program, pair['input'], 'label')
                        if actual != pair['output']:
                            raise ValueError(f'Python/Racket mismatch: seed={seed}, setting={setting}, {split}[{index}]')
                        # Retain the executed answer rather than the Python claim.
                        pair['output'] = copy.deepcopy(actual)
                survivors = []
                candidate_results = []
                # This loop receives demonstrations only; query labels cannot fit rivals.
                for candidate in core.SETTINGS:
                    candidate_program = core.program(candidate)
                    mismatches = []
                    for index, pair in enumerate(episode['train']):
                        if apply(candidate_program, pair['input'], 'fit') != pair['output']:
                            mismatches.append(index)
                    if not mismatches:
                        survivors.append(dict(candidate))
                    candidate_results.append({'settings': dict(candidate), 'mismatching_demos': mismatches})
                if survivors != [dict(setting)]:
                    raise ValueError(f'demonstrations do not identify intended setting: {survivors}')
                episode['label_basis'] = 'protected Racket; Python claims matched'
                public_id = support.public_challenge_id(episode)
                fits.append({'public_id': public_id, 'seed': seed, 'settings': dict(setting),
                             'fit_uses': 'demonstrations_only', 'survivors': survivors,
                             'candidates': candidate_results})
                episodes.append(episode)
    sources = {'prototype': Path(core.__file__), 'export': Path(__file__),
               'reviewer_support': Path(support.__file__), 'rule_wrap': Path(wrap_module.__file__),
               'canonical_ledger': ledger}
    report = {'status': 'proposed_task_local_prototype; no acceptance or training admission',
              'racket_verification': 'pass', 'runtime_identity': identity,
              'canonical_default_exact_equality': True, 'canonical_program_sha256': _digest(canonical.encode()),
              'counts': {**counts, 'episodes': len(episodes), 'demos_per_episode': demos,
                         'queries_per_episode': queries, 'unique_program_grid_evaluations': len(cache)},
              'requested_seeds': list(seeds), 'fits': fits,
              'source_hashes': {key: {'path': str(path.relative_to(ROOT)), 'sha256': _digest(path.read_bytes())}
                                for key, path in sources.items()}}
    return episodes, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, action='append', help='repeatable; default: 0 and 17')
    parser.add_argument('--demos', type=int, default=3)
    parser.add_argument('--queries', type=int, default=4)
    parser.add_argument('--out', type=Path, required=True, help='new export destination')
    args = parser.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink():
            raise FileExistsError(f'Refusing existing export destination: {args.out}')
        seeds = args.seed if args.seed is not None else [0, 17]
        episodes, report = verified_episodes(seeds, args.demos, args.queries)
        manifest = write_export(episodes, args.out, report)
    except (ValueError, FileExistsError) as error:
        parser.exit(2, f'export error: {error}\n')
    print(json.dumps({'out': str(args.out), 'episodes': len(manifest['episodes']),
                      'racket_verification': report['racket_verification'], 'counts': report['counts']}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
