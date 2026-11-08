#!/usr/bin/env python3
"""Source-bound official adversarial audit; no target source edits or Racket calls.

Run this file with the packet's Python. It imports the selected source through
reviewer_support.load_selected_generator, reproduces one exact episode and
writes inputs for supported arcpuzzles apply. Python labels are provisional
until compared to the separately retained Racket receipt.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORK / 'repo/shared/runtime'))
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

EXPECTED = {
    'ebd08d719ed6': '11501342d0db51f960e1e805844fd2c6949936c3c8e7988fc563b86f44af2ae8',
    '05b5a82ace36': '20de203b605235b2d1120b08f31f54b5fb172b77c3400224da0cc416575de305',
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def grid_sha(grid):
    return sha(json.dumps(grid, separators=(',', ':')).encode())

def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def stamp(grid, module, union=False):
    components = [c for c in module._components(grid, {2, 4}) if len(c) > 1]
    source = [p for c in components for p in c] if union else max(components, key=len)
    min_r = min(r for r, c in source)
    min_c = min(c for r, c in source)
    shape = [(r-min_r, c-min_c) for r, c in source]
    h, w = len(grid), len(grid[0])
    output = [[0] * w for _ in range(h)]
    for ar, row in enumerate(grid):
        for ac, color in enumerate(row):
            if color in {6, 7, 8, 9}:
                for r, c in shape:
                    rr, cc = ar+r, ac+c
                    if 0 <= rr < h and 0 <= cc < w:
                        output[rr][cc] = color
    return output

def main():
    task_id = HERE.name
    root = find_root(__file__)
    module, source, digest = load_selected_generator(task_id, root=root)
    assert digest == EXPECTED[task_id], 'Audit must be rerun/reviewed for changed source bytes'
    if task_id == 'ebd08d719ed6':
        seed, total = 1, 7
        reference = module.rule_mirror
        def rival(grid):
            analysis = module._parse_grid(grid)
            eligible = [i for i, cells in enumerate(analysis['tiles'])
                        if any(grid[r][c] == 2 for r, c in cells)]
            target = max(eligible, key=lambda i: analysis['counts'][i])
            return module._recolor_tile(grid, analysis, target)
        rival_name = 'recolor_densest_color_2_tile'
    else:
        seed, total = 12, 4
        reference = lambda grid: stamp(grid, module, False)
        rival = lambda grid: stamp(grid, module, True)
        rival_name = 'stamp_union_of_all_gt1_cell_2_4_components'
    grids = [module.generate(seed, i) for i in range(total)]
    references = [reference(grid) for grid in grids]
    rivals = [rival(grid) for grid in grids]
    agree = [a == b for a, b in zip(references, rivals)]
    assert all(agree[:3]) and not all(agree[3:])
    assert not any(module.self_check(grid) for grid in grids)
    assert len({grid_sha(grid) for grid in grids}) == total
    canonical = canonical_pairs(task_id, root=root)
    canonical_agree = [reference(pair['input']) == pair['output'] for pair in canonical]
    assert all(canonical_agree), 'Independent Python label interpretation does not match canonical examples'
    row = None
    with canonical_path(root).open() as handle:
        for raw in handle:
            candidate = json.loads(raw)
            if candidate.get('task_id') == task_id:
                row = candidate
                break
    assert row is not None
    source_evidence = {}
    for relative in ('generator.py', 'notes.md', 'evidence/review_index.json', 'tests/test_generator.py'):
        p = source.parent / relative
        if p.is_file():
            source_evidence[str(p.relative_to(root))] = sha(p.read_bytes())
    report = {
        'schema': 'arcpuzzles-official-adversarial-audit-v1', 'task_id': task_id,
        'scope': 'Findings only; source unchanged. Reference execution not claimed until racket.json is compared.',
        'generator_source': str(source.relative_to(root)), 'generator_sha256': digest,
        'source_evidence_sha256': source_evidence,
        'canonical_rule_text_sha256': sha(row['program_solution'].encode()),
        'canonical_source': row['source'], 'canonical_pairs_checked': len(canonical),
        'python_reference_matches_canonical': canonical_agree,
        'rival_matches_canonical': [rival(pair['input']) == pair['output'] for pair in canonical],
        'rival': rival_name,
        'episode': {
            'seed': seed, 'sample_indices': list(range(total)), 'difficulty': None,
            'overrides': {}, 'demonstrations': 3, 'queries': total-3,
            'assembly': 'Explicit source calls at these indices; not a claim about default CLI assembly.',
            'self_check_errors': [module.self_check(grid) for grid in grids],
            'distinct_inputs': total, 'input_sha256': [grid_sha(grid) for grid in grids],
            'python_reference_sha256': [grid_sha(grid) for grid in references],
            'rival_sha256': [grid_sha(grid) for grid in rivals],
            'rival_equals_python_reference_by_source_index': agree,
            'all_demonstrations_fit_rival': all(agree[:3]),
            'query_source_indices_with_disagreement': [i for i in range(3, total) if not agree[i]],
        },
        'racket_verification': {'status': 'pending', 'expected_receipt': 'racket.json',
                                'expected_input_count': total},
        'limitations': ['One exact episode, not a prevalence estimate or universal ambiguity proof.',
                       'No production source or approval changed.',
                       'Python output checks need the separately retained supported Racket receipt.'],
    }
    if task_id == 'ebd08d719ed6':
        report['episode']['observed_profiles'] = [module.observe_overrides(grid) for grid in grids]
        report['episode']['existing_fixed_five_rival_matches_demos'] = [
            module.SEMANTIC_RIVALS['fixed_five'](grid) == output
            for grid, output in zip(grids[:3], references[:3])]
        report['finding'] = {
            'kind': 'teaching_ambiguity_for_additional_lawful_color_filter_rival',
            'cause': 'Palette reuse is scheduled, but the true winning tile color is not guaranteed to vary across demonstrations. The declared contract only checks fixed_five.',
            'current_vs_prior': 'Current source 115013... differs from old resolved audit source 7b2d9d99...; no prior defect is reported as current evidence.',
            'suggested_owner_fix': 'Add the color-2-only rival and require a distinguishing demonstration when any requested query needs color independence; preserve fixed-five witnesses and the canonical rule.',
        }
    else:
        report['episode']['template_component_sizes'] = [
            sorted([len(c) for c in module._components(grid, {2, 4}) if len(c)>1], reverse=True)
            for grid in grids]
        calls = []
        for label, overrides in [
            ('declared_min_height', {'grid_h':8}), ('declared_max_height', {'grid_h':18}),
            ('declared_min_width', {'grid_w':10}), ('declared_max_width', {'grid_w':20}),
            ('declared_max_template_size', {'tpl_size':8}), ('declared_max_anchors', {'n_anchors':4}),
            ('unknown_texture', {'texture':'typo'}), ('unknown_axis', {'made_up_axis':1})
        ]:
            call = {'case':label, 'seed':17, 'sample_index':0, 'difficulty':None, 'overrides':overrides}
            try:
                grid = module.generate(17, 0, **overrides)
                call.update({'accepted':True, 'input_sha256':grid_sha(grid),
                             'shape':[len(grid),len(grid[0])], 'self_check':module.self_check(grid)})
            except Exception as exc:
                call.update({'accepted':False, 'error_type':type(exc).__name__, 'error':str(exc)})
            calls.append(call)
        assert all(not call['accepted'] for call in calls[:6])
        assert all(call['accepted'] for call in calls[6:])
        report['override_probe'] = calls
        grid = module.generate(17, 0, texture='plain')
        mutated = [row[:] for row in grid]
        r, c = next((r,c) for r,row in enumerate(mutated) for c,value in enumerate(row) if value==2)
        mutated[r][c] = 2.0
        assert module.self_check(mutated) == []
        report['validator_probe'] = {
            'seed':17, 'sample_index':0, 'overrides':{'texture':'plain'},
            'mutation':{'row':r,'col':c,'from':2,'to':2.0,'to_type':'float'},
            'self_check_errors':module.self_check(mutated),
            'scope':'Validator accepts a non-integer pixel; not a claim that generate emitted it.'}
        dump('float_pixel_input.json', mutated)
        report['findings'] = [
            {'kind':'declared_override_domain_unavailable',
             'cause':'draw_int uses difficulty-specific sampling bounds as override validity bounds.',
             'suggested_owner_fix':'Honor documented exact values in all bands or explicitly narrow/decorrelate the declared contract; reject unknown texture/keys.'},
            {'kind':'lesson_ambiguity_for_declared_in_comments_union_rival',
             'cause':'A decoy may occur yet not produce a discriminating visible output under clipping/placement. Three demonstrations do not guarantee that largest-component selection is taught.',
             'suggested_owner_fix':'Use executable per-query rivals and ensure a demo whose output separates union from largest-component stamping.'},
            {'kind':'self_check_accepts_float_pixel',
             'cause':'Set membership equates 2.0 and 2; final self_check lacks exact integer cell validation.',
             'suggested_owner_fix':'Check exact integer ARC colors before component extraction.'},
        ]
    dump('inputs.json', {'inputs':grids})
    dump('python_reference_outputs.json', {'status':'Python only until Racket comparison', 'outputs':references})
    dump('rival_outputs.json', {'rival':rival_name,'outputs':rivals})
    dump('report.json', report)
    assert sha(source.read_bytes()) == digest
    print(json.dumps({'task_id':task_id,'seed':seed,'source_sha256':digest,
                      'queries_with_disagreement':report['episode']['query_source_indices_with_disagreement'],
                      'report':str(HERE/'report.json'),'inputs':str(HERE/'inputs.json')}))

if __name__ == '__main__':
    main()
