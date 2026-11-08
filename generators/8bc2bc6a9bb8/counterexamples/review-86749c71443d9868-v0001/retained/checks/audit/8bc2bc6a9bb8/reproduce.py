#!/usr/bin/env python3
"""Fresh bounded footprint-vs-cell-count audit; no target source edits."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'repo/shared/runtime'))
from reviewer_support import find_root,canonical_pairs,load_selected_generator,normalize_grid
from puzzle_generators.rule_wrap import wrap_rule
from arc_repl.racket_bridge import RacketBridge
ROOT=find_root(__file__)
# Standard namespace mapping of repository tools to their expected runtime name.
import importlib.machinery, importlib.util
_spec=importlib.machinery.ModuleSpec('scripts',loader=None,is_package=True)
_spec.submodule_search_locations=[str(ROOT/'shared/tools')]
sys.modules['scripts']=importlib.util.module_from_spec(_spec)
TASK='8bc2bc6a9bb8'
EXPECTED='a4628bb6520d8d4805b5a99b699598c00ce1816fc6f4f20fffbeb8b3fb6f01a3'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def rival(grid):
    # Reuse only target's component parser, never its size-ordering or labels.
    items=sorted(GEN._components(grid),key=lambda o:(-o['height']*o['width'],-o['size'],o['bbox']))
    palette=[c for c in grid[0] if c]
    h=max(o['height'] for o in items);w=sum(o['width'] for o in items)+len(items)-1
    out=[[0]*w for _ in range(h)];x=0
    for obj,color in zip(items,palette):
        for r,c in obj['normalized']:out[h-obj['height']+r][x+c]=color
        x+=obj['width']+1
    return out

def main():
    global GEN
    GEN,source,source_hash=load_selected_generator(TASK,root=ROOT)
    assert source_hash==EXPECTED
    pairs=canonical_pairs(TASK,root=ROOT,labeled_only=True)
    rules=[]
    for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open():
        row=json.loads(line)
        if row.get('task_id')==TASK:rules.append(row['program_solution'])
    assert len(set(rules))==1
    program=rules[0];wrapped=wrap_rule(program)
    witness=[[0]*12 for _ in range(8)]
    for c,color in ((0,2),(2,3),(4,4)):witness[0][c]=color
    for c in range(5):witness[2][c]=8
    for r,c in ((4,7),(5,7),(6,7),(6,8),(6,0)):witness[r][c]=8
    assert not GEN.self_check(witness)
    bank={str(n):sorted({GEN._bbox_size(s)[0]*GEN._bbox_size(s)[1] for s in shapes}) for n,shapes in GEN.SHAPE_BANK.items()}
    reversals=[(a,fa,b,fb) for a,afs in bank.items() for b,bfs in bank.items() if int(a)>int(b) for fa in afs for fb in bfs if fa<fb]
    assert not reversals
    generated=[];canonical=[]
    with RacketBridge() as bridge:
        bridge.eval_text(f'(define audit-rule {wrapped})')
        def execute(grid):
            bridge.define_grid('audit-input',grid)
            return normalize_grid(bridge.eval_text('(audit-rule audit-input)'))
        for pair in pairs:
            actual=execute(pair['input']);prediction=rival(pair['input'])
            assert actual==pair['output']
            canonical.append({**pair,'actual_racket_output':actual,'rival_output':prediction,'rival_matches':actual==prediction})
        for band in (None,'easy','medium','hard'):
            for index in range(8):
                call={'seed':17,'sample_index':index,'difficulty':band}
                grid=GEN.generate(**call);actual=execute(grid);prediction=rival(grid)
                assert not GEN.self_check(grid)
                assert actual==GEN.rule_mirror(grid)
                generated.append({'call':call,'profile':GEN.schedule_profile(17,index,band),'input':grid,
                                  'actual_racket_output':actual,'rival_output':prediction,'rival_matches':actual==prediction})
        actual=execute(witness)
    prediction=rival(witness)
    assert actual!=prediction and all(r['rival_matches'] for r in canonical+generated)
    windows=[]
    for offset in range(0,32,8):
        rows=generated[offset:offset+8]
        for first in range(8):
            windows.append({'difficulty':rows[0]['call']['difficulty'],'first':first,
                            'demo_indices':[(first+k)%8 for k in range(4)],'query_index':(first+4)%8,
                            'rival_fits_demos':all(rows[(first+k)%8]['rival_matches'] for k in range(4)),
                            'rival_changes_query':not rows[(first+4)%8]['rival_matches']})
    assert digest(source)==source_hash
    bridge_source=Path(sys.modules['arc_repl.racket_bridge'].__file__)
    wrap_source=Path(sys.modules['puzzle_generators.rule_wrap'].__file__)
    report={'task':TASK,'status':'reproduced under-identification; no canonical reference error',
            'generator_sha256':source_hash,'reproducer_sha256':digest(Path(__file__)),
            'rule_text':program,'rule_sha256':hashlib.sha256(program.encode()).hexdigest(),
            'rule_hash':hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12],
            'wrapped_callable':wrapped,'wrapped_callable_sha256':hashlib.sha256(wrapped.encode()).hexdigest(),
            'bridge_sha256':digest(bridge_source),'rule_wrap_sha256':digest(wrap_source),
            'wrapper_parser_sha256':digest(ROOT/'shared/tools/comment_solutions.py'),
            'wrapper_dependency_mapping':'Full unchanged shared/tools/comment_solutions.py imported via a standard scripts namespace package mapping; no parser functions stubbed.',
            'prelude_sha256':digest(bridge_source.parent/'racket_prelude/arc-prelude.rkt'),
            'canonical_results':canonical,'generated_results':generated,'lesson_windows':windows,
            'counts':{'canonical_pairs':len(canonical),'canonical_rival_matches':sum(r['rival_matches'] for r in canonical),
                      'generated_reference_executions':len(generated),'generated_rival_matches':sum(r['rival_matches'] for r in generated),
                      'four_demo_windows':len(windows),'rival_survives_windows':sum(w['rival_fits_demos'] for w in windows)},
            'shape_bank_footprints_by_area':bank,'shape_bank_footprint_order_reversals':reversals,
            'counterexample':{'input':witness,'self_check_errors':GEN.self_check(witness),
                              'strict_canonical_like_errors':GEN.strict_canonical_like(witness),
                              'actual_racket_output':actual,'rival_output':prediction,'different':actual!=prediction,
                              'area_footprint_pairs':[(o['size'],o['height']*o['width']) for o in GEN._components(witness)]},
            'inherited_context':'Same-source unresolved footprint-first audit was read; the fresh checks here do not claim a rerun of its inherited 8000-draw census.',
            'limits':['Fresh finite sample: seed17, indices0..7, four bands; all32 generated outputs execute actual canonical Racket.',
                      'Rival reuses the audited component parser but independently sorts by footprint and packs; Racket is the label authority.',
                      'SHAPE_BANK footprint monotonicity is structural inspection, not all-seed enumeration.',
                      'Witness is in ordinary validator domain, outside strict canonical inventory (4,3,1).',
                      'No source edits, private solve access, full battery, approval upgrade, or runtime staging.']}
    (HERE/'evidence.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps({'counts':report['counts'],'rule_hash':report['rule_hash'],'counterexample_differs':True,'source_sha256':source_hash}))

if __name__=='__main__':main()
