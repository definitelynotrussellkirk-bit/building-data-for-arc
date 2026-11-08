import hashlib, json
from pathlib import Path
D=Path(__file__).resolve().parent
R=D.parents[2]/'repo'
e=json.loads((D/'evidence.json').read_text());a=json.loads((D/'racket.json').read_text())
e['rule_text_sha256']=a['rule_text_sha256'];e['executed_rule_hash']=a['executed_rule_hash']
e['actual_racket_output']=a['results'][0]['output'];e['actual_racket_valid_output']=a['results'][0]['valid_output']
e['rival_differs_from_racket']=e['rival_output']!=e['actual_racket_output']
e['source_unchanged']=e['generator_sha256']==hashlib.sha256((R/'generators/4cccb4dba000/generator.py').read_bytes()).hexdigest()
e['verification_commands']=[
 {'cwd':'packet_root','argv':['python3','checks/audit/4cccb4dba000/probe.py'],'exit_code':0,'evidence_paths':['checks/audit/4cccb4dba000/input.json','checks/audit/4cccb4dba000/evidence.json']},
 {'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','4cccb4dba000','--input','../checks/audit/4cccb4dba000/input.json','--out','../checks/audit/4cccb4dba000/racket.json'],'exit_code':0,'evidence_paths':['checks/audit/4cccb4dba000/racket.json']},
 {'cwd':'packet_root','argv':['python3','checks/audit/4cccb4dba000/finalize.py'],'exit_code':0,'evidence_paths':['checks/audit/4cccb4dba000/evidence.json','checks/audit/4cccb4dba000/AUDIT_SECTION.md']}
]
# Read only this target's public canonical examples; private solve folders are not used.
ns={};s=(D/'probe.py').read_text();exec(s[:s.index('kwargs=')],{'__file__':str(D/'probe.py')},ns)
# The extracted helper is pure and needs no generator/reference execution.
cs_fn=ns['components']
c=json.loads((R/'shared/data/base/solutions/training/8efcae92__4cccb4dba000.json').read_text())
canonical=[]
for i,pair in enumerate(c['visible_context']['train']):
 cs=cs_fn(pair['input']);mx=max(x['red_count'] for x in cs);wins=[x for x in cs if x['red_count']==mx]
 canonical.append({'split':'train','sample_index':i,'red_counts':[x['red_count'] for x in cs],'maximum_unique':len(wins)==1,'rival_matches_published_output':wins[-1]['output']==pair['output']})
e['canonical_checks']=canonical
e['canonical_denominator']=len(canonical)
e['generated_unique_input_count']=1
e['finding_class']='reproduced generator invariant defect and validator false negative'
(D/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
assert e['source_unchanged'] and e['rival_differs_from_racket'] and not e['self_check_result']
assert all(x['maximum_unique'] and x['rival_matches_published_output'] for x in canonical)
report=f'''## 4cccb4dba000

**A4-1 — Reproduced defect: helpful generation can tie the maximum red count, and its validator accepts the result.** `generate` clips each red count to `rectangle area − 1`; several distinct requested counts above eight therefore become eight on 3×3 rectangles. `self_check` checks only global red presence and nonzero palette size, despite its unique-maximum docstring.

The first focused sample is decisive: seed **0**, sample **0**, difficulty **hard**, overrides `grid_h=22, grid_w=22, n_clusters=5, cluster_size_kind="small", red_count_distribution="wide_spread"`. Its five separated components have row-major red counts **[8, 2, 8, 1, 6]**; `self_check(input)` returns **[]**. The two eight-red components occupy inclusive boxes `[3,4,5,6]` and `[12,15,14,17]`. This is **one generated unique input / one successful focused draw**, not a frequency estimate.

All parameter values belong to the declared helpful axis ranges and hard difficulty bounds. The emitted grid is **outside the documented semantic domain**, because `INVARIANTS` requires a strictly unique maximum. No degenerate texture was requested. Actual Racket execution succeeds and returns `[[3,2,2],[2,2,2],[2,2,2]]`; the equally most-red rival choosing the last tied component returns `[[4,2,2],[2,2,2],[2,2,2]]`. The rival matches **3/3 published canonical train pairs**, all of which have unique maxima; their red counts and comparisons are retained. The finding is the generator's broken invariant and validator false negative, not a claim that the Racket authority incorrectly implements its own deterministic behavior.

Source identity: generator SHA-256 `{e['generator_sha256']}`; canonical executed rule hash `{e['executed_rule_hash']}`; exact rule-text SHA-256 `{e['rule_text_sha256']}`. Both assigned generator and reference remain unchanged.

Evidence: [input](input.json), [public Racket receipt](racket.json), [complete counterexample, validator, rival, canonical comparisons and command records](evidence.json), [reproducer](probe.py), and [analysis finalizer](finalize.py). Execute from `packet_root`: `python3 checks/audit/4cccb4dba000/probe.py`, then `python3 run_with_racket.py python3 -m arcpuzzles apply 4cccb4dba000 --input ../checks/audit/4cccb4dba000/input.json --out ../checks/audit/4cccb4dba000/racket.json`, then `python3 checks/audit/4cccb4dba000/finalize.py`; each completed with exit **0**. The wrapper's actual runtime cwd is `{a['cwd']}`, recorded in its receipt. An initial probe omitted hard difficulty and rejected `grid_h=22` before generating an input (exit 1); [that configuration failure](initial_probe_failure.json) is retained separately.

Checks performed: generator/notes/rule and canonical-example inspection; one focused generated clipping witness; independent 8-connected component/red-count analysis; target `self_check`; one supported public Racket application; last-tie rival comparison; 3 canonical training comparisons; unchanged generator hash. No broad battery was run. Suggested future repair: sample feasible distinct counts after dimensions are chosen, and validate component count and unique maximum on the emitted grid. **Findings only; no audit-target changes.**
'''
(D/'AUDIT_SECTION.md').write_text(report)
print(json.dumps({'finding':e['finding_class'],'racket_output':e['actual_racket_output'],'rival_output':e['rival_output'],'canonical_train':canonical,'report':str(D/'AUDIT_SECTION.md')}))
