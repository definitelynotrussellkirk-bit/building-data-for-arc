"""Run a bounded source-bound union audit; outputs are private controller artifacts.

python -m invocation is unnecessary: run this file through review.py run.
The sampler never reads this report or any original labels.
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
BASE=Path(__file__).resolve().parent/'parametric'
spec=importlib.util.spec_from_file_location('a395_audited_union',BASE/'union.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def check_binding(preflight):
    for row in preflight['source_binding']['files']:
        if sha((ROOT/row['path']).read_bytes())!=row['sha256']:
            raise ValueError('Stale preflight source: '+row['path'])

def run(preflight_path,out,seeds=64):
    pre=json.loads(preflight_path.read_text());check_binding(pre)
    if pre['status']!='passed':raise ValueError('Preflight must pass first')
    out.mkdir(parents=True,exist_ok=False)
    failures=[];seen=set();pairs=episodes=0;clipping_edges=set();policies={}
    for seed in range(seeds):
        bank=u.inputs(seed)
        seen.update(sha(json.dumps(g).encode()) for g in bank)
        for mode in u.OPTIONS:
            names=list(u.rivals(mode))+['clip/drop_partial','clip/wrap']
            policies[mode]=names
            pred=lambda g,n:(u.clipping_predict(g,mode,n.split('/')[1]) if n.startswith('clip/') else u.rival_predict(g,mode,n))
            labels=[u.solve(g,mode) for g in bank]
            for name in names:
                if all(pred(g,name)==o for g,o in zip(bank[:2],labels[:2])) and any(pred(g,name)!=o for g,o in zip(bank[6:],labels[6:])):
                    failures.append({'seed':seed,'mode':mode,'rival':name})
            for demos in range(2,7):
                e=u.generate(seed,{'rule':mode},demos,4);episodes+=1;pairs+=demos+4
                if [p['input'] for p in e['test']]!=bank[6:]:raise ValueError('Query bank changed')
                if len({repr(p['input']) for p in e['train']+e['test']})!=demos+4:raise ValueError('Duplicate input')
                for p in e['train']+e['test']:_grid(p['input']);_grid(p['output'])
        g=u.clipped_scene(seed,6);d=u.one.inspect(g);r,c=d['origin'];h,w=d['shape']
        if r==1:clipping_edges.add('top')
        if c==1:clipping_edges.add('left')
        if r==len(g)-h-1:clipping_edges.add('bottom')
        if c==len(g[0])-w-1:clipping_edges.add('right')
    if failures:
        write(out/'failure.json',failures);raise AssertionError(f'{len(failures)} finite rival failures')
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime');evaluations=0
    try:
        # All ten scenes and each existing setting; extra clipping seeds.
        for seed in (0,17,43):
            for mode in u.OPTIONS:
                for g in (u.inputs(seed) if seed==17 else [u.clipped_scene(seed,1),u.clipped_scene(seed,6)]):
                    assert _grid(apply(u.program({'rule':mode}),g))==u.solve(g,mode)
                    evaluations+=1
        # Execute every retained original rival on a separating demonstration.
        for mode in u.OPTIONS:
            for name,program in u.rivals(mode).items():
                g=next(g for g in u.inputs(17)[:2] if u.rival_predict(g,mode,name)!=u.solve(g,mode))
                actual=_grid(apply(program,g));evaluations+=1
                assert actual==u.rival_predict(g,mode,name),(mode,name)
        g=u.inputs(17)[0];p=u.program({'rule':'ink'});cf=u.one.rival_programs({'tile_mask':'ink'})['pitch_two']
        actual=_grid(apply(p,g));wrong=_grid(apply(cf,g));evaluations+=2
        assert actual!=wrong
        descriptions={
          'step_a':'Recover the primitive row and column pitches by GCD of the singleton control-map coordinates.',
          'intermediate':'The input-dependent primitive lattice pitches (row_pitch, column_pitch).',
          'step_b':'Normalize map displacements by those pitches, then scale them by motif height and width to place the stamps.',
          'why_b_depends_on_a':'Physical symbol spacing is not target tile spacing. B needs the decoded lattice to choose remote tile locations; fixing the pitch to two changes output.'}
        witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':'public_eval_a395ee82',
          'source_binding':pre['source_binding'],'racket':{'backend':'racket','protected':True},**descriptions,
          'cases':[{'input':g,'settings':{'rule':'ink'},'intermediate_value':list(u.one.inspect(g)['pitch']),
                    'program':p,'output':actual,'counterfactual_program':cf,'counterfactual_output':wrong,'ablation':'wrong_intermediate'}]}
        write(out/'witness.json',witness)
        validate_sequential_witness({'sequential_dependency':{**descriptions,'witness_path':'witness.json'}},pre,lambda name:(out/name).read_bytes())
        # Compact old-lesson counterexample: no clipping was observable in old demos.
        old=[u.one.scene(u.one.rng_for(17,'union-demo-0'),0),u.two.sample(17,'train',1)]
        query=u.clipped_scene(17,6);fixed=u.inputs(17)[:2]
        regressions=[]
        for mode in u.OPTIONS:
            rows=[]
            for x in old+[query]+fixed:
                answer=_grid(apply(u.program({'rule':mode}),x));evaluations+=1
                rows.append({'input':x,'output':answer,'drop_partial':u.clipping_predict(x,mode,'drop_partial'),'wrap':u.clipping_predict(x,mode,'wrap')})
            assert all(r['output']==r['drop_partial'] for r in rows[:2])
            assert rows[2]['output']!=rows[2]['drop_partial']
            assert any(r['output']!=r['drop_partial'] for r in rows[3:])
            regressions.append({'rule':mode,'old_train':rows[:2],'new_query':rows[2],'repaired_train':rows[3:],
              'rival_labels':'Independent Python clipping claims; correct labels executed through protected Racket.'})
        write(out/'clipping-regression.json',{'source_binding':pre['source_binding'],'cases':regressions})
    finally:bridge.close()
    replay=replay_witness(ROOT,witness);replay['status']='reviewer_replayed';write(out/'replay.json',replay)
    public=out/'public';public.mkdir();ids=[]
    for seed in (17,43):
        for mode in u.OPTIONS:
            e=u.generate(seed,{'rule':mode},2,4)
            for i in range(4):
                view=u.public_turn(e,i);data=public_challenge_bytes(view)
                polluted=copy.deepcopy(e);polluted['program_solution']='private';polluted['settings']={'private':0}
                for pair in polluted['train']+polluted['test']:pair['settings']='secret'
                for pair in polluted['test']:pair['output']=[[9]]
                assert public_challenge_bytes(u.public_turn(polluted,i))==data
                name=sha(data);assert name not in ids;ids.append(name);(public/(name+'.json')).write_bytes(data)
    e=u.generate(17,{'rule':'ink'},2,4);bad=u.public_turn(e,0);bad['test'][0]['output']=e['test'][0]['output']
    raw=(json.dumps(bad,sort_keys=True,separators=(',',':'))+'\n').encode();negative=out/'negative';negative.mkdir();(negative/(sha(raw)+'.json')).write_bytes(raw)
    report={'status':'passed','seeds':seeds,'settings':list(u.OPTIONS),'demos':[2,6],'episodes':episodes,'labeled_pair_checks':pairs,
      'distinct_inputs':len(seen),'policies':policies,'failures':failures,'clipped_edges':sorted(clipping_edges),
      'protected_racket_evaluations':evaluations,'causal_replay_evaluations':replay['evaluations'],'racket':identity,
      'public_files':len(ids),'public_sha256':sorted(ids),'source_binding':pre['source_binding'],
      'limits':'Finite rivals and retained seeds, not universal identifiability. Python claim sweep is separate from counted Racket executions. No owner acceptance.'}
    check_binding(pre);write(out/'audit.json',report)
    print(json.dumps({k:report[k] for k in ('status','seeds','episodes','labeled_pair_checks','distinct_inputs','protected_racket_evaluations','public_files')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=64);a=p.parse_args()
    if not 1<=a.seeds<=256:p.error('seeds must be 1..256')
    run(a.preflight,a.out,a.seeds)
