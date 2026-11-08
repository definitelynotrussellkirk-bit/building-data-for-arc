from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent
root=p.parents[2]
e=json.loads((p/'evidence.json').read_text())
r=json.loads((p/'racket.json').read_text())
for pair,res in zip(e['pairs'],r['results'],strict=True):
 actual=res['output'];rival=pair['rival_output']
 pair['actual_racket_output']=actual
 pair['rival_matches_actual']=actual==rival
 pair['python_mirror_matches_actual']=actual==pair['python_rule_mirror_output']
 pair['difference_coordinates']=[{'row':rr,'col':cc,'rival':rival[rr][cc],'actual':actual[rr][cc]} for rr,row in enumerate(actual) for cc,v in enumerate(row) if v!=rival[rr][cc]]
 pair['changed_cell_count']=len(pair['difference_coordinates'])
e['actual_execution']={k:r[k] for k in ('schema','task_id','rule_task_id','reference','executed_rule_hash','catalog_rule_hash','rule_hash_matches_catalog','rule_text_sha256','generator_sha256','command','cwd')}
e['actual_execution']['receipt_sha256']=hashlib.sha256((p/'racket.json').read_bytes()).hexdigest()
e['commands'].extend([
 {'command':'python3 run_with_racket.py python3 -m arcpuzzles apply ba32e05911b0 --input ../checks/audit/ba32e05911b0/input.json --out ../checks/audit/ba32e05911b0/racket.json','cwd':str(root),'effective_payload_cwd':str(root/'repo'),'exit_code':0},
 {'command':'python3 checks/audit/ba32e05911b0/finalize.py','cwd':str(root),'exit_code':0}])
e['conclusion']={'rival_fits_all_demonstrations':all(x['rival_matches_actual'] for x in e['pairs'][:3]),'rival_disagrees_with_query':not e['pairs'][3]['rival_matches_actual'],'query_changed_cells':e['pairs'][3]['changed_cell_count'],'rule_mirror_matches_racket_all_four':all(x['python_mirror_matches_actual'] for x in e['pairs'])}
assert e['conclusion']['rival_fits_all_demonstrations'] and e['conclusion']['rival_disagrees_with_query']
(p/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
text='''## ba32e05911b0

**Reproduced an unresolved teaching ambiguity on the current source.** Default sampler seed `10`, difficulty `medium`, indices `0`, `1`, and `2` all produce `clear_climb` scenes. A straight-up rival that traces each bottom color-6 marker in its original column and never rolls matches the actual selected Racket outputs on all three demonstrations. Index `3` produces `long_roll`; the rival disagrees with the actual query output at %s cells.

All four inputs are unmodified default generated draws and pass `self_check`. The generator declares no `EXAMPLES_NEEDED`, so this is an actual native three-demonstration lesson. The supported wrapper `arcpuzzles apply` command executed the canonical rule successfully; its receipt confirms generator SHA-256 `%s` and executed rule hash `%s`. The Python mirror agrees with Racket on all four inputs.

This reproduces the existing audit retained in `repo/generators/ba32e05911b0/evidence/review_index.json` against exactly the same source; it is not a new distinct finding. The rival is refuted by canonical rolling examples, so the finding is a generated teaching flaw rather than a canonical-fitting shortcut.

**Recommendation.** Add a deterministic lesson schedule with explicit no-roll rivals. Require rolling examples in every allowed demonstration window; for arbitrary query holdouts, ensure at least two refuting examples per materialized lesson. Retain stop and multiple-roll teaching coverage. No target or shared source was changed.

Reproduction and complete evidence: `checks/audit/ba32e05911b0/reproduce.py`, `input.json`, `rival.json`, `racket.json`, `finalize.py`, and `evidence.json`. The evidence records full grids, exact differences, source/rule hashes, validator acceptance, domain membership, and commands with working directories and exit codes. Probe scope: four generated pairs and one declared rival; no full battery.
'''%(e['conclusion']['query_changed_cells'],e['source_sha256'],r['executed_rule_hash'])
(p/'AUDIT_SECTION.md').write_text(text)
print(json.dumps(e['conclusion']))
