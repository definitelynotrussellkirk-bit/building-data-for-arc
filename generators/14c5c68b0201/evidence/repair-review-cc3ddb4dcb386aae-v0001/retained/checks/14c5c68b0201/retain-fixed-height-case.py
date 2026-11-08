"""Replay the retained pre-repair two-demo fixed-height ambiguity."""
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

base=Path(__file__).resolve().parent
examples=json.loads((base/'self-audit/examples/private.json').read_text())['episodes']
ep=next(row['episode'] for row in examples if row['episode']['settings']=={'tiling_axes':'both'})
source=ep['program_solution']
site='(sh (+ 1 (- sr2 sr1)))'
assert source.count(site)==1
rival=source.replace(site,'(sh 3)',1)
rows=[]
with RacketBridge(timeout=10.0,startup_timeout=30.0) as bridge:
    identity=bridge.runtime_identity
    assert identity['protected'] is True
    for split,pairs in (('train',ep['train']),('test',ep['test'][:1])):
        for index,pair in enumerate(pairs):
            literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in pair['input'])+')'
            actual=bridge.eval_text(f'({wrap_rule(source)} {literal})')
            alternate=bridge.eval_text(f'({wrap_rule(rival)} {literal})')
            assert actual==pair['output']
            rows.append({'split':split,'index':index,'input':pair['input'],'output':actual,
                         'rival_output':alternate,'matches':actual==alternate})
assert all(row['matches'] for row in rows if row['split']=='train')
assert all(not row['matches'] for row in rows if row['split']=='test')
report={'schema':'14c5c68b0201-fixed-height-counterexample-v1','status':'confirmed_pre_repair_teaching_gap',
        'source_episode':'self-audit/examples/private.json','canonical_program':source,'rival_program':rival,
        'canonical_program_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'generator_sha256':hashlib.sha256(Path('generators/14c5c68b0201/generator.py').read_bytes()).hexdigest(),
        'runtime_identity':identity,'protected_racket_evaluations':6,'cases':rows,
        'limits':'Retained original minimum-demo lesson, before the native teaching repair. Does not describe the final repaired sampler.'}
(base/'fixed-height-before.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':report['status'],'demos_matched':2,'query_disagreed':True,'racket_evaluations':6}))
