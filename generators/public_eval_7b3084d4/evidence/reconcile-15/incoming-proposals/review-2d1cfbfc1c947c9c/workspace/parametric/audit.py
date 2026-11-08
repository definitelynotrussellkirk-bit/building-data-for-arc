"""Finite source-bound authoring audit for public_eval_7b3084d4.

This exercises count/prefix boundaries, unique exact-cover reconstruction,
protected-Racket parity for selected and rival programs, demonstration-only
identifiability, and one-query public projection.  It is bounded evidence only
and grants no owner acceptance or training admission.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent


def load_adapter():
    spec = importlib.util.spec_from_file_location('_audit_7b3084d4', HERE / 'adapter.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def root_path():
    return next(p for p in HERE.parents if (p / 'src/arcpuzzles/parametric_worker.py').is_file())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def run(out: Path, seeds: int):
    if type(seeds) is not int or not 1 <= seeds <= 256:
        raise ValueError('seeds must be 1..256')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'public').mkdir()
    (out / 'private').mkdir()
    root = root_path()
    sys.path[:0] = [str(root / 'src'), str(root / 'shared/runtime')]
    from reviewer_support import public_challenge_bytes
    from arcpuzzles.parametric_worker import _real_evaluator

    a = load_adapter()
    values = a.PARAMETERS['finish_rule']
    report = {
        'status': 'passed',
        'seed_count': seeds,
        'requests': 0,
        'pair_instances': 0,
        'distinct_inputs': 0,
        'matched_input_checks': 0,
        'unique_packing_checks': 0,
        'public_turn_checks': 0,
        'racket_evaluations': 0,
        'finite_teaching': [],
        'limits': 'Finite authored rivals and sampled seeds only; no universal uniqueness, owner acceptance, or training admission.',
    }
    inputs = set()
    first_sources = set()
    for seed in range(seeds):
        full = {value: a.generate(seed, {'finish_rule': value}, 6, 4) for value in values}
        first_sources.add(full[values[0]]['private']['query_permutation'][0])
        left = [p['input'] for split in ('train', 'test') for p in full[values[0]][split]]
        right = [p['input'] for split in ('train', 'test') for p in full[values[1]][split]]
        assert left == right
        assert len({json.dumps(g) for g in left}) == 10
        report['matched_input_checks'] += 1
        for grid in left:
            analysis = a.analyze(grid)
            assert analysis['solution_count'] == 1
            report['unique_packing_checks'] += 1
            inputs.add(sha(json.dumps(grid, separators=(',', ':')).encode()))
        for demos, queries in ((2, 1), (2, 4), (3, 2), (6, 3)):
            for value in values:
                ep = a.generate(seed, {'finish_rule': value}, demos, queries)
                assert ep['train'] == full[value]['train'][:demos]
                assert ep['test'] == full[value]['test'][:queries]
                report['requests'] += 1
                report['pair_instances'] += demos + queries
                for index in range(queries):
                    turn = a.public_turn(ep, index)
                    assert set(turn) == {'train', 'test'}
                    assert len(turn['test']) == 1 and set(turn['test'][0]) == {'input'}
                    changed = deepcopy(ep)
                    changed['private'] = {'canary': 'hidden'}
                    changed['program_solution'] = 'hidden'
                    changed['test'][index]['output'] = [[9]]
                    for later in range(index + 1, queries):
                        changed['test'][later] = {'input': [[7]], 'output': [[6]]}
                    assert a.public_turn(changed, index) == turn
                    report['public_turn_checks'] += 1
    report['distinct_inputs'] = len(inputs)
    report['first_source_indices_observed'] = sorted(first_sources)

    apply, identity, bridge = _real_evaluator(root / 'shared/runtime')
    report['racket'] = identity
    programs = a.rival_programs()
    executions = []
    payloads = {}
    private = []
    try:
        for seed in (17, 43):
            base = a.generate(seed, {'finish_rule': values[0]}, 2, 4)
            outputs = {}
            for name, program in programs.items():
                labels = []
                for split in ('train', 'test'):
                    for index, pair in enumerate(base[split]):
                        got = apply(program, pair['input'])
                        expected = a.predict(pair['input'], name)
                        assert got == expected, (seed, name, split, index)
                        labels.append(got)
                        report['racket_evaluations'] += 1
                        executions.append({
                            'seed': seed, 'name': name, 'split': split, 'index': index,
                            'program_sha256': sha(program.encode()),
                            'input_sha256': sha(json.dumps(pair['input'], separators=(',', ':')).encode()),
                            'output_sha256': sha(json.dumps(got, separators=(',', ':')).encode()),
                        })
                outputs[name] = labels
            for chosen in values:
                ep = a.generate(seed, {'finish_rule': chosen}, 2, 4)
                survivors = [name for name, labels in outputs.items()
                             if labels[:2] == [p['output'] for p in ep['train']]]
                assert survivors == [chosen], (seed, chosen, survivors)
                report['finite_teaching'].append({
                    'seed': seed,
                    'settings': {'finish_rule': chosen},
                    'survivors': survivors,
                    'hypotheses': list(programs),
                })
                for index in range(4):
                    raw = public_challenge_bytes(a.public_turn(ep, index))
                    ident = sha(raw)
                    assert ident not in payloads
                    payloads[ident] = raw
                    private.append({
                        'id': ident,
                        'seed': seed,
                        'settings': {'finish_rule': chosen},
                        'source_query': ep['private']['query_permutation'][index],
                        'answer': ep['test'][index]['output'],
                    })
    finally:
        bridge.close()

    for ident, raw in sorted(payloads.items()):
        (out / 'public' / f'{ident}.json').write_bytes(raw)
    dump(out / 'private' / 'queries.json', private)
    dump(out / 'private' / 'execution.json', executions)
    report['public_files'] = len(payloads)
    report['source_sha256'] = {
        p.name: sha(p.read_bytes()) for p in HERE.iterdir()
        if p.is_file() and p.suffix in ('.py', '.rkt', '.json')
    }
    dump(out / 'audit.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=24)
    args = parser.parse_args()
    report = run(args.out, args.seeds)
    print(json.dumps({k: report[k] for k in (
        'status', 'requests', 'pair_instances', 'distinct_inputs',
        'unique_packing_checks', 'racket_evaluations', 'public_files')}))


if __name__ == '__main__':
    main()
