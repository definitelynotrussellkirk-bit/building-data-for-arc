from pathlib import Path
import hashlib, json
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator

root=Path.cwd()
base=root.parent/'checks/peers/483682b75e12'
search=json.loads((base/'search-result.json').read_text())
found=search['found']
if found is None:
    raise ValueError('no witness')
module, source_path, source_sha256 = load_selected_generator('483682b75e12', root=root)
if source_sha256 != found['source_sha256']:
    raise ValueError('peer source changed after witness search')
canonical=None
for line in (root/'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
    row=json.loads(line)
    if row.get('task_id')=='483682b75e12':
        canonical=row['program_solution']; break
if canonical is None: raise ValueError('canonical missing')
rival=(base/'bbox_area_rival.rkt').read_text()
apply,identity,bridge=_real_evaluator(root/'shared/runtime')
try:
    pairs=found['demonstrations']+[found['query']]
    records=[]
    for index,pair in enumerate(pairs):
        inp=pair['input']
        errors=module.self_check(inp)
        if errors:
            raise AssertionError(f'witness input left current generator domain: {errors}')
        canonical_output=apply(canonical,inp)
        rival_output=apply(rival,inp)
        records.append({
            'role':'query' if index==3 else 'demo',
            'index':index,
            'input':inp,
            'canonical_output':canonical_output,
            'rival_output':rival_output,
            'matches_stored_canonical':canonical_output==pair['canonical_output'],
            'matches_stored_rival':rival_output==pair['rival_output'],
            'programs_agree':canonical_output==rival_output,
        })
finally:
    bridge.close()
result={
    'schema':'arcpuzzles-peer-racket-replay-v1',
    'task_id':'483682b75e12',
    'seed':found['seed'],
    'source_path':str(source_path.relative_to(root)),
    'source_sha256':source_sha256,
    'racket':identity,
    'canonical_program_sha256':hashlib.sha256(canonical.encode()).hexdigest(),
    'rival_program_sha256':hashlib.sha256(rival.encode()).hexdigest(),
    'records':records,
    'demonstrations_all_agree':all(x['programs_agree'] for x in records[:3]),
    'query_disagrees':not records[3]['programs_agree'],
    'all_stored_labels_replayed':all(x['matches_stored_canonical'] and x['matches_stored_rival'] for x in records),
    'all_inputs_pass_current_self_check':True,
    'protected_racket_evaluations':2*len(records),
    'scope':'one source-bound generated lesson; no prevalence claim',
}
(base/'racket-replay.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('demonstrations_all_agree','query_disagrees','all_stored_labels_replayed')},sort_keys=True))
