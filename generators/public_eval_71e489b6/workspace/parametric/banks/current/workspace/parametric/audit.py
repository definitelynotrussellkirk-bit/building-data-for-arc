#!/usr/bin/env python3
"""Replayable, source-bound authoring audit. Never grants owner acceptance.

Run via review.py run, after public-creation preflight. The same script's main
loop can be reused in another assigned home whose adapter implements the small
program/generate/rival/public_turn/query_order/causal_intermediate interface.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def teaching_failures(adapter,train,test):
    """Exceptions are failures, NEVER evidence that a hypothesis was refuted."""
    findings=[]
    for name in adapter.RIVALS:
        demo_outputs=[adapter.rival(p['input'],name)for p in train]
        if all(out==p['output']for out,p in zip(demo_outputs,train)):
            for i,p in enumerate(test):
                if adapter.rival(p['input'],name)!=p['output']:
                    findings.append({'rival':name,'query_index':i});break
    return findings


def bound(preflight):
    if preflight.get('status')!='passed' or preflight.get('owner_accepted') is not False:
        raise ValueError('need passing UNAPPROVED authoring preflight')
    binding=preflight['source_binding']
    for row in binding['files']:
        p=ROOT/row['path']
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT) or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('source binding changed: '+row['path'])
    return binding


def public_checks(a,episodes,out):
    from reviewer_support import public_challenge_bytes
    pub=out/'public';pub.mkdir();private=[];seen=set();mutations=0
    for ei,ep in enumerate(episodes):
        presentation_seed=ep['seed']
        ids=[];order=a.query_order(presentation_seed)
        for turn in range(4):
            view=a.public_turn(ep,turn,presentation_seed=presentation_seed)
            raw=public_challenge_bytes(view);name=hashlib.sha256(raw).hexdigest()
            if name in seen:raise ValueError('duplicate visible challenge')
            seen.add(name);(pub/(name+'.json')).write_bytes(raw);ids.append(name)
            # Only currently visible data may affect the current payload.
            altered=copy.deepcopy(ep)
            altered['program_solution']='private mutation';altered['settings']={'private':True};altered['seed']=-1
            for p in altered['train']:p['private']={'secret':True}
            for i,p in enumerate(altered['test']):
                p['output']={'not':'a grid'};p['private']={'secret':True}
                if i!=order[turn]:p['input']={'future':'not a visible grid'}
            if public_challenge_bytes(a.public_turn(altered,turn,presentation_seed=presentation_seed))!=raw:
                raise AssertionError('private fields changed visible bytes')
            mutations+=1
        private.append({'episode_index':ei,'presentation_seed':presentation_seed,'source_indices':order,'view_ids':ids})
    write(out/'private/presentation.json',{'controller_only':True,'episodes':private})
    first_positions=sorted({a.query_order(s)[0]for s in range(64)})
    if first_positions!=[0,1,2,3]:raise AssertionError('first query is not randomized across presentation seeds')
    checker=ROOT.parent/'check_public_exports.py'
    def run_check(path):
        proc=subprocess.run([sys.executable,str(checker),str(path),'--queries','1','--summary'],text=True,capture_output=True)
        report=json.loads(proc.stdout)
        # Store portable paths: absolute paths are a UI concern, not content identity.
        for item in report.get('findings',[]):
            if item.get('path'):item['path']=Path(item['path']).relative_to(out).as_posix()
        return proc.returncode,report
    code,positive=run_check(pub)
    if code!=0:raise AssertionError(positive)
    write(out/'public-check.json',positive)
    # Exercise the real checker, rather than merely inspecting our own writer.
    bad=copy.deepcopy(a.public_turn(episodes[0],0));bad['test'][0]['output']=[[9]]
    raw=(json.dumps(bad,sort_keys=True,separators=(',',':'))+'\n').encode()
    neg=out/'negative';neg.mkdir();path=neg/(hashlib.sha256(raw).hexdigest()+'.json');path.write_bytes(raw)
    code,negative=run_check(path)
    if code==0 or not any(f['code']=='public_schema'for f in negative.get('findings',[])):
        raise AssertionError('real checker accepted leaked query answer')
    write(out/'negative-check.json',negative)
    return {'public_files':len(seen),'private_mutations_checked':mutations,'first_source_indices_observed':first_positions,
            'deliberate_answer_leak_rejected':True}


def witness_document(binding,dependency,identity,cases):
    """Keep the intake marker exact; retain runtime hashes in a separate field."""
    if identity.get('backend')!='racket' or identity.get('protected') is not True:
        raise ValueError('a protected Racket execution identity is required')
    return {'schema':'arcpuzzles-sequential-dependency-witness-v1',
            'source_binding':copy.deepcopy(binding),**copy.deepcopy(dependency),
            'racket':{'backend':'racket','protected':True},
            'runtime_identity':copy.deepcopy(identity),'cases':copy.deepcopy(cases)}


def audit(preflight_path,out,seeds):
    if out.exists():raise ValueError('choose a new output directory')
    preflight=json.loads(preflight_path.read_text());binding=bound(preflight)
    a=load(HERE/'adapter.py','_audited_adapter_'+HERE.parents[1].name)
    contract=preflight['contract'];axis=next(iter(contract['parameters']));modes=contract['parameters'][axis]
    low,high=contract['limits']['demos'];failures=[];unique=set();counts={'episodes':0,'labeled_pair_checks':0,'boundary_queries':0}
    all_sizes=set();rival_equivalent={mode:set(a.RIVALS)for mode in modes}
    for seed in range(seeds):
        full={mode:a.generate(seed,{axis:mode},high,4)for mode in modes}
        inputs=[p['input']for sp in ('train','test')for p in full[modes[0]][sp]]
        for mode in modes:
            if [p['input']for sp in ('train','test')for p in full[mode][sp]]!=inputs:raise AssertionError('unmatched settings')
        if len({digest(g)for g in inputs})!=len(inputs):raise AssertionError('duplicate episode input')
        unique.update(digest(g)for g in inputs);all_sizes.update((len(g),len(g[0]))for g in inputs)
        cache={name:[a.rival(g,name)for g in inputs]for name in a.RIVALS}
        for mode in modes:
            for demos in range(low,high+1):
                ep=a.generate(seed,{axis:mode},demos,4);counts['episodes']+=1;counts['labeled_pair_checks']+=demos+4
                if ep['train']!=full[mode]['train'][:demos] or ep['test']!=full[mode]['test']:raise AssertionError('count-dependent sampler')
                if ep['program_solution']!=a.program({axis:mode}):raise AssertionError('program mismatch')
                g=ep['test'][-1]['input']
                if max(len(g),len(g[0]),len(ep['test'][-1]['output']),len(ep['test'][-1]['output'][0]))==30:counts['boundary_queries']+=1
                wanted=[p['output']for p in ep['train']]
                for name,outputs in cache.items():
                    if all(outputs[i]==wanted[i]for i in range(demos)):
                        diff=[i for i,p in enumerate(ep['test'])if outputs[high+i]!=p['output']]
                        if diff:failures.append({'seed':seed,'settings':{axis:mode},'demos':demos,'rival':name,'query_index':diff[0]})
                    else:rival_equivalent[mode].discard(name)
    out.mkdir(parents=True)
    write(out/'claims.json',{'status':'failed'if failures else 'passed','source_binding':binding,'seeds':list(range(seeds)),
         **counts,'distinct_inputs':len(unique),'grid_sizes':[list(s)for s in sorted(all_sizes)],'rivals':list(a.RIVALS),
         'policies_fitting_all_demos_across_sweep':{m:sorted(v)for m,v in rival_equivalent.items()},'failures':failures,
         'limits':'Bounded Python-claim comparisons, not universal uniqueness; repeated inputs count across settings and demo counts.'})
    if failures:raise AssertionError(f'{len(failures)} teaching failures; see claims.json')
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    executed=[];programs={}
    def execute(program,g):
        result=_grid(apply(program,g));sha=hashlib.sha256(program.encode()).hexdigest();programs[sha]=program
        executed.append({'program_sha256':sha,'input':g,'output':result});return result
    try:
        for seed in (0,31):
            for mode in modes:
                ep=a.generate(seed,{axis:mode},high,4)
                for p in ep['train']+ep['test']:
                    if execute(ep['program_solution'],p['input'])!=p['output']:raise AssertionError('Python/Racket label mismatch')
        regression=HERE/'regression-diagonal.json'
        if regression.is_file():
            old=json.loads(regression.read_text());rival_program=(HERE/'diagonal_rival.rkt').read_text()
            selected_program=a.program({axis:'largest_rim'})
            for p in old['train']:
                assert execute(selected_program,p['input'])==p['output']
                assert execute(rival_program,p['input'])==p['output']
            q=old['query'];assert execute(selected_program,q['input'])==q['output']
            assert execute(rival_program,q['input'])==old['rival_query']!=q['output']
            repaired=a.generate(old['reason']['seed'],{axis:'largest_rim'},low,4)
            refuted=False
            for p in repaired['train']:
                assert execute(selected_program,p['input'])==p['output']
                refuted |= execute(rival_program,p['input'])!=p['output']
            assert refuted
            write(out/'regression.json',{'status':'passed','rival':'eight_connected_largest',
                'fixture_sha256':hashlib.sha256(regression.read_bytes()).hexdigest(),
                'old_demos_fit':True,'old_query_disagrees':True,'new_minimum_demos_refute':True,
                'source_binding':binding,'racket':identity})
        ex=json.loads(preflight_path.with_name('execution.json').read_text());episodes=ex['episodes']
        dep=json.loads((HERE/'causal-description.json').read_text())
        wrong=(HERE/'wrong_order.rkt').read_text();selected=None
        for ei,ep in enumerate(episodes):
            if ep['settings']==contract['default']:continue
            for split in ('train','test'):
                for pi,p in enumerate(ep[split]):
                    if a.counterfactual(p['input'])!=p['output']:
                        selected=(ei,split,pi,ep,p);break
                if selected:break
            if selected:break
        if not selected:raise AssertionError('no changing counterfactual on preflight pairs')
        ei,split,pi,ep,p=selected
        result=execute(ep['program_solution'],p['input']);counter=execute(wrong,p['input'])
        if result!=p['output'] or counter!=a.counterfactual(p['input']) or result==counter:
            raise AssertionError('invalid causal witness labels')
        witness=witness_document(binding,dep,identity,[{'input':p['input'],'settings':ep['settings'],'intermediate_value':a.causal_intermediate(p['input']),
            'program':ep['program_solution'],'output':result,'counterfactual_program':wrong,'counterfactual_output':counter,'ablation':'wrong_order'}])
        from arcpuzzles.review_parametric_admission import validate_sequential_witness
        checked=validate_sequential_witness({'sequential_dependency':{**dep,'witness_path':'witness.json'}},
            preflight,lambda _:json.dumps(witness,allow_nan=False).encode())
        write(out/'causal/schema-check.json',checked)
        write(out/'causal/witness.json',witness)
        # Fresh evaluations, not equality of stored claims.
        for case in witness['cases']:
            if execute(case['program'],case['input'])!=case['output'] or execute(case['counterfactual_program'],case['input'])!=case['counterfactual_output']:
                raise AssertionError('causal replay mismatch')
        changed=sum(x!=y for row,other in zip(result,counter)for x,y in zip(row,other)) if len(result)==len(counter) and len(result[0])==len(counter[0]) else None
        write(out/'causal/replay.json',{'status':'reviewer_replayed','racket':identity,'source_binding':binding,
            'preflight_pair':{'episode_index':ei,'split':split,'pair_index':pi},'changed_cells_same_shape':changed,'owner_accepted':False,
            'limits':'Final labels replayed. Intermediate and causal interpretation are authored metadata, not runtime instrumentation.'})
    finally:bridge.close()
    write(out/'racket-labels.json',{'racket':identity,'source_binding':binding,'programs':programs,'executions':executed})
    exports=public_checks(a,episodes,out)
    bound(preflight)
    summary={'status':'passed','task_id':binding['task_id'],'seeds':seeds,**counts,'distinct_inputs':len(unique),
             'rival_count':len(a.RIVALS),'racket_evaluations':len(executed),**exports,'owner_accepted':False,
             'training_admitted':False,'verification_status':'authoring_audit_not_owner_qualification'}
    write(out/'summary.json',summary);return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=32);args=p.parse_args()
    if not 1<=args.seeds<=256:p.error('--seeds must be 1..256')
    print(json.dumps(audit(args.preflight.resolve(),args.out.resolve(),args.seeds),sort_keys=True,indent=2))

if __name__=='__main__':main()
