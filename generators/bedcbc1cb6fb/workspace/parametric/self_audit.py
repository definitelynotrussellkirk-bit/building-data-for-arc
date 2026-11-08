"""Bounded teaching-family check with actual protected-Racket labels.

Run from the repo with its independent runtime, e.g.:
  python .../self_audit.py --out ../checks/bedcbc1cb6fb/self-audit
The Python geometry diagnostics never supply authoritative outputs. The sampler
chooses the fixed pool before any reference/query outputs are executed. Every
2..6 demonstration prefix uses the same four preselected novel queries.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(value):
    data = value.encode() if isinstance(value, str) else json.dumps(
        value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(data).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def _difference(a, b):
    return [[r, c, a[r][c], b[r][c]] for r in range(len(a))
            for c in range(len(a[r])) if a[r][c] != b[r][c]]


def run(out, seeds=(0, 17)):
    prototype = _load(HERE / 'prototype.py', '_bed_self_audit_prototype')
    rivals = _load(HERE / 'rivals.py', '_bed_self_audit_rivals')
    from arc_repl.racket_bridge import RacketBridge

    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    private = out / 'private'
    private.mkdir(exist_ok=True)
    counters = {'sample_pools': 0, 'truth_attempts': 0, 'truth_successes': 0,
                'truth_errors': 0, 'diagnostic_comparisons': 0,
                'diagnostic_disagreements': 0, 'prefix_reports': 0,
                'causal_attempts': 0, 'causal_successes': 0}
    summary = {
        'schema': 'bedcbc1cb6fb-finite-teaching-audit-v1',
        'seeds': list(seeds), 'demo_prefixes': [2, 3, 4, 5, 6],
        'queries_per_prefix': 4, 'rival_count': len(rivals.RIVALS),
        'rival_names': list(rivals.RIVALS), 'counters': counters,
        'source_sha256': {name: _sha((HERE / name).read_text())
                          for name in sorted(p.name for p in HERE.glob('*.py'))},
        'reports': [], 'errors': [], 'grammar_findings': [], 'causal_cases': [],
        'label_authority': 'prototype.execute through persistent protected RacketBridge',
        'selection_policy': 'sample_inputs(seed,demos=6,queries=4) completes input selection before Racket labels; sampler may use these same rivals on demo candidates only; fixed prefix demos; no query-answer-driven selection',
        'hypothesis_scope': 'The sampler reuses rivals.py for demo-only input selection. This is a check of that shared finite teaching family, not an independently chosen hypothesis sweep. Protected Racket labels remain independent of Python diagnostic outputs.',
        'limits': ['Finite named rivals and finite seeds only; same hypotheses reused during demo-only input selection.',
                   'Observed equivalent means no sampled disagreement, not semantic equivalence.',
                   'Python diagnostic outputs are comparisons only, never delivered labels.'],
    }
    pools = []
    # Input selection is completed before executing either setting's labels.
    for seed in seeds:
        try:
            pool = prototype.sample_inputs(seed, demos=6, queries=4)
            counters['sample_pools'] += 1
            if len(pool['train']) != 6 or len(pool['test']) != 4:
                raise ValueError('sampler returned wrong pool counts')
            if len({_sha(g) for g in pool['train'] + pool['test']}) != 10:
                raise ValueError('pool repeats inputs')
            pools.append((seed, pool))
        except Exception as exc:
            summary['errors'].append({'seed': seed, 'stage': 'sampling', 'error': repr(exc)})
    causal_counts = set()
    canonical_cases = {}
    with RacketBridge() as bridge:
        summary['runtime_identity'] = bridge.runtime_identity
        for seed, pool in pools:
            for setting in prototype.SETTINGS:
                rule = setting['rule']
                source = prototype.program(setting)
                source_hash = _sha(source)
                reference_file = private / f'{source_hash}.rkt'
                reference_file.write_text(source)
                case = {'seed': seed, 'settings': setting, 'program_sha256': source_hash,
                        'train': [], 'test': [], 'diagnostics': []}
                complete = True
                for split in ('train', 'test'):
                    for index, grid in enumerate(pool[split]):
                        counters['truth_attempts'] += 1
                        try:
                            output = prototype.execute(source, grid, bridge=bridge)
                            counters['truth_successes'] += 1
                            pair = {'input': grid, 'output': output,
                                    'input_sha256': _sha(grid), 'output_sha256': _sha(output)}
                            case[split].append(pair)
                        except Exception as exc:
                            complete = False
                            counters['truth_errors'] += 1
                            summary['errors'].append({'seed': seed, 'rule': rule,
                                                      'split': split, 'index': index,
                                                      'stage': 'reference_execute', 'error': repr(exc)})
                            continue
                        try:
                            info = rivals.analyze(grid)
                            if info['findings']:
                                summary['grammar_findings'].append({
                                    'seed': seed, 'rule': rule, 'split': split, 'index': index,
                                    'input_sha256': pair['input_sha256'],
                                    'findings': info['findings']})
                            diagnostic = rivals.predict(grid, rule)
                            counters['diagnostic_comparisons'] += 1
                            agree = diagnostic == output
                            if not agree:
                                counters['diagnostic_disagreements'] += 1
                            case['diagnostics'].append({
                                'split': split, 'index': index, 'intended_agrees': agree,
                                'difference': _difference(output, diagnostic), 'analysis': info})
                        except Exception as exc:
                            complete = False
                            summary['errors'].append({'seed': seed, 'rule': rule,
                                                      'split': split, 'index': index,
                                                      'stage': 'diagnostic', 'error': repr(exc)})
                _write(private / f'seed-{seed}-{rule}.json', case)
                if not complete:
                    continue
                if rule == 'rings':
                    canonical_cases[seed] = case
                for demos in range(2, 7):
                    report = rivals.teaching_report(case['train'][:demos], case['test'], rule)
                    report.update({'seed': seed, 'demos': demos, 'queries': 4,
                                   'program_sha256': source_hash})
                    counters['prefix_reports'] += 1
                    summary['reports'].append(report)
                # Causal cases use demonstrations already selected without answers.
                # Preserve A exactly; replace only its derived count used by B.
                if rule == 'ring_area_fill':
                    marker = '(define key-area (count-center after-a))'
                    if source.count(marker) != 1:
                        summary['errors'].append({'seed': seed, 'rule': rule, 'stage': 'causal_source',
                                                  'error': 'expected one exact B count marker'})
                        continue
                    for index, pair in enumerate(case['train']):
                        if len(causal_counts) >= 2:
                            break
                        info = rivals.analyze(pair['input'])
                        if seed not in canonical_cases:
                            summary['errors'].append({'seed': seed, 'stage': 'causal_canonical',
                                                      'error': 'canonical pool unavailable; no causal fallback labels inferred'})
                            break
                        canonical = canonical_cases[seed]['train'][index]['output']
                        t, l, b, r = info['innerbbox']
                        last = info['markerlist'][-1]
                        true_count = sum(canonical[y][x] == last
                                         for y in range(t, b+1) for x in range(l, r+1))
                        if true_count in causal_counts:
                            continue
                        wrong_keys = [k for k in info['keys'] if k['area'] != true_count]
                        if not wrong_keys:
                            continue
                        wrong_key = wrong_keys[0]
                        wrong_source = source.replace(marker, f"(define key-area {wrong_key['area']})")
                        counters['causal_attempts'] += 1
                        try:
                            wrong_output = prototype.execute(wrong_source, pair['input'], bridge=bridge)
                            retained_a = all(wrong_output[y][x] == canonical[y][x]
                                             for y in range(t-1, b+2) for x in range(l-1, r+2))
                            expected_wrong = [row[:] for row in canonical]
                            kt, kl, kb, kr = wrong_key['bbox']
                            for y in range(kt, kb+1):
                                for x in range(kl, kr+1):
                                    expected_wrong[y][x] = last
                            selected_bbox_agrees = wrong_output == expected_wrong
                            if wrong_output == pair['output'] or not retained_a or not selected_bbox_agrees:
                                raise AssertionError('count intervention did not change only the selected B bbox')
                            wrong_hash = _sha(wrong_source)
                            (private / f'{wrong_hash}.rkt').write_text(wrong_source)
                            witness = {
                                'seed': seed, 'demo_index': index, 'true_count': true_count,
                                'wrong_count': wrong_key['area'], 'framebbox': info['framebbox'],
                                'keys': info['keys'], 'input': pair['input'],
                                'canonical_a_output': canonical, 'intended_output': pair['output'],
                                'counterfactual_output': wrong_output,
                                'intended_program': source, 'counterfactual_program': wrong_source,
                                'intended_program_sha256': source_hash,
                                'counterfactual_program_sha256': wrong_hash,
                                'input_sha256': pair['input_sha256'],
                                'canonical_a_output_sha256': _sha(canonical),
                                'intended_output_sha256': pair['output_sha256'],
                                'counterfactual_output_sha256': _sha(wrong_output),
                                'changed_cells': _difference(pair['output'], wrong_output),
                                'canonical_frame_retained': retained_a,
                                'counterfactual_matches_selected_bbox': selected_bbox_agrees,
                                'wrong_key_bbox': wrong_key['bbox'],
                                'intervention': 'Only B lookup count changed; canonical A and B paint logic byte-identical.',
                            }
                            filename = f'causal-seed-{seed}-demo-{index}.json'
                            _write(private / filename, witness)
                            summary['causal_cases'].append({
                                'path': 'private/' + filename, 'seed': seed, 'demo_index': index,
                                'true_count': true_count, 'wrong_count': wrong_key['area'],
                                'canonical_frame_retained': retained_a,
                                'changed_cell_count': len(witness['changed_cells'])})
                            counters['causal_successes'] += 1
                            causal_counts.add(true_count)
                        except Exception as exc:
                            summary['errors'].append({'seed': seed, 'rule': rule,
                                                      'stage': 'causal_execute', 'error': repr(exc)})
    summary['teaching_failures'] = [
        {'seed': r['seed'], 'rule': r['rule'], 'demos': r['demos'], 'rivals': r['failures']}
        for r in summary['reports'] if r['failures']]
    summary['inconclusive_reports'] = [
        {'seed': r['seed'], 'rule': r['rule'], 'demos': r['demos'], 'rivals': r['inconclusive']}
        for r in summary['reports'] if r['inconclusive']]
    summary['source_sha256_after'] = {name: _sha((HERE / name).read_text())
                                      for name in sorted(p.name for p in HERE.glob('*.py'))}
    summary['source_stable_during_run'] = summary['source_sha256_after'] == summary['source_sha256']
    if not summary['source_stable_during_run']:
        summary['errors'].append({'stage': 'source_stability',
                                  'error': 'adjacent Python source changed during audit'})
    summary['status'] = ('pass_finite_audit' if not summary['errors']
                         and not summary['teaching_failures'] and not summary['inconclusive_reports']
                         and not summary['grammar_findings']
                         and counters['diagnostic_disagreements'] == 0
                         and counters['causal_successes'] >= 2 else 'findings_or_inconclusive')
    _write(out / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[0, 17])
    args = parser.parse_args()
    summary = run(args.out, args.seeds)
    print(json.dumps({k: summary[k] for k in (
        'status', 'counters', 'teaching_failures', 'inconclusive_reports', 'errors', 'grammar_findings', 'causal_cases')},
        indent=2, sort_keys=True))
    return 0 if summary['status'] == 'pass_finite_audit' else 1


if __name__ == '__main__':
    raise SystemExit(main())
