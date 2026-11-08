"""Findings-only transpose-decoder audit; writes solely beside this file."""
from pathlib import Path
import hashlib,json,sys,types
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
scripts=types.ModuleType('scripts'); scripts.__path__=[str(ROOT/'shared/tools')]
sys.modules['scripts']=scripts
from reviewer_support import canonical_pairs,load_selected_generator
from puzzle_generators import runner
TASK='c5905adcd2cb'
gen,source,sha=load_selected_generator(TASK,root=ROOT)
assert sha=='5d9cebc09f84a2107cc85ebac93abcdad80804818eaec6f3f0a5c501c1b67cfa'
def rival(grid):
    mr,mc=next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==4)
    sr,sc=(mr//4)*4,(mc//4)*4
    dr,dc=(mc%4)*4,(mr%4)*4
    out=[[5 if v==5 else 0 for v in row] for row in grid]
    for r in range(3):
        for c in range(3):
            if grid[sr+r][sc+c] not in (0,5):out[dr+r][dc+c]=grid[sr+r][sc+c]
    return out
rows=[json.loads(s) for s in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(s).get('task_id')==TASK]
program=rows[0]['program_solution']
assert all(r['program_solution']==program for r in rows)
bundle=runner.GeneratorBundle(TASK,TASK,program,runner.wrap_rule(program),'shared/data/canonical/puzzles.jsonl',gen)
bridge,fn=runner._open_bridge_with_rule(bundle.rule_callable_text)
try:
    episode=runner.run_one(TASK,12,0,n_train=3,n_test=1,bundle=bundle,bridge=bridge,fn_name=fn,difficulty='easy')
    ps=episode['train']+episode['test']
    details=[{'index':i,'profile':gen.observe_overrides(p['input']),'source':gen._rule_facts(p['input'])['source_macro'],'destination':gen._rule_facts(p['input'])['destination_macro'],'self_check':gen.self_check(p['input']),'rival_matches_official':rival(p['input'])==p['output'],'mirror_matches_official':gen.rule_mirror(p['input'])==p['output']} for i,p in enumerate(ps)]
    assert [d['rival_matches_official'] for d in details]==[True,True,True,False]
    canonical=[]
    for p in canonical_pairs(TASK,root=ROOT):
        official=runner._apply_rule(bridge,fn,p['input'])
        canonical.append({**{k:v for k,v in p.items() if k not in ('input','output')},'racket_matches_label':official==p['output'],'rival_matches_label':rival(p['input'])==p['output']})
    census=[]
    for band in (None,'easy','medium','hard'):
        ambiguous=[]
        for seed in range(200):
            pairs=[]
            for i in range(4):
                x=gen.generate(seed,i,difficulty=band)
                pairs.append({'input':x,'output':gen.rule_mirror(x)})
            if all(rival(p['input'])==p['output'] for p in pairs[:3]) and rival(pairs[3]['input'])!=pairs[3]['output']:
                assert gen.lesson_identifiable(pairs[:3],pairs[3])==[]
                ambiguous.append(seed)
        census.append({'difficulty':band,'seed_range':[0,199],'ambiguous_seeds':ambiguous})
    out=rival(ps[3]['input'])
    result={'task_id':TASK,'source_path':str(source.relative_to(ROOT)),'generator_sha256':sha,'rule_hash':gen.RULE_HASH,'raw_program_sha256':hashlib.sha256(program.encode()).hexdigest(),'episode':episode,'pair_details':details,'query_rival_output':out,'query_differences':[[r,c,ps[3]['output'][r][c],out[r][c]] for r in range(11) for c in range(11) if ps[3]['output'][r][c]!=out[r][c]],'lesson_identifiable':gen.lesson_identifiable(ps[:3],ps[3]),'canonical':canonical,'census':census,'census_labels':'Python mirror; complete retained episode and canonical occurrences separately verified through Racket'}
    (HERE/'reproducer.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('episode','query_rival_output')},indent=2))
finally:bridge.shutdown()
