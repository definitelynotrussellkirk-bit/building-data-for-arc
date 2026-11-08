from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK='537b409b6744'
FINAL='34b8e36ac6bc1da85db025e34c4d908930dc5ce548cf3872e655312bb2e902cd'
def load(path): return json.loads((ROOT/path).read_text())
def sha(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def check(condition, label, actual=None):
    if not condition: raise AssertionError(f'{label}: {actual!r}')
facts={}
check(sha(f'repo/generators/{TASK}/generator.py')==FINAL,'final hash',sha(f'repo/generators/{TASK}/generator.py'))
facts['final_generator_sha256']=FINAL
text=(ROOT/f'repo/generators/{TASK}/generator.py').read_text()
check('VERSION = "4.1.0"' in text,'version'); check('RULE_HASH = "7b81cecb3b71"' in text,'rule hash')
facts.update(version='4.1.0',rule_hash='7b81cecb3b71')
before=load(f'checks/before/checks/{TASK}_before_battery_summary.json')
check(before['counts']=={'total':12,'green':11,'advisory':0,'failed':1,'interrupted':0,'pending':0,'running':0},'before counts',before['counts'])
check(before['first_failing_stage']=='defect_lint','before failing stage',before['first_failing_stage'])
log=(ROOT/f'checks/before/checks/{TASK}_before_defect_lint.log').read_text()
check("'strict-scalar': 48" in log,'before 48 strict scalar')
facts['before_battery']={'green':11,'total':12,'failed_stage':'defect_lint','warnings':48}
after=load(f'checks/after/checks/{TASK}_after_battery_summary.json')
check(after['counts']['total']==12 and after['counts']['green']==12 and not after['failed_stages'],'after battery',after['counts'])
facts['after_battery']={'green':12,'total':12}
sem=load(f'checks/after/checks/{TASK}_after_semantic_gate.json')['audits'][0]
check(sem['strict_hits']==sem['strict_draws']==600,'strict semantic',(sem['strict_hits'],sem['strict_draws']))
check(sem['strict_canonical']['canonical_inputs']==8 and sem['strict_canonical']['canonical_rejected']==0,'canonical semantic',sem['strict_canonical'])
check(sorted(sem['witnesses'])==['nearest_pair','smallest_mover','wall_growth'],'witness names',sorted(sem['witnesses']))
check(sem['witnesses']['smallest_mover']['hits']==317,'smallest hits',sem['witnesses']['smallest_mover']['hits'])
check(sem['lessons']['requested']==12 and sem['lessons']['unidentifiable']==0,'smoke lessons',sem['lessons'])
check(sem['lessons']['rotations']['checked']==48 and sem['lessons']['rotations']['ambiguous']==0,'smoke rotations',sem['lessons']['rotations'])
val=sem['canonical_ambiguity']['declared_validation']['smallest_mover']
check(val['checked']==8 and val['mismatches']==0,'canonical shortcut validation',val)
facts['semantic_gate']={'strict':'600/600','canonical_inputs':8,'witnesses':3,'smallest_mover_hits':317,'smoke_lessons':12,'smoke_rotations':48,'ambiguous_rotations':0}
over=load(f'checks/after/checks/{TASK}_after_override_results.json')
check(over['draws_total']==31230 and over['finding_count']==0 and over['warning_count']==0,'override totals',{k:over[k] for k in ('draws_total','finding_count','warning_count')})
facts['override']={'draws':31230,'findings':0,'warnings':0}
tests=load('checks/task-tests/result.json')
expected_tests={'tests':90,'failed':0,'errors':0,'skipped':0,'passed':90}
check(tests['passed'] and tests['exit_code']==0 and tests['test_counts']==expected_tests,'task tests',tests.get('test_counts'))
facts['task_tests']=tests['test_counts']
census=load('checks/lesson-census.summary.json'); cs=census['summary']
check(cs['requested']==cs['materialized']==300 and cs['pairs']==cs['unique_inputs']==1200,'census sizes',cs)
check(cs['ambiguous']==0 and cs['rotations']==1200 and cs['ambiguous_rotations']==0,'census ambiguity',cs)
facts['lesson_census']=cs
param=load('checks/parametric/candidate-selection/manifest.json')
check(param['status']=='proposed_unapproved' and param['default_program_exactly_canonical'] is True,'param status',(param['status'],param['default_program_exactly_canonical']))
check(param['counts']['episodes']==2 and param['counts']['racket_executions']==16 and param['counts']['distinguishing_train_pairs']==6,'param counts',param['counts'])
facts['parametric']=param['counts']
shortcut=load('checks/shortcut/smallest-mover-evidence.json')
check(shortcut['canonical_fit']['fits_all'] is True and shortcut['canonical_fit']['labeled_pairs']==8,'shortcut fit',shortcut['canonical_fit'])
check(shortcut.get('outputs_differ') is True,'shortcut differs',shortcut.get('outputs_differ'))
facts['smallest_mover']={'canonical_fit':'8/8','outputs_differ':True}
a1=load('checks/audit/f563fafba6ac/hole-area-rival-evidence.json')
check(a1['generator_sha256']=='ae0ce7c51dbe8cd9a78e2e44771b8364b523451c7ecaf34253a7f79e1f79d404','audit1 hash',a1['generator_sha256'])
check(a1['canonical_pairs_fit']==a1['canonical_pairs_total']==3,'audit1 canonical',(a1['canonical_pairs_fit'],a1['canonical_pairs_total']))
check(a1['generated_sample'].get('rival_matches')==a1['generated_sample'].get('draws')==400,'audit1 generated',a1['generated_sample'])
check(a1['counterexample'].get('python_matches_racket') is True,'audit1 racket',a1['counterexample'])
check(a1['counterexample'].get('outputs_disagree') is True,'audit1 differs',a1['counterexample'])
facts['audit_f563fafba6ac']={'canonical_fit':'3/3','generated_fit':'400/400','counterexample_reproduced':True}
a2=load('checks/audit/64a8d13b4024/override-contract-evidence.json')
check(a2['generator_sha256']=='c814a464d558cc1d3df388a88a67850ab4adfd553eeb95c5af027d599e4b4f71','audit2 hash',a2['generator_sha256'])
check(a2['official_override_check']['draws']==83160 and a2['official_override_check']['finding_count']==4586,'audit2 totals',a2['official_override_check'])
ov2=load('checks/audit/64a8d13b4024-override/checks/64a8d13b4024_audit_override_results.json')
check(ov2['finding_count']==4586 and ov2['draws_total']==83160,'audit2 official',(ov2['finding_count'],ov2['draws_total']))
expected={'override_mismatch':3240,'generation_error':1320,'axis_effect':22,'axis_metadata':2,'axis_provenance':1,'unknown_key':1}
for key,count in expected.items(): check(ov2['finding_categories'].get(key)==count,f'audit2 category {key}',ov2['finding_categories'].get(key))
facts['audit_64a8d13b4024']={'draws':83160,'findings':4586,'categories':expected}
fresh=load('checks/final-replay-candidate/summary.json')
check(fresh['replay_status']=='patch_replay_passed_tests_pending','fresh replay status',fresh['replay_status'])
check(fresh['fresh_generator_sha256']==FINAL,'fresh hash',fresh['fresh_generator_sha256'])
check(fresh['fresh_task_tests']['passed'] and fresh['fresh_task_tests']['counts']['passed']==90,'fresh tests',fresh['fresh_task_tests'])
facts['fresh_replay']={'patch_replay':True,'generator_sha256':FINAL,'task_tests':'90/90'}
reports=['REVIEW.md','DECISIONS.md','QUESTION_ANSWER.md','FEEDBACK_TO_CODEX.md','AUDIT.md',f'repo/generators/{TASK}/notes.md']
missing=[]; checked=[]; pattern=re.compile(r'`([^`]+)`')
for report in reports:
    for token in pattern.findall((ROOT/report).read_text()):
        path=None
        if token.startswith(('checks/','solve/','solve-blind/','repo/')): path=ROOT/token
        elif token.startswith('generators/'): path=ROOT/'repo'/token
        elif token.startswith(('workspace/','tests/','counterexamples/')): path=ROOT/'repo'/'generators'/TASK/token
        if path is not None:
            checked.append({'report':report,'reference':token,'resolved':str(path)})
            if not path.exists(): missing.append({'report':report,'reference':token,'resolved':str(path)})
check(not missing,'report refs',missing)
out={'schema':'arcpuzzles-reviewer-handoff-claim-validation-v1','status':'passed','facts':facts,'report_references_checked':len(checked),'missing_report_references':missing}
path=ROOT/'checks/handoff-claims-validation.json'; path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
