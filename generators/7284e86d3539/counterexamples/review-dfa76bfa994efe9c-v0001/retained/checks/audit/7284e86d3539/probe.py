"""Bounded findings-only audit; uses generator and public authority CLI separately."""
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT.parent / 'checks/audit/7284e86d3539'
SOURCE = ROOT / 'generators/7284e86d3539/generator.py'
spec = importlib.util.spec_from_file_location('audit_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
canonical = json.loads((OUT / 'canonical.json').read_text())

def rival(g):
    """Vertical-bar gallery shortcut, deliberately ignores general component geometry."""
    cols = [c for c in range(len(g[0])) if any(row[c] not in (0, 5) for row in g)]
    blocks = []
    for c in cols:
        points = [(r, g[r][c]) for r in range(len(g)) if g[r][c] not in (0, 5)]
        color = points[0][1]
        # Generator gray flag always appears at the lower-right bar cell.
        mark = any(c + 1 < len(g[0]) and g[r][c+1] == 5 for r, _ in points)
        blocks.append([[color] + ([0] if mark else []), [color] + ([color] if mark else [])])
    w = sum(len(block[0]) for block in blocks)
    return [[0]*w, sum([block[0] for block in blocks], []), sum([block[1] for block in blocks], [])]

records = []
for difficulty in ('easy', 'medium', 'hard'):
    for seed in range(4):
        g = gen.generate(seed, 0, difficulty=difficulty)
        records.append({'kind':'generated', 'seed':seed, 'sample_index':0,
                        'difficulty':difficulty, 'overrides':{}, 'input':g,
                        'self_check':gen.self_check(g, difficulty=difficulty),
                        'domain_membership':'normal selected generator output',
                        'rival_output':rival(g)})
# Distinct canonical witness has top-row occupancy and repeated disconnected color.
pair = canonical['variants'][0]['train'][2]
records.append({'kind':'canonical_witness', 'variant':0, 'split':'train', 'pair_index':2,
                'seed':None,'sample_index':None,'overrides':None,
                'input':pair['input'], 'expected_canonical_output':pair['output'],
                'self_check':gen.self_check(pair['input']),
                'domain_membership':'canonical task domain; not normal generator support',
                'rival_output':rival(pair['input'])})
(OUT/'input.json').write_text(json.dumps([r['input'] for r in records], indent=2)+'\n')
(OUT/'cases.json').write_text(json.dumps({'task_id':gen.TASK_ID,
    'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'selected_rule_hash':canonical['rule_hash'], 'rival_claim':'Fits generated samples only; not asserted to fit canonical pairs.',
    'cases':records}, indent=2)+'\n')

baseline = gen.generate(0, 0, difficulty='medium')
checks=[]
for axis, values in {'palette_kind':['warm','cool','broad','primary'],
                     'anchor_corner':[False,True], 'asymmetry_force':[False,True],
                     'palette_size':[2,5], 'n_distinct_colors':[2,5],
                     'texture':['warm','cool','broad','primary']}.items():
    for value in values:
        g=gen.generate(0,0,difficulty='medium',**{axis:value})
        checks.append({'seed':0,'sample_index':0,'difficulty':'medium','overrides':{axis:value},
                       'identical_to_baseline':g==baseline,'self_check':gen.self_check(g),
                       'input_sha256':hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest()})
(OUT/'overrides.json').write_text(json.dumps({'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'baseline':{'seed':0,'sample_index':0,'difficulty':'medium','overrides':{},'input':baseline},
    'checks':checks},indent=2)+'\n')
print(json.dumps({'normal_cases':len(records)-1,'all_selfchecks_pass':all(not r['self_check'] for r in records),
                  'override_cases':len(checks),'all_identical':all(r['identical_to_baseline'] for r in checks)}))
