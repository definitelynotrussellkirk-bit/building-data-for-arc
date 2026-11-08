"""Replay the unresolved parent discrepancy and bounded candidate evidence.

This never calls a failed preflight successful and never modifies official gold.
The status is blocked even if every generated label and named-rival check passes.
"""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name):
    p=HERE/(name+'.py');s=importlib.util.spec_from_file_location('_e12_audit_'+name+str(HERE),p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def rival_program(mode,rival):
    p=load('adapter').program({'finish':mode})
    replacements={'no_merge':('(define disable-merging #f)','(define disable-merging #t)'),
      'ignore_fraction':('(define unitize #f)','(define unitize #t)'),
      'cardinal_only':('(define emission 0)','(define emission 1)'),
      'diagonal_only':('(define emission 0)','(define emission 2)'),
      'no_finish':('(define mark-mode #t)','(define mark-mode #f)'),
      'mark_all':('(define mark-style 0)','(define mark-style 1)'),
      'pair_only':('(define mark-style 0)','(define mark-style 2)')}
    old,new=replacements[rival]
    if old not in p:raise ValueError('rival anchor absent')
    return p.replace(old,new)

def run(root,out,seeds=32):
    root=Path(root).resolve();out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(root/'src'),str(root/'shared/runtime')]
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_programs import strict_programs
    a=load('adapter');f=a.family;pub=load('public_io')
    episodes=pairs=turns=0;survivors=[]
    for seed in range(seeds):
        for mode in a.MODES:
            ep=a.generate(seed,{'finish':mode},6,4);episodes+=1;pairs+=10
            for rival in f.rivals(mode):
                if not any(f.solve(p['input'],mode,rival=rival)!=p['output'] for p in ep['train'][:2]):survivors.append([seed,mode,rival])
            for i in range(4):pub.view(ep,i);turns+=1
            assert any(len(p['input'])==30 and len(p['input'][0])==30 for p in ep['test'])
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');n=0;originals=[];records=[]
    try:
        data=json.loads((root/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['e12f9a14']
        gold=json.loads((root/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['e12f9a14']
        original_pairs=[('train',i,p) for i,p in enumerate(data['train'])]+[('test',i,dict(input=p['input'],output=o)) for i,(p,o) in enumerate(zip(data['test'],gold))]
        for split,i,p in original_pairs:
            actual=apply(a.program({'finish':'trace'}),p['input']);n+=1
            if actual!=f.solve(p['input']):raise AssertionError('Python/Racket discrepancy')
            differences=[{'row':r,'col':c,'expected':v,'actual':actual[r][c]} for r,row in enumerate(p['output']) for c,v in enumerate(row) if v!=actual[r][c]]
            row={'split':split,'index':i,'status':'passed' if not differences else 'FAILED','differences':differences}
            if differences:row.update(input=p['input'],expected=p['output'],actual=actual)
            originals.append(row)
        bad=[r for r in originals if r['status']=='FAILED']
        if len(bad)!=1 or bad[0]['split']!='train' or bad[0]['index']!=2 or len(bad[0]['differences'])!=6:raise AssertionError('Original diagnosis changed; investigate')
        for seed in (0,17,43):
            for mode in a.MODES:
                ep=a.generate(seed,{'finish':mode},2,4)
                for split in ('train','test'):
                    for p in ep[split]:
                        actual=apply(ep['program_solution'],p['input']);n+=1
                        if actual!=p['output']:raise AssertionError(('generated label',seed,mode,split))
                for rival in f.rivals(mode):
                    prog=rival_program(mode,rival);strict_programs(root,[prog]);fit=True
                    for p in ep['train']:
                        actual=apply(prog,p['input']);n+=1
                        if actual!=f.solve(p['input'],mode,rival=rival):raise AssertionError(('rival parity',rival))
                        fit &= actual==p['output']
                    if fit:raise AssertionError(('harmful rival',seed,mode,rival))
                    records.append({'seed':seed,'finish':mode,'rival':rival,'fits_all_demos':False,'program_sha256':hashlib.sha256(prog.encode()).hexdigest()})
        ep=a.generate(17,{'finish':'mark_merged'},2,4);p=next(p for p in ep['test'] if len(p['input'])==30)
        program=ep['program_solution'];cf=rival_program('mark_merged','no_merge')
        actual=apply(program,p['input']);counter=apply(cf,p['input']);n+=2
        assert actual==p['output'] and actual!=counter
        causal={'status':'unapproved_candidate_replayed','input':p['input'],'settings':{'finish':'mark_merged'},'program':program,'output':actual,'counterfactual_program':cf,'counterfactual_output':counter,'ablation':'wrong_intermediate','changed_cells':sum(v!=counter[r][c] for r,row in enumerate(actual) for c,v in enumerate(row)),
          'step_a':'Trace shield-emitted rays and merge intersecting forward groups, summing normalized directions.',
          'intermediate':'Ordered segment records with each outgoing bundle\'s contributing emitter colors.',
          'step_b':'Recolor segment cells gray exactly when the bundle has at least two contributing colors.',
          'why_b_depends_on_a':'Which rays belong to a merged bundle and its bent path exist only after collision resolution. Disabling collision construction supplies singleton trajectories to the same marking stage.',
          'events':f.trace(p['input'])[2],'racket':identity,'owner_accepted':False,'training_admitted':False}
    finally:bridge.close()
    patch1=[r[1:5] for r in data['train'][1]['input'][2:6]];patch2=[r[11:15] for r in data['train'][2]['input'][10:14]]
    assert [list(r) for r in zip(*patch1)][::-1]==patch2
    binding=[{'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(HERE.parents[1].rglob('*')) if p.is_file() and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json')) and '__pycache__' not in p.parts]
    causal['source_binding']={'task_id':'public_eval_e12f9a14','files':binding}
    (out.parent/'candidate-causal.json').write_text(json.dumps(causal,indent=2)+'\n')
    pub.export([a.generate(s,{'finish':m},2,4) for s in (17,43) for m in a.MODES],out.parent/'public-preview');public=pub.verify(out.parent/'public-preview')
    result={'status':'BLOCKED_original_label_mismatch','originals':originals,'original_passed':5,'original_failed':1,'episodes':episodes,'labeled_pairs':pairs,'public_turns':turns,'harmful_survivors':survivors,'racket':identity,'racket_evaluations':n,'rivals':records,'public_export':public,'source_binding':causal['source_binding'],
     'rotation_diagnostic':{'train_1_emitter':patch1,'train_2_emitter':patch2,'rotation':'counterclockwise90','identical':True,'interpretation':'Uniform local emission predicts six southeast yellow cells missing from train[2]. This is not proof of a bad label; an unknown global rule remains possible.'},
     'limits':'Candidate only. No official preflight success, native qualification, acceptance, or training admission. Finite sampler/rival audit cannot resolve the original-label discrepancy.'}
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','original_passed','original_failed','episodes','labeled_pairs','public_turns','racket_evaluations')}));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=32);args=p.parse_args();run(args.root,args.out,args.seeds)
