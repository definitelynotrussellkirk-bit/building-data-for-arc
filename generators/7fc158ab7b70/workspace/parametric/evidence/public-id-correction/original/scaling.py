#!/usr/bin/env python3
"""Proposed finite aggregate-count / cell-replication family, separate from production."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import shlex
import sys

TASK_ID = '7fc158ab7b70'
VERSION = 'proposed-parametric-1.0.0'
COUNT_BASES = ('cells', 'colors')
SCALE_AXES = ('both', 'rows', 'columns')


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def digest(value):
    return text_hash(json.dumps(value, sort_keys=True, separators=(',', ':')))


@dataclass(frozen=True)
class Setting:
    count_basis: str = 'cells'
    scale_axes: str = 'both'

    def __post_init__(self):
        if self.count_basis not in COUNT_BASES or self.scale_axes not in SCALE_AXES:
            raise ValueError('count_basis must be cells|colors; scale_axes must be both|rows|columns')

    @property
    def name(self):
        return self.count_basis + '-' + self.scale_axes

    def as_dict(self):
        return {'count_basis': self.count_basis, 'scale_axes': self.scale_axes}


DEFAULT = Setting()
SETTINGS = tuple(Setting(basis, axes) for basis in COUNT_BASES for axes in SCALE_AXES)


def _seed(seed):
    if type(seed) is not int:
        raise TypeError('seed must be an int (not bool, float, or string)')


def choose_setting(seed, *, count_basis=None, scale_axes=None, seedchoose=False):
    """Called once per episode; random rule selection has an independent RNG stream."""
    _seed(seed)
    if type(seedchoose) is not bool:
        raise TypeError('seedchoose must be bool')
    if seedchoose:
        if count_basis is not None or scale_axes is not None:
            raise ValueError('seedchoose cannot be combined with explicit parameter values')
        return random.Random(f'{VERSION}:setting:{seed}').choice(SETTINGS)
    return Setting('cells' if count_basis is None else count_basis,
                   'both' if scale_axes is None else scale_axes)


def counts(grid):
    values = [cell for row in grid for cell in row if cell != 0]
    return len(values), len(set(values))


def validate_input(grid):
    if not isinstance(grid, list) or not 3 <= len(grid) <= 5:
        raise ValueError('input must be a square grid of side 3..5')
    n = len(grid)
    if any(not isinstance(row, list) or len(row) != n for row in grid):
        raise ValueError('input must be square')
    if any(type(c) is not int or not 0 <= c <= 9 for row in grid for c in row):
        raise ValueError('input colors must be integer ARC colors 0..9')
    cells, colors = counts(grid)
    if not 2 <= cells <= 6 or n * cells > 30:
        raise ValueError('require 2..6 nonzero cells and side * cells <= 30')
    if colors == 1:
        locations = [(r, c) for r in range(n) for c in range(n) if grid[r][c]]
        if cells != 2 or sum(abs(a - b) for a, b in zip(*locations)) <= 1:
            raise ValueError('monochrome input must be two spatially separated cells')


def predict(grid, setting=DEFAULT):
    """Independent Python mirror used for parity checking, never authoritative labels."""
    validate_input(grid)
    amount = counts(grid)[COUNT_BASES.index(setting.count_basis)]
    row_factor = amount if setting.scale_axes in ('both', 'rows') else 1
    col_factor = amount if setting.scale_axes in ('both', 'columns') else 1
    return [[cell for cell in row for _ in range(col_factor)]
            for row in grid for _ in range(row_factor)]


def racket_source(setting=DEFAULT):
    """A complete callable Racket expression; every setting changes executed semantics."""
    count = ('(length nonzero)' if setting.count_basis == 'cells'
             else '(length (remove-duplicates nonzero))')
    rf = 'amount' if setting.scale_axes in ('both', 'rows') else '1'
    cf = 'amount' if setting.scale_axes in ('both', 'columns') else '1'
    return f'''(lambda (g)
  (let* ((nonzero (filter (lambda (v) (not (= v 0))) (apply append g)))
         (amount {count})
         (row-factor {rf})
         (col-factor {cf}))
    (for*/list ((r (in-range (* (length g) row-factor))))
      (for/list ((c (in-range (* (length (car g)) col-factor))))
        (list-ref (list-ref g (quotient r row-factor))
                  (quotient c col-factor))))))\n'''


def generate_inputs(seed, *, train=3, test=4):
    """Construct a contrastive prefix; all settings use the same legal input domain."""
    _seed(seed)
    if type(train) is not int or not 3 <= train <= 20:
        raise ValueError('train must be an integer in 3..20; three contrastive demos are required')
    if type(test) is not int or not 1 <= test <= 100:
        raise ValueError('test must be an integer in 1..100')
    rng = random.Random(f'{VERSION}:inputs:{seed}')
    # First demo isolates repeated cells from colors; second has >1 color so
    # color-count variants cannot hide their axes behind the identity factor 1.
    profiles = [(3, 2, 1), (4, 4, 2), (3, 3, 3),
                (5, 6, 3), (4, 5, 3), (3, 2, 2), (5, 4, 3)]
    result, seen = [], set()
    for index in range(train + test):
        n, cells, colors = (profiles[index] if index < len(profiles)
                            else (rng.choice((3, 4, 5)), rng.randint(3, 6), rng.choice((2, 3))))
        colors = min(colors, cells)
        for _ in range(5000):
            palette = rng.sample(range(1, 10), colors)
            positions = rng.sample(range(n * n), cells)
            values = [palette[i % colors] for i in range(cells)]
            rng.shuffle(values)
            grid = [[0] * n for _ in range(n)]
            for position, color in zip(positions, values):
                grid[position // n][position % n] = color
            try:
                validate_input(grid)
            except ValueError:
                continue
            identity = digest(grid)
            if identity not in seen:
                seen.add(identity)
                result.append(grid)
                break
        else:
            raise RuntimeError('bounded input sampler exhausted; no short episode was emitted')
    return result


class RacketLabeler:
    """Reuse the included protected bridge; memoization reuses actual Racket executions."""
    def __init__(self, root):
        from arc_repl.racket_bridge import RacketBridge
        from reviewer_support import canonical_path, load_selected_generator
        self.root = Path(root)
        self.generator, self.generator_path, self.generator_hash = load_selected_generator(TASK_ID, root=root)
        rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
        sources = {r['program_solution'] for r in rows if r.get('task_id') == TASK_ID}
        if len(sources) != 1:
            raise ValueError('canonical source must resolve unambiguously')
        self.canonical_source = sources.pop()
        stripped = self.canonical_source.strip()
        if not stripped.startswith('(rule! ') or not stripped.endswith(')'):
            raise ValueError('unsupported canonical rule wrapper')
        self.canonical_callable = stripped[len('(rule! '):-1]
        self.bridge = RacketBridge()
        self.cache = {}
        self.executions = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.bridge.close()

    @property
    def runtime_identity(self):
        return self.bridge.runtime_identity

    def label(self, source, grid):
        validate_input(grid)
        key = (text_hash(source), digest(grid))
        if key not in self.cache:
            literal = '(' + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
            self.cache[key] = self.bridge.eval_text(f"({source} '{literal})")
            self.executions += 1
        output = deepcopy(self.cache[key])
        if (not isinstance(output, list) or not 1 <= len(output) <= 30
                or any(not isinstance(row, list) or not 1 <= len(row) <= 30 for row in output)
                or len({len(row) for row in output}) != 1
                or any(type(c) is not int or not 0 <= c <= 9 for row in output for c in row)):
            raise AssertionError('Racket returned a malformed/out-of-bounds ARC grid')
        return output


def identify_demonstrations(demonstrations, labeler):
    """Only demonstrations enter rule selection. Query labels are not an argument."""
    if not demonstrations:
        raise ValueError('at least one demonstration is required')
    return [setting.name for setting in SETTINGS
            if all(labeler.label(racket_source(setting), p['input']) == p['output']
                   for p in demonstrations)]


def build_episode(seed, *, setting=None, train=3, test=4, labeler=None):
    if labeler is None:
        from reviewer_support import find_root
        with RacketLabeler(find_root(__file__)) as owned_labeler:
            return build_episode(seed, setting=setting, train=train, test=test, labeler=owned_labeler)
    fixed = setting if setting is not None else choose_setting(seed)
    if not isinstance(fixed, Setting):
        raise TypeError('setting must be a Setting')
    inputs = generate_inputs(seed, train=train, test=test)
    source = racket_source(fixed)
    pairs = [{'input': g, 'output': labeler.label(source, g)} for g in inputs]
    if any(p['output'] != predict(p['input'], fixed) for p in pairs):
        raise AssertionError('Python mirror disagrees with matching instantiated Racket')
    demos, queries = pairs[:train], pairs[train:]
    # This set is computed before and without reading a query output.
    survivors = identify_demonstrations(demos, labeler)
    if survivors != [fixed.name]:
        raise AssertionError(f'demonstrations do not uniquely identify setting: {survivors}')
    rivals = []
    for rival in SETTINGS:
        rival_source = racket_source(rival)
        failures = [i for i, pair in enumerate(demos)
                    if labeler.label(rival_source, pair['input']) != pair['output']]
        rivals.append({'setting': rival.name, 'racket_sha256': text_hash(rival_source),
                       'refuted_by_demo_indices': failures, 'survives_demos': not failures})
    per_query = []
    for index, pair in enumerate(queries):
        predictions = []
        ambiguous = []
        for rival in SETTINGS:
            output = labeler.label(racket_source(rival), pair['input'])
            disagrees = output != pair['output']
            if rival.name in survivors and disagrees:
                ambiguous.append(rival.name)
            predictions.append({'setting': rival.name, 'survives_demos': rival.name in survivors,
                                'disagrees_with_selected': disagrees, 'output_sha256': digest(output),
                                'output_shape': [len(output), len(output[0])]})
        per_query.append({'query_index': index, 'ambiguous_rivals': ambiguous, 'predictions': predictions})
    canonical_outputs = [labeler.label(labeler.canonical_callable, g) for g in inputs]
    parity = [out == predict(g, DEFAULT) for out, g in zip(canonical_outputs, inputs)]
    if not all(parity):
        raise AssertionError('canonical setting does not match selected reference execution')
    return {
        'schema': 'proposed-parametric-scaling-v1', 'status': 'proposed_prototype',
        'task_id': TASK_ID, 'seed': seed, 'version': VERSION, 'setting': fixed.as_dict(),
        'pairs': {'train': demos, 'test': queries},
        'authority': {'backend': 'racket', 'rule_text': source, 'rule_sha256': text_hash(source),
                      'runtime': labeler.runtime_identity},
        'canonical_parity': {'source_text': labeler.canonical_source,
                             'source_sha256': text_hash(labeler.canonical_source),
                             'all_equal': all(parity), 'per_pair_equal': parity,
                             'generator_sha256': labeler.generator_hash},
        'identification': {'scope': 'exactly the six declared settings; demonstrations only',
                           'demo_survivors': survivors, 'rivals': rivals, 'queries': per_query},
        'checks': {'input_distinct_count': len({digest(g) for g in inputs}),
                   'demonstration_counts': [list(counts(g)) for g in inputs[:train]],
                   'input_shapes': [[len(g), len(g[0])] for g in inputs],
                   'output_shapes': [[len(p['output']), len(p['output'][0])] for p in pairs]},
    }


def public_challenge(episode):
    return {'train': deepcopy(episode['pairs']['train']),
            'test': [{'input': deepcopy(p['input'])} for p in episode['pairs']['test']]}


def _write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--train', type=int, default=3)
    parser.add_argument('--test', type=int, default=4)
    parser.add_argument('--count-basis', choices=COUNT_BASES)
    parser.add_argument('--scale-axes', choices=SCALE_AXES)
    parser.add_argument('--seedchoose', action='store_true')
    parser.add_argument('--all-settings', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.all_settings and (args.count_basis or args.scale_axes or args.seedchoose):
        parser.error('--all-settings cannot be combined with setting selection')
    settings = SETTINGS if args.all_settings else (choose_setting(
        args.seed, count_basis=args.count_basis, scale_axes=args.scale_axes, seedchoose=args.seedchoose),)
    from reviewer_support import find_root
    root = find_root(__file__)
    # Reject invalid counts before opening runtime or creating an output directory.
    generate_inputs(args.seed, train=args.train, test=args.test)
    args.out.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    source_files = [script, script.with_name('README.md'),
                    root / 'generators' / TASK_ID / 'tests/test_parametric_scaling.py']
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in source_files if p.is_file()}
    summary = {'schema': 'proposed-parametric-scaling-suite-v1', 'status': 'proposed_prototype',
               'command': shlex.join([sys.executable, *sys.argv]),
               'effective_cwd': str(Path.cwd()), 'seed': args.seed,
               'train': args.train, 'test': args.test, 'selection_mode':
               'all-settings' if args.all_settings else 'seedchoose' if args.seedchoose else 'fixed',
               'source_hashes': hashes, 'episodes': [],
               'limitations': ['Finite six-setting rival inventory is not universal identifiability.',
                               'This prototype does not change canonical runtime interfaces or approval.',
                               'Input domain remains square 3..5 with 2..6 nonzero cells; output side <=30.',
                               'Evidence covers recorded seed and settings, not all random seeds.',
                               'train is bounded 3..20 and test 1..100; bounded sampler fails visibly.']}
    with RacketLabeler(root) as labeler:
        for setting in settings:
            episode = build_episode(args.seed, setting=setting, train=args.train, test=args.test, labeler=labeler)
            folder = args.out / setting.name
            folder.mkdir()
            _write_json(folder / 'public.json', public_challenge(episode))
            _write_json(folder / 'private.json', episode)
            (folder / 'rule.rkt').write_text(racket_source(setting))
            summary['episodes'].append({'setting': setting.as_dict(), 'path': setting.name,
                                        'train': args.train, 'test': args.test,
                                        'demo_survivors': episode['identification']['demo_survivors'],
                                        'ambiguous_queries': sum(bool(q['ambiguous_rivals'])
                                                                 for q in episode['identification']['queries']),
                                        'public_sha256': hashlib.sha256((folder / 'public.json').read_bytes()).hexdigest(),
                                        'private_sha256': hashlib.sha256((folder / 'private.json').read_bytes()).hexdigest()})
        summary['actual_racket_evaluations'] = labeler.executions
        summary['runtime'] = labeler.runtime_identity
    _write_json(args.out / 'manifest.json', summary)
    print(json.dumps({'status': summary['status'], 'episodes': len(settings),
                      'train': args.train, 'test': args.test,
                      'racket_evaluations': summary['actual_racket_evaluations'], 'out': str(args.out)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
