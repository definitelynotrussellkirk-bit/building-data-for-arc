"""Focused source-bound color-segmentation teaching audit; no shared edits."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / 'repo'
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = 'b1118feaedd5'
SOURCE = ROOT / f'generators/{TASK}/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def predict(grid, same_color=True):
    """Threshold-3 rule; rival ignores color while finding components."""
    h, w = len(grid), len(grid[0])
    output = [r[:] for r in grid]
    seen = set()
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r,c) in seen:
                continue
            todo, obj = [(r,c)], []
            seen.add((r,c))
            color = grid[r][c]
            while todo:
                rr, cc = todo.pop()
                obj.append((rr,cc))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc = rr+dr,cc+dc
                    if (0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen
                        and grid[nr][nc] and (not same_color or grid[nr][nc] == color)):
                        seen.add((nr,nc))
                        todo.append((nr,nc))
            if len(obj) < 3:
                for rr,cc in obj:
                    output[rr][cc] = 3
    return output

def diffs(a,b):
    return [{'row':r,'col':c,'expected':a[r][c],'rival':b[r][c]}
            for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]

if len(sys.argv) == 1 or sys.argv[1] == 'prepare':
    row = Catalog(ROOT).get(TASK)
    identity = {k:row[k] for k in ('generator_sha256','rule_hash','approved','train_safety','audit_unresolved')}
    identity['version'] = gen.VERSION
    identity['program_solution'] = row['variants'][0]['program_solution']
    identity['generator_sha256_actual'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    (HERE/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    probes = []
    for index in range(8):
        grid = gen.generate(17,index,difficulty='medium')
        probes.append({'kind':'generated','seed':17,'sample_index':index,'difficulty':'medium',
                       'overrides':{},'documented_domain':True,'input':grid,
                       'self_check':gen.self_check(grid,difficulty='medium')})
    for pair in canonical_pairs(TASK,root=ROOT):
        probes.append({'kind':'canonical','variant':pair['variant'],'split':pair['split'],
                       'pair_index':pair['pair_index'],'seed':None,'sample_index':None,
                       'overrides':None,'documented_domain':False,
                       'domain_note':'Canonical task domain; multicolor inputs are absent from declared one-fg-color generator domain.',
                       'input':pair['input'],'canonical_output':pair['output'],
                       'self_check':gen.self_check(pair['input'])})
    (HERE/'probes.json').write_text(json.dumps(probes,indent=2)+'\n')
    (HERE/'input.json').write_text(json.dumps({'inputs':[p['input'] for p in probes]})+'\n')
    print(json.dumps({'identity':identity,'probe_count':len(probes),'all_self_check_accepted':all(not p['self_check'] for p in probes)},indent=2))
elif sys.argv[1] == 'compare':
    probes = json.loads((HERE/'probes.json').read_text())
    reference = json.loads((HERE/'racket.json').read_text())
    results = reference['results']
    comparisons = []
    for i,(probe,result) in enumerate(zip(probes,results,strict=True)):
        expected = result['output']
        aware = predict(probe['input'],True)
        rival = predict(probe['input'],False)
        comparisons.append({'input_index':i,**{k:v for k,v in probe.items() if k not in ('input','canonical_output')},
                            'reference_matches_color_aware':expected==aware,
                            'reference_matches_canonical':None if 'canonical_output' not in probe else expected==probe['canonical_output'],
                            'rival_matches_reference':expected==rival,
                            'rival_prediction':rival,'differences':diffs(expected,rival),
                            'nonzero_colors':sorted({c for r in probe['input'] for c in r if c})})
    summary = {'reference_rule_hash':reference['executed_rule_hash'],
               'generated_rival_matches':sum(p['kind']=='generated' and p['rival_matches_reference'] for p in comparisons),
               'generated_count':sum(p['kind']=='generated' for p in comparisons),
               'canonical_rival_mismatches':sum(p['kind']=='canonical' and not p['rival_matches_reference'] for p in comparisons),
               'canonical_count':sum(p['kind']=='canonical' for p in comparisons),
               'all_reference_matches_color_aware':all(p['reference_matches_color_aware'] for p in comparisons),
               'comparisons':comparisons}
    (HERE/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='comparisons'},indent=2))
