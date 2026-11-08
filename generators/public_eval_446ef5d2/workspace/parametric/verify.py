"""Bounded source-bound audit, public export and protected causal replay.

Run after authoring preflight through review.py run. This never registers,
qualifies or accepts native source. Outputs must be new; source drift fails.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
import random
import sys

HERE=Path(__file__).resolve().parent
TASK='public_eval_446ef5d2'
FIELDS={
 'step_a':'Assemble all translated fragments at the L-marked corner using matching colored contacts.',
 'intermediate':'Same-color connected regions of the assembled rectangle and their actual cell areas, excluding border/background.',
 'step_b':'Recolor all maximum-area completed regions to the removed marker color.',
 'why_b_depends_on_a':'A single completed region can join disconnected raw fragments; raw fragment-region maxima select different cells.'}

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def check_binding(root,receipt):
    root=Path(root).resolve()
    for row in receipt['source_binding']['files']:
        p=root/row['path']
        if not p.resolve().is_relative_to(root) or not p.is_file() or p.is_symlink() or sha(p.read_bytes())!=row['sha256']:
            raise ValueError('stale/invalid source binding: '+row['path'])

def difference(a,b):
    h=min(len(a),len(b));w=min(len(a[0]),len(b[0]))
    overlap=sum(a[r][c]!=b[r][c] for r in range(h) for c in range(w))
    extra=len(a)*len(a[0])+len(b)*len(b[0])-2*h*w
    return {'overlap_changed':overlap,'shape_only_cells':extra,'changed_cells':overlap+extra,
            'shape_changed':(len(a),len(a[0]))!=(len(b),len(b[0]))}

def run(preflight,out,seeds):
    if type(seeds) is not int or not 1<=seeds<=128:raise ValueError('seeds in 1..128 required')
    root=next(p for p in HERE.parents if (p/'src/arcpuzzles/parametric_worker.py').is_file())
    receipt=json.loads(Path(preflight).read_text());check_binding(root,receipt)
    if receipt.get('status')!='passed' or receipt.get('task_id')!=TASK:raise ValueError('expected passing authoring preflight')
    for name,digest in receipt['evidence_sha256'].items():
        if sha(Path(preflight).with_name(name).read_bytes())!=digest:raise ValueError('preflight evidence drift')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    a=load(HERE/'adapter.py','_audit446_adapter');io=load(HERE/'public_io.py','_audit446_public')
    sys.path[:0]=[str(root/'src'),str(root/'shared/runtime')]
    from reviewer_support import public_challenge_bytes
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    from arcpuzzles.review_witness import _validate_programs
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    report={'status':'passed','seeds':seeds,'episodes':0,'rival_checks':0,'ambiguities':[],
            'distinct_inputs':0,'public_files':0,'privacy_checks':0,'racket_evaluations':0,
            'limits':'Finite declared-rival checks and author self-review; no universal uniqueness, owner acceptance or training admission.'}
    seen=set();first=set();profiles=set();global_state=random.getstate()
    names=list(dict.fromkeys(a.PARAMETERS['mode']+list(a.core.RIVALS)))
    for seed in range(seeds):
        scenes=a.core.bank(seed);order=list(range(4));random.Random(f'446ef5d2:presentation:{seed}').shuffle(order)
        first.add(order[0])
        cached={name:[a.predict(s['input'],name,certificate=s['certificate']) for s in scenes] for name in names}
        for scene in scenes:
            seen.add(sha(json.dumps(scene['input']).encode()));profiles.add(scene['profile']['pieces'])
        for mode in a.PARAMETERS['mode']:
            full=a.generate(seed,{'mode':mode},6,4)
            for demos in (2,3,6):
                ep=a.generate(seed,{'mode':mode},demos,4);report['episodes']+=1
                assert ep['train']==full['train'][:demos] and ep['test']==full['test']
                assert a.generate(seed,{'mode':mode},demos,1)['test']==ep['test'][:1]
                for rival in names:
                    if rival==mode:continue
                    report['rival_checks']+=1
                    if cached[rival][:demos]==cached[mode][:demos] and any(cached[rival][6+i]!=cached[mode][6+i] for i in order):
                        report['ambiguities'].append({'seed':seed,'mode':mode,'demos':demos,'rival':rival})
        stress=scenes[9]['input'];bg=scenes[9]['certificate']['background']
        occupied=[(r,c) for r,row in enumerate(stress) for c,v in enumerate(row) if v!=bg]
        assert len(stress)==len(stress[0])==30 and len(occupied)>250
        assert max(r for r,c in occupied)-min(r for r,c in occupied)>=25
        assert max(c for r,c in occupied)-min(c for r,c in occupied)>=25
    assert random.getstate()==global_state
    report['distinct_inputs']=len(seen);report['first_source_indices']=sorted(first);report['piece_counts']=sorted(profiles)
    report['status']='failed' if report['ambiguities'] else 'passed'
    dump(out/'finite-rivals.json',report)
    if report['ambiguities']:raise AssertionError('query-changing lesson ambiguity; see finite-rivals.json')
    execution=[];apply,identity,bridge=_real_evaluator(root/'shared/runtime');public_ids=set();private=[]
    def evaluate(program,grid,expected,label):
        actual=_grid(apply(program,grid));assert actual==expected,label
        report['racket_evaluations']+=1
        execution.append({'label':label,'program_sha256':sha(program.encode()),'input_sha256':sha(json.dumps(grid).encode()),'output_sha256':sha(json.dumps(actual).encode())})
        return actual
    try:
        for seed in (17,43):
            for mode in a.PARAMETERS['mode']:
                ep=a.generate(seed,{'mode':mode},3,4)
                for split in ('train','test'):
                    for i,p in enumerate(ep[split]):evaluate(ep['program_solution'],p['input'],p['output'],[seed,mode,split,i])
                for i in range(4):
                    view=a.public_turn(ep,i);raw=io.encode(view);assert raw==public_challenge_bytes(view)
                    content_id=sha(raw);io.validate(raw,content_id);assert content_id not in public_ids;public_ids.add(content_id)
                    (out/'public').mkdir(exist_ok=True);(out/'public'/f'{content_id}.json').write_bytes(raw)
                    private.append({'id':content_id,'seed':seed,'settings':{'mode':mode},'source_index':ep['private']['query_permutation'][i],'answer':ep['test'][i]['output']})
                    altered=deepcopy(ep);altered['private']={'canary':'secret'};altered['program_solution']='secret'
                    altered['train'][0]['private']='secret';altered['test'][i]['output']=[[True]]
                    for j in range(i+1,4):altered['test'][j]={'input':[[9]],'output':[[8]]}
                    assert a.public_turn(altered,i)==view;report['privacy_checks']+=1
                if mode=='assembly' and seed==17:report['negative_exports_rejected']=io.corruption_probe(view)
            for rival in ('raw_largest','smallest_region','first_region','all_regions'):
                for j,s in enumerate(a.core.bank(seed)[:2]):
                    evaluate(a.rival_program(rival),s['input'],a.predict(s['input'],rival,certificate=s['certificate']),[seed,rival,'demo',j])
        scene=a.core.bank(17)[9];settings={'mode':'largest_region'};program=a.program(settings);counter=a.rival_program('raw_largest')
        correct=evaluate(program,scene['input'],scene['largest_region'],'causal-correct')
        wrong=evaluate(counter,scene['input'],a.predict(scene['input'],'raw_largest',certificate=scene['certificate']),'causal-wrong')
        assert correct!=wrong
        cert=scene['certificate'];cells={(r,c):v for r,row in enumerate(cert['output']) for c,v in enumerate(row) if v not in (cert['background'],cert['base'])}
        regions=a.core.components(cells,True)
        case={'input':scene['input'],'settings':settings,'intermediate_value':{'region_areas':sorted(map(len,regions)),'maximum_area':max(map(len,regions))},
              'program':program,'output':correct,'counterfactual_program':counter,'counterfactual_output':wrong,'ablation':'wrong_intermediate'}
        _validate_programs([case])
        witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':TASK,'source_binding':receipt['source_binding'],
                 **FIELDS,'racket':{'backend':'racket','protected':True},'cases':[case]}
        dump(out/'causal/witness.json',witness)
        validate_sequential_witness({'sequential_dependency':{**FIELDS,'witness_path':'witness.json'}},receipt,lambda _: (out/'causal/witness.json').read_bytes())
        report['causal_difference']=difference(correct,wrong)
    finally:bridge.close()
    replay=replay_witness(root,witness);replay['status']='reviewer_replayed';replay['owner_accepted']=False
    dump(out/'causal/replay.json',replay);dump(out/'private/execution.json',execution);dump(out/'private/queries.json',private)
    report['public_files']=len(public_ids);report['racket']=identity;report['source_binding']=receipt['source_binding']
    check_binding(root,receipt);dump(out/'audit.json',report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=32);args=p.parse_args()
    report=run(args.preflight,args.out,args.seeds)
    print(json.dumps({k:report[k] for k in ('status','episodes','rival_checks','distinct_inputs','racket_evaluations','public_files','causal_difference')}))
if __name__=='__main__':main()
