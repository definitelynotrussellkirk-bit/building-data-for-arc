"""Private bounded peer teaching probe; direct sampling is unapproved research.

No production exporter, source repair, approval mutation, or broad battery.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import load_selected_generator


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--demos', type=int, default=2, choices=(2, 3))
    parser.add_argument('--queries', type=int, default=1, choices=(1, 2))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.out.resolve().is_relative_to(HERE) or args.out.exists():
        parser.error('--out must be a new directory below this peer checks folder')
    args.out.mkdir(parents=True)
    catalog = Catalog(ROOT)
    metadata = catalog.describe('37cec5981f3a')
    generator, path, source_hash = load_selected_generator('37cec5981f3a', root=ROOT)
    variants = catalog._variants()[metadata['rule_task_id']]
    programs = {row['program_solution'] for row in variants}
    if len(programs) != 1:
        raise ValueError('Expected one unambiguous selected canonical program')
    program = next(iter(programs))
    binding = '(control (cell-at g 0 0))'
    if program.count(binding) != 1:
        raise ValueError('Canonical source no longer matches counterfactual binding')
    rival = program.replace(binding, '(control 1)')
    grids = [generator.generate(args.seed, i) for i in range(args.demos + args.queries)]
    errors = [generator.self_check(grid) for grid in grids]
    if any(errors):
        raise ValueError(f'Invalid sampled input: {errors}')
    actual_executions = []
    pairs = []
    with _local_imports(ROOT / 'shared/runtime', HERE):
        apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
        try:
            for i, grid in enumerate(grids):
                original_output = _grid(apply(program, copy.deepcopy(grid)))
                rival_output = _grid(apply(rival, copy.deepcopy(grid)))
                split = 'train' if i < args.demos else 'test'
                pair_index = i if split == 'train' else i - args.demos
                pairs.append({'split': split, 'pair_index': pair_index, 'sample_index': i,
                    'input': grid, 'output': original_output, 'rival_output': rival_output,
                    'control': grid[0][0], 'agrees': original_output == rival_output})
                for name, text, output in (('canonical', program, original_output), ('always_left_right', rival, rival_output)):
                    actual_executions.append({'program': name, 'program_sha256': sha(text.encode()),
                        'input_sha256': sha(raw(grid)), 'output_sha256': sha(raw(output)),
                        'split': split, 'pair_index': pair_index})
        finally:
            bridge.close()
    fits = all(p['agrees'] for p in pairs if p['split'] == 'train')
    differences = [p['pair_index'] for p in pairs if p['split'] == 'test' and not p['agrees']]
    source_binding = {'generator_path': str(path.relative_to(ROOT)), 'generator_sha256': source_hash,
        'canonical_rule_hash': metadata['rule_hash'], 'canonical_program_sha256': sha(program.encode()),
        'probe_sha256': sha(Path(__file__).read_bytes())}
    unchanged = sha(path.read_bytes()) == source_hash
    summary = {'schema': 'bounded-peer-teaching-probe-v1',
        'status': ('research_two_demo_teaching_caveat' if args.demos == 2 else 'proposed_teaching_defect')
                  if fits and differences else 'bounded_no_issue_for_tested_rival',
        'task_id': '37cec5981f3a', 'seed': args.seed, 'demo_count': args.demos, 'query_count': args.queries,
        'settings': {'difficulty': None}, 'sampling': 'direct_sampler_unapproved_research',
        'approved': metadata['approved'], 'train_safety': metadata['train_safety'],
        'approval_reasons': metadata['approval_reasons'], 'source_binding': source_binding,
        'source_unchanged': unchanged, 'racket': identity, 'actual_executions': actual_executions,
        'execution_count': len(actual_executions), 'controls': [p['control'] for p in pairs],
        'rival': 'always_left_right: canonical program with axis selector bound to 1',
        'rival_fits_all_visible_demonstrations': fits, 'disagreeing_queries': differences,
        'documentation_finding': {'generator_summary_claim': 'The control + originals stay.',
            'canonical_rule_behavior': 'Remove top-left control; retain and mirror the non-control sources.',
            'executed_original_outputs_remove_control': all(p['output'][0][0] == 0 for p in pairs)},
        'limitations': ['One seed, one declared plausible rival and this exact demo/query count were tested.',
            'Two-demo subsets, when requested, are explicit research configurations; they do not establish a default three-demo production defect.',
            'Generator is unapproved; this probe used direct sampling and protected execution, not production export.',
            'No generator source, authority, approval hash or parametric family was changed.'],
        'proposed_repair': 'Optional two-demo research lessons should cover both controls before either axis is queried; correct the summary to state control removal.'}
    evidence = {'source_binding': source_binding, 'racket': identity,
        'canonical_program': program, 'rival_program': rival, 'pairs': pairs}
    (args.out / 'summary.json').write_bytes(raw(summary))
    (args.out / 'minimal-counterexample.json').write_bytes(raw(evidence))
    print(json.dumps({'status': summary['status'], 'out': str(args.out), 'executions': len(actual_executions),
        'controls': summary['controls'], 'rival_fits_demos': fits, 'query_disagreements': differences}, sort_keys=True))
    return 0 if unchanged else 1


if __name__ == '__main__':
    raise SystemExit(main())
