"""Bounded peer probe: rectangular rooms do not teach geodesic distance."""
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = '78c2e20ad0f8'
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
generator, source, source_hash = load_selected_generator(TASK, root=ROOT)
with (ROOT/'shared/data/canonical/puzzles.jsonl').open() as handle:
    canonical = next(row for row in map(json.loads,handle) if row.get('task_id') == TASK)
program = canonical['program_solution']
old = '(define (distance-within-room grid room start target) (let ((walls (filter (lambda (p) (not (member? p room))) (grid-positions grid)))) (geo-distance grid start target walls)))'
new = '(define (distance-within-room grid room start target) (+ (abs (- (first start) (first target))) (abs (- (second start) (second target)))))'
assert program.count(old) == 1
rival = program.replace(old,new,1)
recipes = [{'seed':71+i,'sample_index':i} for i in range(3)]
demos = [generator.generate(**recipe) for recipe in recipes]
query = [[8,8,8,8,8], [8,2,8,0,8], [8,0,8,0,8], [8,3,0,0,8], [8,8,8,8,8]]
grids = demos + [query]
bridge = RacketBridge()
try:
    identity = bridge.runtime_identity
    assert identity['backend'] == 'racket' and identity['protected'] is True
    outputs = []
    for rule in (program,rival):
        wrapped = wrap_rule(rule)
        labels=[]
        for grid in grids:
            literal = "'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
            labels.append(bridge.eval_text(f'({wrapped} {literal})'))
        outputs.append(labels)
finally:
    bridge.close()
fits = [a==b for a,b in zip(outputs[0][:3],outputs[1][:3])]
diff = [[r,c,outputs[0][-1][r][c],outputs[1][-1][r][c]] for r in range(5) for c in range(5) if outputs[0][-1][r][c]!=outputs[1][-1][r][c]]
report = {'schema':'78c2e20ad0f8-bounded-manhattan-rival-v1','task_id':TASK,
          'generator_path':str(source.relative_to(ROOT)), 'generator_sha256':source_hash,
          'program_sha256':hashlib.sha256(program.encode()).hexdigest(),
          'rival_sha256':hashlib.sha256(rival.encode()).hexdigest(),
          'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'program':program,'rival_program':rival,
          'runtime':{k:v for k,v in identity.items() if k in {'schema','backend','protected','binary_sha256','prelude_sha256','bridge_sha256','boot_script_sha256','candidate_symbol_policy_sha256'}},
          'demo_recipes':recipes,'demos':[{'input':g,'output':a,'rival_output':b} for g,a,b in zip(demos,outputs[0],outputs[1])],
          'query':{'input':query,'output':outputs[0][-1],'rival_output':outputs[1][-1],
                   'self_check':generator.self_check(query), 'construction':'authored nonrectangular connected room; admitted by current self_check, not emitted by current rectangular-room sampler'},
          'rival_fits_each_demo':fits,'query_differences_rc_authority_rival':diff,
          'finding':all(fits) and bool(diff) and not generator.self_check(query),
          'limits':['Three generated demonstrations and one authored query; no broad census.',
                    'Query is a canonical-language/self-check witness, not a generated query.',
                    'This finding does not claim a mislabeled generated input or an existing generated episode failure.']}
(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('generator_sha256','program_sha256','rival_sha256','probe_sha256','rival_fits_each_demo','query_differences_rc_authority_rival','finding')},indent=2))
assert report['finding']
