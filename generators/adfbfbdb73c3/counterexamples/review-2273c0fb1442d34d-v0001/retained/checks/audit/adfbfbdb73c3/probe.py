"""Findings-only reproduction for adfbfbdb73c3; never edits selected sources."""
from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, sys
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ID='adfbfbdb73c3'
def save(name,value):
 (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def sha(text): return hashlib.sha256(text).hexdigest()
rows=[]
for line in (ROOT/'repo/shared/data/canonical/puzzles.jsonl').open():
 row=json.loads(line)
 if row.get('task_id')==ID: rows.append(row)
assert len(rows)==1
record=rows[0]
source=ROOT/f'repo/generators/{ID}/generator.py'
sys.path.insert(0,str(ROOT/'repo/shared/runtime'))
spec=importlib.util.spec_from_file_location('audit_target',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def vertical_strips(grid):
 """Priority-fill strips separated only by full-height vertical walls."""
 out=[row[:] for row in grid]
 legend=[v for v in grid[0] if v not in (0,5)]
 top=next(r for r,row in enumerate(grid[1:],1) if all(v==5 for v in row))
 walls=[c for c in range(len(grid[0])) if all(grid[r][c]==5 for r in range(top,len(grid)))]
 for a,b in zip(walls,walls[1:]):
  cells=[(r,c) for r in range(top+1,len(grid)) for c in range(a+1,b) if grid[r][c]!=5]
  present=[v for v in legend if any(grid[r][c]==v for r,c in cells)]
  color=present[0] if present else 0
  for r,c in cells: out[r][c]=color
 return out

generated=module.generate(0,0)
canonical=record['train'][0]['input']
save('input.json',generated)
save('canonical_input.json',canonical)
save('canonical_label.json',record['train'][0]['output'])
save('binding.json',{'task_id':ID,'source_path':str(source.relative_to(ROOT)),
 'source_sha256':sha(source.read_bytes()),'rule_sha256':sha(record['program_solution'].encode()),
 'rule_hash_method':'SHA256 of exact UTF-8 program_solution string from the unique canonical task record',
 'prior_lead':'review-0c3255d49c88983e:v0001 audit A1 in target evidence/review_index.json',
 'task_tests':'No tests directory exists for this selected target.'})
commands=[]
for input_name,output_name in ([] if '--analyze' in sys.argv else [('input.json','racket.json'),('canonical_input.json','canonical_racket.json')]):
 argv=['python3','run_with_racket.py','python3','-m','arcpuzzles','apply',ID,'--input',f'../checks/audit/{ID}/{input_name}','--out',f'../checks/audit/{ID}/{output_name}']
 result=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
 stem=Path(output_name).stem
 (OUT/f'{stem}.stdout.txt').write_text(result.stdout)
 (OUT/f'{stem}.stderr.txt').write_text(result.stderr)
 commands.append({'argv':argv,'cwd':str(ROOT),'effective_payload_cwd':str(ROOT/'repo'),
 'exit_code':result.returncode,'input_path':f'checks/audit/{ID}/{input_name}',
 'output_path':f'checks/audit/{ID}/{output_name}','stdout_path':f'checks/audit/{ID}/{stem}.stdout.txt',
 'stderr_path':f'checks/audit/{ID}/{stem}.stderr.txt'})
 save('command.json',commands)
 if result.returncode: raise RuntimeError(result.stderr)
print('Public Racket execution receipts: command.json')

actual=json.loads((OUT/'racket.json').read_text())['results'][0]['output']
canonical_actual=json.loads((OUT/'canonical_racket.json').read_text())['results'][0]['output']
seed_preserving=[row[:] for row in actual]
for r,row in enumerate(generated):
 for c,v in enumerate(row):
  if v not in (0,5): seed_preserving[r][c]=v
strip_generated=vertical_strips(generated)
strip_canonical=vertical_strips(canonical)
save('seed_preserving_rival.json',seed_preserving)
save('strip_rival_generated.json',strip_generated)
save('strip_rival_canonical.json',strip_canonical)
def differences(a,b):
 return [{'row':r,'column':c,'actual':v,'rival':b[r][c]} for r,row in enumerate(a) for c,v in enumerate(row) if v!=b[r][c]]
assert actual==strip_generated
assert canonical_actual==record['train'][0]['output']
assert differences(actual,seed_preserving)
assert differences(canonical_actual,strip_canonical)
save('findings.json',{'task_id':ID,'generated_witness':{'seed':0,'sample_index':0,'difficulty':None,'overrides':{},'shape':[len(generated),len(generated[0])],
 'input_path':'input.json','actual_racket_path':'racket.json','rival_path':'seed_preserving_rival.json',
 'self_check_errors':module.self_check(generated),
 'lawfulness':'Ordinary generate(0,0) with no overrides. Three distinct legend colors at row 0 columns 1..3; two enclosed rectangular chambers bounded by 5; each has two distinct legend seed cells.',
 'differences':differences(actual,seed_preserving)},
 'shortcut_witness':{'canonical_variant':0,'split':'train','pair_index':0,
 'seed':None,'sample_index':None,'overrides':None,'input_path':'canonical_input.json',
 'lawfulness':'Unmodified train pair 0 from the unique canonical task record; actual Racket output equals its supplied label.',
 'actual_racket_path':'canonical_racket.json','rival_path':'strip_rival_canonical.json',
 'generated_control_agrees':actual==strip_generated,'differences':differences(canonical_actual,strip_canonical)},
 'bounded_coverage':'Exactly one ordinary generated input and one canonical labeled input executed through public Racket apply. No task tests, broad battery, or distribution census run.',
 'source_unchanged':sha(source.read_bytes())==json.loads((OUT/'binding.json').read_text())['source_sha256']})
print('Documentation differences:',differences(actual,seed_preserving))
print('Canonical strip-rival mismatches:',len(differences(canonical_actual,strip_canonical)))
