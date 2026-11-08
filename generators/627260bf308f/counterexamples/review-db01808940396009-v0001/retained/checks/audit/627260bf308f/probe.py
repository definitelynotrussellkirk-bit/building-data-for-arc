"""Read-only assigned-source audit; canonical labels use the protected Racket bridge."""
from __future__ import annotations
import argparse
import hashlib
import importlib.machinery
import importlib.util
import itertools
import json
from pathlib import Path
import sys

TASK = '627260bf308f'
EXPECTED_SOURCE = '07ee110e1e46147138b48c2cac3c544ef628cb595a53bc5eb5955fcb58c89b1f'

def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()

def independent_rank_output(grid):
    palette = [value for value in grid[0] if value]
    pending = {(r, c) for r, row in enumerate(grid) if r > 0 for c, value in enumerate(row) if value == 8}
    groups = []
    while pending:
        start = min(pending)
        pending.remove(start)
        stack, group = [start], {start}
        while stack:
            r, c = stack.pop()
            for point in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if point in pending:
                    pending.remove(point)
                    group.add(point)
                    stack.append(point)
        groups.append(group)
    groups.sort(key=lambda group: (len(group), min(r for r,c in group), min(c for r,c in group), max(r for r,c in group), max(c for r,c in group)))
    output = [list(row) for row in grid]
    for group, color in zip(groups, palette):
        for r,c in group:
            output[r][c] = color
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.repo.resolve(), args.out.resolve()
    if out.exists():
        raise FileExistsError(out)
    sys.path.insert(0, str(root / 'shared/runtime'))
    from reviewer_support import load_selected_generator, canonical_pairs
    if importlib.util.find_spec('scripts') is None:
        spec = importlib.machinery.ModuleSpec('scripts', loader=None, is_package=True)
        spec.submodule_search_locations[:] = [str(root / 'shared/tools')]
        sys.modules['scripts'] = importlib.util.module_from_spec(spec)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    module, source, source_hash = load_selected_generator(TASK, root=root)
    if source_hash != EXPECTED_SOURCE:
        raise ValueError('Audit source differs from the assigned immutable source')
    assignment = json.loads((root.parent / 'AUDIT_ASSIGNMENT.json').read_text())
    binding = next(row for row in assignment['targets'] if row['task_id'] == TASK)
    if binding['generator_sha256'] != source_hash:
        raise ValueError('Audit contract differs from selected source')
    record = next(json.loads(line) for line in (root / 'shared/data/canonical/puzzles.jsonl').open()
                  if json.loads(line).get('task_id') == TASK)
    rule = record['program_solution']
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    report = {
        'schema': 'assigned-readonly-audit-v1', 'task_id': TASK,
        'generator_sha256': source_hash, 'generator_version': module.VERSION,
        'rule_text_sha256': digest(rule.encode()),
        'normalized_rule_hash': digest(' '.join(rule.split()).encode())[:12],
        'canonical_record_sha256': digest(record), 'audit_assignment': assignment,
        'probe_sha256': digest(Path(__file__).read_bytes()),
        'argv': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
        'scope': 'Three canonical pairs; 72 default draws; 64 boundary override draws; 36 consecutive lessons and144query rotations against seven declared rivals; malformed and grid-bound validation.',
        'cases': [], 'canonical_checks': [], 'declared_rival_canonical_fit': {},
        'malformed': [], 'invalid_identity_calls': [], 'counterexamples': [],
        'failures': [], 'status': 'running',
    }
    def save():
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    save()
    default_grids = {}
    total = 0
    with RacketBridge() as bridge:
        report['runtime_identity'] = bridge.runtime_identity
        bridge.eval_text('(define __audit_rule ' + wrap_rule(rule) + ')')
        def actual(grid):
            bridge.define_grid('__audit_grid', grid)
            return bridge.eval_text('(__audit_rule __audit_grid)')
        for index, pair in enumerate(canonical):
            output = actual(pair['input'])
            passed = output == pair['output']
            report['canonical_checks'].append({'pair_index': index, 'passed': passed,
                'input_sha256': digest(pair['input']), 'output_sha256': digest(output)})
            if not passed:
                report['failures'].append({'kind': 'canonical_mismatch', 'pair': pair, 'actual': output})
        for name, rival in module.SEMANTIC_RIVALS.items():
            report['declared_rival_canonical_fit'][name] = sum(rival(pair['input']) == pair['output'] for pair in canonical)
        requests = []
        for band, seed, index in itertools.product(('easy','medium','hard'), range(4), range(6)):
            requests.append(('default', seed, index, band, {}))
        for h,w,n,order,index in itertools.product((8,24), (10,24), (2,3,4,5), ('sorted','unsorted'), (0,1)):
            requests.append(('boundary_override', 867, index, 'medium', {'grid_h':h,'grid_w':w,'n_components':n,'palette_order':order}))
        for kind, seed, index, band, overrides in requests:
            grid = module.generate(seed, index, difficulty=band, **overrides)
            errors = module.self_check(grid)
            observed = module.observe_overrides(grid)
            output = actual(grid)
            expected = independent_rank_output(grid)
            matches = output == expected
            observations_match = all(observed[key] == value for key,value in overrides.items())
            rival_matches = {name: rival(grid) == output for name,rival in module.SEMANTIC_RIVALS.items()}
            result = {'kind':kind,'seed':seed,'sample_index':index,'difficulty':band,'overrides':overrides,
                'input_sha256':digest(grid),'output_sha256':digest(output),'shape':[len(grid),len(grid[0])],
                'self_check':errors,'observed':observed,'overrides_exact':observations_match,
                'racket_matches_independent_rank':matches,'declared_rival_matches':rival_matches}
            report['cases'].append(result)
            if errors or not matches or not observations_match:
                report['failures'].append({**result,'input':grid,'racket_output':output,'independent_output':expected})
            if kind == 'default':
                default_grids[(band,seed,index)] = (grid,output,rival_matches)
                if index % 2 == 0 and any(rival_matches.values()):
                    report['failures'].append({**result,'kind':'default_even_did_not_refute_all_declared_rivals','input':grid,'racket_output':output})
            total += 1
            if total % 20 == 0:
                print('Reference-checked generated cases:', total, flush=True)
                save()
        # Positive validator witnesses beyond ARC dimensions; body/palette remain lawful.
        base = default_grids[('easy',0,0)][0]
        for dimension in ('width','height'):
            grid = ([row + [0] * (31-len(row)) for row in base] if dimension == 'width'
                    else [row[:] for row in base] + [[0] * len(base[0]) for _ in range(31-len(base))])
            output = actual(grid)
            report['counterexamples'].append({
                'finding_id':'A627-1','kind':'out_of_ARC_dimensions_accepted','dimension':dimension,
                'constructed_from':{'seed':0,'sample_index':0,'difficulty':'easy','overrides':{}},
                'input':grid,'actual_racket_output':output,'rival_output':None,
                'shape':[len(grid),len(grid[0])],'self_check':module.self_check(grid),
                'strict_canonical_like':module.strict_canonical_like(grid),
                'input_sha256':digest(grid),'output_sha256':digest(output),
                'generator_sha256':source_hash,'rule_text_sha256':report['rule_text_sha256'],
                'belongs_to_advertised_sampler_domain':False,
                'note':'Padding preserves palette, component sizes and separation; dimension31is outside ARC and advertised grid controls.'})
    lessons, rotations, ambiguous, ambiguous_rotations = 0,0,[],[]
    for band, seed, start in itertools.product(('easy','medium','hard'), range(4), range(3)):
        pairs = [default_grids[(band,seed,index)] for index in range(start,start+4)]
        names = tuple(module.SEMANTIC_RIVALS)
        bad = [name for name in names if all(pair[2][name] for pair in pairs[:3]) and not pairs[3][2][name]]
        lessons += 1
        if bad:
            ambiguous.append({'band':band,'seed':seed,'start':start,'rivals':bad})
        for q in range(4):
            bad = [name for name in names if all(pairs[i][2][name] for i in range(4) if i != q) and not pairs[q][2][name]]
            rotations += 1
            if bad:
                ambiguous_rotations.append({'band':band,'seed':seed,'start':start,'query':q,'rivals':bad})
    malformed = [None, [], [[]], [[True]], [['8']], [[8.0]], [[-1]], [[10]], [[0],[0,0]],
                 [0], [[1,2]], [[1,2],[0,0]], [[1,2],[0,0],[8,8]], [[1,1],[0,0],[8,0]]]
    for grid in malformed:
        try:
            errors = module.self_check(grid)
            report['malformed'].append({'input':grid,'errors':errors,'rejected':bool(errors)})
        except Exception as exc:
            report['malformed'].append({'input':grid,'exception':repr(exc),'rejected':False})
    for name, value in [('seed',True),('seed',1.5),('seed','1'),('sample_index',True),('sample_index',1.5),('sample_index',-1)]:
        seed,index = (value,0) if name == 'seed' else (0,value)
        try:
            grid=module.generate(seed,index,difficulty='medium')
            result={'accepted':True,'input_sha256':digest(grid),'self_check':module.self_check(grid)}
        except Exception as exc:
            result={'accepted':False,'exception':repr(exc)}
        report['invalid_identity_calls'].append({'argument':name,'value':value,**result})
    report['summary'] = {'canonical_passed':sum(row['passed'] for row in report['canonical_checks']),
        'canonical_total':len(canonical),'default_cases':72,'boundary_override_cases':64,
        'reference_checked_generated_cases':len(report['cases']),
        'unique_generated_inputs':len({row['input_sha256'] for row in report['cases']}),
        'self_check_failures':sum(bool(row['self_check']) for row in report['cases']),
        'reference_rank_mismatches':sum(not row['racket_matches_independent_rank'] for row in report['cases']),
        'override_mismatches':sum(not row['overrides_exact'] for row in report['cases']),
        'default_even_witnesses':36,'declared_unique_rivals':len(module.SEMANTIC_RIVALS),
        'production_lessons':lessons,'ambiguous_production_lessons':ambiguous,
        'query_role_rotations':rotations,'ambiguous_query_role_rotations':ambiguous_rotations,
        'malformed_cases':len(malformed),'malformed_rejected':sum(row['rejected'] for row in report['malformed']),
        'dimension_counterexamples':len(report['counterexamples'])}
    if digest(source.read_bytes()) != source_hash:
        raise ValueError('Audit source changed during read-only probe')
    report['status']='completed_with_findings'
    save()
    print(json.dumps(report['summary'],sort_keys=True),flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
