"""One ordinary easy lesson against three executable routing rivals."""
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator

ROOT=find_root(__file__)
TASK='40ad7195c775'
OUT=Path(__file__).resolve().parent
gen,path,sha=load_selected_generator(TASK,root=ROOT)
expected='d5bec27143b675aa8bd44e42eb13e477571d75781ac0ce0035af3fe011dfa95c'
assert sha==expected
prototype_path=ROOT/'generators'/TASK/'workspace/parametric/prototype.py'
spec=importlib.util.spec_from_file_location('peer_waypoint_retained',prototype_path)
proto=importlib.util.module_from_spec(spec)
spec.loader.exec_module(proto)
canonical=proto.program_for('middle')
site='                                  stripe-rows))'
assert canonical.count(site)==1
cap=canonical.replace(site,'                                  (if (> (length stripe-rows) 3) (list (first stripe-rows) (second stripe-rows) (nth stripe-rows 2)) stripe-rows)))',1)
programs={'canonical':canonical,'left_waypoint':proto.program_for('left'),
          'right_waypoint':proto.program_for('right'),'three_crossing_cap':cap}
pairs=[]
calls=0
with RacketBridge(timeout=10.0,startup_timeout=30.0) as bridge:
    identity=bridge.runtime_identity
    assert identity['backend']=='racket' and identity['protected'] is True
    wrapped={name:wrap_rule(source) for name,source in programs.items()}
    for index in range(7):
        grid=gen.generate(1,index,difficulty='easy')
        assert gen.self_check(grid)==[]
        literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
        outputs={}
        for name,source in wrapped.items():
            outputs[name]=bridge.eval_text(f'({source} {literal})')
            calls+=1
        assert outputs['canonical']==gen.rule_mirror(grid)
        facts=gen._analysis(grid)['facts']
        pairs.append({'sample_index':index,'split':'train' if index<3 else 'test',
                      'input':grid,'output':outputs.pop('canonical'),'rival_outputs':outputs,
                      'stripe_count':facts['stripe_count'],'orientation':facts['orientation_name']})
train=[{'input':p['input'],'output':p['output']} for p in pairs[:3]]
rivals={}
for name in programs:
    if name=='canonical':continue
    demos=[p['sample_index'] for p in pairs[:3] if p['rival_outputs'][name]!=p['output']]
    queries=[p['sample_index'] for p in pairs[3:] if p['rival_outputs'][name]!=p['output']]
    rivals[name]={'fits_all_demos':not demos,'demo_disagreement_indices':demos,'query_disagreement_indices':queries}
report={'schema':'40ad7195c775-bounded-peer-review-v1','status':'finding' if any(r['fits_all_demos'] and r['query_disagreement_indices'] for r in rivals.values()) else 'bounded_no_finding',
        'task_id':TASK,'generator_sha256':sha,'rule_hash':gen.RULE_HASH,'generator_version':gen.VERSION,
        'canonical_program_sha256':hashlib.sha256(canonical.encode()).hexdigest(),
        'seed':1,'difficulty':'easy','demos':3,'queries':4,'racket_evaluations':calls,
        'runtime_identity':identity,'programs':programs,'rivals':rivals,'pairs':pairs,
        'existing_gate_findings':[gen.lesson_identifiable(train,{'input':p['input'],'output':p['output']}) for p in pairs[3:]],
        'limits':'One ordinary seed-1 easy three-demo/four-query lesson and three rivals. No production repair, full battery, owner acceptance, or universal uniqueness claim.'}
(OUT/'peer-report.json').write_text(json.dumps(report,sort_keys=True)+'\n')
print(json.dumps({k:report[k] for k in ('status','racket_evaluations','rivals','existing_gate_findings')},indent=2))
