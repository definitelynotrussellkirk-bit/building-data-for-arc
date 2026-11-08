#!/usr/bin/env python3
"""Task-local proposed turn-order rules; never changes the production API."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = '563e1df172df'
DEFAULT_TURN_ORDER = 'horizontal_first'
TURN_ORDERS = ('horizontal_first', 'vertical_first')
ROOT = find_root(__file__)
TASK_HOME = ROOT / 'generators' / TASK_ID
CANONICAL_RECORD = ROOT / 'shared/data/base/solutions/training/a2fd1cf0__563e1df172df.json'

VERTICAL_RULE = '''(rule!
 (lambda (g)
   ;; Red is the start and green is the destination.  The elbow belongs on
   ;; green's row and red's column, so the vertical arm is drawn first.
   (define red (first (find-color g 2)))
   (define green (first (find-color g 3)))
   (define rr (first red))
   (define rc (second red))
   (define gr (first green))
   (define gc (second green))
   (define cmin (min rc gc))
   (define cmax (max rc gc))
   (define rmin (min rr gr))
   (define rmax (max rr gr))
   ;; Paint the vertical arm while preserving the red endpoint.
   (define with-column
     (reduce (lambda (out r)
               (if (= r rr) out (set-cell out r rc 8)))
             g
             (range rmin (+ rmax 1))))
   ;; Paint the horizontal arm while preserving the green endpoint.
   (reduce (lambda (out c)
             (if (= c gc) out (set-cell out gr c 8)))
           with-column
           (range cmin (+ cmax 1)))))'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_rule() -> str:
    record = json.loads(CANONICAL_RECORD.read_text())
    if record['task_id'] != TASK_ID:
        raise ValueError('canonical authority task ID mismatch')
    return record['racket_target']['target_code']


def rule_hash(source: str) -> str:
    """Same whitespace-normalized SHA-256 convention as the catalog rule pin."""
    return digest(' '.join(source.split()).encode())


def materialize_rule(turn_order=DEFAULT_TURN_ORDER) -> str:
    if type(turn_order) is not str or turn_order not in TURN_ORDERS:
        raise ValueError(f'turn_order must be one of {TURN_ORDERS!r}')
    return canonical_rule() if turn_order == DEFAULT_TURN_ORDER else VERTICAL_RULE


def select_turn_order(seed: int) -> str:
    """Choose once per episode with stable SHA-256, independent of input draws."""
    if type(seed) is not int:
        raise ValueError('seed must be a literal integer')
    index = hashlib.sha256(f'{TASK_ID}:turn_order:{seed}'.encode()).digest()[0] % 2
    return TURN_ORDERS[index]


def execute_rule(source: str, inputs: list) -> list:
    """Execute the exact rule! source with the included real Racket bridge.

    A lexical identity binding implements the rule! authoring wrapper; the
    wrapped lambda and every grid primitive execute in the included prelude.
    No Python transformation mirror or private runner is used for labels.
    """
    outputs = []
    with RacketBridge(timeout=15.0) as bridge:
        for grid in inputs:
            if (not isinstance(grid, list) or not grid or not grid[0]
                    or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)
                    or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)):
                raise ValueError('input must be a rectangular ARC integer grid')
            bridge.define_grid('parametric-input', grid)
            out = bridge.eval_text(f'(let ([rule! (lambda (f) f)]) ({source} parametric-input))')
            if (not isinstance(out, list) or len(out) != len(grid)
                    or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in out)
                    or any(type(cell) is not int or not 0 <= cell <= 9 for row in out for cell in row)):
                raise RuntimeError('Racket output is not an ARC grid of the input shape')
            outputs.append(out)
    return outputs


def build_episode(seed: int, *, turn_order=DEFAULT_TURN_ORDER, difficulty='medium', start=0) -> dict:
    if type(seed) is not int or type(start) is not int or start < 0:
        raise ValueError('seed and nonnegative start must be literal integers')
    # Parameter is resolved once, before the five independent input draws.
    setting = select_turn_order(seed) if turn_order is None else turn_order
    source = materialize_rule(setting)
    generator, _, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    inputs = [generator.generate(seed, start + offset, difficulty=difficulty) for offset in range(5)]
    if any(generator.self_check(grid) for grid in inputs):
        raise RuntimeError('production generator returned an unlawful input')
    outputs = execute_rule(source, inputs)
    rival = TURN_ORDERS[1 - TURN_ORDERS.index(setting)]
    rival_outputs = execute_rule(materialize_rule(rival), inputs)
    rejected = [i for i in range(4) if rival_outputs[i] != outputs[i]]
    if not rejected:
        raise RuntimeError('demonstrations do not identify turn_order against its declared rival')
    return {
        'challenge': {'train': [{'input': grid, 'output': out} for grid, out in zip(inputs[:4], outputs[:4])],
                      'test': [{'input': inputs[4]}]},
        'private': {
            'schema': 'task-local-parametric-prototype-v1', 'status': 'proposed prototype',
            'task_id': TASK_ID, 'seed': seed, 'difficulty': difficulty, 'start': start,
            'parameters': {'turn_order': setting}, 'query_outputs': outputs[4:],
            'generator_sha256': generator_sha256,
            'racket_text': source, 'racket_text_sha256': digest(source.encode()),
            'rule_hash': rule_hash(source)[:12],
            'input_sha256': [digest(json.dumps(g, separators=(',', ':')).encode()) for g in inputs],
            'rival_setting_check': {'turn_order': rival,
                                    'rejected_by_demo_indices': rejected,
                                    'query_disagrees': rival_outputs[4] != outputs[4],
                                    'rival_outputs': rival_outputs,
                                    'ambiguity': not rejected and rival_outputs[4] != outputs[4]},
            'sampling': {'sample_indices': list(range(start, start + 5)),
                         'rule_selection': 'seeded once' if turn_order is None else 'explicit once'},
        },
    }


def source_hashes() -> dict:
    paths = [*Path(__file__).parent.glob('*.py'), Path(__file__).parent / 'README.md',
             TASK_HOME / 'tests/test_parametric.py', TASK_HOME / 'generator.py', CANONICAL_RECORD,
             ROOT / 'shared/runtime/reviewer_support.py', ROOT / 'shared/runtime/arc_repl/racket_bridge.py',
             ROOT / 'shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt']
    return {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in sorted(paths) if path.is_file()}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def write_evidence(out: Path, *, seed: int, difficulty='medium', start=0) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)  # Never replace retained results.
    episodes = [build_episode(seed, turn_order=setting, difficulty=difficulty, start=start)
                for setting in TURN_ORDERS]
    for index, episode in enumerate(episodes):
        # Neutral public filenames reveal no hidden setting or source code.
        write_json(out / 'public' / f'episode-{index:03d}' / 'challenge.json', episode['challenge'])
        write_json(out / 'private' / f'episode-{index:03d}.json', episode['private'])
        (out / 'private' / f'episode-{index:03d}.rkt').write_text(episode['private']['racket_text'])
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    actual = execute_rule(materialize_rule(), [pair['input'] for pair in pairs])
    parity = [{'variant': p['variant'], 'split': p['split'], 'pair_index': p['pair_index'],
               'input': p['input'], 'expected': p['output'], 'actual': label, 'equal': label == p['output']}
              for p, label in zip(pairs, actual)]
    if not all(row['equal'] for row in parity):
        raise RuntimeError('default parameter disagrees with canonical labels')
    write_json(out / 'private/canonical-parity.json', parity)
    witness_input = episodes[0]['challenge']['train'][0]['input']
    witness = {'input': witness_input, 'self_check_errors': [],
               'outputs': {setting: episodes[i]['challenge']['train'][0]['output']
                           for i, setting in enumerate(TURN_ORDERS)}}
    witness['settings_disagree'] = witness['outputs'][TURN_ORDERS[0]] != witness['outputs'][TURN_ORDERS[1]]
    if not witness['settings_disagree']:
        raise RuntimeError('same-input turn-order witness does not discriminate')
    write_json(out / 'private/same-input-witness.json', witness)
    manifest = {
        'schema': 'task-local-parametric-evidence-v1', 'status': 'proposed prototype',
        'task_id': TASK_ID, 'seed': seed, 'difficulty': difficulty, 'start': start,
        'parameter': {'name': 'turn_order', 'values': TURN_ORDERS, 'default': DEFAULT_TURN_ORDER,
                      'input_constraints_depend_on_parameter': False},
        'prototype_source_hashes': source_hashes(), 'runtime': racket_runtime_status(),
        'rules': {setting: {'text': materialize_rule(setting),
                            'text_sha256': digest(materialize_rule(setting).encode()),
                            'rule_hash': rule_hash(materialize_rule(setting))[:12]}
                  for setting in TURN_ORDERS},
        'canonical_parity': {'checked': len(parity), 'passed': sum(row['equal'] for row in parity)},
        'episodes': [{'public': f'public/episode-{i:03d}/challenge.json',
                      'private': f'private/episode-{i:03d}.json', 'parameters': {'turn_order': setting},
                      'demonstrations': 4, 'queries': 1,
                      'rival_rejected_by_demo_indices': episodes[i]['private']['rival_setting_check']['rejected_by_demo_indices']}
                     for i, setting in enumerate(TURN_ORDERS)],
        'same_input_disagreement': witness['settings_disagree'],
        'command': {'argv': sys.argv, 'executable': sys.executable, 'cwd': str(Path.cwd()),
                    'wrapper': 'python3 run_with_racket.py COMMAND [ARGS...] from WORK'},
        'limitations': ['Two settings and one five-pair episode per setting at this seed; finite evidence only.',
                        'Rival check concerns only the other turn_order; no universal learner identifiability claim.',
                        'Prototype only: neither production parametric API nor rule approval nor training admission.'],
    }
    write_json(out / 'private/manifest.json', manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path, help='fresh evidence directory, relative to repo')
    parser.add_argument('--seed', type=int, default=173)
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], default='medium')
    parser.add_argument('--start', type=int, default=0)
    args = parser.parse_args()
    manifest = write_evidence(args.out, seed=args.seed, difficulty=args.difficulty, start=args.start)
    print(json.dumps({'status': manifest['status'], 'canonical_parity': manifest['canonical_parity'],
                      'episodes': len(manifest['episodes']), 'same_input_disagreement': manifest['same_input_disagreement']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
