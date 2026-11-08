"""One source-bound replay of the retained decoy override witness.
Run from WORK: python checks/tickets/ticket-e04792135edeb06b/probe.py
Requires this packet's Python helpers and its configured Racket runtime.
"""
from pathlib import Path
import hashlib,json,os,sys,time,traceback
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
REPO=WORK/'repo'
TASK='04e2ffe8dc8e'
TICKET='ticket-e04792135edeb06b'
SOURCE='21425260e0af633b53e19f217a8e6ba3f5959fa48b77b62a1356156ad465a165'
ASSETS='26a9cbdf55a3881b77dc1fa9af7f35c339288d604f32e8d5fc97f31e0159f440'
INDEX='e0974c598d0fe8365b6223179543ff87c3f5a1e123a97102402e803373925139'
RECORD='5a6bbf0ec474f6b114650e750fe2cd44ceba6187a84b9cc501e4f6bd18e31ef3'
RETURN='review-4a7edb2bdad2ea8b:v0001'
RULE='c67640298f12'
SEED='f4c7accc65b881c88f1d164615921419db836327fef50373eaba86d017d6218c'
def sha(data): return hashlib.sha256(data).hexdigest()
def digest(path): return sha(path.read_bytes())
def dump(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def components(board):
    seen=set();out=[];h=len(board);w=len(board[0])
    for r in range(h):
        for c in range(w):
            if board[r][c]==0 or (r,c) in seen: continue
            color=board[r][c];stack=[(r,c)];seen.add((r,c));cells=[]
            while stack:
                x,y=stack.pop();cells.append((x,y))
                for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=nx<h and 0<=ny<w and (nx,ny) not in seen and board[nx][ny]==color:
                        seen.add((nx,ny));stack.append((nx,ny))
            out.append((len(cells),min(cells),cells))
    return out
started=time.monotonic()
evidence={'schema':'arcpuzzles-bounded-audit-replay-v1','ticket_id':TICKET,'task_id':TASK,
 'audit_return_id':RETURN,'probe_seed':SEED,'targeted_probes':1,'targeted_probe_limit_seconds':120,
 'claim':'texture=decoy, small_size=1 silently omits the promised non-green decoy and permits the global-smallest rival',
 'audit_status_changed':False,'maintainer_assessment':'unresolved; reviewer evidence only',
 'lint_and_override_battery_rerun':False,'broader_lesson_claim_tested':False,
 'retained_racket_asset_present_in_manifest':False,'elapsed_minutes':None}
bridge=None
status='blocked'
summary='Bounded replay blocked before the retained claim was established.'
try:
    source=REPO/f'generators/{TASK}/generator.py'
    assets=REPO/f'generators/{TASK}/counterexamples/review-4a7edb2bdad2ea8b-v0001/audit_assets.json'
    index=REPO/f'generators/{TASK}/evidence/review_index.json'
    bindings={str(p.relative_to(WORK)):digest(p) for p in (source,assets,index)}
    assert digest(source)==SOURCE
    assert digest(assets)==ASSETS
    assert digest(index)==INDEX
    record=next(r for r in json.loads(index.read_text())['audits'] if r['return_id']==RETURN)
    record_hash=sha(json.dumps(record,sort_keys=True,separators=(',',':')).encode())
    assert record_hash==RECORD
    evidence.update({'identity_hashes':bindings,'audit_record_sha256':record_hash,
                     'original_resolution':record['resolution'],'original_verification_status':record['verification_status']})
    retained_hashes={}
    for row in json.loads(assets.read_text())['files']:
        if '/checks/audit/04e2ffe8dc8e/' in row['path']:
            p=HERE/'retained'/Path(row['path']).name
            assert digest(p)==row['sha256']
            retained_hashes[p.name]={'sha256':digest(p),'original_asset_path':row['path']}
    evidence['retained_assets']=retained_hashes
    sys.path.insert(0,str(REPO/'shared/runtime'))
    from reviewer_support import load_selected_generator
    gen,selected,selected_sha=load_selected_generator(TASK,root=REPO)
    assert selected==source and selected_sha==SOURCE
    case=json.loads((HERE/'retained/case.json').read_text())
    kwargs={'seed':case['seed'],'sample_index':case['sample_index'],**case['overrides']}
    grid=gen.generate(**kwargs)
    errors=gen.self_check(grid)
    non_green=sum(v not in (0,3) for row in grid for v in row)
    assert errors==[]
    assert grid==json.loads((HERE/'retained/input.json').read_text())
    rival=[row[:] for row in grid]
    for r,c in min(components(grid),key=lambda x:(x[0],x[1]))[2]:rival[r][c]=6
    assert rival==json.loads((HERE/'retained/rival-smallest-any-color.json').read_text())
    evidence.update({'generate_kwargs':kwargs,'input':grid,'validator_errors':errors,
      'non_green_nonzero_cells':non_green,'generated_input_equals_retained':True,
      'rival_output':rival,'rival_output_equals_retained':True})
    assert non_green==0
    status='finding'
    summary='Reproduced the source-bound advertised-decoy omission: seed 0, index 0, texture=decoy, small_size=1 passes self_check with zero non-green foreground cells. Authority comparison not completed; audit remains unresolved.'
    canonical=REPO/'shared/data/canonical/puzzles.jsonl'
    rows=[json.loads(line) for line in canonical.open() if line.strip() and json.loads(line).get('task_id')==TASK]
    assert len(rows)==1
    rule=rows[0]['program_solution']
    rule_sha=sha(rule.encode())
    assert rule_sha[:12]==RULE,(rule_sha,RULE)
    from puzzle_generators.rule_wrap import wrap_rule
    from arc_repl.racket_bridge import RacketBridge
    os.environ['TMPDIR']=str(HERE)
    import tempfile
    tempfile.tempdir=str(HERE)
    bridge=RacketBridge(timeout=20.0,startup_timeout=45.0)
    wrapped=wrap_rule(rule)
    bridge.eval_text('(define __ticket_rule '+wrapped+')')
    bridge.define_grid('__ticket_input',grid)
    output=bridge.eval_text('(__ticket_rule __ticket_input)')
    evidence.update({'rule_hash':RULE,'rule_source_sha256':rule_sha,'rule_source':rule,
      'canonical_output':output,'canonical_output_equals_rival':output==rival,
      'canonical_execution':'actual RacketBridge using packet wrap_rule',
      'racket_binary':bridge.racket_binary,'wrapped_rule_sha256':sha(wrapped.encode())})
    assert output==rival
    assert digest(source)==SOURCE and digest(index)==INDEX and digest(assets)==ASSETS
    evidence['bounded_claim_reproduced']=True
    evidence['source_and_audit_state_unchanged']=True
    summary='Reproduced retained source-bound decoy omission and shortcut: seed 0/index 0 with texture=decoy, small_size=1 yields the exact retained input, passes self_check, has zero non-green foreground cells, and actual Racket rule c67640298f12 equals the retained global-smallest rival. Audit remains unresolved; no lint/battery claims were rerun.'
except Exception as error:
    evidence['error']={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
finally:
    if bridge is not None:bridge.close()
    evidence['targeted_probe_seconds']=round(time.monotonic()-started,6)
    evidence['ticket_status']=status
    dump(HERE/'evidence.json',evidence)
    result={'ticket_id':TICKET,'type':'audit_replay','status':status,'summary':summary,
      'evidence_paths':[f'checks/tickets/{TICKET}/evidence.json',f'checks/tickets/{TICKET}/probe.py',f'checks/tickets/{TICKET}/command.json'],
      'elapsed_minutes':None}
    dump(HERE/'ticket_result.json',result)
    print(json.dumps({'status':status,'bounded_claim_reproduced':evidence.get('bounded_claim_reproduced',False),'targeted_probe_seconds':evidence['targeted_probe_seconds'],'error':evidence.get('error')}))
