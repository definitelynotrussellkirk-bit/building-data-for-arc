"""Join supported Racket receipts with task-local, explicitly named rivals."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'probe.json').read_text())
r=json.loads((HERE/'racket.json').read_text())
l=json.loads((HERE/'lesson.jsonl').read_text())
lr=json.loads((HERE/'lesson-racket.json').read_text())

def components(g):
    seen=set(); out=[]
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if not color or (r,c) in seen: continue
            todo=[(r,c)]; seen.add((r,c)); pts=[]
            while todo:
                rr,cc=todo.pop(); pts.append((rr,cc))
                for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<len(g) and 0<=nc<len(row) and (nr,nc) not in seen and g[nr][nc]==color:
                        seen.add((nr,nc));todo.append((nr,nc))
            out.append((color,pts))
    return out

def draw_bbox(g,*,solid=False,per_color=False):
    objs=components(g)
    if per_color:
        colors={}
        for color,pts in objs: colors.setdefault(color,[]).extend(pts)
        objs=list(colors.items())
    out=[[0]*len(g[0]) for _ in g]
    for color,pts in objs:
        r1=min(r for r,c in pts);r2=max(r for r,c in pts)
        c1=min(c for r,c in pts);c2=max(c for r,c in pts)
        for rr in range(r1,r2+1):
            for cc in range(c1,c2+1):
                if solid or rr in [r1,r2] or cc in [c1,c2]:out[rr][cc]=color
    return out

def differences(a,b):
    return [{'row':rr,'col':cc,'actual_racket':x,'rival':y} for rr,(row1,row2) in enumerate(zip(a,b)) for cc,(x,y) in enumerate(zip(row1,row2)) if x!=y]

commands=[
 {'cwd':'packet_root','argv':['python3','checks/audit/6347dcb736b5/probe.py'],'exit_code':0,'evidence_paths':['checks/audit/6347dcb736b5/probe.json','checks/audit/6347dcb736b5/input.json']},
 {'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','6347dcb736b5','--input','../checks/audit/6347dcb736b5/input.json','--out','../checks/audit/6347dcb736b5/racket.json'],'exit_code':0,'effective_cwd':'repo','evidence_paths':['checks/audit/6347dcb736b5/racket.json']},
 {'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','generate','6347dcb736b5','--count','1','--seed','6347','--sample-index','5','--difficulty','easy','--train','3','--test','1','--allow-unapproved','--out','../checks/audit/6347dcb736b5/lesson.jsonl'],'exit_code':0,'effective_cwd':'repo','evidence_paths':['checks/audit/6347dcb736b5/lesson.jsonl']},
 {'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','6347dcb736b5','--input','../checks/audit/6347dcb736b5/lesson-input.json','--out','../checks/audit/6347dcb736b5/lesson-racket.json'],'exit_code':0,'effective_cwd':'repo','evidence_paths':['checks/audit/6347dcb736b5/lesson-input.json','checks/audit/6347dcb736b5/lesson-racket.json']},
 {'cwd':'packet_root','argv':['python3','checks/audit/6347dcb736b5/summarize.py'],'exit_code':0,'evidence_paths':['checks/audit/6347dcb736b5/counterexample.json','checks/audit/6347dcb736b5/commands.json']}
]
identity={'task_id':'6347dcb736b5','generator_version':p['identity']['generator_version'],'generator_sha256':r['generator_sha256'],'selected_rule_source_sha256':p['identity']['rule_text_sha256'],'normalized_rule_hash':r['executed_rule_hash'],'wrapped_executed_rule_sha256':r['rule_text_sha256'],'catalog_rule_hash':r['catalog_rule_hash'],'rule_hash_matches_catalog':r['rule_hash_matches_catalog'],'canonical_record_sha256':p['identity']['canonical_record_sha256']}
assert identity['generator_sha256']==p['identity']['generator_sha256']==lr['generator_sha256']==l['provenance']['generator_sha256']
assert r['executed_rule_hash']==lr['executed_rule_hash']==l['executed_rule_hash']
assert all(x['valid_output'] and x['error'] is None for x in r['results']+lr['results'])
canonical=[]
for saved,actual in zip(p['canonical'],r['results'][:3],strict=True):
    fill=draw_bbox(actual['input'],solid=True); global_box=draw_bbox(actual['input'],per_color=True)
    canonical.append({'split':saved['split'],'pair_index':saved['pair_index'],'input':actual['input'],'actual_racket_output':actual['output'],'stored_canonical_output':saved['stored_canonical_output'],'stored_output_matches_actual_racket':saved['stored_canonical_output']==actual['output'],'solid_fill_rival_output':fill,'solid_fill_rival_matches':fill==actual['output'],'per_color_bbox_rival_output':global_box,'per_color_bbox_rival_matches':global_box==actual['output'],'validator_errors':saved['validator_errors']})
lesson=[]
for accepted,actual,pair in zip(l['sampling']['accepted_pairs'],lr['results'],l['train']+l['test'],strict=True):
    rival=draw_bbox(actual['input'],solid=True)
    assert pair['input']==actual['input'] and pair['output']==actual['output']
    lesson.append({'split':accepted['split'],'pair_index':accepted['pair_index'],'seed':6347,'sample_index':accepted['sample_index'],'difficulty':'easy','overrides':{},'input':actual['input'],'input_sha256':actual['input_sha256'],'actual_racket_output':actual['output'],'rival_output':rival,'rival_matches':rival==actual['output'],'differences':differences(actual['output'],rival),'validator_errors':next(x['validator_errors'] for x in p['draws'] if x['difficulty']=='easy' and x['sample_index']==accepted['sample_index']),'documented_domain':'Helpful default generate domain: multiple separate, distinct-color blobs; raw draw accepted by actual production sampler.'})
assert [x['rival_matches'] for x in lesson]==[True,True,True,False]
single=p['controls'][7]
assert single['overrides']=={'texture':'single_blob'}
single_actual=r['results'][10]
global_out=draw_bbox(single['input'],per_color=True)
control_cases=[]
for src,actual in zip(p['input_index_map'],r['results'],strict=True):
    if src['kind']!='generated_control':continue
    control=p['controls'][src['control_index']]
    control_cases.append({**control,'actual_racket_output':actual['output'],'actual_racket_output_sha256':actual['output_sha256'],'documented_domain':'Explicit declared texture control' if control['overrides'].get('texture') in ['single_blob','all_rectangular','no_blobs'] else 'Helpful layout; exact requested control may be unsatisfied'})
result={'identity':identity,'primary_finding':{'id':'A6347-L1','classification':'Reproduced teaching defect','rival':'Fill the bounding box of each four-connected nonzero component solid in its original color','assembly':'Public production generate, 3 train then 1 test, easy, seed 6347, start 5, accepted indices [5,6,7,8], no rejections; fixed query, no rotation','demonstration_fit':'3/3','query_differences':lesson[-1]['differences'],'canonical_fit':'2/3; not claimed as a canonical-fitting shortcut; fails canonical train[1]','lesson':lesson},'independent_control_findings':{'id':'A6347-C1','classification':'Reproduced generator control defects','description':'n_distinct_colors=5 and palette_size=5 are silently ignored, each yielding baseline 2 colors (3 including background); warm/cool palette and helpful-texture requests also leave exact grid unchanged. Declared single_blob gives two four-connected same-color components. 6x6 is advertised but rejected under easy; this may require documenting band compatibility.','controls':control_cases,'rejected_control':p['controls'][10]},'additional_rival':{'id':'A6347-D1','classification':'Domain question / possible shortcut; not a demonstrated ordinary production lesson defect','name':'Outline one global bbox per nonzero color, ignoring component identity','canonical_fit':'3/3 newly compared to supported Racket outputs','generated_witness':{**single,'actual_racket_output':single_actual['output'],'rival_output':global_out,'differences':differences(single_actual['output'],global_out),'documented_domain':'Generated by an explicitly declared degenerate texture; violates that control single_blob name by having two 4-connected components. Default helpful generator requires distinct blob colors, so rival is extensionally equivalent there.'}},'canonical_checks':canonical,'bounded_census':{'sample_set':'seed 6347, sample indices 0..63 independently per easy, medium, hard; 192 unique raw helpful inputs. Deterministic probe reruns are not additional population members.','summary':p['summary'],'targeted_control_attempts':11,'targeted_control_grids':10,'targeted_control_exceptions':1,'production_episodes':1,'production_pairs':4,'production_pair_inputs_overlap_raw_census':True,'racket_apply_inputs':17,'racket_apply_note':'3 canonical + 10 control inputs in first call; 4 production lesson inputs in second. Outputs for the other raw draws were not executed.','not_run':'No full battery or 100-lessons-per-band census; no rotated queries or exhaustive assembly checks. No universal identifiability or arbitrary-rival claim.'},'declarations':{'CANONICAL_SHORTCUTS':p['identity']['declared_canonical_shortcuts'],'LESSON_COMPETITORS':p['identity']['declared_lesson_competitors'],'note':'Neither executable declaration exists; additional task-local rivals above are explicit probes, not a copied declaration list.'},'commands':commands,'prior_failed_probe':'probe-first-failure.json retains initial exception and original script bytes; final probe catches and records it.','source_edits':'None. Generator, canonical rule, and solve files left unchanged.'}
(HERE/'counterexample.json').write_text(json.dumps(result,indent=2)+'\n')
(HERE/'commands.json').write_text(json.dumps({'verification_commands':commands,'earlier_failure':json.loads((HERE/'probe-first-failure.json').read_text())},indent=2)+'\n')
print(json.dumps({'identity':identity,'primary':{k:v for k,v in result['primary_finding'].items() if k!='lesson'},'single_blob_differences':result['additional_rival']['generated_witness']['differences'],'canonical_fits':{'solid':sum(x['solid_fill_rival_matches'] for x in canonical),'per_color':sum(x['per_color_bbox_rival_matches'] for x in canonical)},'output_files':['counterexample.json','commands.json']},indent=2))
