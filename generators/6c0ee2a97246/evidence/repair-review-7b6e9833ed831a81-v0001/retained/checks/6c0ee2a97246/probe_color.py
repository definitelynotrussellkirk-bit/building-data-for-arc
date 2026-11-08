"""Minimal accepted-lesson ambiguity; mixed per-grid palette overrides disclosed."""
import hashlib, json, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_path, find_root, load_selected_generator
from arc_repl.isolated_verifier import Limits, verify_candidate
assert find_root(__file__) == ROOT
TASK = '6c0ee2a97246'
gen, path, source_hash = load_selected_generator(TASK, root=ROOT)
row = next(json.loads(s) for s in canonical_path(ROOT).open() if json.loads(s).get('task_id') == TASK)
rule = row['program_solution']

def rival(g):
    out = [[0]*len(g[0]) for _ in g]
    for color in sorted({v for line in g for v in line} - {0}):
        cells = [(r,c) for r,line in enumerate(g) for c,v in enumerate(line) if v == color]
        rs,cs = zip(*cells)
        r0,r1,c0,c1 = min(rs),max(rs),min(cs),max(cs)
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):
                if r in (r0,r1) or c in (c0,c1): out[r][c] = color
    return out

RIVAL = '''(rule! (for/fold ((out (empty-grid (rows g) (cols g) 0)))
 ((color (in-list (sort (remove-duplicates (map obj-color (objects g 0))) <))))
 (let* ((cells (find-color g color)) (rs (map first cells)) (cs (map second cells))
        (r0 (apply min rs)) (r1 (apply max rs)) (c0 (apply min cs)) (c1 (apply max cs)))
 (paint-cells out (remove-duplicates (append
  (for/list ((c (in-range c0 (+ c1 1)))) (list r0 c))
  (for/list ((c (in-range c0 (+ c1 1)))) (list r1 c))
  (for/list ((r (in-range r0 (+ r1 1)))) (list r c0))
  (for/list ((r (in-range r0 (+ r1 1)))) (list r c1)))) color))))'''

pairs=[]
for index in range(1,6):
    overrides={'palette_mode':'distinct'} if index < 5 else {}
    g=gen.generate(11,index,difficulty='medium',**overrides)
    assert gen.self_check(g,meta={'overrides':overrides}) == []
    pairs.append({'input':g,'output':gen.rule_mirror(g)})
task={'train':pairs[:4],'test':pairs[4:]}
reasons=gen.lesson_identifiable(task['train'],task['test'][0])
assert reasons == []
assert all(rival(p['input']) == p['output'] for p in task['train'])
assert rival(task['test'][0]['input']) != task['test'][0]['output']
limits=Limits(wall_seconds=35,step_seconds=3,cpu_seconds=20,memory_mb=2048,max_pairs=8)
reports={name:verify_candidate(task,src,racket_path=os.environ['RACKET_PATH'],limits=limits)
         for name,src in [('reference',rule),('rival',RIVAL)]}
report={'task_id':TASK,'assignment':'review-7b6e9833ed831a81','generator_sha256':source_hash,
 'rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'seed':11,'difficulty':'medium','demo_indices':[1,2,3,4],'query_index':5,
 'demo_overrides':{'palette_mode':'distinct'},'query_overrides':{},
 'lesson_identifiable_reasons':reasons,'rival_rule':RIVAL,'protected_reports':reports,
 'scope':'Accepted recombined lesson with per-grid palette overrides; NOT a default shared-axis export failure.',
 'finding':'lesson_identifiable accepts demos that do not distinguish grouping by component from grouping by color, although query repeats colors.'}
witness={**task,'rival_query_output':rival(task['test'][0]['input'])}
(HERE/'color_witness.json').write_text(json.dumps(witness,indent=2)+'\n')
(HERE/'color_result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'gate':reasons,'generator_sha256':source_hash,'native':{k:{'status':v['status'],'hidden_exact':v.get('hidden_exact'),'error':v.get('error')} for k,v in reports.items()}},indent=2))
assert all(v['status']=='pass' for v in reports.values())
assert reports['reference']['hidden_exact'] is True and reports['rival']['hidden_exact'] is False
assert reports['rival']['test_outputs'] == [witness['rival_query_output']]
