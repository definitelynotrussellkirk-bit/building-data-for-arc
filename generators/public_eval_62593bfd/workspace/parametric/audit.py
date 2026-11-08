"""Finite, demonstration-only rival audit, not universal rule identification.

The expected labels come from the episode's Python mirror. Racket parity is
independently retained in preflight, boundary and protected-rival evidence.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_audit_size_'+str(BASE).encode().hex(),BASE/'adapter.py')
a=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(a)
m=a.model
RIVALS=('occupied_area','bbox_area','width','height','bbox_perimeter','color','shape',
        'four_connected','exact_pairs','reverse','all_top','all_bottom','largest',
        'smallest','fixed_3_4','fixed_3_7_9','identity')


def predict(grid,name,setting):
    choice=setting['match_by']
    if name in ('occupied_area','bbox_area','width','height','bbox_perimeter','color','shape'):
        return m.solve(grid,name)
    if name=='four_connected':return m.solve(grid,choice,connectivity=4)
    if name=='exact_pairs':return m.solve(grid,choice,exact_pairs=True)
    if name=='identity':return [row[:] for row in grid]
    if name=='fixed_3_7_9':
        data=m.analyze(grid);out=[[data['background']]*data['width'] for _ in range(data['height'])]
        for obj in data['objects']:
            dr=-obj['bbox'][0] if obj['area'] in (3,7,9) else data['height']-1-obj['bbox'][2]
            for r,c in obj['cells']:out[r+dr][c]=obj['color']
        return out
    return m.solve(grid,choice,direction=name)


def audit(seeds, demo_counts):
    seeds=list(seeds);demo_counts=list(demo_counts)
    result={'schema':'size-frequency-finite-rival-audit-v1','seeds':seeds,'demo_counts':demo_counts,
            'rivals':list(RIVALS),'episodes':0,'pairs':0,'max_size_episodes':0,
            'harmful_survivors':0,'failures':[],'survivors':[],
            'limits':'Python finite rivals; independently Racket-checked labels elsewhere. No universal uniqueness claim.'}
    for seed in seeds:
        for demos in demo_counts:
            for setting in a.SETTINGS:
                episode=a.generate(seed,setting,demos,4)
                survivors=[]
                for name in RIVALS:
                    # Evaluate every demo. A failed rival is an audit error, never
                    # a convenient way to distinguish that candidate.
                    predictions=[predict(p['input'],name,setting) for p in episode['train']]
                    if predictions==[p['output'] for p in episode['train']]:
                        survivors.append(name)
                        for i,p in enumerate(episode['test']):
                            if predict(p['input'],name,setting)!=p['output']:
                                result['failures'].append({'seed':seed,'demos':demos,'settings':setting,
                                                          'rival':name,'query':i})
                result['survivors'].append({'seed':seed,'demos':demos,'settings':setting,'rules':survivors})
                result['episodes']+=1;result['pairs']+=demos+4
                result['max_size_episodes']+=any(len(p['input'])==len(p['input'][0])==30 for p in episode['test'])
    result['harmful_survivors']=len(result['failures'])
    result['status']='passed' if not result['failures'] else 'failed'
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();report=audit(range(args.seeds),(2,3,6));args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','pairs','harmful_survivors')}))
    raise SystemExit(report['status']!='passed')
