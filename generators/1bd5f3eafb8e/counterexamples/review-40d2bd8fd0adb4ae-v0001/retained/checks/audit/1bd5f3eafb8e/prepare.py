from pathlib import Path
import hashlib, importlib.util, json
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = '1bd5f3eafb8e'
HERE = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
source = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
catalog = Catalog(ROOT)
description = catalog.get(TASK)
pairs = canonical_pairs(TASK, root=ROOT)
(HERE / 'catalog.json').write_text(json.dumps(description, indent=2)+'\n')
(HERE / 'canonical-pairs.json').write_text(json.dumps(pairs, indent=2)+'\n')
rule = description['variants'][0]['program_solution']
(HERE / 'canonical-rule.rkt').write_text(rule+'\n')
print(rule)
print(json.dumps({'pairs':len(pairs), 'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'rule_hash': description['rule_hash'], 'raw_rule_sha256': hashlib.sha256(rule.encode()).hexdigest(), 'canonical_pair_shapes': [[len(p['input']),len(p['input'][0]),len(p['output']),len(p['output'][0])] for p in pairs]},indent=2))

def rival(g):
    h,w=len(g),len(g[0])
    fives=[(r,c) for r,row in enumerate(g) for c,x in enumerate(row) if x==5]
    fr,fc=fives[0]
    horizontal=fives[0][1]==fives[1][1]
    if horizontal:
        cropped=g[:h//2] if fr<h//2 else g[h//2:]
    else:
        cropped=[row[:w//2] if fc<w//2 else row[w//2:] for row in g]
    return [[1 if x==1 else 8 for x in row] for row in cropped]

cases=[]
for p in pairs:
    cases.append({'name':f"canonical-{p['split']}-{p['pair_index']}", 'kind':'canonical', 'variant':p['variant'], 'input':p['input'], 'canonical_expected':p['output'], 'self_check':gen.self_check(p['input']), 'rival_output':rival(p['input'])})
for anchor in (False,True):
    overrides={'grid_h':10,'grid_w':10,'ones_pattern':'scattered','ones_density':0.25,'marker_orientation':'horizontal_split','marker_side':'bottom_or_right','anchor_corner':anchor}
    grid=gen.generate(17,0,difficulty='easy',**overrides)
    cases.append({'name':f'generated-anchor-{anchor}', 'kind':'generated', 'seed':17, 'sample_index':0, 'difficulty':'easy', 'overrides':overrides, 'input':grid, 'self_check':gen.self_check(grid, difficulty='easy', meta=overrides), 'rival_output':rival(grid)})
payload={'inputs':[c['input'] for c in cases]}
(HERE / 'input.json').write_text(json.dumps(payload,indent=2)+'\n')
evidence={'task_id':TASK, 'audited_generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'catalog_generator_sha256':description['generator_sha256'], 'catalog_rule_hash':description['rule_hash'], 'raw_rule_sha256':hashlib.sha256(rule.encode()).hexdigest(), 'retained_rule_file_sha256':hashlib.sha256((HERE/'canonical-rule.rkt').read_bytes()).hexdigest(), 'rival':'perform marker-directed half crop, then set all non-1 cells to 8', 'cases':cases}
(HERE / 'probe.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps({'public_apply_input_count':len(cases),'self_checks':[c['self_check'] for c in cases]},indent=2))
