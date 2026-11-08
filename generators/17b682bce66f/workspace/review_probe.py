"""Source-bound, repeatable diversity and Racket probes.

Run from the packet root.  ``stage`` creates a fresh portable runtime; ``census``
measures input recurrence, not model accuracy; ``parity`` executes the authority.
No approval labels or canonical sources are changed. Outputs are exclusive.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import time

TASK = '17b682bce66f'
BANDS = ('easy', 'medium', 'hard')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def translation_signature(grid):
    """Preserve canvas, colors and relative geometry; remove foreground position."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('grid must be nonempty and rectangular')
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not cells:
        return len(grid), len(grid[0]), ()
    r0 = min(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    return len(grid), len(grid[0]), tuple((r-r0, c-c0, v) for r, c, v in cells)


def summarize(rows):
    if len(rows) < 2:
        raise ValueError('at least two rows are required for a split')
    split = len(rows) // 2
    seen = {r['signature_hash'] for r in rows[:split]}
    hits = sum(r['signature_hash'] in seen for r in rows[split:])
    return {
        'draws': len(rows),
        'distinct_raw_inputs': len({r['raw_hash'] for r in rows}),
        'distinct_translation_normalized_inputs': len({r['signature_hash'] for r in rows}),
        'distinct_rotation_normalized_clouds': len({r['cloud_orbit_hash'] for r in rows
                                                   if r['cloud_orbit_hash'] is not None}),
        'profile_counts': dict(Counter(r['profile'] for r in rows)),
        'lookup_train_rows': split, 'lookup_test_rows': len(rows)-split,
        'lookup_test_signature_hits': hits,
        'lookup_test_signature_hit_fraction': hits/(len(rows)-split),
    }


def stage(args):
    library = args.library.resolve()
    sys.path.insert(0, str(library / 'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    receipt = prepare_runtime(Catalog(library), args.runtime, task_id=args.task_id)
    home = library / 'generators' / args.task_id
    for name in ('tests', 'workspace'):
        if (home/name).is_dir():
            shutil.copytree(home/name, args.runtime/name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    return {'runtime': str(args.runtime.resolve()), 'mapped_files': len(receipt['files']),
            'extra_task_test_workspace_files_copied': True}


def load_runtime(args):
    runtime = args.runtime.resolve()
    if not (runtime / 'RUNTIME_MANIFEST.json').is_file():
        raise ValueError('runtime is missing RUNTIME_MANIFEST.json; use stage first')
    sys.path.insert(0, str(runtime))
    module = importlib.import_module(f'puzzle_generators.per_puzzle.{args.task_id}.generator')
    return runtime, module


def census(args):
    runtime, module = load_runtime(args)
    report = {'schema': 'translation-concentration-v1', 'task_id': args.task_id,
              'generator_sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
              'interpretation': 'Signature recurrence is a shortcut warning, not measured model accuracy.',
              'seed_start': args.seed_start, 'seeds_per_band': args.samples,
              'sample_index_formula': '17*seed+1', 'bands': {}, 'failures': []}
    for band in BANDS:
        rows, witness = [], {}
        for seed in range(args.seed_start, args.seed_start + args.samples):
            kwargs = {'difficulty': band}
            if args.profile:
                kwargs['scene_profile'] = args.profile
            try:
                grid = module.generate(seed, 17*seed+1, **kwargs)
                original = copy.deepcopy(grid)
                errors = module.self_check(grid) if hasattr(module, 'self_check') else []
                if errors or grid != original:
                    raise ValueError(f'self_check={errors}; mutated={grid != original}')
                profile, cloud_hash = 'not_declared', None
                if hasattr(module, 'scene_observables'):
                    obs = module.scene_observables(grid)
                    profile = obs['scene_profile']
                    offsets = obs.get('cloud_offsets')
                    if offsets and hasattr(module, '_rotation_forms'):
                        cloud_hash = digest(min(module._rotation_forms(offsets)))
                row = {'seed': seed, 'sample_index': 17*seed+1, 'profile': profile,
                       'raw_hash': digest(grid), 'signature_hash': digest(translation_signature(grid)),
                       'cloud_orbit_hash': cloud_hash}
                rows.append(row)
                witness.setdefault(profile, {'seed': seed, 'sample_index': 17*seed+1, 'input': grid})
            except Exception as exc:
                report['failures'].append({'band': band, 'seed': seed,
                                           'sample_index': 17*seed+1,
                                           'error': f'{type(exc).__name__}: {exc}'})
        report['bands'][band] = {'summary': summarize(rows) if len(rows) >= 2 else {},
                                 'rows': rows, 'first_profile_examples': witness}
    report['novelty_gate'] = {'policy': 'task-local medium distinct normalized fraction >= 0.40',
                             'result': 'not_requested'}
    if args.assert_novelty:
        count = report['bands']['medium']['summary'].get('distinct_translation_normalized_inputs', 0)
        report['novelty_gate']['result'] = 'pass' if count >= .4*args.samples and not report['failures'] else 'fail'
    return report


def parity(args):
    runtime, module = load_runtime(args)
    from arc_repl.racket_bridge import RacketBridge
    from scripts.rule_smoke import rule_application
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source
    source = canonical_rule_source(args.task_id)
    cases = []
    for i, pair in enumerate(canonical_pairs(args.task_id)):
        cases.append(({'kind': 'canonical', 'pair_index': i}, pair['input'], pair['output']))
    # Distinct namespaces avoid counting the same seeded draw twice.
    for band in BANDS:
        for seed in range(args.seed_start, args.seed_start + args.samples):
            cases.append(({'kind': 'mixed', 'band': band, 'seed': seed,
                           'sample_index': 17*seed+1}, None, None))
    for profile in getattr(module, 'SCENE_PROFILES', ()):
        for j in range(args.profile_samples):
            seed = args.seed_start + 1_000_000 + j
            cases.append(({'kind': 'override', 'band': 'hard', 'seed': seed,
                           'sample_index': 17*seed+1, 'scene_profile': profile}, None, None))
    report = {'schema': 'keyed-offset-authority-parity-v1', 'task_id': args.task_id,
              'generator_sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
              'canonical_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'cases_requested': len(cases), 'cases_checked': 0, 'canonical_exact': 0,
              'mirror_checked': 0, 'mirror_exact': 0, 'identity_outputs': 0,
              'distinct_input_hashes': [], 'rows': [], 'failures': []}
    bridge = RacketBridge(max_calls_before_restart=48)
    hashes = set()
    try:
        for meta, given, expected in cases:
            grid = given
            try:
                if grid is None:
                    overrides = ({'scene_profile': meta['scene_profile']}
                                 if 'scene_profile' in meta else {})
                    grid = module.generate(meta['seed'], meta['sample_index'],
                                           difficulty=meta['band'], **overrides)
                original = copy.deepcopy(grid)
                errors = module.self_check(grid) if hasattr(module, 'self_check') else []
                output = bridge.eval_text(rule_application(source, grid))
                report['cases_checked'] += 1
                if grid != original or errors:
                    raise ValueError(f'input mutated={grid != original}; self_check={errors}')
                if expected is not None:
                    if output != expected:
                        raise ValueError('canonical output mismatch')
                    report['canonical_exact'] += 1
                if hasattr(module, 'rule_mirror'):
                    report['mirror_checked'] += 1
                    mirror = module.rule_mirror(grid)
                    if mirror != output:
                        report['failures'].append({**meta, 'error': 'mirror mismatch',
                                                   'input': grid, 'racket': output, 'mirror': mirror})
                    else:
                        report['mirror_exact'] += 1
                report['identity_outputs'] += (output == grid)
                hashes.add(digest(grid))
                report['rows'].append({**meta, 'input_sha256': digest(grid), 'output_sha256': digest(output)})
            except Exception as exc:
                report['failures'].append({**meta, 'input': grid, 'error': f'{type(exc).__name__}: {exc}'})
    finally:
        bridge.close()
    report['distinct_input_hashes'] = sorted(hashes)
    report['distinct_inputs'] = len(hashes)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('stage', 'census', 'parity'))
    parser.add_argument('--library', type=Path, default=Path('repo'))
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--task-id', default=TASK)
    parser.add_argument('--samples', type=int, default=600)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--profile-samples', type=int, default=12)
    parser.add_argument('--profile')
    parser.add_argument('--assert-novelty', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 2 or args.profile_samples < 0:
        parser.error('samples must be >= 2 and profile-samples >= 0')
    if args.out.exists():
        parser.error('output already exists; choose a new evidence path')
    start = time.monotonic()
    report = {'stage': stage, 'census': census, 'parity': parity}[args.mode](args)
    report['elapsed_seconds'] = time.monotonic() - start
    report['command_argv'] = sys.argv
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(str(args.out))
    return int(bool(report.get('failures')) or report.get('novelty_gate', {}).get('result') == 'fail')


if __name__ == '__main__':
    raise SystemExit(main())
