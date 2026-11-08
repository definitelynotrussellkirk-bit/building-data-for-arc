#!/usr/bin/env python3
"""Findings-only, bounded audit of vector support for 733d5c4a475a."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = '733d5c4a475a'
EXPECTED_SOURCE = 'e7799d8f26d57bd514a3c2869706a22d38e8aad63c4ee3d9f6a1192461c2aacb'
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def save(name, data):
    with (OUT/name).open('x', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2)
        handle.write('\n')


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()


def vector(grid):
    a,b = sorted((r,c) for r,row in enumerate(grid) for c,value in enumerate(row) if value==9)
    return b[0]-a[0],b[1]-a[1]


def base(grid):
    return [[0 if value==9 else value for value in row] for row in grid]


def translate(grid):
    result = base(grid)
    dr,dc = vector(grid)
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            if value not in (0,9) and 0<=r+dr<len(grid) and 0<=c+dc<len(row):
                result[r+dr][c+dc] = value
    return result


def diagonal_only(grid):
    dr,dc = vector(grid)
    return translate(grid) if dr and dc else base(grid)


def displacement_at_most_two(grid):
    return translate(grid) if abs(vector(grid)[1])<=2 else base(grid)


def shape_signature(grid):
    cells = [(r,c) for r,row in enumerate(grid) for c,value in enumerate(row) if value not in (0,9)]
    top,left = min(r for r,c in cells),min(c for r,c in cells)
    return tuple(sorted((r-top,c-left) for r,c in cells))


def main():
    module, source, source_sha = load_selected_generator(TASK,root=ROOT)
    if source_sha != EXPECTED_SOURCE:
        raise ValueError('Selected source differs from drawn audit assignment')
    shapes = {tuple(sorted(shape)) for shape in module._SHAPES}
    cases = []
    for pair in canonical_pairs(TASK,root=ROOT,labeled_only=True):
        cases.append({'kind':'canonical','variant':pair['variant'],'split':pair['split'],
                      'pair_index':pair['pair_index'],'input':pair['input'],
                      'canonical_output':pair['output']})
    for band in ('easy','medium','hard'):
        for seed in range(6):
            grid = module.generate(seed,0,difficulty=band)
            cases.append({'kind':'generated','seed':seed,'sample_index':0,
                          'difficulty':band,'input':grid})
    vertical = [[0]*6 for _ in range(6)]
    vertical[0][4] = vertical[3][4] = 9
    for r,c in ((1,1),(1,2),(2,1)):
        vertical[r][c] = 4
    horizontal = [[0]*7 for _ in range(6)]
    horizontal[0][0] = horizontal[0][3] = 9
    for r,c in ((2,1),(2,2),(3,1)):
        horizontal[r][c] = 4
    cases.extend([
        {'kind':'handmade','name':'vertical_vector','input':vertical},
        {'kind':'handmade','name':'horizontal_vector','input':horizontal},
    ])
    for index,case in enumerate(cases):
        grid = case['input']
        case.update(index=index,input_sha256=grid_sha(grid),vector=vector(grid),
                    self_check=module.self_check(copy.deepcopy(grid)),
                    normalized_shape_in_generator_bank=shape_signature(grid) in shapes)
    save('inputs.json',{'inputs':[case['input'] for case in cases]})
    apply_argv = [sys.executable,'-m','arcpuzzles','--library',str(ROOT),'apply',TASK,
                  '--input',str(OUT/'inputs.json'),'--check-generator-domain','--allow-unapproved',
                  '--timeout','120','--out',str(OUT/'racket.json')]
    run = subprocess.run(apply_argv,cwd=ROOT,text=True,capture_output=True,timeout=180,check=False)
    (OUT/'apply.stdout.log').write_text(run.stdout,encoding='utf-8')
    (OUT/'apply.stderr.log').write_text(run.stderr,encoding='utf-8')
    save('commands.json',[{'cwd':str(ROOT),'argv':apply_argv,'exit_code':run.returncode,
                           'evidence_paths':['inputs.json','racket.json','apply.stdout.log','apply.stderr.log']}])
    if run.returncode:
        raise RuntimeError(f'Public apply failed, exit {run.returncode}; see apply.stderr.log')
    receipt = json.loads((OUT/'racket.json').read_text())
    if receipt['generator_sha256'] != source_sha:
        raise ValueError('Authority source binding differs')
    if not receipt['rule_hash_matches_catalog']:
        raise ValueError('Authority rule hash mismatch')
    rivals = {'diagonal_only':diagonal_only,'horizontal_displacement_at_most_two':displacement_at_most_two}
    failures = []
    for case,result in zip(cases,receipt['results'],strict=True):
        if result['input']!=case['input'] or result['input_sha256']!=case['input_sha256']:
            raise ValueError('Authority input identity mismatch')
        if result['error'] or not result['valid_output']:
            raise ValueError('Authority evaluation failed')
        case['output'] = result['output']
        case['output_sha256'] = result['output_sha256']
        case['public_generator_domain'] = result['generator_domain']
        case['translation_mirror_matches_authority'] = translate(case['input'])==case['output']
        if not case['translation_mirror_matches_authority']:
            failures.append(f"Python mirror mismatch in case {case['index']}")
        if case['kind']=='canonical' and case['canonical_output']!=case['output']:
            failures.append(f"Canonical label mismatch in case {case['index']}")
        case['rivals'] = {}
        for name,solver in rivals.items():
            prediction = solver(case['input'])
            diff = [{'row':r,'col':c,'reference':value,'rival':prediction[r][c]}
                    for r,row in enumerate(case['output']) for c,value in enumerate(row)
                    if prediction[r][c]!=value]
            case['rivals'][name] = {'matches':not diff,'prediction':prediction,'differences':diff}
    save('cases.json',cases)
    stats = {}
    for kind in ('canonical','generated','handmade'):
        subset = [case for case in cases if case['kind']==kind]
        stats[kind] = {
            'count':len(subset),'all_self_check_valid':all(case['self_check']==[] for case in subset),
            'horizontal_vectors':sum(case['vector'][0]==0 for case in subset),
            'vertical_vectors':sum(case['vector'][1]==0 for case in subset),
            'diagonal_vectors':sum(all(case['vector']) for case in subset),
            'abs_horizontal_displacement_over_two':sum(abs(case['vector'][1])>2 for case in subset),
            'shape_outside_generator_bank':sum(not case['normalized_shape_in_generator_bank'] for case in subset),
            'rival_matches':{name:sum(case['rivals'][name]['matches'] for case in subset) for name in rivals},
        }
    after_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if after_sha!=source_sha:
        failures.append('Audit source changed during the probe')
    save('summary.json',{
        'schema':'arcpuzzles-focused-audit-v1','task_id':TASK,'phase':'audit',
        'generator_sha256':source_sha,'generator_sha256_after':after_sha,
        'executed_rule_hash':receipt['executed_rule_hash'],'rule_text_sha256':receipt['rule_text_sha256'],
        'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rule_hash_matches_catalog':receipt['rule_hash_matches_catalog'],
        'case_statistics':stats,'evaluation_failures':failures,
        'finding':'Reproduced existing axis-aligned-vector support gap; canonical test also lies beyond horizontal displacement and shape-bank support.',
        'scope':'All 3 usable canonical labels; seeds 0..5, sample index0, easy/medium/hard (18 default draws); 2 lawful handmade inputs. No source edits or broad battery.',
    })
    print(json.dumps({'evaluation_failures':failures,'case_statistics':stats,
                      'generator_sha256':source_sha,'rule_hash':receipt['executed_rule_hash']},indent=2))
    return bool(failures)


if __name__=='__main__':
    raise SystemExit(main())
