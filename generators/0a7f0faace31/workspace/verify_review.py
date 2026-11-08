"""Reusable source-bound controls, canonical rival fit, and public Racket parity.

From packet root:
  python3 run_with_racket.py python3 generators/0a7f0faace31/workspace/verify_review.py --seeds 1 --out ../checks/reusable-probe-final.json

Full: all declared integer dimensions, styles/textures, and four difficulty
settings. Quick: minimum/middle/maximum dimensions and default difficulty only.
This authoring probe never reads solve records and does not assemble lessons.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys
import time

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = '0a7f0faace31'
NAMESPACES = ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS', 'SEMANTIC_RIVALS')


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path, report):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def domain(axis, quick):
    valid = axis['valid']
    match = re.fullmatch(r'(\d+)\.\.(\d+)', valid)
    if match:
        lo, hi = map(int, match.groups())
        return sorted({lo, (lo+hi)//2, hi}) if quick else list(range(lo, hi+1))
    return valid.split('|')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='new source-bound JSON report path')
    parser.add_argument('--seeds', type=int, nargs='+', default=[1], help='explicit generator seeds (default: 1)')
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    if len(args.seeds) != len(set(args.seeds)):
        parser.error('--seeds must not contain duplicates')
    if args.out.exists():
        parser.error('--out must be a new path')
    root = find_root(__file__)
    source = root / 'generators' / TASK / 'generator.py'
    source_hash = file_sha(source)
    spec = importlib.util.spec_from_file_location('review_generator', source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    catalog = Catalog(root=root)
    metadata = catalog.describe(TASK)
    started = time.monotonic()
    report = {
        'schema': 'task-review-probe-v1', 'task_id': TASK, 'status': 'running',
        'source': {'generator_sha256': source_hash, 'generator_version': generator.VERSION,
                   'probe_sha256': file_sha(Path(__file__)),
                   'canonical_ledger_sha256': file_sha(canonical_path(root)),
                   'catalog_rule_hash': metadata['rule_hash'], 'declared_rule_hash': generator.RULE_HASH},
        'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
        'seeds': args.seeds, 'quick': args.quick,
        'failures': [], 'failure_count': 0,
        'limitations': ['Finite source-bound checks; no universal identifiability claim.',
                        'Controls use the selected Python validator and pixel observer.',
                        'Only a representative batch receives actual Racket labels.',
                        'Production lesson ambiguity and rotations belong to shared lesson-census.'],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        handle.write(json.dumps(report, indent=2) + '\n')

    def failure(kind, **details):
        report['failure_count'] += 1
        if len(report['failures']) < 20:
            report['failures'].append({'kind': kind, **details})
        if report['failure_count'] == 1:
            write_report(args.out, report)
            print(f"first failure saved: {kind}; see {args.out}", file=sys.stderr, flush=True)

    if metadata['generator_sha256'] != source_hash:
        failure('catalog_source_mismatch', catalog_sha256=metadata['generator_sha256'])
    if generator.RULE_HASH != metadata['rule_hash']:
        failure('declared_rule_mismatch')

    pairs = canonical_pairs(TASK, root=root)
    hooks = {}
    rival_report = {}
    mirror_fit = 0
    canonical_validator_pass = 0
    for pair in pairs:
        if generator._mirror(pair['input']) == pair['output']:
            mirror_fit += 1
        else:
            failure('canonical_mirror', pair=pair)
        errors = generator.self_check(pair['input'])
        if errors:
            failure('canonical_validator', pair=pair, errors=errors)
        else:
            canonical_validator_pass += 1
    for namespace in NAMESPACES:
        declaration = getattr(generator, namespace, None)
        if not isinstance(declaration, dict) or not declaration:
            failure('invalid_rival_declaration', namespace=namespace)
            continue
        hooks[namespace] = declaration
        rival_report[namespace] = {}
        for name, hook in declaration.items():
            fit = 0
            errors = []
            first_mismatch = None
            for pair in pairs:
                try:
                    prediction = hook(pair['input'])
                    if prediction == pair['output']:
                        fit += 1
                    elif first_mismatch is None:
                        first_mismatch = {'variant': pair['variant'], 'split': pair['split'],
                                          'pair_index': pair['pair_index'], 'prediction': prediction,
                                          'expected': pair['output'], 'input_sha256': digest(pair['input'])}
                except Exception as exc:
                    errors.append(str(exc))
            rival_report[namespace][name] = {'fit_count': fit, 'pair_count': len(pairs),
                                             'fits_all': fit == len(pairs), 'errors': errors,
                                             'first_mismatch': first_mismatch}
            if errors:
                failure('canonical_rival_execution', namespace=namespace, name=name, errors=errors)
            if namespace == 'CANONICAL_SHORTCUTS' and fit != len(pairs):
                failure('canonical_shortcut_refuted', name=name, fit_count=fit, pair_count=len(pairs))
    report['canonical'] = {'pair_count': len(pairs), 'mirror_fit_count': mirror_fit,
                           'validator_pass_count': canonical_validator_pass,
                           'namespace_declaration_counts': {n: len(d) for n, d in hooks.items()},
                           'rival_fit': rival_report}

    heights = domain(generator.AXES['grid_h'], args.quick)
    widths = domain(generator.AXES['grid_w'], args.quick)
    styles = domain(generator.AXES['frame_style'], False)
    textures = domain(generator.AXES['texture'], False)
    bands = [None] if args.quick else [None, 'easy', 'medium', 'hard']
    incompatible = generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS
    controls = {'heights': heights, 'widths': widths, 'styles': styles, 'textures': textures,
                'difficulty_settings': bands, 'declared_incompatibilities': incompatible,
                'enumeration_order': 'seed,difficulty,grid_h,grid_w,frame_style,texture; sample_index is zero-based attempt index across the whole product',
                'planned_attempts': len(args.seeds)*len(bands)*len(heights)*len(widths)*len(styles)*len(textures),
                'attempt_count': 0, 'accepted_count': 0, 'expected_rejection_count': 0,
                'exact_observation_count': 0, 'validator_pass_count': 0}
    report['controls'] = controls
    rejection_groups = {}
    per_band = Counter()
    unique_inputs = set()
    trace = hashlib.sha256()
    parity = [{'origin': 'canonical', 'identity': {k: p[k] for k in ('variant','split','pair_index')},
               'input': p['input']} for p in pairs]
    representative_pairs = set()
    for seed, band, height, width, style, texture in itertools.product(args.seeds, bands, heights, widths, styles, textures):
        index = controls['attempt_count']
        controls['attempt_count'] += 1
        request = {'seed': seed, 'sample_index': index, 'difficulty': band,
                   'overrides': {'grid_h': height, 'grid_w': width, 'frame_style': style, 'texture': texture}}
        expected_incompatible = any(all(request['overrides'].get(key) == value for key, value in entry.items())
                                    for entry in incompatible)
        try:
            grid = generator.generate(seed, index, difficulty=band, **request['overrides'])
        except Exception as exc:
            if expected_incompatible and isinstance(exc, ValueError):
                controls['expected_rejection_count'] += 1
                key = json.dumps({'difficulty': band, 'frame_style': style, 'texture': texture}, sort_keys=True)
                group = rejection_groups.setdefault(key, {'difficulty': band, 'frame_style': style, 'texture': texture,
                                                          'count': 0, 'representative_request': request,
                                                          'representative_error': str(exc)})
                group['count'] += 1
                trace.update(json.dumps([request, 'expected_rejection', str(exc)], sort_keys=True).encode()+b'\n')
            else:
                failure('compatible_generation_error', request=request, error=repr(exc))
            continue
        controls['accepted_count'] += 1
        per_band[str(band)] += 1
        if expected_incompatible:
            failure('incompatible_override_accepted', request=request, input=grid)
        observed = generator.observe_overrides(grid)
        if observed == request['overrides']:
            controls['exact_observation_count'] += 1
        else:
            failure('override_observation_mismatch', request=request, observed=observed, input=grid)
        errors = generator.self_check(grid, difficulty=band)
        if not errors:
            controls['validator_pass_count'] += 1
        else:
            failure('generated_validator_rejection', request=request, errors=errors, input=grid)
        input_hash = digest(grid)
        unique_inputs.add(input_hash)
        trace.update(json.dumps([request, input_hash, observed, errors], sort_keys=True).encode()+b'\n')
        if (style, texture) not in representative_pairs:
            representative_pairs.add((style, texture))
            parity.append({'origin': 'explicit_control', 'request': request, 'input': grid})
        if width == widths[-1] and height == heights[-1] and texture == textures[-1] and style == styles[0] and band is None:
            parity.append({'origin': 'maximum_size_control', 'request': request, 'input': grid})
        if controls['attempt_count'] % (len(heights)*len(widths)*len(styles)*len(textures)) == 0:
            print(f"controls: {controls['attempt_count']}/{controls['planned_attempts']} attempts; {report['failure_count']} failures", flush=True)
            write_report(args.out, report)
    controls.update(unique_input_count=len(unique_inputs), accepted_per_difficulty=dict(per_band),
                    structured_rejections=list(rejection_groups.values()), replay_trace_sha256=trace.hexdigest())

    defaults = []
    for band in bands:
        for index in range(3):
            grid = generator.generate(args.seeds[0], index, difficulty=band)
            observed = generator.observe_overrides(grid)
            row = {'seed': args.seeds[0], 'sample_index': index, 'difficulty': band,
                   'input_sha256': digest(grid), 'observed': observed, 'refutation_counts': {}}
            output = generator._mirror(grid)
            for namespace, declaration in hooks.items():
                row['refutation_counts'][namespace] = sum(hook(grid) != output for hook in declaration.values())
            defaults.append(row)
            parity.append({'origin': 'default_schedule', 'request': {'seed':args.seeds[0], 'sample_index':index,
                                                                   'difficulty':band}, 'input':grid})
    report['default_individual_samples'] = defaults
    if len(parity) > 64:
        failure('parity_batch_too_large', requested_count=len(parity))
        parity = parity[:64]
    try:
        actual = catalog.apply(TASK, [row['input'] for row in parity], timeout=120)
        actual['command'] = [sys.executable, *sys.argv]
        actual['cwd'] = str(Path.cwd())
        agreement = 0
        for row, result in zip(parity, actual['results'], strict=True):
            mirror = generator._mirror(row['input'])
            row['mirror_output'] = mirror
            row['actual_output'] = result['output']
            row['racket_error'] = result['error']
            if not result['error'] and mirror == result['output']:
                agreement += 1
            else:
                failure('racket_mirror_parity', counterexample=row)
        if actual['generator_sha256'] != source_hash:
            failure('racket_source_mismatch', actual_sha256=actual['generator_sha256'])
        report['parity'] = {'sample_count': len(parity), 'unique_input_count': len({digest(p['input']) for p in parity}),
                            'agreement_count': agreement, 'samples': parity, 'public_catalog_apply': actual}
    except Exception as exc:
        failure('public_apply_error', error=repr(exc), sample_count=len(parity))
    final_hash = file_sha(source)
    report['source']['generator_sha256_after'] = final_hash
    if final_hash != source_hash:
        failure('source_changed_during_probe', final_sha256=final_hash)
    report['elapsed_seconds'] = round(time.monotonic()-started, 3)
    report['status'] = 'pass' if not report['failure_count'] else 'fail'
    write_report(args.out, report)
    print(json.dumps({'status': report['status'], 'generator_sha256': source_hash,
                      'attempts': controls['attempt_count'], 'accepted': controls['accepted_count'],
                      'expected_rejections': controls['expected_rejection_count'],
                      'failures': report['failure_count'], 'parity': report.get('parity', {}).get('agreement_count'),
                      'elapsed_seconds': report['elapsed_seconds']}, indent=2))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
