"""Directed family-choice search; materialize only four consecutive inputs."""
from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path.cwd(); OUT=Path(__file__).resolve().parent
source=ROOT/'generators/0b8ba9bb3c63/generator.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='06b6e79989cf7d2b850ff4aa327930c33cb603c3e3089c000662fa4a6420f965'
spec=importlib.util.spec_from_file_location('audit_lesson_beam',source)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
choices=('public','public','generalized','generalized','generalized')
chosen=None
for seed in range(1,129):
    family=[g.gen_ctx(seed=seed,sample_index=i,version=g.VERSION,task_id=g.TASK_ID,
                     difficulty=None,overrides={}).draw_choice('scene_family',choices)
            for i in range(4)]
    if family==['public','public','public','generalized']:
        chosen=seed;break
assert chosen is not None
def rival(grid):
    objects=g._components(grid);cyan=next(o for o in objects if o['color']==8)
    blockers=[o for o in objects if o['color'] not in (2,8)]
    output=g._paint_cross(grid,cyan,[o for o in blockers if o['color']==1])
    for obj in blockers:
        for r,c in obj['cells']:output[r][c]=obj['color']
    return output
cases=[]
for i in range(4):
    grid=g.generate(chosen,i);assert not g.self_check(grid)
    cases.append({'seed':chosen,'sample_index':i,'difficulty':None,'overrides':{},
                  'input':grid,'family':g.canonical_profile_signature(grid),
                  'mirror_output':g.rule_mirror(grid),'rival_output':rival(grid),
                  'validator_problems':[]})
assert all(c['mirror_output']==c['rival_output'] for c in cases[:3])
assert cases[3]['mirror_output']!=cases[3]['rival_output']
report={'schema':'directed-ordinary-lesson-audit-v1','task_id':g.TASK_ID,
        'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_selection':'Generator family choice predicted with its gen_ctx; no full scene generated during seed search. This is adversarial selection, not a prevalence estimate.',
        'seed_search_range':[1,chosen],'family_choices_tested':chosen*4,
        'generated_draws':4,'seed':chosen,'sample_indices':[0,1,2,3],
        'n_demos':3,'n_queries':1,'policy':'three consecutive ordinary demos then consecutive query',
        'cases':cases,'finding':'Only-blue-clips rival survives public demos and differs on ordinary generalized query.'}
(OUT/'lesson-inputs.json').write_text(json.dumps([c['input'] for c in cases])+'\n')
(OUT/'lesson.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('seed','sample_indices','seed_search_range','family_choices_tested','generated_draws','finding')}))
