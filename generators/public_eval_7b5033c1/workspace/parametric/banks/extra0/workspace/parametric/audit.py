"""Bounded, source-bound grammar/rival/public audit and protected causal replay.

Controller-only tool. Use --out DIR [--seed-count N], or --preflight FILE
--witness-out DIR. Outputs never confer owner registration or acceptance.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HOME.parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE/file)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


a = load('_path_audit_adapter', 'adapter.py')
pub = load('_path_audit_public', 'public_views.py')


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def source_binding():
    sources = [p for p in HOME.rglob('*') if p.is_file() and '__pycache__' not in p.parts
               and (p.suffix in ('.py', '.rkt') or p.name in ('promotion.json', 'public-parent.json'))]
    return {'task_id': HOME.name, 'files': [
        {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(sources)]}


def verify_binding(binding):
    for row in binding['files']:
        path = ROOT/row['path']; resolved = path.resolve()
        if (not resolved.is_relative_to(ROOT) or path.is_symlink() or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']):
            raise ValueError('Bound source drift or escape: '+row['path'])


def python_rival(grid, settings, name):
    finish = settings['finish']
    if name == 'other_setting':
        return a.family.solve(grid, a.SETTINGS[1-a.SETTINGS.index(finish)])
    if name in ('row_major', 'column_major', 'reverse', 'histogram'):
        return a.family.solve(grid, finish, order=name)
    if name.startswith('select_'):
        text = name.removeprefix('select_')
        return a.family.solve(grid, finish, selector=int(text) if text.isdigit() else text)
    if name == 'paint_all_matching':
        return a.family.solve(grid, finish, paint='all_matching')
    if name == 'all_header_color':
        return a.family.solve(grid, finish, selector='all_header_color')
    raise ValueError('Unknown declared rival '+name)


def structural(seeds):
    report = {'seeds': list(seeds), 'episodes': 0, 'pairs': 0, 'public_turns': 0,
              'stress_30x30': 0, 'teaching_checks': 0, 'harmful_survivors': 0,
              'failures': [], 'max_constructor_attempt': 0,
              'scope': 'Finite induced-path grammar and named rivals, not unique induction.'}
    for seed in report['seeds']:
        matched = None
        for finish in a.SETTINGS:
            setting = {'finish': finish}; e = a.generate(seed, setting, 6, 4)
            pairs = e['train'] + e['test']; inputs = [p['input'] for p in pairs]
            assert len({pub.encoded(g) for g in inputs}) == 10
            if matched is not None: assert inputs == matched
            matched = inputs
            assert len(inputs[6]) == len(inputs[6][0]) == 30
            assert len(e['test'][0]['output']) == 30
            assert all(not a.family.self_check(g) for g in inputs)
            headers = [a.family.stages(p['input'])['address'] for p in e['train'][:2]]
            assert headers[0] != headers[1]
            for name in a.rival_programs(setting):
                fits = all(python_rival(p['input'], setting, name) == p['output'] for p in e['train'][:2])
                harms = any(python_rival(p['input'], setting, name) != p['output'] for p in e['test'])
                report['teaching_checks'] += 1
                assert not (fits and harms), ('harmful survivor', seed, finish, name)
            views, order = pub.project(e, seed, 4)
            assert pub.project(e, seed, 1) == (views[:1], order[:1])
            mutant = copy.deepcopy(e); mutant['program_solution'] = 'PRIVATE'
            for p in mutant['test']: p['output'] = [[9]]
            for p in mutant['train']: p['metadata'] = 'PRIVATE'
            assert pub.project(mutant, seed, 4) == (views, order)
            assert all(set(v) == {'train', 'test'} and set(v['test'][0]) == {'input'} for v in views)
            _, blueprint = a.family.construct(seed, 1000, stress=True)
            report['max_constructor_attempt'] = max(report['max_constructor_attempt'], blueprint['attempt'])
            report['episodes'] += 1; report['pairs'] += 10
            report['public_turns'] += 4; report['stress_30x30'] += 1
    return report


def audit(out, seeds):
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    binding = source_binding(); report = structural(seeds)
    apply, identity, bridge = _real_evaluator(ROOT/'shared/runtime')
    report.update(source_binding=binding, racket=identity, racket_evaluations=0, rival_checks=[])
    requests = []
    try:
        for seed in (17, 43):
            for finish in a.SETTINGS:
                settings = {'finish': finish}; e = a.generate(seed, settings, 2, 4)
                pairs = e['train'] + e['test']
                for p in pairs:
                    actual = _grid(apply(e['program_solution'], p['input'])); report['racket_evaluations'] += 1
                    assert actual == p['output'], ('selected label mismatch', seed, finish)
                for name, program in a.rival_programs(settings).items():
                    labels = [_grid(apply(program, p['input'])) for p in pairs]
                    report['racket_evaluations'] += len(pairs)
                    assert labels == [python_rival(p['input'], settings, name) for p in pairs], ('rival mirror mismatch', name)
                    fits = all(g == p['output'] for g, p in zip(labels[:2], e['train']))
                    harms = any(g != p['output'] for g, p in zip(labels[2:], e['test']))
                    report['rival_checks'].append({'seed': seed, 'settings': settings, 'rival': name,
                        'program_sha256': hashlib.sha256(program.encode()).hexdigest(),
                        'fits_all_demonstrations': fits, 'differs_on_query': harms,
                        'rival_query_indices_executed': [0, 1, 2, 3], 'all_executions_valid': True})
                    assert not (fits and harms), ('harmful protected rival', seed, finish, name)
                requests.append((e, seed))
                print(f'Completed {seed} {finish}: {report["racket_evaluations"]} Racket evaluations', flush=True)
    finally:
        bridge.close()
    report['exports'] = pub.export_batch(requests, out/'public')
    report['public_verification'] = pub.verify(out/'public', report['exports']['physical_creation_order'])
    verify_binding(binding)
    report['status'] = 'passed'
    write(out/'audit.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_binding', 'racket', 'rival_checks', 'exports')}))
    return report


def witness(preflight, out):
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    receipt = json.loads(Path(preflight).read_text()); verify_binding(receipt['source_binding'])
    execution = json.loads(Path(preflight).with_name('execution.json').read_text())
    episode = next(e for e in execution['episodes'] if e['settings']['finish'] == 'length_addressed_run')
    pair = episode['test'][0]; settings = episode['settings']
    program = a.program(settings); counter = a.rival_programs(settings)['row_major']
    apply, identity, bridge = _real_evaluator(ROOT/'shared/runtime')
    try:
        output = apply(program, pair['input']); alternative = apply(counter, pair['input'])
    finally:
        bridge.close()
    assert output == pair['output'] and output != alternative
    explanations = {
        'step_a': 'Follow the unique four-neighbor colored path from its row-major smaller endpoint, producing its ordered color sequence.',
        'intermediate': 'The traced sequence, its maximal equal-color runs, and the length k of its first run.',
        'step_b': 'Use k as a one-based address among subsequent runs; recolor exactly that run to 9, not every occurrence of its color.',
        'why_b_depends_on_a': 'B needs the order and run boundaries recovered from the winding route. Spatial row-major scanning changes the header or addressed run even though the same colored cells are present.'}
    result = {'schema': 'arcpuzzles-sequential-dependency-witness-v1',
              'source_binding': receipt['source_binding'], 'racket': {'backend': 'racket', 'protected': True},
              **explanations, 'cases': [{'input': pair['input'], 'settings': settings,
              'intermediate_value': a.family.stages(pair['input']), 'program': program, 'output': output,
              'counterfactual_program': counter, 'counterfactual_output': alternative, 'ablation': 'wrong_intermediate'}],
              'authority': 'Reviewer-authored causal interpretation, not owner acceptance.'}
    validate_sequential_witness({'sequential_dependency': {**explanations, 'witness_path': 'witness.json'}},
                                receipt, lambda _: json.dumps(result).encode())
    replay = replay_witness(ROOT, result)
    replay['engine_status'] = replay['status']; replay['status'] = 'reviewer_replayed'
    replay['authority'] = 'Fresh reviewer execution; no owner acceptance.'
    verify_binding(receipt['source_binding'])
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    write(out/'witness.json', result); write(out/'replay.json', replay)
    print(json.dumps({'status': 'reviewer_replayed',
                      'cells_changed': sum(x != y for r, s in zip(output, alternative) for x, y in zip(r, s))}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--seed-count', type=int, default=64)
    parser.add_argument('--preflight', type=Path)
    parser.add_argument('--witness-out', type=Path)
    args = parser.parse_args()
    if args.preflight:
        if args.witness_out is None: parser.error('--witness-out is required')
        witness(args.preflight, args.witness_out)
    else:
        if args.out is None or not 1 <= args.seed_count <= 256: parser.error('Need --out and seed-count 1..256')
        audit(args.out, range(args.seed_count))
