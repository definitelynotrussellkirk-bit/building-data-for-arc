"""Bounded marker-submatrix learnability and declared palette-control probe."""
from pathlib import Path
import hashlib
import json

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK='3f600d3093b8'
ROOT=find_root(__file__)
GEN,path,sha=load_selected_generator(TASK,root=ROOT)
assert sha=='1e6369fd9067dae9de338776d8498664c307be6545170859093866b35fb6a8f2'
programs={json.loads(line)['program_solution'] for line in canonical_path(ROOT).read_text().splitlines()
          if line.strip() and json.loads(line).get('task_id')==TASK}
assert len(programs)==1
canonical=programs.pop()
assert canonical.count('(range 1 (rows g))')==1
reverse_rows=canonical.replace('(range 1 (rows g))','(reverse (range 1 (rows g)))',1)
transpose='''(rule! (let* ((rs (filter (lambda (r) (= (at g r 0) 8)) (range 1 (rows g))))
                             (cs (filter (lambda (c) (= (at g 0 c) 8)) (range 1 (cols g)))))
  (if (or (empty? rs) (empty? cs)) (list (list 0))
      (for/list ([c (in-list cs)]) (for/list ([r (in-list rs)]) (at g r c))))))'''
bounding_box='''(rule! (let* ((rs (filter (lambda (r) (= (at g r 0) 8)) (range 1 (rows g))))
                                (cs (filter (lambda (c) (= (at g 0 c) 8)) (range 1 (cols g)))))
  (if (or (empty? rs) (empty? cs)) (list (list 0))
      (for/list ([r (in-list (range (first rs) (+ 1 (last rs)))))])
        (for/list ([c (in-list (range (first cs) (+ 1 (last cs)))))]) (at g r c))))))'''
# Keep bindings in the standard native for/list grammar.
bounding_box=bounding_box.replace(')))))])', '))))])')
rivals={'reverse_marked_rows':reverse_rows,'transpose_selected_matrix':transpose,'crop_markers_bounding_box':bounding_box}
pairs=[]
with RacketBridge(timeout=10.0,startup_timeout=30.0) as bridge:
    identity=bridge.runtime_identity
    assert identity['backend']=='racket' and identity['protected'] is True
    for index in range(7):
        grid=GEN.generate(0,index,difficulty='medium')
        assert GEN.self_check(grid)==[]
        rows=[r for r in range(1,len(grid)) if grid[r][0]==8]
        cols=[c for c in range(1,len(grid[0])) if grid[0][c]==8]
        expected=[[grid[r][c] for c in cols] for r in rows]
        literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
        def execute(source):
            return bridge.eval_text(f'({wrap_rule(source)} {literal})')
        answer=execute(canonical)
        assert answer==expected
        other={name:execute(source) for name,source in rivals.items()}
        pairs.append({'sample_index':index,'split':'train' if index<3 else 'test','input':grid,
                      'output':answer,'marked_rows':rows,'marked_columns':cols,'rival_outputs':other})
rows=[]
for name in rivals:
    demo_disagreements=[p['sample_index'] for p in pairs[:3] if p['rival_outputs'][name]!=p['output']]
    query_disagreements=[p['sample_index'] for p in pairs[3:] if p['rival_outputs'][name]!=p['output']]
    rows.append({'name':name,'fits_all_demos':not demo_disagreements,'demo_disagreements':demo_disagreements,
                 'query_disagreements':query_disagreements,'ambiguity':not demo_disagreements and bool(query_disagreements)})
controls=[]
baseline=pairs[0]['input']
for name in ('palette_size','n_distinct_colors'):
    grid=GEN.generate(0,0,difficulty='medium',**{name:2})
    colors=sorted({v for row in grid[1:] for v in row[1:] if v not in (0,8)})
    controls.append({'override':{name:2},'observed_interior_colors':colors,'observed_count':len(colors),
                     'same_input_as_unoverridden':grid==baseline,'self_check':GEN.self_check(grid),
                     'violates_requested_count':len(colors)!=2,'input':grid})
report={'schema':'3f600d3093b8-bounded-peer-review-v1','task_id':TASK,'status':'bounded_check_completed',
        'seed':0,'demos':3,'queries':4,'difficulty':'medium','generator_sha256':sha,'rule_hash':'3a689bf821bc',
        'canonical_program_sha256':hashlib.sha256(canonical.encode()).hexdigest(),'canonical_program':canonical,
        'rival_programs':rivals,'rivals':rows,'pairs':pairs,'protected_racket_evaluations':28,'runtime_identity':identity,
        'ambiguous_lesson_found':any(r['ambiguity'] for r in rows),'palette_control_findings':controls,
        'source_cause':'generate() requests a fixed four-color palette with label palette and does not read palette_size or n_distinct_colors.',
        'limits':'One ordinary three-demo/four-query lesson and three finite rivals; two palette override calls. No full battery, production repair, approval or training change.'}
target=Path(__file__).with_name('peer-report.json')
target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':report['status'],'protected_racket_evaluations':28,'rivals':rows,
                  'palette_controls':[{k:v for k,v in row.items() if k!='input'} for row in controls]}))
