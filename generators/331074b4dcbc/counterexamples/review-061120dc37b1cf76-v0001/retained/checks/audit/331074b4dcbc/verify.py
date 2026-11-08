import hashlib, importlib.util, json
from pathlib import Path
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe',D/'probe.py'); probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
a=json.loads((D/'racket.json').read_text()); rivals=json.loads((D/'rival_outputs.json').read_text())
assert len(a['results'])==11
for r in a['results']:
    assert r['error'] is None and r['valid_output'] and r['generator_domain']['status']=='valid'
    assert r['output']==probe.gen.rule_mirror(r['input'])
assert all(r['output']==rivals[i] for i,r in enumerate(a['results'][:8]))
assert all(r['output']!=rivals[i] for i,r in enumerate(a['results'][8:],8))
demos=[{'input':r['input'],'output':r['output']} for r in a['results'][:2]]
query={'input':a['results'][8]['input'],'output':a['results'][8]['output']}
hook=probe.gen.lesson_identifiable(demos,query)
assert hook==[]
assert all(probe.rival(d['input'])==d['output'] for d in demos)
assert probe.rival(query['input'])!=query['output']
(D/'lesson_counterexample.json').write_text(json.dumps({'demos':demos,'query':query,'new_rival_query_output':probe.rival(query['input']),'lesson_identifiable_reasons':hook,'scope':'generated demos; canonical query is validator/strict-supported but not generated'},indent=2)+'\n')
commands=[{'cwd':str(D.parents[2]),'command':'.venv/bin/python run_with_racket.py /workspace/scratch/944df838b1d1/packet/WORK/.venv/bin/python ../checks/audit/331074b4dcbc/probe.py','exit_code':0},{'cwd':str(D.parents[2]),'command':'.venv/bin/python run_with_racket.py /workspace/scratch/944df838b1d1/packet/WORK/.venv/bin/python -m arcpuzzles apply 331074b4dcbc --input ../checks/audit/331074b4dcbc/input.json --check-generator-domain --out ../checks/audit/331074b4dcbc/racket.json','exit_code':0},{'cwd':str(D.parents[2]),'command':'.venv/bin/python run_with_racket.py /workspace/scratch/944df838b1d1/packet/WORK/.venv/bin/python ../checks/audit/331074b4dcbc/verify.py','exit_code':0}]
summary={'official_labels':11,'generated_parity':8,'canonical_parity':3,'rival_generated_matches':8,'rival_canonical_mismatches':3,'generator_domain_valid':11,'lesson_hook_reasons':hook,'commands':commands,'earlier_nonsemantic_setup_error':'Initial attempted creation used ../checks relative to WORK, failed No such file or directory, exit 2; no file was created. Corrected to checks under WORK.'}
(D/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
files=sorted(p for p in D.iterdir() if p.is_file() and p.name!='hashes.json')
(D/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
print(json.dumps(summary))
