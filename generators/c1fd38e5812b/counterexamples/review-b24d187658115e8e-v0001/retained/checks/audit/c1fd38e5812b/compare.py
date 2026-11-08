import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
probe=json.loads((OUT/'probe.json').read_text())
actual=json.loads((OUT/'racket.json').read_text())
assert actual['generator_sha256']==probe['generator_sha256']
assert len(actual['results'])==64
assert all(r['error'] is None and r['output']==c['expected'] and r['input']==c['input'] for r,c in zip(actual['results'],probe['cases']))
# Rival: compress rows at first-column boundaries. If those row spans are
# uniform, assume column spans are uniform too; use the first column span as
# a fixed stride. Otherwise retain all first-row run starts independently.
def coupled_uniformity(grid):
    rs=[0]+[r for r in range(1,len(grid)) if grid[r][0]!=grid[r-1][0]]
    cs=[0]+[c for c in range(1,len(grid[0])) if grid[0][c]!=grid[0][c-1]]
    spans=[b-a for a,b in zip(rs,rs[1:]+[len(grid)])]
    if len(set(spans))==1:
        stride=cs[1] if len(cs)>1 else len(grid[0])
        cs=list(range(0,len(grid[0]),stride))
    return [[grid[r][c] for c in cs] for r in rs]
generated=[c for c in probe['cases'] if c['kind']=='generated']
assert all(coupled_uniformity(c['input'])==actual['results'][c['batch_index']]['output'] for c in generated)
witnesses=[c for c in probe['cases'] if coupled_uniformity(c['input'])!=actual['results'][c['batch_index']]['output']]
assert witnesses
w=witnesses[0];result=actual['results'][w['batch_index']]
report={'task_id':probe['task_id'],'generator_sha256':probe['generator_sha256'],'generator_declared_rule_hash':probe['rule_hash'],'executed_rule_hash':actual['executed_rule_hash'],'catalog_rule_hash':actual['catalog_rule_hash'],'rule_text_sha256':actual['rule_text_sha256'],'status':'bounded coverage gap with public-Racket-confirmed lawful witness; no generator output mismatch found','counts':{'public_racket_cases':64,'expected_matches':64,'generated_rival_passes':len(generated),'generated_rival_total':len(generated),'handcrafted_rival_failures':len(witnesses),'global_dedup_failures':sum(c['rivals']['global_row_column_dedup']!=r['output'] for c,r in zip(probe['cases'],actual['results'])),'equal_stride_failures':sum(c['rivals']['equal_stride']!=r['output'] for c,r in zip(probe['cases'],actual['results']))},'witness':dict(w,actual_racket_output=result['output'],rival_output=coupled_uniformity(w['input'])),'public_apply_command':actual['command'],'public_apply_cwd':actual['cwd'],'files':{'input_sha256':hashlib.sha256((OUT/'input.json').read_bytes()).hexdigest(),'racket_sha256':hashlib.sha256((OUT/'racket.json').read_bytes()).hexdigest()}}
(OUT/'findings.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'counts':report['counts'],'witness_batch_index':w['batch_index'],'witness_logical':w['logical'],'witness_spans':[w['row_spans'],w['col_spans']],'self_check':w['self_check'],'actual_output':result['output'],'rival_output':report['witness']['rival_output']}))
