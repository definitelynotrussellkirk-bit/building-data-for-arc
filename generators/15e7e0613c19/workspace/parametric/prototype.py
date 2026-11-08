"""Task-local rule prototype; deliberately independent of the production sampler."""
import argparse
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import canonical_path, find_root
from arc_repl.racket_bridge import RacketBridge

TASK_ID = '15e7e0613c19'
AREA_ORDERS = ('ascending', 'descending')
DEFAULT = 'ascending'
PRIMARY = '(< (obj-size a) (obj-size b))'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical_program(root):
    with canonical_path(root).open() as source:
        matches = []
        for line in source:
            if line.strip():
                row = json.loads(line)
                if row.get('task_id') == TASK_ID:
                    matches.append(row)
    if len(matches) != 1:
        raise ValueError('Expected exactly one main-task canonical row')
    return matches[0]['program_solution']


def instantiate(program, area_order=DEFAULT):
    if area_order not in AREA_ORDERS:
        raise ValueError('Unsupported area_order')
    if program.count(PRIMARY) != 1:
        raise ValueError('Canonical primary comparator changed')
    return program if area_order == DEFAULT else program.replace(
        PRIMARY, '(> (obj-size a) (obj-size b))', 1)


def parameters(seed):
    # One draw per episode; never redrawn per demonstration or query.
    return {'area_order': random.Random(seed).choice(AREA_ORDERS)}


def fixture_inputs(seed):
    """Four controlled layouts with connected, separated monochrome motifs."""
    patterns = [
        [[[1]], [[1, 1, 1]], [[1, 1], [1, 1], [1, 0]]],
        [[[1, 1, 1, 1]], [[1, 1], [1, 1]],
         [[1, 1, 1], [1, 0, 0]], [[1], [1], [1], [1]]],
        [[[1, 1, 1], [1, 0, 1], [1, 1, 1]], [[1, 1, 1], [1, 1, 1]],
         [[1, 1], [1, 0]], [[1, 1], [1, 0]]],
        [[[1], [1]], [[1, 1], [1, 1]], [[1, 1, 1], [1, 1, 1]]],
    ]
    rng = random.Random(seed ^ 0x5EED)
    inputs = []
    for motifs in patterns:
        colors = rng.sample(range(1, 10), len(motifs))
        slots = list(range(len(motifs)))
        rng.shuffle(slots)
        grid = [[0] * 25 for _ in range(9)]
        for motif, color, slot in zip(motifs, colors, slots):
            top, left = rng.randrange(1, 5), 1 + slot * 6
            for r, row in enumerate(motif):
                for c, value in enumerate(row):
                    if value:
                        grid[top + r][left + c] = color
        inputs.append(grid)
    return inputs


def execute(bridge, program, grid):
    # rule! is an executor directive; the exact body evaluates with grid bound to g.
    if not program.startswith('(rule! ') or not program.endswith(')'):
        raise ValueError('Expected canonical rule! wrapper')
    bridge.define_grid('g', grid)
    output = bridge.eval_text(program[len('(rule! '):-1])
    if (not isinstance(output, list) or not output or not output[0]
            or any(len(row) != len(output[0]) for row in output)):
        raise ValueError('Racket did not return a rectangular nonempty grid')
    return output


def episode(seed, canonical, bridge):
    params = parameters(seed)
    chosen = params['area_order']
    program = instantiate(canonical, chosen)
    inputs = fixture_inputs(seed)
    pairs = [{'input': grid, 'output': execute(bridge, program, grid)} for grid in inputs]
    rivals = []
    for rival in AREA_ORDERS:
        if rival == chosen:
            continue
        rival_program = instantiate(canonical, rival)
        outputs = [execute(bridge, rival_program, grid) for grid in inputs]
        differences = [i for i, pair in enumerate(pairs[:3]) if pair['output'] != outputs[i]]
        query_differs = pairs[3]['output'] != outputs[3]
        rivals.append({'area_order': rival, 'demo_differences': differences,
                       'query_differs': query_differs,
                       'status': 'distinguished' if differences else 'ambiguous'})
        if query_differs and not differences:
            raise ValueError('Query requires a parameter distinction absent from demonstrations')
    return {'seed': seed, 'parameters': params, 'program': program,
            'program_sha256': sha256(program.encode()), 'train': pairs[:3],
            'test': pairs[3:], 'rivals': rivals}


def public_challenge(private):
    return {'train': private['train'],
            'test': [{'input': pair['input']} for pair in private['test']]}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def materialize(output):
    root = find_root(__file__)
    canonical = canonical_program(root)
    sources = {p.name: sha256(p.read_bytes()) for p in Path(__file__).parent.iterdir()
               if p.is_file() and p.suffix in ('.py', '.md')}
    bridge = RacketBridge()
    try:
        episodes = [episode(seed, canonical, bridge) for seed in (1, 0)]
        assert {e['parameters']['area_order'] for e in episodes} == set(AREA_ORDERS)
        for index, record in enumerate(episodes):
            record['prototype_source_sha256'] = sources
            record['label_authority'] = 'included Racket bridge, exact instantiated rule body'
            write_json(output / 'public' / f'episode-{index}.json', public_challenge(record))
            write_json(output / 'private' / f'episode-{index}.json', record)
            # No trailing newline added: bytes hash exactly matches the record.
            (output / 'private' / f'episode-{index}.rkt').write_text(record['program'])
        witness_input = fixture_inputs(1)[0]
        witness = {'input': witness_input, 'outputs': {
            order: execute(bridge, instantiate(canonical, order), witness_input)
            for order in AREA_ORDERS}}
        assert witness['outputs']['ascending'] != witness['outputs']['descending']
        write_json(output / 'private' / 'witness.json', witness)
        report = {'status': 'prototype', 'task_id': TASK_ID,
                  'parameters': {'area_order': list(AREA_ORDERS)}, 'default': DEFAULT,
                  'default_program_exact': instantiate(canonical) == canonical,
                  'episode_count': len(episodes), 'labels_executed': 8,
                  'rival_executions': 8, 'witness_executions': 2,
                  'rivals': [e['rivals'] for e in episodes],
                  'source_sha256': sources,
                  'scope': 'two seeds; controlled connected motif fixtures; not production approval'}
        write_json(output / 'report.json', report)
        return report
    finally:
        bridge.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(materialize(args.out), indent=2))
