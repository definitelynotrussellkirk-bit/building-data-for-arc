"""Source-bound bounded terrain-route audit and private one-turn export.

The rule and sampler read no official labels. Run original-label preflight first,
then this tool. All outputs, including future-query directory listings, are private.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
from arcpuzzles.parametric_worker import _real_evaluator, _grid
from arcpuzzles.review_parametric_admission import validate_sequential_witness
from arcpuzzles.review_sequential_replay import replay_witness
from reviewer_support import public_challenge_bytes

ROOT=Path(__file__).resolve().parents[3]
HOME=Path(__file__).resolve().parent.parent
BASE=HOME/'workspace/parametric'
s=importlib.util.spec_from_file_location('terrain195_audited_adapter',BASE/'adapter.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

def sha(data):return hashlib.sha256(data).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def check_binding(preflight):
    for row in preflight['source_binding']['files']:
        if sha((ROOT/row['path']).read_bytes())!=row['sha256']:raise ValueError('Stale preflight source: '+row['path'])
    if (HOME/'generator.py').read_bytes()!=(BASE/'core.py').read_bytes():raise ValueError('Standalone/native code copies differ')


def segment_summary(events):
    segments=[]
    for kind,r,c,total,local in events:
        if kind:continue
        if local==0:segments.append({'origin':[r,c],'cells':0,'global_start':total})
        segments[-1]['cells']+=1
    return segments


def run(preflight_path,out,seeds=64):
    pre=json.loads(preflight_path.read_text());check_binding(pre)
    if pre['status']!='passed':raise ValueError('Passing original-label and native preflight required')
    out.mkdir(parents=True,exist_ok=False)
    seen=set();episodes=pairs=0;failures=[];cycles=set();source_counts=set();endings=set();turn_counts=set();first_indices=set();size_bounds=[]
    for seed in range(seeds):
        bank=a.inputs(seed);seen.update(sha(json.dumps(g).encode()) for g in bank)
        e=a.generate(seed,{'phase':'carry'},2,4)
        first_indices.add(next(i for i in range(6,10) if bank[i]==e['test'][0]['input']))
        for g in bank:
            d=a.core.parse(g);paths=a.core.routes(g);size_bounds.append([len(g),len(g[0])]);cycles.add(len(d['cycle']));source_counts.add(len(paths))
            occupied=[]
            for p in paths:
                ending='blocked' if p[-1][0] else ('top_edge' if p[-1][1]==0 else 'right_edge')
                endings.add(ending);turn_counts.add(len(segment_summary(p))-1)
                occupied += [(e[1],e[2]) for e in p]
            # Native sampler keeps trails and collision cells separate.
            if len(set(occupied))!=len(occupied):failures.append({'seed':seed,'failure':'overlapping routes/marks'})
        for mode in a.core.MODES:
            lesson=a.generate(seed,{'phase':mode},2,4)
            for rival in a.RIVALS:
                if all(a.core.solve(p['input'],mode,rival=rival)==p['output'] for p in lesson['train']):
                    if any(a.core.solve(p['input'],mode,rival=rival)!=p['output'] for p in lesson['test']):
                        failures.append({'seed':seed,'mode':mode,'rival':rival})
            for n in range(2,7):
                e=a.generate(seed,{'phase':mode},n,4);episodes+=1;pairs+=n+4
                if len({repr(p['input']) for p in e['train']+e['test']})!=n+4:raise ValueError('Duplicate input')
                for p in e['train']+e['test']:_grid(p['input']);_grid(p['output'])
    if failures:
        write(out/'failure.json',failures);raise AssertionError(f'{len(failures)} bounded audit failures')
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime');evaluations=0
    try:
        for seed in (0,17,43):
            for mode in a.core.MODES:
                for g in a.inputs(seed):
                    assert _grid(apply(a.program({'phase':mode}),g))==a.core.solve(g,mode),(seed,mode)
                    evaluations+=1
        # Re-execute each shortcut on a separating demonstration when available.
        for mode in a.core.MODES:
            lesson=a.generate(17,{'phase':mode},2,4)
            for rival in a.RIVALS:
                options=[p for p in lesson['train'] if a.core.solve(p['input'],mode,rival=rival)!=p['output']]
                p=options[0] if options else lesson['train'][0]
                assert _grid(apply(a.rival_program(mode,rival),p['input']))==a.core.solve(p['input'],mode,rival=rival),(mode,rival)
                evaluations+=1
        chosen=a.generate(17,{'phase':'restart'},2,4)['train'][1]
        program=a.program({'phase':'restart'})
        counter=program.replace('(list-ref e (if restart? 4 3))','(list-ref e 3)')
        assert counter!=program
        actual=_grid(apply(program,chosen['input']));wrong=_grid(apply(counter,chosen['input']));evaluations+=2
        assert actual==chosen['output'] and actual!=wrong
        descriptions={
          'step_a':'Trace immutable terrain from each start through first-obstruction rays and successful right/up turns, computing each segment origin and per-cell segment-relative index.',
          'intermediate':'Input-dependent ordered route segments and their per-cell distances from the first cell after the latest successful turn.',
          'step_b':'For phase=restart, color each traced cell using its segment-relative index into the ordered repeated-color legend; leave terrain elsewhere unchanged and mark first obstructions.',
          'why_b_depends_on_a':'The terrain determines where the next segment begins. B cannot select its reset phase or destination cells without those first-hit boundaries. The counterfactual replaces the derived local indices with global path indices while preserving the exact traced cells and collision markers.'}
        witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':'public_eval_195c6913',
          'source_binding':pre['source_binding'],'racket':{'backend':'racket','protected':True},**descriptions,
          'cases':[{'input':chosen['input'],'settings':{'phase':'restart'},
            'intermediate_value':{'cycle':a.core.parse(chosen['input'])['cycle'],'segments':[segment_summary(p) for p in a.core.routes(chosen['input'])]},
            'program':program,'output':actual,'counterfactual_program':counter,'counterfactual_output':wrong,'ablation':'wrong_intermediate'}]}
        write(out/'witness.json',witness)
        validate_sequential_witness({'sequential_dependency':{**descriptions,'witness_path':'witness.json'}},pre,lambda name:(out/name).read_bytes())
        diffs=sum(x!=y for r,s in zip(actual,wrong) for x,y in zip(r,s))
        # Retain explicit teaching refutations using Racket, not only booleans.
        refutations=[]
        for mode,rival,index in [('carry','unique_cycle',1),('carry','first_start',1),('carry','count_walls',0),('restart','opposite_setting',1)]:
            pair=a.generate(17,{'phase':mode},2,4)['train'][index]
            correct=_grid(apply(a.program({'phase':mode}),pair['input']));predicted=_grid(apply(a.rival_program(mode,rival),pair['input']));evaluations+=2
            assert correct!=predicted
            refutations.append({'settings':{'phase':mode},'rival':rival,'input':pair['input'],'output':correct,
                                'rival_program':a.rival_program(mode,rival),'rival_output':predicted})
        write(out/'teaching-refutations.json',{'source_binding':pre['source_binding'],'cases':refutations})
    finally:bridge.close()
    replay=replay_witness(ROOT,witness);replay['status']='reviewer_replayed';write(out/'replay.json',replay)
    public=out/'public';public.mkdir();ids=[]
    for seed in (17,43):
        for mode in a.core.MODES:
            e=a.generate(seed,{'phase':mode},2,4)
            for i in range(4):
                view=a.public_turn(e,i);raw=public_challenge_bytes(view)
                contaminated=copy.deepcopy(e);contaminated['program_solution']='secret';contaminated['settings']={'seed':99};contaminated['future']=e['test'][i+1:]
                for p in contaminated['train']+contaminated['test']:p['private']='secret'
                for p in contaminated['test']:p['output']=[[9]]
                assert public_challenge_bytes(a.public_turn(contaminated,i))==raw
                name=sha(raw);assert name not in ids;ids.append(name);(public/(name+'.json')).write_bytes(raw)
    e=a.generate(17,{'phase':'carry'},2,4);bad=a.public_turn(e,0);bad['test'][0]['output']=e['test'][0]['output']
    raw=(json.dumps(bad,sort_keys=True,separators=(',',':'))+'\n').encode();negative=out/'negative';negative.mkdir();(negative/(sha(raw)+'.json')).write_bytes(raw)
    report={'status':'passed','seeds':seeds,'settings':list(a.core.MODES),'demos':[2,6],'episodes':episodes,'labeled_pair_checks':pairs,
      'distinct_inputs':len(seen),'policies':list(a.RIVALS),'failures':failures,'cycle_lengths':sorted(cycles),'source_counts':sorted(source_counts),
      'endings':sorted(endings),'turn_counts':sorted(turn_counts),'first_query_source_indices':sorted(first_indices),
      'size_min':[min(x[i] for x in size_bounds) for i in (0,1)],'size_max':[max(x[i] for x in size_bounds) for i in (0,1)],
      'protected_racket_evaluations':evaluations,'causal_replay_evaluations':replay['evaluations'],'causal_cell_differences':diffs,
      'racket':identity,'public_files':len(ids),'public_sha256':sorted(ids),'source_binding':pre['source_binding'],
      'limits':'Finite rivals and sampled seeds, not universal identifiability. Python claim sweep is separate from Racket replay. Original gold is authoring verification, not blind evaluation. No owner acceptance.'}
    check_binding(pre);write(out/'audit.json',report)
    print(json.dumps({k:report[k] for k in ('status','seeds','episodes','labeled_pair_checks','distinct_inputs','protected_racket_evaluations','causal_cell_differences','public_files')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=64);o=p.parse_args()
    if not 1<=o.seeds<=256:p.error('seeds must be 1..256')
    run(o.preflight,o.out,o.seeds)
