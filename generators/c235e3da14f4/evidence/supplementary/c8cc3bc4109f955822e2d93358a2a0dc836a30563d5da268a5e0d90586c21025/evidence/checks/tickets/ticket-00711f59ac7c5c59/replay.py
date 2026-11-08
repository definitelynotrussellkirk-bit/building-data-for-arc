"""Replay one retained audit witness against pinned source and canonical Racket."""
from collections import deque
from pathlib import Path
import copy,hashlib,importlib.util,json,time
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
W=Path(__file__).resolve().parents[3]
E=Path(__file__).resolve().parent
SOURCE=W/'repo/generators/c235e3da14f4/generator.py'
EXPECTED_SOURCE='691c126ec9e72d0eef4e09556f097fd84a850b71779fac00a6840acfcf43a9e4'
def sha(data):return hashlib.sha256(data).hexdigest()
def grid_sha(grid):return sha(json.dumps(grid,separators=(',',':')).encode())
assert sha(SOURCE.read_bytes())==EXPECTED_SOURCE
verification=json.loads((E/'asset-verification.json').read_text())
for asset in verification['materialized']:
    assert sha((W/asset['evidence_path']).read_bytes())==asset['sha256']
retained=json.loads((E/'retained/shortcut-census.json').read_text())
retained_racket=json.loads((E/'retained/racket.json').read_text())
grid=json.loads((E/'retained/input.json').read_text())
assert grid==retained['counterexample']['input']==retained_racket['results'][0]['input']
original=copy.deepcopy(grid)
spec=importlib.util.spec_from_file_location('ticket_c235e3da14f4_pinned_generator',SOURCE)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
assert g.RULE_HASH=='f44de8fa965f'
errors=g.self_check(grid)
mirror=g.rule_mirror(grid)
assert errors==retained['counterexample']['validator_errors']
assert mirror==retained['counterexample']['canonical_python_output']==[[0]]
# Independent implementation of precisely the retained shortcut: exclude 0 and 2,
# then choose the first smallest same-color 4-connected object and crop its box.
seen=set();objects=[];height=len(grid);width=len(grid[0])
for r in range(height):
    for c in range(width):
        if grid[r][c] in (0,2) or (r,c) in seen:continue
        color=grid[r][c];cells=[];queue=deque([(r,c)]);seen.add((r,c))
        while queue:
            rr,cc=queue.popleft();cells.append((rr,cc))
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr,nc=rr+dr,cc+dc
                if 0<=nr<height and 0<=nc<width and (nr,nc) not in seen and grid[nr][nc]==color:
                    seen.add((nr,nc));queue.append((nr,nc))
        objects.append(cells)
selected=min(objects,key=len)
r0=min(r for r,c in selected);r1=max(r for r,c in selected)
c0=min(c for r,c in selected);c1=max(c for r,c in selected)
rival=[row[c0:c1+1] for row in grid[r0:r1+1]]
assert rival==retained['counterexample']['rival_output']==[[6,6,6]]*3
canonical_path=W/'repo/shared/data/canonical/puzzles.jsonl'
canonical_sha=sha(canonical_path.read_bytes())
assert canonical_sha=='53695968f60110206563b093011331cffc2a6a32fe42e3e1d443ff6c7458ccac'
rows=[json.loads(line) for line in canonical_path.read_text().splitlines() if json.loads(line).get('task_id')=='c235e3da14f4']
assert len({row['program_solution'] for row in rows})==1
raw=rows[0]['program_solution'];wrapped=wrap_rule(raw)
assert sha(raw.encode())=='4c9ca5e55f8ee74a6261cb5e8a94ea8ca0702c9b2dcb615a6d18d33f3da8ea10'
assert sha(' '.join(raw.split()).encode())[:12]==g.RULE_HASH
start=time.monotonic()
with RacketBridge(timeout=30.0) as bridge:
    version=bridge.eval_text('(version)')
    bridge.eval_text(f'(define audit-replay-rule {wrapped})')
    bridge.define_grid('audit-replay-input',grid)
    actual=bridge.eval_text('(audit-replay-rule audit-replay-input)')
racket_seconds=time.monotonic()-start
assert actual==retained_racket['results'][0]['output']==mirror==[[0]]
assert actual!=rival
assert grid==original
assert sha(SOURCE.read_bytes())==EXPECTED_SOURCE
print(json.dumps({'schema':'bounded-existing-audit-replay-v1','ticket_id':'ticket-00711f59ac7c5c59','audit_return_id':'review-20843cd2d2a3ea7d:v0001','status':'reproduced','generator_sha256':EXPECTED_SOURCE,'rule_hash':g.RULE_HASH,'canonical_identity':{'path':'repo/shared/data/canonical/puzzles.jsonl','collection_sha256':canonical_sha,'raw_program_sha256':sha(raw.encode()),'wrapped_callable_sha256':sha(wrapped.encode()),'definition_sha256':sha(f'(define audit-replay-rule {wrapped})'.encode()),'retained_apply_rule_text_sha256':retained_racket['rule_text_sha256'],'retained_apply_hash_matches_wrapped_callable':sha(wrapped.encode())==retained_racket['rule_text_sha256']},'input':grid,'input_sha256':grid_sha(grid),'validator_errors':errors,'passes_generator_validator':not errors,'python_mirror_output':mirror,'actual_racket_output':actual,'shortcut_output':rival,'canonical_output_sha256':grid_sha(actual),'shortcut_output_sha256':grid_sha(rival),'racket_version':version,'racket_elapsed_seconds':racket_seconds,'racket_rule_application_count':1,'retained_claim_checks':{'witness_identity_exact':True,'validator_errors_exact':True,'python_output_exact':True,'racket_output_exact':True,'shortcut_output_exact':True,'peer_source_unchanged':True,'input_unchanged':True},'scope':'Exact retained broad-rule witness and calibrated-validator exclusion reproduced; this is a teaching-domain limitation, not an emitted wrong label or validator-admitted counterexample.','not_rerun':['1408-example census','six official anchors','portable task tests','semantic gate','peer battery'],'disposition':'Existing source-bound audit remains unresolved; this replay does not clear or independently qualify the generator.'},indent=2))
