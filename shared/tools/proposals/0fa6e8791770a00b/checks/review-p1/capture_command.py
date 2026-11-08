import hashlib,json
from pathlib import Path
from reviewer_support import find_root,load_selected_generator
root=find_root(Path('generators/144c5d002191/generator.py'))
source=root/'generators/144c5d002191/generator.py'
body=source.read_bytes()
expected='a3e21d4ea25700280832635bb9af391686399b3b7926cc8944f16d7ee6ae4d14'
assert hashlib.sha256(body).hexdigest()==expected,'Source changed before capture'
gen,_,sha=load_selected_generator('144c5d002191',root=root)
assert sha==expected
out=root.parent/'checks/review-p1'
out.mkdir(parents=True,exist_ok=False)
(out/'prior_generator.py').write_bytes(body)
rows=[]
for index in range(23,27):
    grid=gen.generate(0,index,difficulty='medium')
    canonical=json.dumps(grid,separators=(',',':')).encode()
    rows.append({'sample_index':index,'input':grid,'input_sha256':hashlib.sha256(canonical).hexdigest()})
record={'schema':'arcpuzzles-review-p1-captured-inputs-v1','task_id':'144c5d002191','input_generator_sha256':sha,'seed':0,'difficulty':'medium','start':23,'train_sample_indices':[23,24,25],'query_sample_index':26,'overrides':{},'rule_hash':'c3118b3e9e62','hash_serialization':'UTF-8 json.dumps(grid,separators=(comma,colon))','pairs':rows}
(out/'captured_inputs.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'source_identity.json').write_text(json.dumps({'path':'prior_generator.py','sha256':sha,'original_selected_path':'generators/144c5d002191/generator.py','version':gen.VERSION,'rule_hash':gen.RULE_HASH},indent=2)+'\n')
print(json.dumps({'captured':True,'directory':str(out),'source_sha256':sha,'samples':[r['sample_index'] for r in rows],'input_sha256':[r['input_sha256'] for r in rows]}))
