import sys
sys.dont_write_bytecode = True
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT.parent / 'checks/audit/4f7ed198556e'
sys.path.insert(0, str(ROOT/'shared/runtime'))
from reviewer_support import canonical_pairs, canonical_path

ID = '4f7ed198556e'
source = ROOT/'generators'/ID/'generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
record = next(row for row in rows if row.get('task_id') == ID)
rule = record['program_solution']
pairs = canonical_pairs(ID, root=ROOT)

def rival(g):
    h,w=len(g),len(g[0])
    out=[[0]*(2*w) for _ in range(2*h)]
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if color == 5:
                out[2*r][2*c:2*c+2] = [1,2]
                out[2*r+1][2*c:2*c+2] = [2,1]
    return out

seed,index,difficulty,overrides = 20261007,0,'medium',{'texture':'no_triggers'}
witness = gen.generate(seed,index,difficulty=difficulty,**overrides)
controls=[]
for sample_index in range(3):
    grid=gen.generate(seed,sample_index,difficulty=difficulty)
    controls.append({'seed':seed,'sample_index':sample_index,'difficulty':difficulty,'overrides':{},'input':grid,'self_check':gen.self_check(grid,difficulty=difficulty),'rival_output':rival(grid)})
canonical_fits = [{'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],'matches':rival(p['input'])==p['output']} for p in pairs]
assert all(p['matches'] for p in canonical_fits)
assert not any(v==5 for row in witness for v in row)
assert any(v==4 for row in witness for v in row)
probe = {
 'task_id':ID,'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'rule':rule,'rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
 'advertised_texture_axis':gen.AXES['texture'],'generator_version':gen.VERSION,
 'label_basis':'Actual selected canonical Racket execution in racket.json, to be populated by public apply command; no Python label substituted for authority.',
 'canonical_pairs_checked':canonical_fits,
 'ordinary_bounded_controls':controls,
 'witness':{'seed':seed,'sample_index':index,'difficulty':difficulty,'overrides':overrides,'input':witness,'generator_can_emit':True,'self_check_accepts':not gen.self_check(witness,difficulty=difficulty),'self_check_errors':gen.self_check(witness,difficulty=difficulty),'rival_output':rival(witness)},
 'existing_open_audit':'generators/4f7ed198556e/evidence/review_index.json: review-5b86b9773f7c67e4:v0001; independently corroborated with a fresh seed/index, not claimed as new.'
}
(OUT/'input.json').write_text(json.dumps({'inputs':[witness]},indent=2)+'\n')
(OUT/'rival.json').write_text(json.dumps({'outputs':[rival(witness)]},indent=2)+'\n')
(OUT/'probe.json').write_text(json.dumps(probe,indent=2)+'\n')
(OUT/'generator_snapshot.py').write_bytes(source.read_bytes())
(OUT/'rule.rkt').write_text(rule+'\n')
print(json.dumps({'generator_sha256':probe['generator_sha256'],'rule_sha256':probe['rule_sha256'],'witness':probe['witness'],'canonical_pairs_checked':canonical_fits},indent=2))
