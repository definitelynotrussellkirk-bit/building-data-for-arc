"""Findings-only transpose-decoder audit; writes solely beside this file."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'repo'
from reviewer_support import canonical_pairs,load_selected_generator
from arcpuzzles.catalog import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from puzzle_generators.runner import GeneratorBundle,run_one
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
rows=Catalog(ROOT).get(TASK)['variants']
program=rows[0]['program_solution']
assert all(r['program_solution']==program for r in rows)
# This canonical rule is a self-contained lambda: no source conversion is needed.
callable_text=strip_rule_wrapper(program)
assert callable_text.lstrip().startswith('(lambda (g)')
bundle=GeneratorBundle(TASK,TASK,program,callable_text,'shared/data/canonical/puzzles.jsonl',gen)
bridge=RacketBridge()
fn='audit_reference'
bridge.eval_text(f'(define {fn} {callable_text})')
def execute(grid):
    bridge.define_grid('audit_input',grid)
    return bridge.eval_text(f'({fn} audit_input)')
def marker_geometry(grid):
    r,c=next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==4)
    return {'source_macro':(r//4,c//4),'destination_macro':(r%4,c%4)}
try:
    episode=run_one(TASK,12,0,n_train=3,n_test=1,bundle=bundle,bridge=bridge,fn_name=fn,difficulty='easy')
    ps=episode['train']+episode['test']
    details=[{'index':i,'profile':gen.observe_overrides(p['input']),'source':marker_geometry(p['input'])['source_macro'],'destination':marker_geometry(p['input'])['destination_macro'],'self_check':gen.self_check(p['input']),'rival_matches_official':rival(p['input'])==p['output'],'mirror_matches_official':gen.rule_mirror(p['input'])==p['output']} for i,p in enumerate(ps)]
    assert [d['rival_matches_official'] for d in details]==[True,True,True,False]
    canonical=[]
    for p in canonical_pairs(TASK,root=ROOT):
        official=execute(p['input'])
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
    previous=json.loads((HERE/'history/superseded-private-runner/reproducer.json').read_text())
    comparison={key:json.loads(json.dumps(result[key]))==previous[key] for key in ('episode','pair_details','query_rival_output','query_differences','lesson_identifiable','canonical','census')}
    assert all(comparison.values()),comparison
    assert len(canonical)==10 and all(c['racket_matches_label'] for c in canonical)
    assert len(result['query_differences'])==8
    assert sum(len(c['ambiguous_seeds']) for c in census)==17
    result['public_api_portability']={'status':'current','old_evidence_status':'superseded-private-runner','unchanged_evidence_comparison':comparison,'execution_api':'RacketBridge + strip_rule_wrapper; public GeneratorBundle/run_one accepted episode; public Catalog.get authority'}
    (HERE/'reproducer.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('episode','query_rival_output')},indent=2))
finally:bridge.shutdown()
