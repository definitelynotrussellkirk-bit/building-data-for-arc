"""Bounded adversarial checks against plausible feature and location shortcuts.

Run locally with `python .../adversarial_probe.py --out .../evidence/attacks.json`.
The JSON is private authoring evidence (contains exact labeled counterexamples).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import copy
from itertools import permutations
import prototype as p


def _ranked(grid, metric):
    recs = p._extract(grid)
    if metric == 'matched':
        ranked = recs
    elif metric == 'reversed':
        ranked = list(reversed(recs))
    elif metric.startswith('fixed:'):
        order = [int(x) for x in metric[6:]]
        if len(order) != len(recs):
            ranked = recs  # A fixed-length shortcut defaults to no reassignment.
        else:
            ranked = [recs[i] for i in order]
    else:
        def score(rec):
            if metric == 'height': return rec['height']
            if metric == 'width': return rec['width']
            if metric == 'bbox_area': return rec['bbox_area']
            if metric == 'color': return rec['color']
            if metric == 'negative_color': return -rec['color']
            if metric == 'source_col':
                return -min(c for r, row in enumerate(grid[1:], 1)
                            for c, v in enumerate(row) if v == rec['color'])
            if metric == 'horizontal':
                return sum(1 for row in rec['crop'] if rec['color'] in row)
            if metric == 'sparsity':
                return rec['bbox_area'] - rec['area']
            if metric == 'area_reversed': return -rec['area']
            raise ValueError(metric)
        ranked = sorted(recs, key=lambda r: (-score(r), r['marker']))
    slots = [rec['marker'] for rec in recs]
    h=max(x['height'] for x in recs); w=len(grid[0]); out=[[0]*w for _ in range(h)]
    for rec,anchor in zip(ranked, slots):
        top=h-rec['height']
        if anchor+rec['width']>w: return None
        for dy,row in enumerate(rec['crop']):
            for dx,v in enumerate(row):
                if v:
                    if out[top+dy][anchor+dx]: return None
                    out[top+dy][anchor+dx]=v
    return out


def rivals_for(grid):
    n=len(p._extract(grid))
    base=['matched','reversed','height','width','bbox_area','color',
          'negative_color','source_col','horizontal','sparsity','area_reversed']
    return base + ['fixed:'+''.join(map(str,order))
                   for order in permutations(range(n))]


def audit_seeds(seeds, *, demos=2):
    report={'schema':'c8ab-area-queue-adversarial-v1','seed_count':len(seeds),
            'minimum_demos':demos,'settings':{},'learnability_findings':[],
            'scores':{},'rival_bank': 'occupied area versus bbox, height, width, source position, marker color, fixed permutations; default matching'}
    for setting in p.MODES:
        setting_dict={'dock_mode':setting}
        bad=0; claims=0; query_scenes=0; disagreements={}
        for seed in seeds:
            episode=p.generate(seed,setting_dict,demos,4)
            pairs=episode['train']+episode['test']
            query_scenes+=4
            names=set(rivals_for(pairs[0]['input']))
            # Filter fixed-permutation rivals to the same marker count;
            # lessons need demonstrate general ranking for all counts.
            for name in sorted(names):
                predictions=[_ranked(row['input'],name) for row in pairs]
                fits=all(pred == row['output'] for pred,row in zip(predictions[:demos],pairs[:demos]))
                if not fits: continue
                if all(pred == row['output'] for pred,row in zip(predictions[demos:],pairs[demos:])):
                    continue
                key=f'{setting}:{name}'
                disagreements[key]=disagreements.get(key,0)+1
                if bad < 12:
                    report['learnability_findings'].append({
                        'setting':setting,'seed':seed,'rival':name,
                        'demo_count':demos,'first_query_disagreement':
                            next(i for i,(pred,row) in enumerate(zip(predictions[demos:],pairs[demos:]))
                                 if pred != row['output'])})
                bad += 1
            claims+=1
        report['settings'][setting]={'episodes':claims,'queries':query_scenes,
                                    'underidentified_rival_seed_pairs':bad,
                                    'rival_occurrences':disagreements}
    return report


def run(out):
    seeds=list(range(128))
    rep=audit_seeds(seeds)
    if out:
        path=Path(out)
        if path.exists(): raise FileExistsError(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'settings':rep['settings'],'findings':rep['learnability_findings'][:12]},indent=2))
    return 0 if not rep['learnability_findings'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out')
    args=parser.parse_args()
    raise SystemExit(run(args.out))
