"""Reproduce three exact final-source generated inputs; obtain labels via public apply.
Run from packet root with:
  python3 run_with_racket.py python3 ../checks/final-witnesses/reproduce.py
This authoring probe must not be imported during a visible-only solve.
"""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path('generators/312fb4bdff00/workspace').resolve()))
from review_probe import load_generator,oracle,canonical_pairs

gen=load_generator(); out=Path('../checks/final-witnesses')
cases=[('translated_unique',0,2,{'panel_s':3,'n_cands':1,'shape_k':3,'match_count':1,'target_color':4}),
       ('first_match_precedence',0,0,{'panel_s':3,'n_cands':2,'shape_k':3,'match_count':2,'target_color':4}),
       ('absent_equal_count',0,1,{'panel_s':3,'n_cands':2,'shape_k':3,'match_count':0,'target_color':4})]
rows=[]
for name,seed,index,overrides in cases:
 grid=gen.generate(seed,index,difficulty='medium',**overrides)
 assert not gen.self_check(grid)
 rows.append({'name':name,'seed':seed,'sample_index':index,'difficulty':'medium',
              'overrides':overrides,'input':grid,'independent_oracle_output':oracle(grid),
              'rival_outputs':{name:fn(grid) for name,fn in gen.CANONICAL_SHORTCUTS.items()},
              'observed_overrides':gen.observe_overrides(grid)})
report={'task_id':gen.TASK_ID,'generator_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
        'rule_hash':gen.RULE_HASH,'cases':rows,
        'canonical_fit':{name:{'matched':sum(fn(p['input'])==p['output'] for p in canonical_pairs()),'total':len(canonical_pairs())}
                         for name,fn in gen.CANONICAL_SHORTCUTS.items()},
        'label_status':'independent predictions pending supported Racket apply receipt'}
(out/'inputs.json').write_text(json.dumps([r['input'] for r in rows],indent=2)+'\n')
(out/'predictions.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
