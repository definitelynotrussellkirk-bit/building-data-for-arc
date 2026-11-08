"""Focused finite review; no Racket execution or private runner functions.

python review_source.py --root /path/to/repo --out /path/to/output
Outputs reproduce source-bound singleton morphology and alternate-priority tests.
Generated labels are independent Python first-visible mirrors, not Racket receipts.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

TASK = 'ed860c0a9107'
BASELINE = 'e1094f19d9fdddc9c645c810cba5949a937c35f47c05df395b479b3a13dde462'


def boxes(grid):
    bg = grid[0][0]
    h, w = len(grid), len(grid[0])
    remaining = {(r,c) for r in range(h) for c in range(w) if grid[r][c] != bg}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo, cells = [start], [start]
        while todo:
            r,c = todo.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p = r+dr,c+dc
                    if p in remaining:
                        remaining.remove(p)
                        todo.append(p)
                        cells.append(p)
        result.append((min(r for r,c in cells),min(c for r,c in cells),
                       max(r for r,c in cells),max(c for r,c in cells)))
    return sorted(result)


def overlay(grid, mode='first_visible'):
    bg=grid[0][0]
    ordered=boxes(grid)
    if mode=='column_major_first':
        ordered.sort(key=lambda b:(b[1],b[0]))
    if mode=='numeric_box_color_order':
        ordered.sort(key=lambda b:next(grid[r][c] for r in range(b[0],b[2]+1)
                    for c in range(b[1],b[3]+1) if grid[r][c] not in (0,bg)))
    palette_order = {}
    for row in grid:
        for value in row:
            if value not in (0,bg):
                palette_order.setdefault(value,len(palette_order))
    top,left,bottom,right=ordered[0]
    out=[]
    for r in range(bottom-top+1):
        row=[]
        for c in range(right-left+1):
            values=[grid[t+r][l+c] for t,l,b,z in ordered if grid[t+r][l+c] not in (0,bg)]
            if mode=='first_box_only':
                value=grid[top+r][left+c]
            elif not values:
                value=0
            elif mode=='last_visible':
                value=values[-1]
            elif mode=='lowest_color':
                value=min(values)
            elif mode=='highest_color':
                value=max(values)
            elif mode=='palette_scan_priority':
                value=min(values,key=palette_order.get)
            else:
                value=values[0]
            row.append(value)
        out.append(row)
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--expect-sha',default=BASELINE)
    args=parser.parse_args()
    root=args.root.resolve()
    sys.path.insert(0,str(root/'shared/runtime'))
    from reviewer_support import load_selected_generator, canonical_pairs, canonical_path
    from review_diagnostics import structural_signature
    gen,source,digest=load_selected_generator(TASK,root=root)
    if args.expect_sha and digest != args.expect_sha:
        raise SystemExit(f'Source changed: expected {args.expect_sha}, got {digest}')
    cp=canonical_pairs(TASK,root=root,labeled_only=True)
    selected_rows=[json.loads(line) for line in canonical_path(root).read_text().splitlines()
                   if json.loads(line).get('task_id') == TASK]
    source_meta={'task_id':TASK,'generator_sha256':digest,'generator_version':gen.VERSION,
                 'generator_source':str(source),'rule_source_sha256':sorted({hashlib.sha256(p['program_solution'].encode()).hexdigest() for p in selected_rows}),
                 'generated_label_basis':'Independent Python first-visible mirror; no Racket execution in this script.'}
    structural={**source_meta,'canonical':[],'generated':[],
                'schedule':{'bands':['easy','medium','hard'],'seeds':list(range(1,21)),
                            'sample_index':'same integer as seed','overrides':{}},
                'detector':'review_diagnostics.structural_signature.marker_count = 4-connected same-color nonzero singleton components; not semantic container markers.'}
    for p in cp:
        assert overlay(p['input']) == p['output']
        structural['canonical'].append({k:p[k] for k in ['variant','split','pair_index']} |
                                      {'signature':structural_signature(p)})
    for band in ['easy','medium','hard']:
        for seed in range(1,21):
            grid=gen.generate(seed,seed,difficulty=band)
            out=overlay(grid)
            assert out == gen.rule_mirror(grid)
            structural['generated'].append({'seed':seed,'sample_index':seed,'difficulty':band,
                    'signature':structural_signature({'input':grid,'output':out})})
    structural['summary']={'canonical_pair_count':len(cp),'canonical_unique_pair_count':len({json.dumps({'input':p['input'],'output':p['output']},sort_keys=True) for p in cp}),
        'canonical_marker_counts':dict(Counter(x['signature']['marker_count'] for x in structural['canonical'])),
        'generated_pair_count':len(structural['generated']),
        'generated_marker_histograms':{b:dict(Counter(x['signature']['marker_count'] for x in structural['generated'] if x['difficulty']==b)) for b in ['easy','medium','hard']}}
    modes=['last_visible','column_major_first','lowest_color','highest_color','first_box_only','palette_scan_priority','numeric_box_color_order']
    rivals={**source_meta,'canonical_fit':{},'schedule':{'bands':['easy','medium','hard'],'seeds':list(range(20000,20100)),'sample_indexes':[0,1,2,3],'production_demo_indexes':[0,1,2],'production_query_index':3},'counts':{},'first_production_ambiguity':{},'first_rotation_ambiguity':{}}
    for m in modes:
        matches=[overlay(p['input'],m)==p['output'] for p in cp]
        rivals['canonical_fit'][m]={'match_count':sum(matches),'pair_count':len(cp),'mismatches':[{'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index']} for p,match in zip(cp,matches) if not match]}
        rivals['counts'][m]={'pair_matches':0,'pair_mismatches':0,'production':{'refuted':0,'support_equivalent':0,'ambiguous':0},'rotations':{'refuted':0,'support_equivalent':0,'ambiguous':0}}
    for band in ['easy','medium','hard']:
        for seed in range(20000,20100):
            grids=[gen.generate(seed,index,difficulty=band) for index in range(4)]
            expected=[overlay(grid) for grid in grids]
            assert all(out == gen.rule_mirror(grid) for out,grid in zip(expected,grids))
            for m in modes:
                predictions=[overlay(grid,m) for grid in grids]
                matches=[out==answer for out,answer in zip(predictions,expected)]
                counts=rivals['counts'][m]
                counts['pair_matches']+=sum(matches)
                counts['pair_mismatches']+=4-sum(matches)
                for q in range(4):
                    status='refuted' if not all(matches[i] for i in range(4) if i!=q) else ('support_equivalent' if matches[q] else 'ambiguous')
                    counts['rotations'][status]+=1
                    if q==3:counts['production'][status]+=1
                    if status=='ambiguous':
                        witness={'seed':seed,'difficulty':band,'sample_indexes':[0,1,2,3],'demo_indexes':[i for i in range(4) if i!=q],'query_index':q,
                                 'query':{'input':grids[q],'expected':expected[q],'rival':predictions[q]},
                                 'query_boxes':boxes(grids[q]),'demo_agreement':[matches[i] for i in range(4) if i!=q]}
                        rivals['first_rotation_ambiguity'].setdefault(m,witness)
                        if q==3:rivals['first_production_ambiguity'].setdefault(m,witness)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'structural-baseline.json').write_text(json.dumps(structural,indent=2)+'\n')
    (args.out/'rival-baseline.json').write_text(json.dumps(rivals,indent=2)+'\n')
    print(json.dumps({'source':source_meta,'structural':structural['summary'],'canonical_fit':rivals['canonical_fit'],'counts':rivals['counts'],
                     'first_production_ambiguities':{m:{k:v for k,v in w.items() if k not in ['query']} for m,w in rivals['first_production_ambiguity'].items()}},indent=2))

if __name__=='__main__':main()
