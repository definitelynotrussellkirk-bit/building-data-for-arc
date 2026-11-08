"""Bounded protected-Racket self-review for the color-key family.

Run through review.py run; stores counterexamples and all executed audit cases.
This is authoring evidence, never owner acceptance or a uniqueness proof.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from arcpuzzles.review_programs import strict_programs


def load(path):
    spec = importlib.util.spec_from_file_location('_d59_audit_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rivals(program):
    marker = '(if (selected? palette)'
    if program.count(marker) != 1:
        raise ValueError('Selection marker changed')
    predicates = {
        'ignore_key_nonempty': '(not (null? palette))',
        'at_least_two_key_colors': '(>= (length (filter (lambda (k) (member k palette)) key)) 2)',
        'palette_count_only': '(>= (length palette) (length key))',
        'payload_dot_count': '(>= (length (filter (lambda (p) (not (= (at g (first p) (second p)) 0))) (obj-cells panel))) (length key))',
        'largest_panel': '(= (obj-size panel) (apply max (map obj-size panels)))',
        'smallest_panel': '(= (obj-size panel) (apply min (map obj-size panels)))',
        'fixed_key_124': "(for/and ([k '(1 2 4)]) (member k palette))",
        'erase_every_panel': '#t',
        'erase_no_panels': '#f',
    }
    return {name: program.replace(marker, '(if ' + pred) for name, pred in predicates.items()}


def audit(root, out):
    home = Path(__file__).resolve().parents[1]
    adapter = load(home / 'workspace/parametric/adapter.py')
    settings = [{'match_mode': mode} for mode in adapter.MODES]
    all_programs = {mode: adapter.program({'match_mode': mode}) for mode in adapter.MODES}
    extras = {mode: rivals(p) for mode, p in all_programs.items()}
    strict = strict_programs(root, list(all_programs.values()) + [p for r in extras.values() for p in r.values()])
    records, teaching, failures, stress = [], [], [], []
    cache = {}
    with _local_imports(root / 'shared/runtime', home / 'workspace/parametric'):
        apply, identity, bridge = _real_evaluator(root / 'shared/runtime')
        def executed(program, grid):
            key = program, json.dumps(grid, separators=(',', ':'))
            if key not in cache:
                cache[key] = _grid(apply(program, _grid(grid)))
            return cache[key]
        try:
            for setting in settings:
                mode = setting['match_mode']
                correct = all_programs[mode]
                candidate = {**extras[mode], **{'setting_' + k: p for k, p in all_programs.items() if k != mode}}
                for seed in (5, 101):
                    lesson = adapter.generate(seed, setting, 6, 4)
                    for split in ('train', 'test'):
                        for i, pair in enumerate(lesson[split]):
                            actual = executed(correct, pair['input'])
                            if actual != pair['output']:
                                failures.append({'kind': 'label', 'mode': mode, 'seed': seed, 'split': split, 'index': i})
                            records.append({'settings': setting, 'seed': seed, 'split': split, 'index': i, **pair})
                            if len(pair['input']) == len(pair['input'][0]) == 30:
                                view = adapter.kernel.analyze(pair['input'])
                                panels = sum(len(x['cells']) for x in view['panels'])
                                changed = sum(a != b for ar, br in zip(pair['input'], actual) for a, b in zip(ar, br))
                                assert panels > 450 and changed > 0
                                stress.append({'mode': mode, 'seed': seed, 'shape': [30, 30], 'panel_cells': panels, 'changed_cells': changed})
                    for name, rival in candidate.items():
                        demo_results = [executed(rival, p['input']) for p in lesson['train'][:2]]
                        mismatches = [i for i, (actual, p) in enumerate(zip(demo_results, lesson['train'])) if actual != p['output']]
                        if not mismatches:
                            query_diffs = [i for i, p in enumerate(lesson['test']) if executed(rival, p['input']) != p['output']]
                            if query_diffs:
                                failures.append({'kind': 'underidentified_rival', 'mode': mode, 'seed': seed, 'rival': name, 'queries': query_diffs})
                            teaching.append({'mode': mode, 'seed': seed, 'rival': name, 'status': 'same_bounded_predictions' if not query_diffs else 'query_divergence'})
                        else:
                            i = mismatches[0]
                            teaching.append({'mode': mode, 'seed': seed, 'rival': name, 'status': 'rejected_by_demo',
                                             'demo_index': i, 'input': lesson['train'][i]['input'],
                                             'output': lesson['train'][i]['output'], 'rival_program': rival, 'rival_output': demo_results[i]})
            # All eight orientations at both geometric extremes, not cosmetic padding.
            for code in range(8):
                size = 13 if code % 2 == 0 else 30
                g = adapter.kernel.generate(300 + code, code, grid_h=size, grid_w=size, orientation=code, key_count=2 + code % 3)
                for setting in settings:
                    p = all_programs[setting['match_mode']]
                    expected = adapter.kernel.solve(g, setting['match_mode'])
                    assert executed(p, g) == expected
                    records.append({'settings': setting, 'seed': 300 + code, 'orientation': code, 'input': g, 'output': expected})
        finally:
            bridge.close()
    source_files = [home / 'generator.py', home / 'reference.rkt', home / 'workspace/parametric/adapter.py',
                    home / 'workspace/parametric/kernel.py', Path(__file__)]
    report = {'schema': 'arcpuzzles-d59b0160-self-review-v1', 'status': 'failed' if failures else 'passed',
              'racket': identity, 'program_syntax': strict,
              'source_sha256': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
              'settings': settings, 'seeds': [5, 101], 'tested_demo_counts': [2, 6], 'queries': 4,
              'executed_program_input_pairs': len(cache), 'label_cases': len(records), 'cases': records,
              'teaching_checks': teaching, 'stress_30x30': stress, 'failures': failures,
              'limits': 'Finite named rivals and seeds only; no universal uniqueness, owner acceptance, or training admission.'}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({k: report[k] for k in ('status', 'executed_program_input_pairs', 'label_cases', 'failures')}))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    audit(args.root.resolve(), args.out.resolve())
