"""Demonstration-only finite rival checks for edge legends and hole selection."""
import argparse
import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_holes_audit_'+str(BASE).encode().hex(),BASE/'adapter.py')
a=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(a);m=a.model
RIVALS=('all','largest_per_color','smallest_per_color','largest_per_object','global_largest',
        'first_per_color','last_per_color','single_largest','unique_largest','bbox_area',
        'owner_size','reverse_legend','forward_legend','backward_legend','self_color',
        'transitive_map','bidirectional_map','eight_connected_background','rectangles_only',
        'paint_hole_boxes','unmapped_self','identity')


def predict(grid,name,setting):
    scope=setting['fill_scope']
    if name in ('all','largest_per_color','smallest_per_color','largest_per_object','global_largest',
                'first_per_color','last_per_color','single_largest','unique_largest'):
        return m.solve(grid,name)
    if name in ('bbox_area','owner_size'):return m.solve(grid,scope,size_measure=name)
    if name.endswith('_legend'):return m.solve(grid,scope,legend_direction=name.split('_')[0])
    if name=='self_color':return m.solve(grid,scope,mapping_mode='self')
    if name=='transitive_map':return m.solve(grid,scope,mapping_mode='transitive')
    if name=='bidirectional_map':return m.solve(grid,scope,mapping_mode='bidirectional')
    if name=='eight_connected_background':return m.solve(grid,scope,connectivity=8)
    if name=='identity':return [row[:] for row in grid]
    data=m.analyze(grid);out=m.solve(grid,scope);bg=data['background'];mapping=data['legend']['mapping']
    if name=='rectangles_only':
        for region in data['regions']:
            if region['area']!=region['bbox_area']:
                for r,c in region['cells']:out[r][c]=bg
        return out
    if name=='paint_hole_boxes':
        for region in data['regions']:
            if any(out[r][c]!=bg for r,c in region['cells']):
                r0,c0,r1,c1=region['bbox'];color=mapping[region['color']]
                for r in range(r0,r1+1):
                    for c in range(c0,c1+1):out[r][c]=color
        return out
    if name=='unmapped_self':
        for region in data['regions']:
            if region['color'] not in mapping:
                for r,c in region['cells']:out[r][c]=region['color']
        return out
    raise ValueError('unknown rival')


def audit(seeds,demo_counts):
    seeds=list(seeds);demo_counts=list(demo_counts)
    result={'schema':'inward-hole-finite-rival-audit-v1','seeds':seeds,'demo_counts':demo_counts,
            'rivals':list(RIVALS),'episodes':0,'pairs':0,'max_size_episodes':0,
            'harmful_survivors':0,'failures':[],'survivors':[],
            'limits':'Finite Python rivals only; Racket parity is retained independently. Equivalent behavior is not counted as ambiguity.'}
    for seed in seeds:
        cache={}
        def checked_prediction(grid,name,setting):
            key=(name,setting['fill_scope'],tuple(tuple(row) for row in grid))
            if key not in cache:cache[key]=predict(grid,name,setting)
            return cache[key]
        for demos in demo_counts:
            for setting in a.SETTINGS[:2]:
                episode=a.generate(seed,setting,demos,4);survivors=[]
                for name in RIVALS:
                    # All candidates must execute normally: errors cannot teach.
                    predictions=[checked_prediction(p['input'],name,setting) for p in episode['train']]
                    if predictions==[p['output'] for p in episode['train']]:
                        survivors.append(name)
                        for i,p in enumerate(episode['test']):
                            if checked_prediction(p['input'],name,setting)!=p['output']:
                                result['failures'].append({'seed':seed,'demos':demos,'settings':setting,'rival':name,'query':i})
                result['survivors'].append({'seed':seed,'demos':demos,'settings':setting,'rules':survivors})
                result['episodes']+=1;result['pairs']+=demos+4
                result['max_size_episodes']+=any(len(p['input'])==len(p['input'][0])==30 for p in episode['test'])
    result['harmful_survivors']=len(result['failures']);result['status']='failed' if result['failures'] else 'passed'
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();result=audit(range(args.seeds),(2,3,6));args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','episodes','pairs','harmful_survivors','failures')}))
    raise SystemExit(result['status']!='passed')
