from pathlib import Path
import sys, json, importlib.util, hashlib
BASE=Path(__file__).resolve().parent
REPO=BASE.parents[2]/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
spec=importlib.util.spec_from_file_location('audit_generator',REPO/'generators/3a3258548fa3/generator.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def bbox(g):
    out=[r[:] for r in g]; seen=set(); h=len(g); w=len(g[0])
    for r in range(h):
        for c in range(w):
            color=g[r][c]
            if not color or (r,c) in seen: continue
            cells=[]; todo=[(r,c)]; seen.add((r,c))
            while todo:
                rr,cc=todo.pop(); cells.append((rr,cc))
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    p=(rr+dr,cc+dc)
                    if 0<=p[0]<h and 0<=p[1]<w and p not in seen and g[p[0]][p[1]]==color:
                        seen.add(p); todo.append(p)
            for rr in range(min(x[0] for x in cells),max(x[0] for x in cells)+1):
                for cc in range(min(x[1] for x in cells),max(x[1] for x in cells)+1): out[rr][cc]=color
    return out

def prepare():
    row=next(json.loads(x) for x in (REPO/'shared/data/canonical/puzzles.jsonl').open() if json.loads(x)['task_id']=='3a3258548fa3')
    witness=[[0]*6 for _ in range(5)]
    for r,c in ((1,1),(1,2),(1,3),(2,1)): witness[r][c]=4
    cases=[dict(kind='accepted_domain_counterexample',seed=None,sample_index=None,difficulty=None,overrides={},input=witness)]
    for band in ('easy','medium','hard'):
        for seed in range(20):
            cases.append(dict(kind='generated',seed=seed,sample_index=seed,difficulty=band,overrides={},input=mod.generate(seed,seed,difficulty=band)))
    for i,p in enumerate(row['train']+[row['test']]): cases.append(dict(kind='canonical',canonical_pair=i,input=p['input'],stored_output=p['output']))
    axes={}
    for key,lo,hi in [('n_blocks',1,9),('palette_size',1,9),('n_distinct_colors',1,9),('palette_kind','warm','cool'),('texture','warm','cool')]:
        same=0; mismatches=[]
        for seed in range(30):
            low=mod.generate(seed,seed,difficulty='medium',**{key:lo}); high=mod.generate(seed,seed,difficulty='medium',**{key:hi})
            same+=low==high
            if key=='n_distinct_colors' and len({v for r in low for v in r if v} ) != lo:
                mismatches.append(dict(seed=seed,sample_index=seed,difficulty='medium',overrides={key:lo},observed_nonzero_colors=sorted({v for r in low for v in r if v}),input=low,self_check=mod.self_check(low)))
        axes[key]=dict(low=lo,high=hi,trials=30,identical_grids=same,low_override_mismatch_count=len(mismatches),first_low_override_mismatch=mismatches[0] if mismatches else None)
    (BASE/'input.json').write_text(json.dumps({'inputs':[x['input'] for x in cases]},separators=(',',':'))+'\n')
    (BASE/'cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    (BASE/'overrides.json').write_text(json.dumps(axes,indent=2)+'\n')
    (BASE/'source_binding.json').write_text(json.dumps(dict(task_id='3a3258548fa3',generator_sha256=hashlib.sha256((REPO/'generators/3a3258548fa3/generator.py').read_bytes()).hexdigest(),rule_text_sha256=hashlib.sha256(row['program_solution'].encode()).hexdigest(),prior_lead='review-c4014dc571c9792f:v0001',domain_note='self_check acceptance is broader than documented isolated-L generator invariants; counterexample is not claimed to be in default generation support.'),indent=2)+'\n')
    print('prepared',len(cases),'public apply inputs and 5 x 30 paired override probes')

def analyze():
    applied=json.loads((BASE/'racket.json').read_text()); cases=json.loads((BASE/'cases.json').read_text()); records=[]
    for case,result in zip(cases,applied['results'],strict=True):
        rival=bbox(case['input'])
        records.append(dict(kind=case['kind'],seed=case.get('seed'),sample_index=case.get('sample_index'),difficulty=case.get('difficulty'),rival_matches_racket=(rival==result['output']),rival_output=rival,reference_output=result['output'],self_check=mod.self_check(case['input']),canonical_matches_stored=(result['output']==case.get('stored_output')) if case['kind']=='canonical' else None))
    generated=[x for x in records if x['kind']=='generated']; canonical=[x for x in records if x['kind']=='canonical']
    summary=dict(generator_sha256=applied['generator_sha256'],executed_rule_hash=applied['executed_rule_hash'],catalog_rule_hash=applied['catalog_rule_hash'],rule_text_sha256=applied['rule_text_sha256'],rule_hash_matches_catalog=applied['rule_hash_matches_catalog'],generated_total=len(generated),generated_bbox_matches=sum(x['rival_matches_racket'] for x in generated),canonical_total=len(canonical),canonical_bbox_matches=sum(x['rival_matches_racket'] for x in canonical),canonical_racket_matches_stored=sum(x['canonical_matches_stored'] for x in canonical),witness=records[0],generated_selfcheck_errors=sum(bool(x['self_check']) for x in generated),by_band={b:sum(x['rival_matches_racket'] for x in generated if x['difficulty']==b) for b in ('easy','medium','hard')})
    (BASE/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':
    {'prepare':prepare,'analyze':analyze}[sys.argv[1]]()
