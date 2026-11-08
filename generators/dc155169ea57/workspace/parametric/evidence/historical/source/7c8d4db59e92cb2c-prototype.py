#!/usr/bin/env python3
"""Proposed task-local barrier-capacity episodes, never a production rule override."""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = 'dc155169ea57'
CANONICAL_RULE_HASH = 'c0f1818b0fb2'
CAPACITIES = (1, 2, 3)
DEFAULT_CAPACITY = 1
ROOT = find_root(__file__)
TASK_HOME = Path(__file__).resolve().parents[2]
THRESHOLD_EXPRESSION = '(> (row-count rr) 1)'


def sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def catalog_rule_hash(program):
    return sha256_text(' '.join(program.split()))[:12]


def grid_hash(grid):
    return sha256_text(json.dumps(grid, separators=(',', ':')))


@lru_cache(maxsize=1)
def canonical_program():
    programs = set()
    with canonical_path(ROOT).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get('task_id') == TASK_ID:
                    programs.add(row['program_solution'])
    if len(programs) != 1:
        raise ValueError('The assigned canonical Racket authority is missing or ambiguous')
    program = programs.pop()
    if catalog_rule_hash(program) != CANONICAL_RULE_HASH:
        raise ValueError('Canonical Racket authority drifted; review the new source first')
    return program


def validate_capacity(capacity):
    if type(capacity) is not int or capacity not in CAPACITIES:
        raise ValueError('barrier_capacity must be the integer 1, 2, or 3')
    return capacity


def replace_once(program, old, new):
    if program.count(old) != 1:
        raise ValueError('Expected exactly one canonical semantic edit site')
    return program.replace(old, new)


def materialize_rule(barrier_capacity=DEFAULT_CAPACITY):
    """Default preserves every byte; alternatives change one literal threshold."""
    capacity = validate_capacity(barrier_capacity)
    program = canonical_program()
    if capacity == DEFAULT_CAPACITY:
        return program
    return replace_once(program, THRESHOLD_EXPRESSION,
                        f'(> (row-count rr) {capacity})')


class RuleOracle:
    """Use only the public RacketBridge lifecycle/grid/expression methods."""
    def __init__(self):
        self.bridge = None
        self.programs = set()
        self.execution_count = 0

    def __enter__(self):
        self.bridge = RacketBridge(timeout=20.0)
        self.bridge.eval_text('(define (rule! procedure) procedure)')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.bridge is not None:
            self.bridge.close()
            self.bridge = None
        return False

    def apply(self, program, grid):
        if self.bridge is None:
            raise RuntimeError('Use RuleOracle as a context manager')
        grid = normalize_grid(grid)
        digest = sha256_text(program)
        name = 'capacity-rule-' + digest
        if digest not in self.programs:
            self.bridge.eval_text(f'(define {name} {program})')
            self.programs.add(digest)
        self.bridge.define_grid('capacity-input', grid)
        output = normalize_grid(self.bridge.eval_text(f'({name} capacity-input)'))
        self.execution_count += 1
        if len(output) != len(grid) or len(output[0]) != len(grid[0]):
            raise ValueError('Reference changed the grid dimensions unexpectedly')
        return output


def validate_input(grid):
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    if not (7 <= h <= 30 and 7 <= w <= 30):
        raise ValueError('Inputs must be within the canonical 7..30 dimensional envelope')
    if {value for row in grid for value in row} != {1, 2, 8}:
        raise ValueError('Expected the literal canonical palette {1, 2, 8}')
    lines = [r for r, row in enumerate(grid) if all(value == 2 for value in row)]
    if len(lines) != 1 or not 3 <= lines[0] <= h - 4:
        raise ValueError('Expected one full red line with three rows above and below')
    line = lines[0]
    if any(value == 2 for r, row in enumerate(grid) if r != line for value in row):
        raise ValueError('Red cells outside the line')
    if any(value == 1 for row in grid[line:] for value in row):
        raise ValueError('Input shapes must lie strictly above the line')
    return grid, line


