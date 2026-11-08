"""Bounded, source-bound teaching audit with protected Racket labels.

Run from WORK through the packet wrapper, for example::

    ../review.py run python3 generators/b57f299dcdb3/workspace/parametric/check_family.py \
        --out ../checks/b57f299dcdb3/self-audit

The declared shortcut rivals are Python hypotheses, except the retained global
frequency selector, which is also replayed as standalone Racket. A rival that
fits every demonstration is reported even when it agrees on all four queries.
This audit neither accepts a family nor establishes completeness of its rivals.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = 'b57f299dcdb3'
FAMILY_HOME = Path(__file__).resolve().parent
ROOT = next(parent for parent in FAMILY_HOME.parents
            if (parent / 'shared/runtime/reviewer_support.py').is_file()
            and (parent / 'src/arcpuzzles').is_dir())
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]

from arcpuzzles import parametric_worker  # noqa: E402
from reviewer_support import (  # noqa: E402
    canonical_path, find_root, public_challenge_bytes, public_challenge_id,
)

if find_root(__file__) != ROOT:
    raise RuntimeError('audit and canonical authority must belong to the same checkout')


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(raw(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_adapter():
    path = FAMILY_HOME / 'adapter.py'
    name = '_b57_audit_adapter_' + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_inventory():
    paths = [ROOT / f'generators/{TASK_ID}/generator.py',
             *(FAMILY_HOME / name for name in
               ('prototype.py', 'adapter.py', 'canonical.rkt', 'promotion.json', 'check_family.py')),
             canonical_path(ROOT), ROOT / 'src/arcpuzzles/parametric_worker.py',
             ROOT / 'shared/runtime/reviewer_support.py',
             ROOT / 'shared/runtime/puzzle_generators/rule_wrap.py']
    return [{'path': str(path.relative_to(ROOT)), 'sha256': file_hash(path),
             'bytes': path.stat().st_size} for path in paths]


def best_color(colors):
    """Deterministic total rival selector: lowest color wins frequency ties."""
    counts = Counter(colors)
    return min(counts, key=lambda color: (-counts[color], color)) if counts else 0


RIVAL_DESCRIPTIONS = {
    'global_frequency': 'Most frequent eligible pixel color in the entire input; lowest-color tie break.',
    'first_center': 'Petal color of the first complete yellow-centered plus in row-major order.',
    'last_center': 'Petal color of the last complete yellow-centered plus in row-major order.',
    'min_color': 'Smallest color among complete yellow-centered pluses.',
    'max_color': 'Largest color among complete yellow-centered pluses.',
    'first_duplicate': 'First petal color encountered twice in row-major order; first color if none repeats.',
    'loose_three_arms': 'Census admits a yellow center when at least three orthogonal arms match.',
    'north_of_yellow': 'Census uses the eligible northern neighbor of every interior yellow pixel.',
    'marker_free_census': 'Census admits four equal eligible arms around a center of any color.',
    'four_petals_per_valid_plus': 'Count all four petals per complete plus; an intentionally equivalent census control.',
    'all_pluses': 'Keep every complete yellow-centered plus, without choosing a winner.',
    'repeated_pluses': 'Keep complete pluses of every color that occurs at least twice.',
    'winner_pixels': 'Keep all winner-color pixels, plus the centers of complete winning pluses.',
    'partial_winner': 'Keep winner-colored arms and the yellow center whenever at least three arms match the winner.',
}
MASK_RIVALS = {'all_pluses', 'repeated_pluses', 'winner_pixels', 'partial_winner'}


def rival_outputs(prototype, grid, settings):
    """Pure Python rivals. Selector rivals retain the intended readout stage."""
    info = prototype.analyze(grid)
    background, centers = info['background'], info['centers']
    colors = [color for _, _, color in centers]
    eligible = lambda color: color not in (0, 4, background)
    selectors = {
        'global_frequency': best_color(color for row in grid for color in row if eligible(color)),
        'first_center': colors[0] if colors else 0,
        'last_center': colors[-1] if colors else 0,
        'min_color': min(colors) if colors else 0,
        'max_color': max(colors) if colors else 0,
        'four_petals_per_valid_plus': best_color(color for color in colors for _ in range(4)),
    }
    seen = set()
    duplicate = colors[0] if colors else 0
    for color in colors:
        if color in seen:
            duplicate = color
            break
        seen.add(color)
    selectors['first_duplicate'] = duplicate
    loose, north, marker_free = [], [], []
    for row in range(1, len(grid)-1):
        for col in range(1, len(grid[0])-1):
            petals = [grid[row+dr][col+dc] for dr, dc in prototype.ARMS]
            if len(set(petals)) == 1 and eligible(petals[0]):
                marker_free.append(petals[0])
            if grid[row][col] == 4:
                if eligible(petals[0]):
                    north.append(petals[0])
                frequent = best_color(color for color in petals if eligible(color))
                if frequent and petals.count(frequent) >= 3:
                    loose.append(frequent)
    selectors.update(loose_three_arms=best_color(loose), north_of_yellow=best_color(north),
                     marker_free_census=best_color(marker_free))
    if settings['readout'] == 'winner_color':
        return {name: [[color]] for name, color in selectors.items()}
    outputs = {name: prototype.mask_for_colors(grid, centers, {color})
               for name, color in selectors.items()}
    outputs['all_pluses'] = prototype.mask_for_colors(grid, centers, set(colors))
    outputs['repeated_pluses'] = prototype.mask_for_colors(
        grid, centers, {color for color, n in info['counts'].items() if n >= 2})
    winning_centers = {(row, col) for row, col, color in centers if color == info['winner']}
    outputs['winner_pixels'] = [
        [value if value == info['winner'] or (row, col) in winning_centers else 0
         for col, value in enumerate(values)] for row, values in enumerate(grid)]
    partial = [[0] * len(grid[0]) for _ in grid]
    for row in range(1, len(grid)-1):
        for col in range(1, len(grid[0])-1):
            petals = [grid[row+dr][col+dc] for dr, dc in prototype.ARMS]
            if grid[row][col] == 4 and petals.count(info['winner']) >= 3:
                partial[row][col] = 4
                for dr, dc in prototype.ARMS:
                    if grid[row+dr][col+dc] == info['winner']:
                        partial[row+dr][col+dc] = info['winner']
    outputs['partial_winner'] = partial
    return outputs


def global_frequency_program(prototype, readout):
    expression = '''(let* ((field-bg (mode g)) (freq (make-hash))
                           (best 0) (best-count -1))
      (for* ((r (range (rows g))) (c (range (cols g))))
        (let ((color (at g r c)))
          (when (and (!= color 0) (!= color 4) (!= color field-bg))
            (hash-set! freq color (+ 1 (hash-ref freq color 0))))))
      (for ((color (range 10)))
        (when (and (hash-has-key? freq color) (> (hash-ref freq color) best-count))
          (set! best color) (set! best-count (hash-ref freq color))))
      best)'''
    if readout == 'winner_color':
        return f'(rule! (lambda (g) (let ((winner {expression})) (build-grid 1 1 (r c) winner))))'
    return prototype.mask_program(expression)


def write_json(path, value):
    path.write_bytes(raw(value))


def audit(out, seeds, demo_counts):
    if out.exists():
        raise ValueError(f'output must be a new path: {out}')
    out.mkdir(parents=True)
    (out / 'private').mkdir()
    (out / 'public').mkdir()
    inventory = source_inventory()
    adapter = load_adapter()
    prototype = adapter._prototype
    programs = {readout: adapter.program({'readout': readout}) for readout in prototype.READOUTS}
    canonical_programs = set()
    for line in canonical_path(ROOT).read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        if row.get('task_id') == TASK_ID:
            canonical_programs.add(row['program_solution'])
    if canonical_programs != {programs['winner_color']}:
        raise ValueError('the default does not match selected canonical authority byte-for-byte')

    report = {'schema': 'b57f299dcdb3-finite-rival-audit-v1', 'task_id': TASK_ID,
              'status': 'running', 'scope': {'seeds': seeds, 'demos': demo_counts, 'queries': 4},
              'limits': ['Finite declared Python rivals are not an exhaustive rule search.',
                         'A query-equivalent survivor is retained, not treated as eliminated.',
                         'This report does not grant family acceptance or training admission.'],
              'sources': inventory, 'programs': {name: hashlib.sha256(text.encode()).hexdigest()
                                               for name, text in programs.items()},
              'rivals': RIVAL_DESCRIPTIONS, 'jobs': [], 'boundary_probes': [], 'failures': []}
    labels, refs, ambiguous, baselines = [], {}, [], {}
    examples = {}
    evaluations = 0
    claims = 0
    apply, identity, bridge = parametric_worker._real_evaluator(ROOT / 'shared/runtime')
    report['racket'] = identity

    def execute(program, grid):
        nonlocal evaluations
        evaluations += 1
        return parametric_worker._grid(apply(program, copy.deepcopy(grid)))

    def check_label(claim, actual, context):
        nonlocal claims
        claims += 1
        if claim != actual:
            report['failures'].append({'kind': 'racket_label_mismatch', **context,
                                       'claim_sha256': digest(claim), 'actual_sha256': digest(actual)})

    try:
        for seed in seeds:
            for demos in demo_counts:
                for readout in prototype.READOUTS:
                    settings = {'readout': readout}
                    job_id = f's{seed}-d{demos}-{readout}'
                    episode = adapter.generate(seed, settings, demos, 4)
                    if episode.get('program_solution') != programs[readout]:
                        raise ValueError('generated program differs from declared program')
                    if len(episode['train']) != demos or len(episode['test']) != 4:
                        raise ValueError('the episode did not satisfy requested pair counts')
                    pairs = episode['train'] + episode['test']
                    input_hashes = [digest(pair['input']) for pair in pairs]
                    if len(set(input_hashes)) != len(input_hashes):
                        report['failures'].append({'kind': 'duplicate_input', 'job': job_id})
                    baseline_key = (seed, demos)
                    if baseline_key not in baselines:
                        baselines[baseline_key] = input_hashes
                    matched = baselines[baseline_key] == input_hashes
                    if not matched:
                        report['failures'].append({'kind': 'settings_change_inputs', 'job': job_id})
                    actual = []
                    for index, pair in enumerate(pairs):
                        parametric_worker._grid(pair['input'])
                        output = execute(programs[readout], pair['input'])
                        check_label(pair['output'], output, {'job': job_id, 'pair': index})
                        actual.append(output)
                    verified = {'train': [{'input': pair['input'], 'output': output}
                                           for pair, output in zip(pairs[:demos], actual[:demos])],
                                'test': [{'input': pair['input'], 'output': output}
                                         for pair, output in zip(pairs[demos:], actual[demos:])]}
                    turn_ids = []
                    for pair in verified['test']:
                        challenge = {'train': verified['train'], 'test': [{'input': pair['input']}]}
                        public_id = public_challenge_id(challenge)
                        public_bytes = public_challenge_bytes(challenge)
                        if hashlib.sha256(public_bytes).hexdigest() != public_id:
                            raise RuntimeError('public helper ID and bytes disagree')
                        path = out / 'public' / f'{public_id}.json'
                        if path.exists() and path.read_bytes() != public_bytes:
                            raise RuntimeError('conflicting public bytes')
                        path.write_bytes(public_bytes)
                        public_value = json.loads(public_bytes)
                        if set(public_value) != {'train', 'test'} or any(set(q) != {'input'} for q in public_value['test']):
                            raise RuntimeError('public projection leaked private fields')
                        turn_ids.append(public_id)
                    rows = [rival_outputs(prototype, pair['input'], settings) for pair in pairs]
                    names = sorted(rows[0])
                    rivals = {}
                    for name in names:
                        outputs = [parametric_worker._grid(row[name]) for row in rows]
                        demo_matches = [a == b for a, b in zip(outputs[:demos], actual[:demos])]
                        query_matches = [a == b for a, b in zip(outputs[demos:], actual[demos:])]
                        fits = all(demo_matches)
                        status = ('eliminated_by_demonstrations' if not fits else
                                  'survives_demos_and_agrees_on_checked_queries' if all(query_matches) else
                                  'survives_demos_but_disagrees_on_query')
                        rivals[name] = {'status': status, 'demo_matches': demo_matches,
                                        'query_matches': query_matches,
                                        'output_sha256': [digest(value) for value in outputs]}
                        if fits and not all(query_matches):
                            witness = {'job': job_id, 'rival': name,
                                       'disagreeing_queries': [i for i, equal in enumerate(query_matches) if not equal],
                                       'public_turn_ids': turn_ids,
                                       'rival_train_outputs': outputs[:demos],
                                       'rival_query_outputs': outputs[demos:]}
                            ambiguous.append(witness)
                            report['failures'].append({'kind': 'demo_consistent_query_disagreement',
                                                       'job': job_id, 'rival': name})
                        if not fits:
                            index = next(i for i, equal in enumerate(demo_matches) if not equal)
                            grid = pairs[index]['input']
                            key = (readout, name)
                            witness = {'job': job_id, 'settings': settings, 'rival': name,
                                       'demo_index': index, 'input': grid, 'racket_output': actual[index],
                                       'rival_output': outputs[index], 'input_sha256': input_hashes[index],
                                       'program_sha256': report['programs'][readout]}
                            old = refs.get(key)
                            if old is None or len(grid)*len(grid[0]) < len(old['input'])*len(old['input'][0]):
                                refs[key] = witness
                    record = {'id': job_id, 'seed': seed, 'settings': settings, 'demos': demos, 'queries': 4,
                              'matched_inputs_across_settings': matched, 'all_inputs_distinct': len(set(input_hashes)) == len(input_hashes),
                              'shapes': [[len(p['input']), len(p['input'][0])] for p in pairs],
                              'census_counts': [sorted(prototype.analyze(p['input'])['counts'].values(), reverse=True) for p in pairs],
                              'input_sha256': input_hashes, 'public_turn_ids': turn_ids,
                              'rivals': rivals, 'surviving_rivals': [name for name, row in rivals.items()
                                                                    if row['status'] != 'eliminated_by_demonstrations']}
                    report['jobs'].append(record)
                    labels.append({'job': job_id, 'program_sha256': report['programs'][readout],
                                   'public_turn_ids': turn_ids, 'racket_train_outputs': actual[:demos],
                                   'racket_query_outputs': actual[demos:]})
                    if seed == seeds[0] and demos == demo_counts[0]:
                        examples[readout] = verified

        # The selector used in a later causal witness is an actual standalone
        # Racket hypothesis here, with the same deterministic tie policy.
        replay = []
        for readout, episode in examples.items():
            program = global_frequency_program(prototype, readout)
            program_path = out / 'private' / f'global_frequency.{readout}.rkt'
            program_path.write_text(program, encoding='utf-8')
            pairs = episode['train'] + episode['test']
            outputs = [execute(program, pair['input']) for pair in pairs]
            python_outputs = [rival_outputs(prototype, pair['input'], {'readout': readout})['global_frequency']
                              for pair in pairs]
            parity = outputs == python_outputs
            if not parity:
                report['failures'].append({'kind': 'global_rival_racket_python_disagreement', 'readout': readout})
            replay.append({'settings': {'readout': readout}, 'program_path': str(program_path.relative_to(out)),
                           'program_sha256': hashlib.sha256(program.encode()).hexdigest(),
                           'racket_python_parity': parity, 'racket_outputs': outputs,
                           'matches_truth': [output == pair['output'] for output, pair in zip(outputs, pairs)]})
        write_json(out / 'private' / 'global_rival_replay.json', replay)
        report['global_rival_replay'] = [{key: value for key, value in row.items() if key != 'racket_outputs'}
                                          for row in replay]

        for seed in seeds:
            for side in (12, 30):
                for counts in ((2,1,1), (3,2,1), (4,1,1), (4,3,2,1)):
                    probe = {'seed': seed, 'shape': [side, side], 'requested_counts': list(counts)}
                    slots = len(prototype._axis_positions(side)) ** 2
                    needed = sum(counts) + 2*max(counts) + 2
                    probe.update(required_motif_slots=needed, available_motif_slots=slots)
                    try:
                        grid = prototype.sample_input(seed, height=side, width=side, counts=counts, boundary=True)
                    except ValueError as error:
                        probe.update(status='capacity_rejection' if needed > slots else 'unexpected_rejection',
                                     message=str(error))
                        if needed <= slots:
                            report['failures'].append({'kind': 'boundary_probe_rejected', **probe})
                    else:
                        probe.update(status='executed', input_sha256=digest(grid),
                                     actual_counts=sorted(prototype.analyze(grid)['counts'].values(), reverse=True),
                                     outputs={})
                        for readout in prototype.READOUTS:
                            settings = {'readout': readout}
                            output = execute(programs[readout], grid)
                            check_label(adapter.solve_python(grid, settings), output,
                                        {'boundary_probe': {'seed': seed, 'side': side, 'counts': list(counts)},
                                         'settings': settings})
                            probe['outputs'][readout] = {'shape': [len(output), len(output[0])],
                                                         'sha256': digest(output),
                                                         'nonzero_cells': sum(value != 0 for row in output for value in row)}
                    report['boundary_probes'].append(probe)
    except Exception as error:
        # Execution errors are failures, never evidence that a rival was taught
        # away. Retain any completed jobs and the exact interruption reason.
        report['failures'].append({'kind': 'execution_error', 'error': type(error).__name__,
                                   'message': str(error)})
    finally:
        bridge.close()

    stable = inventory == source_inventory()
    if not stable:
        report['failures'].append({'kind': 'source_changed_during_audit'})
    report.update(status='pass' if not report['failures'] else 'fail', sources_unchanged=stable,
                  racket_evaluations=evaluations, checked_label_claims=claims,
                  python_rival_implementation='check_family.py; selector rivals share the complete-object detector and selected readout',
                  private_labels='private/labels.json', smallest_sampled_refuters='private/refuters.json',
                  ambiguous_survivors='private/ambiguous_survivors.json', private_example='private/example.json')
    write_json(out / 'private' / 'labels.json', labels)
    write_json(out / 'private' / 'refuters.json', list(refs.values()))
    write_json(out / 'private' / 'ambiguous_survivors.json', ambiguous)
    write_json(out / 'private' / 'example.json',
               {'seed': seeds[0], 'demos': demo_counts[0], 'queries': 4,
                'programs': programs, 'episodes': examples, 'sources': inventory})
    write_json(out / 'report.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New evidence directory; existing paths are refused.')
    parser.add_argument('--seed', type=int, action='append', help='Repeat to override bounded default seeds 0 and 17.')
    parser.add_argument('--demos', type=int, action='append', help='Repeat to override default counts 2 and 3; allowed 2..6.')
    args = parser.parse_args(argv)
    seeds, demos = args.seed or [0,17], args.demos or [2,3]
    if len(seeds) != len(set(seeds)) or any(not 0 <= seed < 2**63 for seed in seeds):
        parser.error('seeds must be distinct integers in 0..2**63-1')
    if len(demos) != len(set(demos)) or any(not 2 <= value <= 6 for value in demos):
        parser.error('demonstration counts must be distinct integers in 2..6')
    report = audit(args.out.resolve(), seeds, demos)
    print(json.dumps({'status': report['status'], 'jobs': len(report['jobs']),
                      'racket_evaluations': report['racket_evaluations'],
                      'checked_label_claims': report['checked_label_claims'],
                      'survivors': {job['id']: job['surviving_rivals'] for job in report['jobs']},
                      'failures': report['failures'], 'report': str(args.out.resolve() / 'report.json')},
                     sort_keys=True))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
