#!/usr/bin/env python3
"""Opt-in, authoring-only role-position counterfactual gate for 5639e60f0fac.

Never use during a blind solve: prepare reads canonical labels. From repo cwd:
  python generators/5639e60f0fac/workspace/probe_role_positions.py prepare --out ../checks/roles-input.json
  python -m arcpuzzles apply 5639e60f0fac --input ../checks/roles-input.json --out ../checks/roles-racket.json
  python generators/5639e60f0fac/workspace/probe_role_positions.py score --inputs ../checks/roles-input.json --racket ../checks/roles-racket.json --out ../checks/roles-report.json

Use the public command recorder around these commands. This tool never executes
Racket or imports a private runner. Stored public Racket outputs are scored
separately from independent Python expected masks and the generator mirror.
The record's provenance must be established by its external command receipt;
JSON hashes alone do not authenticate who produced it.
Prepare writes the public {"inputs": [...]} payload at --out and its bound
metadata beside it with suffix .meta.json. Keep both files for score/replay.

Applicability is intentionally narrow: one isolated connected green3 stencil,
one same-sized solid cyan8 canvas, zero background, bbox 3x3 or 3x4. Role colors,
mask, orientation and size stay fixed. Moving objects is NOT a valid generic
augmentation for tasks where position changes the rule. A mirror suitability
check rejects such behavior on these witnesses; authority disagreements block
a PASS. Finite witnesses cannot prove position invariance in every possible grid.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = '5639e60f0fac'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_generator():
    source = Path(__file__).resolve().parents[1] / 'generator.py'
    spec = importlib.util.spec_from_file_location('role_position_generator', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def public_support(source):
    # Bind to the explicit source tree, never whichever repository happens to be cwd.
    for ancestor in Path(source).resolve().parents:
        for runtime in (ancestor / 'shared/runtime', ancestor / 'runtime'):
            if (runtime / 'reviewer_support.py').is_file():
                sys.path.insert(0, str(runtime))
                from reviewer_support import find_root, canonical_pairs, canonical_path
                return find_root(source), canonical_pairs, canonical_path
    raise ValueError('portable reviewer_support is unavailable')


def role_data(grid):
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)):
        raise ValueError('domain requires a rectangular nonempty grid')
    if any(type(v) is not int for row in grid for v in row):
        raise ValueError('domain requires integer grid colors, excluding bool')
    if any(v not in (0, 3, 8) for row in grid for v in row):
        raise ValueError('domain requires colors 0, 3, 8 only')
    result = {}
    for color, name in ((3, 'template'), (8, 'canvas')):
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
        if not cells:
            raise ValueError('domain requires both role objects')
        reached = set(); todo = [next(iter(cells))]
        while todo:
            r, c = todo.pop()
            if (r, c) in reached:
                continue
            reached.add((r, c))
            todo.extend(p for p in ((r+1,c), (r-1,c), (r,c+1), (r,c-1)) if p in cells and p not in reached)
        if reached != cells:
            raise ValueError('domain requires one connected component per role color')
        bbox = (min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells))
        result[name] = {'cells': cells, 'bbox': bbox}
    t, c = result['template'], result['canvas']
    tr, tc, tb, te = t['bbox']; cr, cc, cb, ce = c['bbox']
    shape = (tb-tr+1, te-tc+1)
    if shape not in ((3,3), (3,4)) or shape != (cb-cr+1, ce-cc+1):
        raise ValueError('domain requires matching 3x3 or 3x4 role boxes')
    if len(c['cells']) != shape[0]*shape[1] or len(t['cells']) == shape[0]*shape[1]:
        raise ValueError('domain requires a solid canvas and sparse stencil')
    if not (tb+1 < cr or cb+1 < tr or te+1 < cc or ce+1 < tc):
        raise ValueError('role boxes overlap or lack an empty buffer')
    result['shape'] = shape
    return result


def move_roles(grid, template_at, canvas_at):
    roles = role_data(grid); h, w = len(grid), len(grid[0]); bh, bw = roles['shape']
    for r, c in (template_at, canvas_at):
        if r < 0 or c < 0 or r+bh > h or c+bw > w:
            raise ValueError('movement exceeds grid bounds')
    out = [[0]*w for _ in range(h)]
    tr, tc, _, _ = roles['template']['bbox']
    for r, c in roles['template']['cells']:
        out[template_at[0]+r-tr][template_at[1]+c-tc] = 3
    for r in range(bh):
        for c in range(bw):
            if out[canvas_at[0]+r][canvas_at[1]+c]:
                raise ValueError('movement would overlap the two roles')
            out[canvas_at[0]+r][canvas_at[1]+c] = 8
    role_data(out)
    return out


def color_expected(grid):
    roles = role_data(grid); tr, tc, _, _ = roles['template']['bbox']; cr, cc, _, _ = roles['canvas']['bbox']
    out = [row[:] for row in grid]
    for r in range(roles['shape'][0]):
        for c in range(roles['shape'][1]):
            out[cr+r][cc+c] = 8 if grid[tr+r][tc+c] == 3 else 0
    return out


def declarations(generator):
    groups = {}
    union = {}
    for field in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS'):
        group = getattr(generator, field, None)
        if not isinstance(group, dict) or not group:
            raise ValueError(f'{field} must be a nonempty callable mapping')
        for name, fn in group.items():
            if not isinstance(name, str) or not callable(fn):
                raise ValueError(f'invalid callable declaration in {field}')
            if name in union and union[name] is not fn:
                raise ValueError(f'conflicting callable definitions for {name}')
            union[name] = fn
        groups[field] = group
    return groups


def rule_identity(root, canonical_path):
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
    rules = [row['program_solution'] for row in rows if row.get('task_id') == TASK_ID]
    hashes = {hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12] for rule in rules}
    if len(hashes) != 1:
        raise ValueError('canonical rule identity is absent or ambiguous')
    return hashes.pop(), hashlib.sha256(rules[0].encode()).hexdigest()


def ordinary_coverage(generator, shortcuts):
    """A cheap finite ordinary-sample census, expressly using Python predictions."""
    quadrants = {q: 0 for q in ('upper_left', 'upper_right', 'lower_left', 'lower_right')}
    rivals = {name: {'agreements': 0, 'disagreements': 0} for name in shortcuts}
    bands = {}; selected = []; selected_names = set()
    for band in ('easy', 'medium', 'hard'):
        band_counts = {'samples': 0, 'quadrants': dict.fromkeys(quadrants, 0),
                       'shortcut_disagreements': dict.fromkeys(shortcuts, 0)}
        for seed in range(8):
            for index in range(12):
                grid = generator.generate(seed, index, difficulty=band)
                if generator.self_check(grid):
                    raise ValueError(f'ordinary generated sample fails domain: {band}/{seed}/{index}')
                roles = role_data(grid); t = roles['template']['bbox']; c = roles['canvas']['bbox']
                q = ('upper' if t[0] < c[0] else 'lower') + '_' + ('left' if t[1] < c[1] else 'right')
                expected = generator.rule_mirror(grid)
                if expected != color_expected(grid):
                    raise ValueError('ordinary sample has position semantics: applicability check failed')
                band_counts['samples'] += 1; quadrants[q] += 1; band_counts['quadrants'][q] += 1
                refuted = []
                for name, fn in shortcuts.items():
                    agrees = fn(grid) == expected
                    rivals[name]['agreements' if agrees else 'disagreements'] += 1
                    if not agrees:
                        band_counts['shortcut_disagreements'][name] += 1
                        refuted.append(name)
                new_names = set(refuted) - selected_names
                if new_names:
                    selected.append({'kind': 'generated_witness', 'seed': seed, 'sample_index': index,
                                     'difficulty': band, 'position_bias': q, 'proxy_refuted_names': refuted,
                                     'python_expected': expected, 'input': grid})
                    selected_names.update(new_names)
        bands[band] = band_counts
    return {'samples': 288, 'seeds': list(range(8)), 'sample_indices': list(range(12)),
            'prediction_kind': 'Python rule_mirror proxy; not Racket authority',
            'quadrants': quadrants, 'per_band': bands, 'shortcuts': rivals,
            'uncovered_quadrants': [q for q, count in quadrants.items() if not count],
            'unrefuted_shortcuts': [name for name, count in rivals.items() if not count['disagreements']]}, selected


def prepare(generator, source, *, coverage=False):
    if getattr(generator, 'TASK_ID', None) != TASK_ID:
        raise ValueError('this role-position gate is task-specific, not a generic augmentation')
    root, canonical_pairs, canonical_path = public_support(source)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    groups = declarations(generator); claims = {}
    for name, fn in groups['CANONICAL_SHORTCUTS'].items():
        hits = sum(fn(pair['input']) == pair['output'] for pair in pairs)
        claims[name] = {'canonical_matches': hits, 'canonical_denominator': len(pairs)}
        if hits != len(pairs):
            raise ValueError(f'claimed canonical shortcut {name} fits only {hits}/{len(pairs)} labels')
    cases = []
    for pair in pairs:
        identity = {key: pair[key] for key in ('variant', 'split', 'pair_index')}
        grid = pair['input']; roles = role_data(grid)
        cases.append({'kind': 'canonical', 'canonical_pair': identity, 'python_expected': pair['output'], 'input': grid})
        bh, bw = roles['shape']; h, w = len(grid), len(grid[0])
        corners = {'upper_left': (1,1), 'upper_right': (1,w-bw-1),
                   'lower_left': (h-bh-1,1), 'lower_right': (h-bh-1,w-bw-1)}
        opposites = {'upper_left': 'lower_right', 'upper_right': 'lower_left',
                     'lower_left': 'upper_right', 'lower_right': 'upper_left'}
        for quadrant, at in corners.items():
            moved = move_roles(grid, at, corners[opposites[quadrant]])
            expected = color_expected(moved)
            cases.append({'kind': 'counterfactual', 'canonical_pair': identity,
                          'position_bias': quadrant, 'python_expected': expected, 'input': moved})
    ordinary = None
    if coverage:
        ordinary, selected = ordinary_coverage(generator, groups['CANONICAL_SHORTCUTS'])
        cases.extend(selected)
    for case in cases:
        errors = generator.self_check(case['input'])
        if errors:
            raise ValueError(f'counterfactual outside generator domain: {errors}')
        if generator.rule_mirror(case['input']) != case['python_expected']:
            raise ValueError('position semantics or mirror mismatch: applicability check failed')
    rule_hash, raw_rule_sha = rule_identity(root, canonical_path)
    counts = {split: sum(p['split'] == split for p in pairs) for split in ('train','test')}
    packet = {'schema': 'role-position-inputs-v1', 'task_id': TASK_ID,
              'generator_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
              'rule_hash': rule_hash, 'rule_text_sha256': raw_rule_sha,
              'canonical_rule_source_sha256': raw_rule_sha,
              'canonical_labeled_pairs': len(pairs), 'canonical_split_counts': counts,
              'canonical_shortcuts': claims, 'competitor_names': sorted(groups['LESSON_COMPETITORS']),
              'coverage_requested': coverage, 'ordinary_coverage': ordinary,
              'cases': cases, 'inputs': [case.pop('input') for case in cases]}
    packet['payload_sha256'] = digest(packet)
    return packet


def score(packet, racket, generator, source):
    current = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    if packet.get('generator_sha256') != current or racket.get('generator_sha256') != current:
        raise ValueError('source identity mismatch: prepare/apply/score must use identical generator bytes')
    unsigned = {k:v for k,v in packet.items() if k != 'payload_sha256'}
    if packet.get('payload_sha256') != digest(unsigned):
        raise ValueError('prepared input payload integrity mismatch')
    fresh = prepare(generator, source, coverage=packet.get('coverage_requested', False))
    if fresh['payload_sha256'] != packet['payload_sha256']:
        raise ValueError('prepared inputs no longer match canonical/source declarations')
    if (racket.get('schema') != 'arcpuzzles-apply-v1' or racket.get('task_id') != TASK_ID
            or racket.get('rule_task_id') != TASK_ID
            or racket.get('reference') != 'canonical' or not racket.get('rule_hash_matches_catalog')
            or racket.get('executed_rule_hash') != packet['rule_hash']
            or racket.get('catalog_rule_hash') != packet['rule_hash']):
        raise ValueError('stored public Racket rule identity mismatch')
    results = racket.get('results', [])
    if len(results) != len(packet['inputs']) or [r.get('index') for r in results] != list(range(len(results))):
        raise ValueError('stored Racket result coverage/index mismatch')
    for index, (grid, result) in enumerate(zip(packet['inputs'], results)):
        if result.get('input') != grid or result.get('input_sha256') != digest(grid):
            raise ValueError(f'stored Racket input identity mismatch at index {index}')
        output = result.get('output')
        if output is None or result.get('output_sha256') != digest(output):
            raise ValueError(f'stored Racket output integrity mismatch at index {index}')
        if result.get('error') or result.get('valid_output') is not True:
            raise ValueError(f'stored Racket output is invalid at index {index}')
    mismatches = [i for i, (case,r) in enumerate(zip(packet['cases'], results)) if r.get('output') != case['python_expected']]
    coverage = {}
    for field, group in declarations(generator).items():
        scored = {}
        for name, fn in group.items():
            agreements = [fn(grid) == result.get('output') for grid, result in zip(packet['inputs'], results)]
            scored[name] = {'canonical_agreements': sum(a for a,c in zip(agreements,packet['cases']) if c['kind']=='canonical'),
                            'counterfactual_disagreements': sum(not a for a,c in zip(agreements,packet['cases']) if c['kind']=='counterfactual'),
                            'disagreement_indices': [i for i,a in enumerate(agreements) if not a]}
        coverage[field] = scored
    unrefuted = [n for n,v in coverage['CANONICAL_SHORTCUTS'].items() if not v['counterfactual_disagreements']]
    ordinary = packet.get('ordinary_coverage')
    ordinary_missing = bool(ordinary and (ordinary['uncovered_quadrants'] or ordinary['unrefuted_shortcuts']))
    return {'schema': 'role-position-report-v1', 'task_id': TASK_ID,
            'status': 'PASS' if not mismatches and not unrefuted and not ordinary_missing else 'FAIL',
            'generator_sha256': current, 'executed_rule_hash': racket['executed_rule_hash'],
            'executed_rule_text_sha256': racket.get('rule_text_sha256'),
            'canonical_rule_source_sha256': packet['canonical_rule_source_sha256'],
            'input_payload_sha256': packet['payload_sha256'], 'authority_record_sha256': digest(racket),
            'authority_label_kind': 'stored_public_racket_record',
            'python_label_kind': 'canonical authoring labels plus independent fixed-role mask predictions',
            'canonical_labeled_pairs': packet['canonical_labeled_pairs'],
            'canonical_split_counts': packet['canonical_split_counts'], 'inputs_scored': len(results),
            'authority_inputs_by_kind': {kind: sum(c['kind'] == kind for c in packet['cases'])
                                        for kind in ('canonical','counterfactual','generated_witness')},
            'ordinary_coverage': ordinary,
            'python_mirror_mismatches': mismatches, 'position_invariance_supported': not mismatches,
            'canonical_shortcuts': coverage['CANONICAL_SHORTCUTS'],
            'lesson_competitors': coverage['LESSON_COMPETITORS'], 'unrefuted_shortcuts': unrefuted,
            'applicability_limits': ['Opt-in task-local authoring tool; never use during blind solves.',
                'Fixed colors and masks; one sparse green3 object and one isolated matching solid cyan8 canvas.',
                'Position-semantic tasks can invalidate movement; mirror or authority disagreement blocks PASS.',
                'Finite witness coverage is not a distribution census or proof of universal position invariance.',
                'A stored JSON record requires an external public-command receipt for authentic authority provenance.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare'); p.add_argument('--out', type=Path, required=True,
        help='public apply payload; matching identity metadata is written at .meta.json')
    p.add_argument('--coverage', action='store_true', help='scan 288 ordinary samples with Python mirror and include selected generated witnesses')
    s = commands.add_parser('score'); s.add_argument('--inputs', type=Path, required=True)
    s.add_argument('--racket', type=Path, required=True); s.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); generator, source = load_generator()
    if args.command == 'prepare':
        report = prepare(generator, source, coverage=args.coverage)
        metadata = args.out.with_suffix('.meta.json')
        if args.out.exists() or metadata.exists():
            raise ValueError('output already exists; choose a new payload and metadata path')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with metadata.open('x') as handle:
            json.dump(report, handle, indent=2); handle.write('\n')
        payload = {'inputs': report['inputs']}
    else:
        payload = json.loads(args.inputs.read_text())
        packet = json.loads(args.inputs.with_suffix('.meta.json').read_text())
        if payload != {'inputs': packet.get('inputs')}:
            raise ValueError('public input payload does not match bound preparation metadata')
        report = score(packet, json.loads(args.racket.read_text()), generator, source)
        payload = report
    with args.out.open('x') as handle:
        json.dump(payload, handle, indent=2); handle.write('\n')
    print(json.dumps({'command':args.command, 'out':str(args.out), 'status':report.get('status','PREPARED'),
                      'generator_sha256':report['generator_sha256']}))
    return 1 if report.get('status') == 'FAIL' else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except ValueError as exc:
        raise SystemExit(str(exc))
