"""Source-bound marked-partition audit, protected replay and public projection."""
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
spec=importlib.util.spec_from_file_location('_partition_audit_'+hashlib.sha256(str(BASE).encode()).hexdigest(),BASE/'adapter.py')
adapter=importlib.util.module_from_spec(spec);sys.modules[spec.name]=adapter;spec.loader.exec_module(adapter)
model=adapter.model
PARAMETER='side_assignment'
MODES=('marker_first','marker_second')
DEPENDENCY={
 'step_a':'Parse the four panels, separate the long divider from the singleton hint by eight-connectivity, and flood the divider complement from that hint using four-neighbor moves.',
 'intermediate':'The input-derived divider coordinates and exact indicated connected-region mask.',
 'step_b':'Select the appropriate source at each side-mask cell, overlay sources with first-source precedence on divider cells, and write only the fourth panel.',
 'why_b_depends_on_a':'A bent or diagonal separator cannot be reduced to a fixed half-plane or palette choice. The hint and divider topology determine the region mask that B uses at every non-divider destination cell.'}


def rivals(grid,mode):
    d=model.analyze(grid);ph,pw=d['shape'];bg=d['background'];panels=d['panels'];line=set(d['line'])
    domain={(r,c)for r in range(ph)for c in range(pw)}
    a,b=panels[1:3];marked=set(d['selected']);first=mode=='marker_first'
    def mask(cells):return model.render(grid,d,mode,selected=cells)
    def panel(piece):
        out=[row[:]for row in grid];top,left,_,_=d['boxes'][3]
        for r in range(ph):
            for c in range(pw):out[top+r][left+c]=piece[r][c]
        return out
    union=lambda x,y:[[x[r][c]if x[r][c]!=bg else y[r][c]for c in range(pw)]for r in range(ph)]
    out={'identity':[row[:]for row in grid],
         'wrong_setting':model.render(grid,d,MODES[1-MODES.index(mode)]),
         'copy_first':panel(a),'copy_second':panel(b),
         'union_first':panel(union(a,b)),'union_second':panel(union(b,a)),
         'intersection':panel([[a[r][c]if a[r][c]!=bg and b[r][c]!=bg else bg for c in range(pw)]for r in range(ph)]),
         'xor':panel([[a[r][c]if a[r][c]!=bg and b[r][c]==bg else b[r][c]if b[r][c]!=bg and a[r][c]==bg else bg for c in range(pw)]for r in range(ph)]),
         'first_region':mask(d['regions'][0]),'last_region':mask(d['regions'][-1]),
         'largest_region':mask(max(d['regions'],key=len)),'smallest_region':mask(min(d['regions'],key=len)),
         'eight_neighbor_flood':mask(model.flood(d['hint'],domain-line,True)),
         'top_half':mask({(r,c)for r,c in domain if r<ph//2}),
         'left_half':mask({(r,c)for r,c in domain if c<pw//2}),
         'boundary_second':model.render(grid,d,mode,boundary='second'),
         'erase_boundary':model.render(grid,d,mode,boundary='background'),
         'hint_is_boundary':model.render(grid,dict(d,line=sorted(line|{d['hint']})),mode)}
    for which,source in (('first',a),('second',b)):
        raw=model.render(grid,d,mode);top,left,_,_=d['boxes'][3]
        for r,c in line:raw[top+r][left+c]=source[r][c]
        out['boundary_'+which+'_only']=raw
    start,end=min(line),max(line)
    def cross(p):return (end[0]-start[0])*(p[1]-start[1])-(end[1]-start[1])*(p[0]-start[0])
    sign=1 if cross(d['hint'])>=0 else -1
    out['endpoint_halfplane']=mask({p for p in domain-line if sign*cross(p)>=0})
    ca=min(v for row in a for v in row if v!=bg);cb=min(v for row in b for v in row if v!=bg)
    area_a=sum(v!=bg for row in a for v in row);area_b=sum(v!=bg for row in b for v in row)
    for name,condition in (('palette_low_first',ca<cb),('palette_high_first',ca>cb),
                           ('area_low_first',area_a<area_b),('area_high_first',area_a>area_b)):
        chosen=marked if condition else domain-line-marked
        out[name]=mask(chosen)
    return out


def intermediate(grid,mode):
    d=model.analyze(grid)
    return {'divider':d['line'],'hint':d['hint'],'selected_region':d['selected'],
            'region_sizes':[len(x)for x in d['regions']], 'side_assignment':mode}


def counterfactual(program):
    old='(define selected (flood hint (filter (lambda (p) (not (member p divider))) domain) directions4))'
    if program.count(old)!=1:raise ValueError('Expected one indicated-region intermediate')
    return program.replace(old,"(define selected '())")


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
