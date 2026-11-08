#!/usr/bin/env python3
"""Authoring-only exhaustive local-vote audit; Python expectations are not authority.

Prepare 18 lawful grids, execute them with public arcpuzzles apply, then score
the retained receipt. No canonical answers are used during a blind solve.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
from itertools import product
import hashlib
import json
from pathlib import Path
import runpy
import sys

from reviewer_support import canonical_path, find_root

TASK_ID = '2ca05c7eef24'
RULE_HASH = '92b2f8e4de94'
CALLABLE_RULE_SHA256 = '1c8d679ea0148b92ecee58933fa8afe2255779f9c0f90a04d05a8fa35667ffab'
ALPHABET = (0, 1, 2, 3, 4, 6, 7, 8, 9)
HEIGHT, PANEL_WIDTH = 7, 6
SOURCE = Path(__file__).resolve()
GENERATOR = SOURCE.parent.parent / 'generator.py'
CLASSES = ('empty', 'singleton', 'pair_same', 'pair_distinct',
           'triple_same', 'triple_majority', 'triple_distinct')
RIVALS = ('union_max', 'exactly_two_max', 'threshold_max',
          'threshold_first', 'threshold_last', 'same_color_pair')


def _competitors(namespace):
    declared = namespace.get('LESSON_COMPETITORS')
    if declared is not None:
        _check(isinstance(declared, dict) and declared
               and all(isinstance(name, str) and callable(fn) for name, fn in declared.items()),
               'LESSON_COMPETITORS must be a nonempty string-to-callable mapping')
        return declared, 'generator LESSON_COMPETITORS'
    return None, 'explicit fallback operator adapters in authoring tool; baseline has no declarations'


def _rival_outputs(grid, declared):
    if declared is not None:
        return {name: fn(grid) for name, fn in declared.items()}
    h, pw = len(grid), (len(grid[0]) - 2) // 3
    return {name: [[_rival_vote([grid[r][p * (pw + 1) + c] for p in range(3)], name)
                    for c in range(pw)] for r in range(h)] for name in RIVALS}


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_sha256(grid):
    """Public apply's compact JSON digest, independently reproduced here."""
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def _check(condition, message):
    if not condition:
        raise ValueError(message)


