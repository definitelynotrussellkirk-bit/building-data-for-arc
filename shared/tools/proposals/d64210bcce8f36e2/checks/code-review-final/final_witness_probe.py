"""Bounded final-source Racket witnesses; separate public challenge projection."""
import hashlib
import json
from pathlib import Path
import sys

WORK=Path(__file__).resolve().parents[2]
ROOT=WORK/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, load_selected_generator

EXPECTED_SOURCE='c90ed220b7bad99f254f4c1bf96336105b1298ee902eff503e1398d99c1c07a5'


def sha(value):
    if not isinstance(value,bytes):value=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(value).hexdigest()


def execute(bridge,program,grid):
    source=program.strip()
    assert source.startswith('(rule! (lambda (g)') and source.endswith(')')
    body=source[len('(rule!'):-1].strip()
    literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
    return bridge.eval_text(f'({body} {literal})')


def frame(grid,t,l,h,w,color):
    for r in range(t,t+h):
        for c in range(l,l+w):
            if r in (t,t+h-1) or c in (l,l+w-1):grid[r][c]=color


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def main():
    mod,path,source_sha=load_selected_generator('18bd3cd2985e',root=ROOT)
    assert source_sha==EXPECTED_SOURCE
    programs=set()
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row=json.loads(line)
            if row.get('task_id')==mod.TASK_ID:programs.add(row['program_solution'])
    assert len(programs)==1
    program=programs.pop()
    canonical=[]
    for pair in canonical_pairs(mod.TASK_ID,root=ROOT,labeled_only=True):
        canonical.append({'variant':pair['variant'],'split':pair['split'],'pair_index':pair['pair_index'],
                          'input_sha256':sha(pair['input']),
                          'rival_fits':{name:rival(pair['input'])==pair['output']
                                        for name,rival in mod.CANONICAL_SHORTCUTS.items()}})
    witness=[[0]*12 for _ in range(12)]
    frame(witness,1,1,3,5,2)  # capacity2
    frame(witness,6,1,3,7,3)  # capacity3
    witness[0][9]=6          # count1, too small
    for r,c in ((0,0),(0,2),(4,9),(10,10)):witness[r][c]=7  # count4, too large
    assert not mod.self_check(witness)
    with RacketBridge() as bridge:
        witness_output=execute(bridge,program,witness)
        rival_outputs={name:mod.SEMANTIC_RIVALS[name](witness)
                       for name in ('rank_pairing','smallest_fitting_frame','smallest_sufficient_group')}
        counter={'schema':'arc-count-equality-counterexample-v1','status':'verified_with_racket',
                 'task_id':mod.TASK_ID,'generator_sha256':source_sha,'rule_hash':mod.RULE_HASH,
                 'program_sha256':sha(program.encode()),'input':witness,'input_sha256':sha(witness),
                 'output':witness_output,'rival_outputs':rival_outputs,
                 'rival_disagrees':{name:prediction!=witness_output for name,prediction in rival_outputs.items()},
                 'description':'Two frame capacities2 and3; singleton counts1 and4. All groups are erased and frames remain empty. Rank and both natural threshold directions predict a fill.',
                 'reproducer':'checks/code-review-final/final_witness_probe.py'}
        write(ROOT/'generators/18bd3cd2985e/counterexamples/count-equality-12x12.json',counter)
        pairs=[]
        for index in (2,3,4,5):
            grid=mod.generate(0,index)
            answer=execute(bridge,program,grid)
            pairs.append({'seed':0,'sample_index':index,'input':grid,'output':answer,
                          'input_sha256':sha(grid),'output_sha256':sha(answer),
                          'observed':mod.observe_overrides(grid)})
        predictions={name:[rival(pair['input']) for pair in pairs]
                     for name,rival in mod.LESSON_COMPETITORS.items()}
        rotations=[]
        for q in range(4):
            demos=[i for i in range(4) if i!=q]
            statuses={name:{'demonstration_refutations':[i for i in demos if results[i]!=pairs[i]['output']],
                            'query_disagrees':results[q]!=pairs[q]['output']}
                      for name,results in predictions.items()}
            rotations.append({'query_position':q,'demonstration_positions':demos,'rivals':statuses,
                              'lesson_hook_reasons':mod.lesson_identifiable([pairs[i] for i in demos],pairs[q])})
        runtime=bridge.runtime_identity
    checks={'canonical_shortcuts_fit_all_labels':all(all(p['rival_fits'].values()) for p in canonical),
            'counterexample_refutes_all_three_count_rivals':all(counter['rival_disagrees'].values()),
            'all_seven_rivals_refuted_in_every_rotation':all(all(row['demonstration_refutations'] for row in r['rivals'].values()) for r in rotations),
            'no_lesson_hook_warnings':all(not r['lesson_hook_reasons'] for r in rotations),
            'source_unchanged':sha(path.read_bytes())==source_sha}
    report={'schema':'arc-final-source-bounded-witness-v1','status':'passed' if all(checks.values()) else 'failed',
            'checks':checks,'generator_sha256':source_sha,'program_sha256':sha(program.encode()),'rule_hash':mod.RULE_HASH,
            'canonical_program':program,'probe_sha256':sha(Path(__file__).read_bytes()),'python':sys.executable,
            'argv':sys.argv,'cwd':str(Path.cwd()),'racket_runtime':runtime,'canonical_rival_fit':canonical,
            'production_pairs':pairs,'rotations':rotations,'reference_applications':5,
            'counterexample_path':'repo/generators/18bd3cd2985e/counterexamples/count-equality-12x12.json',
            'counterexample_sha256':sha((ROOT/'generators/18bd3cd2985e/counterexamples/count-equality-12x12.json').read_bytes()),
            'limitations':['Finite evidence against seven declared rivals, not universal identifiability.',
                           'Default lesson schedule only; arbitrary input overrides do not inherit its rotation guarantee.',
                           'In partial scenes the largest frame remains matched, a deliberate bounded-curriculum tradeoff.']}
    out=WORK/'checks/code-review-final'
    write(out/'production-witness.json',report)
    write(out/'production-challenge.json',{'train':[{'input':p['input'],'output':p['output']} for p in pairs[:3]],
                                          'test':[{'input':pairs[3]['input']}]})
    print(json.dumps({'status':report['status'],'checks':checks,'generator_sha256':source_sha,
                      'production_rivals':list(predictions),'reference_applications':5,
                      'counterexample_sha256':report['counterexample_sha256']},indent=2))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':raise SystemExit(main())
