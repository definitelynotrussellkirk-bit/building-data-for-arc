#!/usr/bin/env python3
"""Proposed panel rule parameter. Labels come exclusively from included Racket.

This is a research prototype, independent of production sampler/approval APIs.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile

from reviewer_support import canonical_path, find_root

TASK_ID = '2b34f380ed25'
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
SETTINGS = ('half_swap', 'reflection')
DEFAULT = 'half_swap'
_TOOL_STAGE = None


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


@lru_cache(maxsize=1)
def canonical_record():
    path = canonical_path(ROOT)
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get('task_id') == TASK_ID:
                return row
    raise ValueError('canonical task missing')


def program_for(mark_action=DEFAULT):
    if mark_action not in SETTINGS:
        raise ValueError(f'mark_action must be one of {SETTINGS}')
    source = canonical_record()['program_solution']
    # Anchors are exact and unique: refuse to mutate a future changed authority.
    for old in ('(zip-lists lefts rights)', '(zip-lists tops bots)'):
        if source.count(old) != 1:
            raise ValueError('canonical pairing expression changed; review prototype')
    if mark_action == DEFAULT:
        return source
    return source.replace('(zip-lists lefts rights)', '(zip-lists lefts (reverse rights))').replace('(zip-lists tops bots)', '(zip-lists tops (reverse bots))')


def ensure_tools():
    """Use official copier for mapped scripts; keep disposable runtime out of evidence."""
    global _TOOL_STAGE
    try:
        have_scripts = importlib.util.find_spec('scripts.comment_solutions') is not None
    except ModuleNotFoundError:
        have_scripts = False
    if not have_scripts:
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import prepare_runtime
        _TOOL_STAGE = tempfile.TemporaryDirectory(prefix='panel-parametric-runtime-')
        prepare_runtime(Catalog(ROOT), Path(_TOOL_STAGE.name), TASK_ID)
        sys.path.insert(0, _TOOL_STAGE.name)


def execute(bridge, program, grid):
    from puzzle_generators.rule_wrap import wrap_rule
    ensure_tools()
    bridge.eval_text(f'(define __panel_rule {wrap_rule(program)})')
    bridge.define_grid('__panel_input', grid)
    return bridge.eval_text('(__panel_rule __panel_input)')


def canvas(matrix, *, row_cut=None, col_cut=None, vertical=None, horizontal=None, mark_rows=None, mark_cols=None, separator=9):
    """Render lawful nonzero 3x3 macro blocks, yellow gaps, and full dividers."""
    rows, cols = len(matrix), len(matrix[0])
    rs = [1 + 4*i + (2 if row_cut is not None and i > row_cut else 0) for i in range(rows)]
    cs = [1 + 4*j + (2 if col_cut is not None and j > col_cut else 0) for j in range(cols)]
    height, width = rs[-1]+4, cs[-1]+4
    grid = [[0]*width for _ in range(height)]
    for i in range(rows):
        for j in range(cols):
            for r in range(rs[i], rs[i]+3):
                for c in range(cs[j], cs[j]+3):
                    grid[r][c] = matrix[i][j]
    if vertical is not None:
        lo, hi = mark_rows or (0, rows-1)
        for r in range(rs[lo], rs[hi]+3):
            grid[r][cs[vertical]+3] = 4
    if horizontal is not None:
        lo, hi = mark_cols or (0, cols-1)
        for c in range(cs[lo], cs[hi]+3):
            grid[rs[horizontal]+3][c] = 4
    if row_cut is not None:
        grid[rs[row_cut]+4] = [separator]*width
    if col_cut is not None:
        for line in grid:
            line[cs[col_cut]+4] = separator
    if height > 30 or width > 30:
        raise ValueError('macro canvas exceeds ARC bounds')
    return grid


def transpose(grid):
    return [list(line) for line in zip(*grid)]


def padded(grid, size=30):
    result = [[0]*size for _ in range(size)]
    for i, line in enumerate(grid):
        result[i][:len(line)] = line
    # A separator must remain uniform across the ENTIRE padded canvas.
    for i, line in enumerate(grid):
        if len(set(line)) == 1 and line[0] not in (0, 4):
            result[i] = [line[0]]*size
    for j in range(len(grid[0])):
        column = [line[j] for line in grid]
        if len(set(column)) == 1 and column[0] not in (0, 4):
            for line in result:
                line[j] = column[0]
    return result


def draw_inputs(seed):
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError('seed must be an integer')
    rng = random.Random(int(digest(f'{TASK_ID}:layout:{seed}'.encode()), 16))
    colors = rng.sample([2, 3, 5, 6, 7, 8], 6)
    a, b, c, d, fill, sep = colors
    marked = [[a, b, c, d], [d, c, a, b]]
    for line, tail in zip(marked, ([1, fill], [1, 1])):
        line.extend(tail)
    vertical = canvas(marked, col_cut=3, vertical=1, separator=sep)
    preserve_fill = canvas([[a, b, 1, fill], [1, a, 1, 1]], col_cut=1, separator=sep)
    # Queries have more active macro cells than demos as well as larger canvases.
    query_macro = [[a, b, c, d], [d, c, a, b], [b, a, d, c], [c, d, b, a], [1, fill, 1, 1], [1, 1, fill, 1]]
    query = padded(canvas(query_macro, row_cut=3, vertical=1, mark_rows=(0, 3), separator=sep))
    return [
        {'role': 'demo_vertical_four_plus_fill', 'input': vertical},
        {'role': 'demo_horizontal_four_plus_fill', 'input': transpose(vertical)},
        {'role': 'demo_preserve_multicolor_plus_fill', 'input': preserve_fill},
        {'role': 'query_vertical_four_larger', 'input': query},
        {'role': 'query_horizontal_four_larger', 'input': transpose(query)},
    ]


def select_setting(seed):
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError('seed must be an integer')
    return SETTINGS[int(digest(f'{TASK_ID}:rule:{seed}'.encode()), 16) % len(SETTINGS)]


def episode(bridge, seed, mark_action=None):
    # Select once before any input/label draw; explicit setting is for review probes.
    setting = select_setting(seed) if mark_action is None else mark_action
    program = program_for(setting)
    draws = draw_inputs(seed)
    pairs = [{'input': item['input'], 'output': execute(bridge, program, item['input'])} for item in draws]
    predictions = {rival: [execute(bridge, program_for(rival), p['input']) for p in pairs] for rival in SETTINGS}
    consistent = [rival for rival in SETTINGS if all(predictions[rival][i] == pairs[i]['output'] for i in range(3))]
    other = next(rival for rival in SETTINGS if rival != setting)
    mismatches = [i for i in range(3) if predictions[other][i] != pairs[i]['output']]
    query_mismatches = [i for i in range(2) if predictions[other][i+3] != pairs[i+3]['output']]
    if consistent != [setting] or mismatches != [0, 1] or query_mismatches != [0, 1]:
        raise ValueError('demonstrations failed declared-rival identifiability')
    return {'status': 'proposed_research_prototype', 'task_id': TASK_ID, 'original_family': 'training:4e7e0eb9',
            'seed': seed, 'parameters': {'mark_action': setting}, 'program': program,
            'program_sha256': digest(program.encode()), 'train': pairs[:3], 'test': pairs[3:],
            'roles': [item['role'] for item in draws],
            'rivals': {'declared_settings': list(SETTINGS), 'consistent_settings': consistent,
                       'rival_demo_mismatches': mismatches,
                       'rival_query_mismatches': query_mismatches,
                       'executed_predictions': predictions}}


def public_challenge(private):
    return copy.deepcopy({'train': private['train'], 'test': [{'input': pair['input']} for pair in private['test']]})


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--mark-action', choices=SETTINGS)
    parser.add_argument('--all-settings', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.all_settings and args.mark_action:
        parser.error('--all-settings and --mark-action are mutually exclusive')
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'private').mkdir()
    (args.out / 'public').mkdir()
    ensure_tools()
    from arc_repl.racket_bridge import RacketBridge
    settings = SETTINGS if args.all_settings else (args.mark_action or select_setting(args.seed),)
    with RacketBridge(timeout=30) as bridge:
        canonical = canonical_record()
        parity = []
        for i, pair in enumerate(canonical['train'] + canonical['test']):
            result = execute(bridge, program_for(), pair['input'])
            parity.append({'index': i, 'input_sha256': digest(pair['input']), 'output_sha256': digest(result), 'matches': result == pair['output']})
        if not all(p['matches'] for p in parity):
            raise ValueError('canonical default parity failed')
        episodes = []
        for i, setting in enumerate(settings):
            private = episode(bridge, args.seed, setting)
            name = f'episode-{i}'
            write_json(args.out / 'private' / f'{name}.json', private)
            write_json(args.out / 'public' / f'{name}.json', public_challenge(private))
            (args.out / 'private' / f'{name}.rkt').write_text(private['program'])
            episodes.append({'private_path': f'private/{name}.json', 'public_path': f'public/{name}.json',
                             'program_path': f'private/{name}.rkt', 'parameters': private['parameters'],
                             'program_sha256': private['program_sha256'], 'rivals': {k:v for k,v in private['rivals'].items() if k != 'executed_predictions'},
                             'input_shapes': [[len(p['input']), len(p['input'][0])] for p in private['train']+private['test']]})
        ambiguous_input = canvas([[2, 3], [6, 8]], vertical=0)
        ambiguity = {setting: execute(bridge, program_for(setting), ambiguous_input) for setting in SETTINGS}
        write_json(args.out / 'private/two-band-ambiguity.json', {'input': ambiguous_input, 'executed_predictions': ambiguity, 'same_output': ambiguity[SETTINGS[0]] == ambiguity[SETTINGS[1]]})
    tracked = [HERE / 'prototype.py', HERE / 'README.md', HERE.parents[1] / 'tests/test_parametric_mark_action.py', canonical_path(ROOT), ROOT / 'shared/runtime/arc_repl/racket_bridge.py', ROOT / 'shared/runtime/puzzle_generators/rule_wrap.py']
    manifest = {'schema': 'arc-panel-parametric-prototype-v1', 'status': 'proposed', 'seed': args.seed,
                'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
                'canonical_default_parity': parity, 'episodes': episodes,
                'source_sha256': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in tracked},
                'files': {str(p.relative_to(args.out)): digest(p.read_bytes()) for p in sorted(args.out.rglob('*')) if p.is_file()},
                'limits': ['Finite two-setting rival set; no completeness or training-admission claim.', 'Research prototype only; production fixed canonical rule remains authoritative.', 'Balanced marked panels only in authored episodes; canonical program semantics for unbalanced and multiple marks preserved.']}
    write_json(args.out / 'manifest.json', manifest)
    print(json.dumps({'status': 'ok', 'canonical_pairs': len(parity), 'episodes': len(episodes), 'out': str(args.out)}))


if __name__ == '__main__':
    main()
