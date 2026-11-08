import hashlib, importlib.util, json
from pathlib import Path
from math import isqrt
from reviewer_support import find_root, canonical_path, canonical_pairs
TASK='cde6cd1740f9'
root=find_root(Path('generators')/TASK/'generator.py')
out=root.parent/'checks/audit'/TASK
source=root/'generators'/TASK/'generator.py'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('audited_generator',source); gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
rows=[json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip() and json.loads(line).get('task_id')==TASK]
programs=[r['program_solution'] for r in rows]
rule_hashes={hashlib.sha256(' '.join(p.split()).encode()).hexdigest()[:12] for p in programs}
assert rule_hashes=={gen.RULE_HASH}
(out/'reference_rule.json').write_text(json.dumps({'task_id':TASK,'generator_sha256':sha,'rule_hashes':sorted(rule_hashes),'programs':programs},indent=2)+'\n')

def rival(grid):
    h,w=len(grid),len(grid[0]); result=[[0]*w for _ in range(h)]
    for c in range(w):
        values=[grid[r][c] for r in reversed(range(h)) if grid[r][c]]
        if not values: continue
        k=isqrt(len(values)); colors=list(dict.fromkeys(values))
        layers=colors+[colors[-1]]*(k-len(colors))
        for i,col in enumerate(layers):
            radius=k-i-1
            for x in range(c-radius,c+radius+1): result[h-i-1][x]=col
    return result

pairs=canonical_pairs(TASK,root=root,labeled_only=True)
unique=[]
for pair in pairs:
    if not any(p['input']==pair['input'] and p['output']==pair['output'] for p in unique): unique.append(pair)
assert len(unique)<=8
ordinary=[{'seed':73,'sample_index':i,'difficulty':'medium','overrides':{},'input':gen.generate(73,i,difficulty='medium')} for i in range(8)]
base=gen.generate(73,0,difficulty='medium',profile='16x13',structure='mixed_k3_k2',active_columns=1,primary_color=2,layout_shift=1)
col=6; colored=[r for r in range(len(base)) if base[r][col]]
handmade=[r[:] for r in base]
for idx,r in enumerate(colored): handmade[r][col]=5 if idx==0 else 2
records=[]
for label,items in [('canonical',unique),('ordinary',ordinary),('witness',[{'input':handmade,'origin':'handmade mutation of generated scattered rows','baseline_seed':73,'baseline_sample_index':0,'baseline_difficulty':'medium','baseline_overrides':{'profile':'16x13','structure':'mixed_k3_k2','active_columns':1,'primary_color':2,'layout_shift':1}}])]:
    (out/f'{label}-input.json').write_text(json.dumps({'inputs':[p['input'] for p in items]})+'\n')
    for item in items:
        rec={**item,'group':label,'rival_output':rival(item['input']),'self_check':gen.self_check(item['input']),'strict_canonical_like':gen.strict_canonical_like(item['input'])}
        records.append(rec)
(out/'probe-spec.json').write_text(json.dumps({'task_id':TASK,'generator_sha256':sha,'rule_hash':gen.RULE_HASH,'rival':'Ignore individual color counts; use total cell count for k and bottom-to-top distinct colors for layers, repeating final color to reach k layers.','records':records},indent=2)+'\n')
print(json.dumps({'generator_sha256':sha,'rule_hash':gen.RULE_HASH,'canonical_pair_count':len(pairs),'unique_canonical_pairs':len(unique),'ordinary_pairs':len(ordinary),'witness_self_check':gen.self_check(handmade),'witness_strict':gen.strict_canonical_like(handmade),'witness_axes':gen.observe_overrides(handmade),'programs':programs}))
