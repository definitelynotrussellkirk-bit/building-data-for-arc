from __future__ import annotations
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root
import hashlib, json

ROOT=Path.cwd()
OUT=ROOT.parent/'checks'/'audits'
OUT.mkdir(parents=True,exist_ok=True)

def load(task):
    p=ROOT/'generators'/task/'generator.py'
    s=spec_from_file_location('audit_'+task,p); m=module_from_spec(s); assert s and s.loader; s.loader.exec_module(m)
    return m,p

# Audit 6c: exact transform override becomes unobservable on a symmetric scene.
task='6c5bf76aa982'; m,p=load(task)
settings={'seed':64,'sample_index':81,'difficulty':'medium','overrides':{'scene_profile':'balanced_small','transform':1}}
g1=m.generate(settings['seed'],settings['sample_index'],difficulty=settings['difficulty'],**settings['overrides'])
g0=m.generate(settings['seed'],settings['sample_index'],difficulty=settings['difficulty'],scene_profile='balanced_small',transform=0)
r6={
 'schema':'adversarial_audit_evidence/1','task_id':task,'finding':'exact_transform_override_not_observable',
 'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'settings':settings,
 'observed':m.observe_overrides(g1),'self_check':m.self_check(g1),
 'transform_0_grid_equals_transform_1_grid':g0==g1,'grid':g1,
 'requested_transform':1,'observed_transform':m.observe_overrides(g1)['transform'],
 'reproduced':m.self_check(g1)==[] and m.observe_overrides(g1)['transform']!=1 and g0==g1,
}
(OUT/'6c5bf76aa982-transform-override.json').write_text(json.dumps(r6,indent=2)+'\n')

# Audit 5d: actual generated lesson where rightmost-panel shortcut fits every demo but fails query.
task='5d1263287a4f'; m,p=load(task)
canon=canonical_pairs(task,root=ROOT)
def rightmost(grid):
    third=len(grid[0])//3
    return [list(row[2*third:]) for row in grid]
canonical_fit=[rightmost(pair['input'])==pair['output'] for pair in canon]
episodes=Catalog(ROOT).generate(task,count=200,seed=20261006,difficulty='medium')
found=None
for episode in episodes:
    train_fit=[rightmost(pair['input'])==pair['output'] for pair in episode['train']]
    for qi,pair in enumerate(episode['test']):
        if all(train_fit) and rightmost(pair['input'])!=pair['output']:
            found=(episode,qi,train_fit)
            break
    if found: break
assert found is not None
episode,qi,train_fit=found
train_entries=[]
for pair in episode['train']:
    train_entries.append({
      'layout':m.observe_overrides(pair['input'])['panel_layout'],
      'self_check':m.self_check(pair['input']),
      'input':pair['input'],'authoritative_output':pair['output'],
      'rightmost_output':rightmost(pair['input']),
      'shortcut_fits':rightmost(pair['input'])==pair['output'],
    })
q=episode['test'][qi]
query_entry={
  'layout':m.observe_overrides(q['input'])['panel_layout'],
  'self_check':m.self_check(q['input']),
  'input':q['input'],'authoritative_output':q['output'],
  'rightmost_output':rightmost(q['input']),
  'shortcut_fits':rightmost(q['input'])==q['output'],
}
r5={
 'schema':'adversarial_audit_evidence/1','task_id':task,
 'finding':'rightmost_panel_shortcut_survives_generated_demonstrations',
 'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'catalog_seed':20261006,'catalog_count_scanned':200,'difficulty':'medium',
 'episode_index':episode['episode_index'],'sample_indices':episode['sample_indices'],
 'sampling':episode['sampling'],'executed_rule_hash':episode['executed_rule_hash'],
 'canonical_pair_count':len(canon),'rightmost_fits_all_canonical_pairs':all(canonical_fit),
 'canonical_fit_by_pair':canonical_fit,'train':train_entries,'query_index':qi,'query':query_entry,
 'lesson_check':episode.get('lesson_check'),
 'reproduced':all(e['shortcut_fits'] for e in train_entries) and not query_entry['shortcut_fits'] and all(e['self_check']==[] for e in train_entries+[query_entry]),
}
(OUT/'5d1263287a4f-rightmost-shortcut.json').write_text(json.dumps(r5,indent=2)+'\n')
print(json.dumps({'6c':{k:r6[k] for k in ('generator_sha256','requested_transform','observed_transform','transform_0_grid_equals_transform_1_grid','reproduced')},'5d':{'generator_sha256':r5['generator_sha256'],'episode_index':r5['episode_index'],'sample_indices':r5['sample_indices'],'train_layouts':[e['layout'] for e in train_entries],'query_layout':query_entry['layout'],'canonical_fit':r5['rightmost_fits_all_canonical_pairs'],'reproduced':r5['reproduced']}},indent=2))