def _dump(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def expected_vote(votes):
    """Independent count-and-numeric-tie proxy; never calls generator.apply_rule."""
    _check(len(votes) == 3 and all(type(v) is int and v in ALPHABET for v in votes),
           'expected exactly three votes from the non-gray alphabet')
    counts = Counter(v for v in votes if v != 0)
    if sum(counts.values()) < 2:
        return 0
    largest_count = max(counts.values())
    return max(color for color, count in counts.items() if count == largest_count)


def vote_class(votes):
    nonzero = [v for v in votes if v]
    n, distinct = len(nonzero), len(set(nonzero))
    if n == 0:
        return 'empty'
    if n == 1:
        return 'singleton'
    if n == 2:
        return 'pair_same' if distinct == 1 else 'pair_distinct'
    return {1: 'triple_same', 2: 'triple_majority', 3: 'triple_distinct'}[distinct]


def _rival_vote(votes, rival):
    nz = [v for v in votes if v]
    if rival == 'union_max':
        return max(nz, default=0)
    if len(nz) < 2:
        return 0
    if rival == 'exactly_two_max':
        return max(nz) if len(nz) == 2 else 0
    if rival == 'threshold_max':
        return max(nz)
    if rival == 'threshold_first':
        return nz[0]
    if rival == 'threshold_last':
        return nz[-1]
    if rival == 'same_color_pair':
        return max((v for v in nz if nz.count(v) >= 2), default=0)
    raise ValueError('unknown authoring rival: ' + rival)


@lru_cache(maxsize=4)
def _read_authority(path, mtime_ns, size):
    """Cache selected-task ledger reads, invalidating when the file changes."""
    rows = []
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get('task_id') == TASK_ID:
                    rows.append(row)
    _check(len(rows) == 1, 'expected one exact canonical task row')
    program = rows[0].get('program_solution')
    _check(isinstance(program, str) and program.strip(), 'missing canonical program')
    digest = hashlib.sha256(' '.join(program.split()).encode()).hexdigest()
    _check(digest[:12] == RULE_HASH, 'canonical source changed; review this tool before reuse')
    return {'raw_program': program, 'raw_program_sha256': hashlib.sha256(program.encode()).hexdigest(),
            'normalized_program_sha256': digest, 'rule_hash': digest[:12],
            'callable_rule_sha256': CALLABLE_RULE_SHA256}


def canonical_authority():
    ledger = canonical_path(find_root(SOURCE))
    stat = ledger.stat()
    return dict(_read_authority(str(ledger), stat.st_mtime_ns, stat.st_size))


def _packed_request():
    inputs, mapping = [], []
    for index, votes in enumerate(product(ALPHABET, repeat=3)):
        grid_index, cell = divmod(index, HEIGHT * PANEL_WIDTH)
        row, col = divmod(cell, PANEL_WIDTH)
        if grid_index == len(inputs):
            grid = [[0] * (3 * PANEL_WIDTH + 2) for _ in range(HEIGHT)]
            for line in grid:
                line[PANEL_WIDTH] = line[2 * PANEL_WIDTH + 1] = 5
            inputs.append(grid)
        for panel, value in enumerate(votes):
            inputs[grid_index][row][panel * (PANEL_WIDTH + 1) + col] = value
        mapping.append({'triple_index': index, 'votes': list(votes),
                        'grid_index': grid_index, 'row': row, 'col': col})
    return {'inputs': inputs}, mapping


def _metadata(request, mapping, request_bytes):
    meta = {'schema': 'vote-support-preparation-v1', 'task_id': TASK_ID,
            'alphabet': list(ALPHABET), 'height': HEIGHT, 'panel_width': PANEL_WIDTH,
            'triple_count': len(mapping), 'input_count': len(request['inputs']),
            'padding_cells': HEIGHT * PANEL_WIDTH * len(request['inputs']) - len(mapping),
            'mapping': mapping, 'canonical': canonical_authority(),
            'generator_file': str(GENERATOR), 'generator_sha256': file_sha256(GENERATOR),
            'tool_source_file': str(SOURCE), 'tool_source_sha256': file_sha256(SOURCE),
            'request_sha256': hashlib.sha256(request_bytes).hexdigest(),
            'input_sha256': [grid_sha256(g) for g in request['inputs']],
            'notice': 'Authoring only. Python expectations are not reference labels.'}
    meta['metadata_sha256'] = grid_sha256(meta)
    return meta


def prepare(out):
    """Write an exact public-apply request and same-stem .meta.json sidecar."""
    out = Path(out)
    request, mapping = _packed_request()
    _dump(out, request)
    meta = _metadata(request, mapping, out.read_bytes())
    _dump(out.with_suffix('.meta.json'), meta)
    return meta


def _valid_output(output):
    return (isinstance(output, list) and len(output) == HEIGHT
            and all(isinstance(row, list) and len(row) == PANEL_WIDTH
                    and all(type(v) is int and 0 <= v <= 9 for v in row) for row in output))


def score(prepared, racket, out):
    """Fail closed on stale/tampered preparation or any invalid/mismatching receipt.

    Receipts are unsigned: this verifies consistency, not provenance authenticity.
    Use a recorded public apply command to establish where the receipt came from.
    """
    prepared, racket, out = Path(prepared), Path(racket), Path(out)
    request = json.loads(prepared.read_text())
    meta = json.loads(prepared.with_suffix('.meta.json').read_text())
    expected_request, mapping = _packed_request()
    _check(request == expected_request and grid_sha256(request) == grid_sha256(expected_request)
           and set(request) == {'inputs'}, 'prepared request changed')
    current_meta = _metadata(expected_request, mapping, prepared.read_bytes())
    _check(isinstance(meta, dict), 'preparation sidecar must be an object')
    actual_meta_core = {key: value for key, value in meta.items() if key != 'metadata_sha256'}
    _check(meta.get('metadata_sha256') == grid_sha256(actual_meta_core),
           'preparation sidecar metadata digest mismatch')
    _check(json.dumps(meta, sort_keys=True, separators=(',', ':'), allow_nan=False)
           == json.dumps(current_meta, sort_keys=True, separators=(',', ':'), allow_nan=False),
           'preparation sidecar tampered or generator/tool/canonical source stale')
    receipt = json.loads(racket.read_text())
    _check(isinstance(receipt, dict), 'expected a public apply receipt object')
    fields = {'schema': 'arcpuzzles-apply-v1', 'task_id': TASK_ID, 'rule_task_id': TASK_ID,
              'reference': 'canonical', 'rule_file': 'data/canonical/puzzles.jsonl',
              'executed_rule_hash': RULE_HASH, 'catalog_rule_hash': RULE_HASH,
              'rule_hash_matches_catalog': True, 'rule_text_sha256': CALLABLE_RULE_SHA256,
              'generator_sha256': meta['generator_sha256']}
    for name, value in fields.items():
        _check(receipt.get(name) == value, 'receipt binding mismatch: ' + name)
    _check(receipt.get('rule_hash_matches_catalog') is True, 'catalog match must be true')
    results = receipt.get('results')
    _check(isinstance(results, list) and len(results) == len(request['inputs']), 'incomplete/extra result batch')
    source_hash = file_sha256(GENERATOR)
    namespace = runpy.run_path(str(GENERATOR))
    declared, rival_source = _competitors(namespace)
    names = tuple(declared) if declared is not None else RIVALS
    disagreements = Counter({name: 0 for name in names})
    classes = Counter({name: 0 for name in CLASSES})
    for index, (grid, result) in enumerate(zip(request['inputs'], results)):
        _check(isinstance(result, dict), 'result must be an object')
        _check(type(result.get('index')) is int and result['index'] == index, 'result order/index mismatch')
        _check(result.get('input') == grid and grid_sha256(result.get('input')) == grid_sha256(grid),
               'returned input differs from prepared input')
        _check(result.get('input_sha256') == grid_sha256(grid), 'returned input digest mismatch')
        _check(result.get('valid_output') is True and result.get('error', 'missing') is None,
               'reference output rejected/errored')
        output = result.get('output')
        _check(_valid_output(output), 'reference output dimensions/type invalid')
        _check(result.get('output_sha256') == grid_sha256(output), 'reference output digest mismatch')
        for row in range(HEIGHT):
            for col in range(PANEL_WIDTH):
                votes = [grid[row][panel * (PANEL_WIDTH + 1) + col] for panel in range(3)]
                expected = expected_vote(votes)
                _check(output[row][col] == expected,
                       f'actual reference disagrees at input={index} row={row} col={col} votes={votes}')
    rival_batches = [_rival_outputs(grid, declared) for grid in request['inputs']]
    _check(file_sha256(GENERATOR) == source_hash, 'generator changed during scoring')
    for predictions in rival_batches:
        _check(all(_valid_output(prediction) for prediction in predictions.values()),
               'competitor returned invalid dimensions/type')
    for item in mapping:
        votes = item['votes']
        actual = results[item['grid_index']]['output'][item['row']][item['col']]
        classes[vote_class(votes)] += 1
        for name in names:
            pred = rival_batches[item['grid_index']][name][item['row']][item['col']]
            disagreements[name] += pred != actual
    report = {'schema': 'vote-support-score-v1', 'task_id': TASK_ID, 'passed': True,
              'actual_reference': 'canonical public arcpuzzles apply receipt',
              'provenance_limit': 'Unsigned receipt; retain recorded apply invocation for provenance.',
              'generator_sha256': meta['generator_sha256'], 'tool_source_sha256': meta['tool_source_sha256'],
              'canonical': meta['canonical'], 'request_sha256': meta['request_sha256'],
              'sidecar_sha256': file_sha256(prepared.with_suffix('.meta.json')),
              'receipt_sha256': file_sha256(racket), 'input_count': len(results),
              'checked_triples': len(mapping), 'checked_padding_cells': meta['padding_cells'],
              'vote_classes': dict(classes), 'rival_cell_disagreements': dict(disagreements),
              'rival_source': rival_source}
    _dump(out, report)
    return report


def coverage(*, seeds=(0, 1, 2, 3), indices=range(12), bands=('easy', 'medium', 'hard')):
    """Cheap source-bound measurements using only generate/self_check and own proxy."""
    seeds, indices, bands = list(seeds), list(indices), list(bands)
    source_hash = file_sha256(GENERATOR)
    module = runpy.run_path(str(GENERATOR))
    declared, rival_source = _competitors(module)
    names = tuple(declared) if declared is not None else RIVALS
    classes = Counter({name: 0 for name in CLASSES})
    rival_cells = Counter({name: 0 for name in names})
    rival_inputs = Counter({name: 0 for name in names})
    count = cells = 0
    for band, seed, sample_index in product(bands, seeds, indices):
        grid = module['generate'](seed, sample_index, difficulty=band)
        errors = module['self_check'](grid, difficulty=band)
        _check(not errors, f'generator self_check failed: {errors}')
        h, width = len(grid), len(grid[0])
        pw = (width - 2) // 3
        _check(width == 3 * pw + 2 and 3 <= h <= 7 and 2 <= pw <= 6
               and all(len(row) == width and row[pw] == row[2 * pw + 1] == 5 for row in grid),
               'generated panel geometry invalid')
        hit = set()
        predictions = _rival_outputs(grid, declared)
        _check(all(isinstance(p, list) and len(p) == h and all(isinstance(row, list) and len(row) == pw
                    and all(type(v) is int and 0 <= v <= 9 for v in row) for row in p)
                    for p in predictions.values()), 'competitor returned invalid dimensions/type')
        for r, c in product(range(h), range(pw)):
            votes = [grid[r][p * (pw + 1) + c] for p in range(3)]
            expected = expected_vote(votes)
            classes[vote_class(votes)] += 1
            cells += 1
            for rival in names:
                if predictions[rival][r][c] != expected:
                    rival_cells[rival] += 1
                    hit.add(rival)
        rival_inputs.update(hit)
        count += 1
    _check(file_sha256(GENERATOR) == source_hash, 'generator changed during coverage')
    return {'schema': 'vote-support-coverage-v1', 'task_id': TASK_ID,
            'measurement': 'independent Python vote proxy; not Racket authority',
            'generator_sha256': source_hash, 'tool_source_sha256': file_sha256(SOURCE),
            'seeds': seeds, 'sample_indices': indices, 'difficulty_bands': bands,
            'input_count': count, 'cell_count': cells, 'vote_classes': dict(classes),
            'rival_cell_disagreements': dict(rival_cells), 'rival_input_disagreements': dict(rival_inputs),
            'rival_source': rival_source}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare'); prep.add_argument('--out', type=Path, required=True)
    scoring = commands.add_parser('score')
    for name in ('prepared', 'racket', 'out'):
        scoring.add_argument('--' + name, type=Path, required=True)
    cov = commands.add_parser('coverage'); cov.add_argument('--out', type=Path, required=True)
    cov.add_argument('--seeds', default='0,1,2,3'); cov.add_argument('--indices', type=int, default=12)
    cov.add_argument('--bands', default='easy,medium,hard')
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            report = prepare(args.out)
            print(json.dumps({'prepared': str(args.out), 'input_count': report['input_count'], 'triple_count': report['triple_count']}))
        elif args.command == 'score':
            report = score(args.prepared, args.racket, args.out)
            print(json.dumps({'passed': report['passed'], 'checked_triples': report['checked_triples'], 'out': str(args.out)}))
        else:
            _check(args.indices > 0, '--indices must be positive')
            seeds = [int(x) for x in args.seeds.split(',')]
            bands = [None if x == 'default' else x for x in args.bands.split(',')]
            _check(all(x in ('easy', 'medium', None, 'hard') for x in bands), 'unknown difficulty band')
            report = coverage(seeds=seeds, indices=range(args.indices), bands=bands)
            _dump(args.out, report)
            print(json.dumps({'measurement': report['measurement'], 'input_count': report['input_count'], 'out': str(args.out)}))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('vote-support probe failed: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
