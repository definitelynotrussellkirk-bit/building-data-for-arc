"""Independent bounded Python-only sampler/claim check; no Racket claims."""
from collections import Counter
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time

ROOT=Path.cwd()
HOME=ROOT/'generators/323fded12174'
path=HOME/'workspace/parametric/prototype.py'
spec=importlib.util.spec_from_file_location('bounded_row_family',path)
f=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=f
spec.loader.exec_module(f)


def inspect(g):
    assert type(g) is list and 3<=len(g)<=30
    w=len(g[0]); assert 5<=w<=30
    assert all(type(row) is list and len(row)==w for row in g)
    assert all(type(v) is int and 0<=v<=9 for row in g for v in row)
    assert len({v for row in g for v in row if v})>=3
    occ=[sum(v!=0 for v in row) for row in g]
    assert all(0<n<w for n in occ)
    assert occ.count(max(occ))==1
    a=occ.index(max(occ)); counts=Counter(v for v in g[a] if v)
    assert len(counts)>=2
    assert list(counts.values()).count(max(counts.values()))==1
    target=max(counts,key=counts.get)
    ts=[sum(v==target for v in row) for row in g]
    return occ,a,target,ts


def label(g,mode):
    occ,a,target,ts=inspect(g)
    scores=occ if mode=='occupancy' else ts
    order=sorted(range(len(g)),key=lambda i:(-scores[i],i))
    return [g[i][:] for i in order]


def fingerprint(g):
    return json.dumps(g,separators=(',',':'))


def run():
    start=time.monotonic()
    requests=[]; failures=[]; unique_inputs=set(); unique_labeled=set(); query_inputs=set()
    shapes=set(); first_shapes=set(); first_inputs=set(); anchor_colors=set(); anchor_locations=set()
    core_count_profiles=set(); dense_occupancies=[]; first_identity=Counter(); source_counts=Counter()
    teaching=[]; novelty=[]
    for seed in range(24):
        base={}
        for mode in ('occupancy','anchor_color'):
            for demos,queries in ((6,4),(3,1),(3,4)):
                request={'seed':seed,'rank_by':mode,'demos':demos,'queries':queries}
                try:
                    e=f.generate(seed,{'rank_by':mode},demos=demos,queries=queries)
                    assert len(e['train'])==demos and len(e['test'])==queries
                    assert e['program_solution']==f.program({'rank_by':mode})
                    ids=[]
                    for part in ('train','test'):
                        for p in e[part]:
                            g=p['input']; out=p['output']; occ,a,target,ts=inspect(g)
                            assert out==label(g,mode)
                            key=fingerprint(g); ids.append(key); unique_inputs.add(key)
                            unique_labeled.add((mode,key,fingerprint(out)))
                            shapes.add((len(g),len(g[0])))
                            if part=='test':query_inputs.add(key)
                    assert len(set(ids))==len(ids)
                    if (demos,queries)==(6,4):
                        base[mode]=e
                    else:
                        assert e['train']==base[mode]['train'][:demos]
                        assert e['test']==base[mode]['test'][:queries]
                    request.update(status='passed',sampling=e['sampling'])
                    teaching.append(e['sampling']['teaching_attempts']);novelty.extend(e['sampling']['novelty_attempts'])
                    if mode=='occupancy' and demos==6:
                        for p in e['train'][:3]:
                            g=p['input'];occ,a,target,ts=inspect(g)
                            anchor_colors.add(target);anchor_locations.add((a,len(g)))
                            core_count_profiles.add(tuple(sorted(zip(occ,ts))))
                        first=e['test'][0]['input'];first_inputs.add(fingerprint(first));first_shapes.add((len(first),len(first[0])))
                        large=e['test'][3]['input']
                        assert (len(large),len(large[0]))==(30,30)
                        assert len(set(map(tuple,large)))==30
                        assert sum(v!=0 for row in large for v in row)>=300
                        dense_occupancies.append(sum(v!=0 for row in large for v in row))
                    if demos==6:
                        first_identity[mode]+=e['test'][0]['input']==e['test'][0]['output']
                except Exception as error:
                    request.update(status='failed',error=f'{type(error).__name__}: {error}')
                    failures.append(request.copy())
                requests.append(request)
        if len(base)==2:
            assert [p['input'] for p in base['occupancy']['train']+base['occupancy']['test']]==[p['input'] for p in base['anchor_color']['train']+base['anchor_color']['test']]
    files=[HOME/'workspace/parametric'/name for name in ('prototype.py','adapter.py','promotion.json','canonical.rkt')]+[HOME/'tests/test_parametric_323fded12174.py']
    report={'schema':'arc-family-bounded-sampler-v1','task_id':'323fded12174','scope':'Python-only, independent grammar and label checks; no protected-runtime execution claimed.',
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'seeds':list(range(24)),'request_count':len(requests),'passed':sum(x['status']=='passed' for x in requests),'failures':failures,
            'unique_inputs':len(unique_inputs),'unique_claim_labeled_pairs':len(unique_labeled),'unique_query_inputs':len(query_inputs),
            'unique_first_query_inputs':len(first_inputs),'first_query_shapes':sorted(first_shapes),'all_input_shapes':sorted(shapes),
            'core_anchor_colors':sorted(anchor_colors),'core_anchor_locations':sorted(anchor_locations),
            'core_occupancy_target_profiles':len(core_count_profiles),'dense_foreground_cells_range':[min(dense_occupancies),max(dense_occupancies)],
            'first_query_identity_count_by_setting':dict(first_identity),'maximum_teaching_attempts':max(teaching),'maximum_novelty_attempts':max(novelty),
            'elapsed_seconds':time.monotonic()-start,'requests':requests}
    out=ROOT.parent/'checks/323fded12174/family-sampler-final.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('request_count','passed','unique_inputs','unique_claim_labeled_pairs','unique_query_inputs','core_occupancy_target_profiles','maximum_teaching_attempts','maximum_novelty_attempts','elapsed_seconds','failures')}))
    if failures:raise SystemExit(1)

if __name__=='__main__':run()
