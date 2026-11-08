import hashlib,json
from pathlib import Path
root=Path.cwd()
work=root.parent
area=work/'checks/audit/87754dbb8687'
census=json.loads((area/'census.json').read_text())
packet=json.loads((work/'PACKET-MANIFEST.json').read_text())
selected={name:digest for name,digest in packet['files'].items() if name.startswith('repo/generators/87754dbb8687/')}
rows=[]
for name,expected in sorted(selected.items()):
 path=work/name
 actual=hashlib.sha256(path.read_bytes()).hexdigest()
 rows.append({'path':name,'expected_sha256':expected,'actual_sha256':actual,'unchanged':actual==expected})
result={'schema':'review-audit-source-integrity-v1','task_id':'87754dbb8687','files':rows,'all_target_files_unchanged':all(row['unchanged'] for row in rows),'generated_draws':48,'generated_unique_inputs':len({row['input_sha256'] for row in census['generated']}),'canonical_labeled_pairs':5,'canonical_unique_inputs':len({row['input_sha256'] for row in census['canonical']}),'public_racket_input_count':54}
with (area/'source-integrity.json').open('x') as f:
 json.dump(result,f,indent=2,sort_keys=True)
 f.write('\n')
print(json.dumps(result,indent=2))
