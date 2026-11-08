"""Source-bound corner-motif learnability audit, protected replay and exports.

Finite rivals/seeds only. This is not native owner acceptance.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import random
import sys
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_corner_audit_'+hashlib.sha256(str(BASE).encode()).hexdigest(),BASE/'adapter.py')
adapter=importlib.util.module_from_spec(spec);sys.modules[spec.name]=adapter;spec.loader.exec_module(adapter)
model=adapter.model
PARAMETER='copy_extent'
MODES=('full','outside')
DEPENDENCY={
 'step_a':'Recover black-frame corner positions and inward axes, assign nearby colored marks, and normalize the largest completed motif to those axes.',
 'intermediate':'Input-derived normalized motif offsets and the active corner/color/orientation records.',
 'step_b':'Reorient and recolor the recovered motif at each marked corner, clipping to the canvas and optionally limiting additions to the frame/exterior.',
 'why_b_depends_on_a':'The copied shape and orientation cannot be fixed in advance: different inputs contain distinct glyph geometries and differently oriented frame corners. B directly consumes A’s offsets and axes.'}


def rivals(grid,mode):
    d=model.analyze(grid);actual=model.render(grid,d,mode);motif=d['motif']
    out={'identity':[row[:]for row in grid],
         'wrong_setting':model.render(grid,d,MODES[1-MODES.index(mode)]),
         'transpose_motif':model.render(grid,d,mode,[(b,a)for a,b in motif]),
         'fixed_diagonal_square':model.render(grid,d,mode,adapter.MOTIFS[2]),
         'fixed_corner_triangle':model.render(grid,d,mode,[(-1,0),(0,-1),(0,0),(1,1)]),
         'bbox_fill':model.render(grid,d,mode,[(a,b)for a in range(min(a for a,b in motif),max(a for a,b in motif)+1)for b in range(min(b for a,b in motif),max(b for a,b in motif)+1)]),
         'inner_only':model.render(grid,d,'full',[(a,b)for a,b in motif if a>0 and b>0]),
         'first_corner_only':model.render(grid,dict(d,groups=d['groups'][:1]),mode),
         'last_corner_only':model.render(grid,dict(d,groups=d['groups'][-1:]),mode)}
    source=next(x for x in d['groups']if x['corner']==d['exemplar_corner'])
    out['source_color_only']=model.render(grid,dict(d,groups=[x for x in d['groups']if x['color']==source['color']]),mode)
    out['all_source_color']=model.render(grid,dict(d,groups=[dict(x,color=source['color'])for x in d['groups']]),mode)
    out['always_topleft_axes']=model.render(grid,dict(d,groups=[dict(x,corner=(*x['corner'][:2],1,1))for x in d['groups']]),mode)
    sr,sc=source['corner'][2:]
    out['raw_translation']=model.render(grid,dict(d,groups=[dict(x,corner=(*x['corner'][:2],sr,sc))for x in d['groups']]),mode)
    out['preserve_black']=[[v if v==0 else actual[r][c] for c,v in enumerate(row)]for r,row in enumerate(grid)]
    unclipped=[x for x in d['groups']if all(0<=x['corner'][0]+x['corner'][2]*a<len(grid)and 0<=x['corner'][1]+x['corner'][3]*b<len(grid[0])for a,b in motif)]
    out['skip_clipped_corners']=model.render(grid,dict(d,groups=unclipped),mode)
    # Reconstruct a shape from the global extent of all occurrences of its color.
    pts=[(r,c)for r,row in enumerate(grid)for c,v in enumerate(row)if v==source['color']]
    rr,cc,sr,sc=source['corner']
    out['global_color_motif']=model.render(grid,d,mode,[((r-rr)*sr,(c-cc)*sc)for r,c in pts])
    return out


def intermediate(grid,mode):
    d=model.analyze(grid)
    return {'motif':d['motif'],'exemplar_corner':d['exemplar_corner'],
            'active_corners':[{'corner':x['corner'],'color':x['color']}for x in d['groups']],
            'copy_extent':mode}


def counterfactual(program):
    old='(define motif (third exemplar))'
    if program.count(old)!=1:raise ValueError('Expected a unique motif intermediate')
    return program.replace(old,"(define motif '((0 0)))")


def assert_binding(root, binding):
    for item in binding['files']:
        p=(Path(root)/item['path']).resolve()
        if not p.is_relative_to(Path(root).resolve()) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Source drift: '+item['path'])


def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def make_witness(binding, identity, case):
    """Use the exact intake marker; retain full runtime attestation separately."""
    if identity.get('backend') != 'racket' or identity.get('protected') is not True:
        raise ValueError('Witness requires a protected Racket evaluator')
    return {'schema':'arcpuzzles-sequential-dependency-witness-v1',
            'task_id':adapter.TASK,'source_binding':binding,**DEPENDENCY,
            'racket':{'backend':'racket','protected':True},
            'runtime_identity':identity,'cases':[case]}


def run(root, preflight, output, seeds):
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes
    root=root.resolve();preflight=preflight.resolve();output=output.resolve()
    if output.exists():raise ValueError('Use a fresh output directory')
    if type(seeds) is not int or not 1<=seeds<=512:raise ValueError('seeds must be 1..512')
    receipt=json.loads(preflight.read_text());binding=receipt['source_binding']
    if receipt.get('status')!='passed' or receipt['task_id']!=adapter.TASK:raise ValueError('Wrong or failed preflight')
    assert_binding(root,binding)
    output.mkdir(parents=True)
    findings=[];views=0;exposures=0;names=set();survivals={}
    for seed in range(seeds):
        for mode in MODES:
            ep=adapter.generate(seed,{PARAMETER:mode},6,4)
            inputs=[p['input'] for split in ('train','test') for p in ep[split]]
            if len({json.dumps(g) for g in inputs})!=10:raise AssertionError('duplicate inputs')
            predictions=[rivals(p['input'],mode) for p in ep['train']+ep['test']]
            names.update(predictions[0])
            for demos in range(2,7):
                views+=1;exposures+=demos+4
                for name in predictions[0]:
                    fits=all(predictions[i][name]==ep['train'][i]['output'] for i in range(demos))
                    if fits:
                        survivals[name]=survivals.get(name,0)+1
                        bad=[q for q,p in enumerate(ep['test']) if predictions[6+q][name]!=p['output']]
                        if bad:
                            row={'seed':seed,'mode':mode,'demos':demos,'rival':name,'query_indices':bad}
                            findings.append(row)
                            if len(findings)==1:dump(output/'counterexample.json',dict(row,episode=ep,rival_outputs=predictions))
    sweep={'status':'passed' if not findings else 'failed','seeds':seeds,'lesson_views':views,
           'pair_exposures':exposures,'distinct_input_draws':seeds*10,
           'rivals':sorted(names),'query_changing_survivors':len(findings),'findings':findings[:20],
           'demo_fit_counts':survivals,'source_binding':binding,
           'limits':'Python finite-rival audit; nested demo prefixes and matched settings are not independent samples.'}
    dump(output/'teaching.json',sweep)
    if findings:raise AssertionError(f'{len(findings)} query-changing rival survivors; retained counterexample.json')
    # Extra protected checks use max supported demo count, beyond preflight.
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');count=0
    try:
        for mode in MODES:
            ep=adapter.generate(59,{PARAMETER:mode},6,4)
            for split in ('train','test'):
                for p in ep[split]:
                    if apply(ep['program_solution'],p['input'])!=p['output']:raise AssertionError('protected label mismatch')
                    count+=1
        ep=adapter.generate(17,{PARAMETER:MODES[-1]},2,4);pair=ep['test'][3]
        prog=ep['program_solution'];cf=counterfactual(prog)
        actual=apply(prog,pair['input']);alternative=apply(cf,pair['input']);count+=2
        if actual!=pair['output'] or actual==alternative:raise AssertionError('causal counterfactual invalid')
        case={'input':pair['input'],'settings':ep['settings'],'intermediate_value':intermediate(pair['input'],MODES[-1]),
              'program':prog,'output':actual,'counterfactual_program':cf,'counterfactual_output':alternative,
              'ablation':'wrong_intermediate'}
        witness=make_witness(binding,identity,case)
        dump(output/'witness.json',witness)
    finally:bridge.close()
    # Separate live process, not a cached label assertion.
    replay,identity2,bridge2=_real_evaluator(root/'shared/runtime')
    try:
        assert replay(case['program'],case['input'])==case['output']
        assert replay(case['counterfactual_program'],case['input'])==case['counterfactual_output']
    finally:bridge2.close()
    changed=sum(a!=b for ra,rb in zip(case['output'],case['counterfactual_output']) for a,b in zip(ra,rb))
    dump(output/'replay.json',{'status':'passed','source_binding':binding,'racket':identity2,
                             'protected_evaluations':2,'changed_cells':changed})
    dump(output/'max-labels.json',{'status':'passed','source_binding':binding,'racket':identity,
                                 'seed':59,'demos':6,'queries':4,'evaluations_including_causal':count})
    public={};mutation_checks=0;positive_controls=0
    for seed in (17,43):
        for mode in MODES:
            ep=adapter.generate(seed,{PARAMETER:mode},2,4)
            for turn in range(4):
                view=adapter.public_view(ep,turn,13)
                body=public_challenge_bytes(view);key=hashlib.sha256(body).hexdigest()
                if key in public:raise AssertionError('duplicate public payload')
                public[key]=body
            before=adapter.public_view(ep,0,13)
            x=copy.deepcopy(ep);x['settings']={'private':'changed'};x['seed']=-1;x['program_solution']='private'
            for p in x['train']:p['hidden']={'private':True}
            for p in x['test']:p['output']=[[9]]
            for p in x['private']['query_bank']:p['output']=[[9]]
            assert adapter.public_view(x,0,13)==before;mutation_checks+=1
            order=list(range(4));random.Random(13).shuffle(order)
            for i in order[1:]:x['private']['query_bank'][i]['input']=[[9]]
            assert adapter.public_view(x,0,13)==before;mutation_checks+=1
            x=copy.deepcopy(ep);x['train'][0]['output'][0][0]=(x['train'][0]['output'][0][0]+1)%10
            assert public_challenge_bytes(adapter.public_view(x,0,13))!=public_challenge_bytes(before);positive_controls+=1
            short=adapter.generate(seed,{PARAMETER:mode},2,1)
            assert adapter.public_view(short,0,13)==before;mutation_checks+=1
    (output/'public').mkdir()
    for key,body in sorted(public.items()):(output/'public'/f'{key}.json').write_bytes(body)
    dump(output/'public-checks.json',{'status':'passed','single_query_files':len(public),
        'hidden_future_prefix_checks':mutation_checks,'visible_positive_controls':positive_controls,
        'public_ids':sorted(public),'source_binding':binding,'presentation_seed':13,
        'note':'The public directory and its listing stay controller-private; expose only one selected file.'})
    assert_binding(root,binding)
    summary={'status':'passed','task_id':adapter.TASK,'lesson_views':views,'pair_exposures':exposures,
             'rivals':len(names),'query_changing_survivors':0,'protected_evaluations':count+2,
             'public_files':len(public),'causal_changed_cells':changed}
    dump(output/'summary.json',summary);return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=BASE.parents[3])
    parser.add_argument('--preflight',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seeds',type=int,default=64)
    a=parser.parse_args();print(json.dumps(run(a.root,a.preflight,a.out,a.seeds),sort_keys=True))

if __name__=='__main__':main()