def components(grid, line):
    seen = set()
    result = []
    for r in range(line):
        for c in range(len(grid[0])):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack, shape = [(r, c)], []
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                shape.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (0 <= nr < line and 0 <= nc < len(grid[0])
                            and grid[nr][nc] == 1 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(shape)
    return result


def rule_mirror(grid, barrier_capacity=DEFAULT_CAPACITY):
    """Independent parity check only. Exported labels always come from Racket."""
    capacity = validate_capacity(barrier_capacity)
    grid, line = validate_input(grid)
    h = len(grid)
    output = [[8 if r < line and value == 1 else value for value in row]
              for r, row in enumerate(grid)]
    pass_columns = set()
    for shape in components(grid, line):
        row_counts = Counter(r for r, _ in shape)
        supporting_rows = [r for r, count in row_counts.items() if count > capacity]
        if supporting_rows:
            delta = line - 1 - max(supporting_rows)
        else:
            delta = h - 1 - max(r for r, _ in shape)
            pass_columns.update(c for _, c in shape)
        for r, c in shape:
            if 0 <= r + delta < h:
                output[r + delta][c] = 1
    for c in pass_columns:
        output[line][c] = 8
    return output


def rival_programs(capacity):
    selected = materialize_rule(capacity)
    rivals = {f'capacity_{other}': materialize_rule(other)
              for other in CAPACITIES if other != capacity}
    rivals['stop_at_lowest_cell'] = replace_once(
        selected, '(- (- red-row 1) (max-list wide-rows))', '(- (- red-row 1) rmax)')
    rivals['stop_at_highest_support_row'] = replace_once(
        selected, '(max-list wide-rows)', '(min-list wide-rows)')
    rivals['all_shapes_reach_floor'] = replace_once(
        selected, f'(> (row-count rr) {capacity})', '(> (row-count rr) 30)')
    rivals['leave_line_unpunched'] = replace_once(
        selected, '(set! result (set-cell result red-row c 8))',
        '(set! result (set-cell result red-row c 2))')
    if capacity > 1:
        # At capacity 1 this is equivalent on four-connected components.
        # At 2/3 it wrongly blocks a staircase with only two cells per row.
        bbox = replace_once(selected, f'(> (row-count rr) {capacity})',
                            '(> (row-count rr) 1)')
        rivals['bounding_box_capacity'] = replace_once(
            bbox, '(null? wide-rows)', f'(<= (+ (- cmax cmin) 1) {capacity})')
    return rivals


def fit_rivals(demonstrations, barrier_capacity, oracle):
    """Fit only labelled demonstrations. Query inputs/answers are not accepted."""
    capacity = validate_capacity(barrier_capacity)
    rivals = []
    for name, program in rival_programs(capacity).items():
        results, refuted = [], []
        for index, pair in enumerate(demonstrations):
            if set(pair) != {'input', 'output'}:
                raise ValueError('Rival fitting requires demonstration input/output pairs only')
            prediction = oracle.apply(program, pair['input'])
            matches = prediction == pair['output']
            results.append({'demo_index': index, 'matches': matches, 'prediction': prediction})
            if not matches:
                refuted.append(index)
        rivals.append({'name': name, 'program': program,
                       'program_sha256': sha256_text(program),
                       'refuted_by_demo': refuted, 'demo_results': results})
    return {'basis': 'demonstrations_only', 'rivals': rivals,
            'surviving_rivals': [row['name'] for row in rivals if not row['refuted_by_demo']]}


def sample_input(rng, index, *, query_position=None):
    """Vary connected profiles, tail lengths, positions and dimensions together."""
    if query_position is None:
        h, w = (16 + index % 3, 20 + index % 3)
    else:
        h, w = ((20, 24), (24, 20), (30, 30), (23, 28))[query_position % 4]
    line = h // 2 - 1
    output = [[8] * w for _ in range(h)]
    output[line] = [2] * w
    columns = (1, 7, 12, w - 2)

    def place(cells, column, top=None):
        height = 1 + max(r for r, _ in cells)
        top = rng.randrange(line - height) if top is None else top
        for r, c in cells:
            output[r + top][c + column] = 1

    # Both row-width boundaries (2 and 3) appear in every teaching scene.
    if index == 1 and query_position is None:
        # Independent components share a projection but have a vertical gap.
        place([(0, 0), (0, 1)], columns[0], 0)
        place([(0, 0), (1, 0)], columns[0], 3)
    elif index % 2 or (query_position is None and index == 0):
        # Demo 0 teaches row-count versus bbox width before any query.
        # Bounding-box width is 4 while every occupied row contains 2 cells.
        place([(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)], columns[0])
    else:
        tail = rng.randint(1, min(4, line - 3))
        place([(0, 0), (0, 1)] + [(r, 0) for r in range(1, tail + 1)], columns[0])
    tail = rng.randint(1, min(4, line - 3))
    center = rng.randrange(3)
    place([(0, c) for c in range(3)] + [(r, center) for r in range(1, tail + 1)], columns[1])
    # Two separate supporting rows make lowest-vs-highest support observable.
    tail = rng.randint(1, min(4, line - 5))
    center = rng.randrange(4)
    wide = ([(0, c) for c in range(4)] + [(1, center)]
            + [(2, c) for c in range(4)]
            + [(r, center) for r in range(3, 3 + tail)])
    place(wide, columns[2])
    thin_height = rng.randint(1, line - 2)
    place([(r, 0) for r in range(thin_height)], columns[3])
    if rng.choice((False, True)):
        output = [row[::-1] for row in output]
    validate_input(output)
    return output


def source_hashes():
    paths = [Path(__file__).resolve(), TASK_HOME / 'tests' / 'test_parametric.py']
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def build_episode(*, seed, barrier_capacity=DEFAULT_CAPACITY, demo_count=2,
                  query_count=4, oracle=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(demo_count) is not int or not 2 <= demo_count <= 64:
        raise ValueError('demo_count must be an integer from 2 through 64')
    if type(query_count) is not int or not 1 <= query_count <= 64:
        raise ValueError('query_count must be an integer from 1 through 64')
    if barrier_capacity is not None:
        validate_capacity(barrier_capacity)
    if oracle is None:
        with RuleOracle() as evaluator:
            return build_episode(seed=seed, barrier_capacity=barrier_capacity,
                                 demo_count=demo_count, query_count=query_count, oracle=evaluator)
    selection = 'explicit_once'
    if barrier_capacity is None:
        selection = 'seeded_once'
        barrier_capacity = random.Random(f'{TASK_ID}/parameter/{seed}').choice(CAPACITIES)
    capacity = validate_capacity(barrier_capacity)
    program = materialize_rule(capacity)
    rng = random.Random(f'{TASK_ID}/inputs/{seed}')
    seen, accepted = set(), []
    attempts = 0

    def next_input(index, query_position=None):
        nonlocal attempts
        for _ in range(128):
            attempts += 1
            candidate = sample_input(rng, index, query_position=query_position)
            digest = grid_hash(candidate)
            if digest not in seen:
                seen.add(digest)
                accepted.append({'split': 'train' if query_position is None else 'test',
                                 'pair_index': index if query_position is None else query_position,
                                 'input_sha256': digest, 'height': len(candidate),
                                 'width': len(candidate[0])})
                return candidate
        raise RuntimeError('Unique-input attempt limit reached; no short episode was returned')

    def label(candidate):
        output = oracle.apply(program, candidate)
        if output != rule_mirror(candidate, capacity):
            raise ValueError('Racket/reference-mirror disagreement')
        return output

    demonstrations = []
    for index in range(demo_count):
        candidate = next_input(index)
        demonstrations.append({'input': candidate, 'output': label(candidate)})
    # All rivals are eliminated before any query is even sampled or labelled.
    fit = fit_rivals(demonstrations, capacity, oracle)
    if fit['surviving_rivals']:
        raise ValueError('Ambiguous demonstrations: ' + ', '.join(fit['surviving_rivals']))
    queries, labels, checks = [], [], []
    for position in range(query_count):
        candidate = next_input(demo_count + position, query_position=position)
        queries.append({'input': candidate})
        labels.append(label(candidate))
        checks.append({'query_index': position, 'input_sha256': grid_hash(candidate),
                       'identified_from_demonstrations': True,
                       'basis': 'same demonstrations_only fit, computed before query sampling',
                       'refuted_rivals': [rival['name'] for rival in fit['rivals']],
                       'racket_label_sha256': grid_hash(labels[-1]), 'mirror_agrees': True})
    public = {'train': demonstrations, 'test': queries}
    private = {'schema': 'dc155169ea57-parametric-prototype-v1', 'status': 'proposed',
               'parent_task_id': TASK_ID, 'canonical_rule_hash': CANONICAL_RULE_HASH,
               'seed': seed, 'selection': selection,
               'parameters': {'barrier_capacity': capacity},
               'parameter_domain': {'barrier_capacity': list(CAPACITIES)},
               'default_parameters': {'barrier_capacity': DEFAULT_CAPACITY},
               'demo_count': demo_count, 'query_count': query_count,
               'program': program, 'program_sha256': sha256_text(program),
               'program_rule_hash': catalog_rule_hash(program),
               'prototype_source_sha256': source_hashes(),
               'query_outputs': labels, 'rival_fit': fit, 'per_query_checks': checks,
               'sampling': {'attempts': attempts, 'unique_input_count': len(seen),
                            'accepted_pairs': accepted},
               'limitations': [f'Finite evidence against {len(fit["rivals"])} declared rivals for this setting.',
                               'The generated grammar is narrower than all lawful inputs.',
                               'This workspace prototype is not production approval.']}
    return {'public': public, 'private': private}


def distinguishing_witness(oracle):
    rows = ['8888888', '8111888', '8188888', '8118888', '8188888',
            '8888888', '2222222', '8888888', '8888888', '8888888', '8888888']
    source = [[int(value) for value in row] for row in rows]
    outputs = {str(capacity): oracle.apply(materialize_rule(capacity), source) for capacity in CAPACITIES}
    if len({grid_hash(value) for value in outputs.values()}) != len(CAPACITIES):
        raise ValueError('Parameter witness did not distinguish every allowed setting')
    return {'input': source, 'outputs_by_barrier_capacity': outputs,
            'program_sha256_by_capacity': {str(k): sha256_text(materialize_rule(k)) for k in CAPACITIES},
            'input_sha256': grid_hash(source),
            'all_three_outputs_distinct': True,
            'meaning': 'Capacity 1 stops at the lower width-2 row; capacity 2 stops at the upper width-3 row; capacity 3 reaches the floor.'}


def run(args):
    output = Path(args.out)
    if output.exists():
        raise FileExistsError('Use a new evidence directory: ' + str(output))
    capacities = args.capacity or [DEFAULT_CAPACITY]
    if len(set(capacities)) != len(capacities):
        raise ValueError('Duplicate capacity requests would repeat episodes')
    if args.sample_capacity:
        if args.capacity:
            raise ValueError('--sample-capacity and --capacity are mutually exclusive')
        capacities = [None]
    with RuleOracle() as oracle:
        episodes = [build_episode(seed=args.seed, barrier_capacity=capacity,
                                  demo_count=args.demo_count, query_count=args.query_count,
                                  oracle=oracle) for capacity in capacities]
        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            actual = oracle.apply(materialize_rule(), pair['input'])
            if actual != pair['output']:
                raise ValueError('Default rule disagrees with a labelled canonical pair')
            canonical_checks.append({'variant': pair['variant'], 'split': pair['split'],
                                     'pair_index': pair['pair_index'], 'matches': True,
                                     'input_sha256': grid_hash(pair['input']),
                                     'output_sha256': grid_hash(actual)})
        witness = distinguishing_witness(oracle)
        runtime_identity = oracle.bridge.runtime_identity
        executed = oracle.execution_count
    output.mkdir(parents=True)
    inventory, summaries = [], []

    def write_json(name, value):
        path = output / name
        path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
        inventory.append({'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'bytes': path.stat().st_size})

    for index, episode in enumerate(episodes, 1):
        name = f'episode-{index:02d}'
        write_json(name + '-challenge.json', episode['public'])
        write_json(name + '-private.json', episode['private'])
        path = output / (name + '-rule.rkt')
        path.write_text(episode['private']['program'])
        inventory.append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'bytes': path.stat().st_size})
        summaries.append({'episode': name, 'parameters': episode['private']['parameters'],
                          'demo_count': len(episode['public']['train']),
                          'query_count': len(episode['public']['test']),
                          'unique_input_count': episode['private']['sampling']['unique_input_count'],
                          'rivals_refuted': len(episode['private']['rival_fit']['rivals']),
                          'program_sha256': episode['private']['program_sha256']})
    write_json('witness.json', witness)
    manifest = {'schema': 'dc155169ea57-parametric-evidence-v1', 'status': 'proposed',
                'seed': args.seed, 'payload_argv': sys.argv, 'effective_cwd': str(Path.cwd()),
                'prototype_source_sha256': source_hashes(),
                'canonical_ledger_sha256': hashlib.sha256(canonical_path(ROOT).read_bytes()).hexdigest(),
                'canonical_program_sha256': sha256_text(canonical_program()),
                'canonical_checks': canonical_checks, 'racket_runtime': runtime_identity,
                'racket_grid_executions': executed, 'episodes': summaries, 'files': inventory,
                'public_file_contract': 'Only train input/output pairs and test input grids; no seed, parameter, program, reference label or metadata.',
                'limits': 'Finite deterministic evidence: six declared rivals at capacity 1, seven at capacities 2/3; no universal identifiability or training-admission claim.'}
    write_json('manifest.json', manifest)
    print(json.dumps({'status': 'proposed', 'episodes': summaries,
                      'canonical_pairs_verified': len(canonical_checks),
                      'racket_grid_executions': executed, 'evidence': str(output),
                      'file_count': len(inventory)}, sort_keys=True))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--capacity', type=int, choices=CAPACITIES, action='append',
                        help='Fixed capacity, repeat for separate episodes; default is canonical 1')
    parser.add_argument('--sample-capacity', action='store_true',
                        help='Choose one episode capacity deterministically from seed')
    parser.add_argument('--demo-count', type=int, default=2)
    parser.add_argument('--query-count', type=int, default=4)
    parser.add_argument('--out', required=True)
    return run(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
