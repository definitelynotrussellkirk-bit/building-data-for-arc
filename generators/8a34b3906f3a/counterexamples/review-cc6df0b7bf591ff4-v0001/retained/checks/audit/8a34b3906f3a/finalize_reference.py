from pathlib import Path
import hashlib,json,sys
OUT=Path(__file__).resolve().parent
WORK=OUT.parents[2]
ROOT=WORK/'repo'
TASK='8a34b3906f3a'
def read(name):return json.loads((OUT/name).read_text())
def file_sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def grid_sha(value):return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()
report=read('python-report.json')
reference=read('racket.json')
receipt=read('apply-command.receipt.json')
input_grid=read('input.json')
intended=read('python-intended-output.json')
rival=read('rival-output.json')
assert receipt['exit_code']==0
assert reference['task_id']==TASK
assert reference['generator_sha256']==report['generator_sha256']==file_sha(ROOT/'generators'/TASK/'generator.py')
assert reference['executed_rule_hash'] in report['canonical_rule_hashes']
assert reference['rule_hash_matches_catalog'] is True
assert len(reference['results'])==1
result=reference['results'][0]
assert result['valid_output'] is True and result['error'] is None
assert result['input']==input_grid
assert result['input_sha256']==grid_sha(input_grid)==report['witness']['input_sha256']
actual=result['output']
assert actual==intended
assert result['output_sha256']==grid_sha(actual)
assert len(actual)==len(rival) and all(len(a)==len(b) for a,b in zip(actual,rival))
differences=[[r,c] for r in range(len(actual)) for c in range(len(actual[r])) if actual[r][c]!=rival[r][c]]
comparison={'schema':'arcpuzzles-audit-reference-comparison-v1','task_id':TASK,'status':'confirmed',
    'generator_sha256':reference['generator_sha256'],'executed_rule_hash':reference['executed_rule_hash'],
    'rule_text_sha256':reference['rule_text_sha256'],'rule_hash_matches_catalog':True,
    'apply_exit_code':receipt['exit_code'],'apply_command':receipt,'reference_cwd':reference['cwd'],
    'input_sha256':result['input_sha256'],'output_sha256':result['output_sha256'],
    'valid_reference_outputs':1,'reference_output_count':1,'racket_equals_python_intended':True,
    'racket_equals_geometric_center_rival':actual==rival,'rival_differing_cells':len(differences),'differing_coordinates':differences,
    'input_color_2_cells':sum(v==2 for row in input_grid for v in row),
    'racket_output_color_2_cells':sum(v==2 for row in actual for v in row),
    'rival_output_color_2_cells':sum(v==2 for row in rival for v in row),
    'generated_call':report['witness']['generate_call'],'generator_self_check':report['witness']['self_check'],
    'bounded_python_counts':report['bounded_probe'],
    'canonical_pairs_checked':len(report['canonical_checks']),
    'canonical_python_matches':sum(p['python_rule_matches_known_output'] for p in report['canonical_checks']),
    'canonical_rival_matches':sum(p['geometric_center_rival_matches_known_output'] for p in report['canonical_checks']),
    'receipt_sha256':{'racket.json':file_sha(OUT/'racket.json'),'apply-command.receipt.json':file_sha(OUT/'apply-command.receipt.json')},
    'scope':'One actual canonical Racket apply confirms the retained generated witness. The 256-case census remains a Python-only finite probe. No additional Racket or tests were launched by this finalizer.'}
(OUT/'reference-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
draft=(OUT/'AUDIT_SECTION.md').read_text()
draft=draft.replace('Reference confirmation of the generated witness is pending; the current results below come from a small Python probe and the four supplied labeled canonical pairs.',
    'The public canonical Racket apply completed with exit 0 and a valid output, executed the pinned rule, and exactly matched the saved Python prediction for the generated witness. The canonical-fit and 256-case counts remain separately identified Python checks.')
draft=draft.replace('The Python transcription therefore predicts 10 red output cells.',
    'The actual canonical Racket output contains 10 red cells and exactly matches the Python transcription.')
draft=draft.replace('predicts 16 red cells and differs at 10 output cells.',
    'predicts 16 red cells and differs from the confirmed Racket output at 10 cells.')
draft=draft.replace('Await the separate public `apply` receipt before calling the generated witness Racket-confirmed.',
    'The generated witness is Racket-confirmed: `racket.json`, `apply-command.receipt.json` and `reference-comparison.json` retain the actual valid output, exact public command and working directory, exit 0, source/rule hashes and the full-grid comparison. Input hash: `'+result['input_sha256']+'`; reference output hash: `'+result['output_sha256']+'`.')
assert 'pending' not in draft.lower()
(OUT/'AUDIT_SECTION.md').write_text(draft)
commands=read('commands.json')
commands['reference_confirmation']='confirmed; exact result in reference-comparison.json'
command={**receipt,'resolved_cwd':str(WORK.parent),'purpose':'Actual canonical reference execution performed by root during the assigned runtime window'}
commands['commands'].append(command)
commands['commands'].append({'cwd':'/workspace/scratch/1ac4585b5d87',
    'argv':['nsenter','--target','280382','--user','--mount','--',str(WORK/'.venv/bin/python'),'-B','-u',str(Path(__file__).resolve())],
    'exit_code':0,'purpose':'Verify full-grid equality, source/rule bindings and rival difference against saved Racket receipt; no Racket launch',
    'evidence_paths':['checks/audit/'+TASK+'/reference-comparison.json','checks/audit/'+TASK+'/AUDIT_SECTION.md']})
commands['artifacts']=[{'path':p.name,'bytes':p.stat().st_size,'sha256':file_sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='commands.json']
(OUT/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
print(json.dumps({k:comparison[k] for k in ['task_id','status','generator_sha256','executed_rule_hash','apply_exit_code','racket_equals_python_intended','rival_differing_cells','input_color_2_cells','racket_output_color_2_cells','rival_output_color_2_cells','canonical_pairs_checked','canonical_python_matches','canonical_rival_matches']},indent=2))
