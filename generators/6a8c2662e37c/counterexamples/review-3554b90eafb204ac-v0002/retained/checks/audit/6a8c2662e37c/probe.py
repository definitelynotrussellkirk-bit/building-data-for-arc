"""Findings-only audit: exact control observations and sampled teaching rival."""
import importlib.util
import hashlib
import json
from pathlib import Path
from collections import Counter
from copy import deepcopy
from reviewer_support import canonical_pairs, find_root
from arcpuzzles import Catalog

root = find_root('.')
task = '6a8c2662e37c'
out = root.parent / 'checks/audit' / task
source = root / 'generators' / task / 'generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
catalog = Catalog(root)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def orientation(grid):
    return 'vertical' if any(all(row[c] == 8 for row in grid) for c in range(len(grid[0]))) else 'horizontal'

def vertical_only(grid):
    output = deepcopy(grid)
    walls = [c for c in range(len(grid[0])) if all(row[c] == 8 for row in grid)]
    if not walls:
        return output
    wall = walls[0]
    objects = [(r,c,color) for r,row in enumerate(grid) for c,color in enumerate(row) if color not in (0,8)]
    left_side = max(c for r,c,color in objects) < wall
    for r,c,color in objects:
        for cc in (range(c,wall) if left_side else range(wall+1,c+1)):
            if output[r][cc] == 0:
                output[r][cc] = color
    return output

report = {'task_id':task,'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'generator_version':gen.VERSION,'catalog_rule_hash':catalog.describe(task)['rule_hash'],
          'scope':'32 direct medium draws seed17 indices0..31 for exact axes; 32 public production lessons seed17 medium4demos1query',
          'axis_rows':[]}
for i in range(32):
    controls = {'palette_size':5, 'n_distinct_colors':5, 'palette_kind':'warm', 'texture':'warm'}
    grid = gen.generate(17,i,difficulty='medium',**controls)
    alternate = gen.generate(17,i,difficulty='medium',**{**controls,'palette_kind':'cool','texture':'cool'})
    colors = sorted({cell for row in grid for cell in row})
    report['axis_rows'].append({'seed':17,'sample_index':i,'difficulty':'medium','overrides':controls,
                               'observed_colors':colors,'observed_n_distinct_colors':len(colors),
                               'input_sha256':digest(grid),'self_check':gen.self_check(grid),
                               'warm_equals_cool':grid==alternate})
    if len(colors)!=5 and 'axis_counterexample' not in report:
        applied = catalog.apply(task,[grid])
        report['axis_counterexample'] = {**report['axis_rows'][-1], 'input':grid,'racket':applied,
                                        'alternate_overrides':{**controls,'palette_kind':'cool','texture':'cool'},
                                        'alternate_input':alternate,'vertical_only_rival_output':vertical_only(grid)}
canonical = canonical_pairs(task,root=root,labeled_only=True)
report['vertical_only_canonical_fit'] = {'fits':sum(vertical_only(p['input'])==p['output'] for p in canonical),'pairs':len(canonical)}
episodes = catalog.generate(task,count=32,seed=17,difficulty='medium',n_train=4,n_test=1,allow_unapproved=True,timeout=180)
report['production_counts'] = {'episodes':len(episodes),'pairs':sum(len(e['train'])+len(e['test'])for e in episodes),
                             'orientation_sequences':Counter(''.join('V' if orientation(p['input'])=='vertical' else 'H' for p in e['train']+e['test'])for e in episodes),
                             'self_check_errors':sum(bool(gen.self_check(p['input']))for e in episodes for p in e['train']+e['test']),
                             'unique_inputs':len({digest(p['input'])for e in episodes for p in e['train']+e['test']})}
report['ambiguous_episode_indices'] = [i for i,e in enumerate(episodes) if all(vertical_only(p['input'])==p['output'] for p in e['train']) and any(vertical_only(p['input'])!=p['output'] for p in e['test'])]
for i,e in enumerate(episodes):
    if all(vertical_only(p['input'])==p['output'] for p in e['train']) and any(vertical_only(p['input'])!=p['output']for p in e['test']):
        query = e['test'][0]
        report['production_counterexample'] = {'episode_index':i,'instance':e,'rival':'vertical_only_wall_shadow',
                 'rival_fits_all_demos':True,'rival_query_output':vertical_only(query['input']),
                 'reference_query_output':query['output'],'self_check':[gen.self_check(p['input'])for p in e['train']+e['test']],
                 'query_input_sha256':digest(query['input'])}
        break
report['axis_counts'] = {'n_distinct_color_mismatches':sum(r['observed_n_distinct_colors']!=5 for r in report['axis_rows']),
                        'warm_cool_identical':sum(r['warm_equals_cool']for r in report['axis_rows'])}
(out/'evidence-final.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'generator_sha256':report['generator_sha256'],'rule_hash':report['catalog_rule_hash'],
                  'axis_counts':report['axis_counts'],'production_counts':report['production_counts'],
                  'ambiguous_episode_indices':report['ambiguous_episode_indices'],'production_counterexample_index':report.get('production_counterexample',{}).get('episode_index')}))
