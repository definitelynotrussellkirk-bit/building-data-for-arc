"""Re-run bounded teaching, exact-source, Racket, causal and privacy evidence.

Run through review.py run python3 .../audit.py --preflight PATH --out NEW_PATH.
The report is author evidence only; it never registers, approves or accepts.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
HOME = HERE.parent.parent
ROOT = HOME.parents[1]
_path = HERE/'prototype.py'
_name = '_rays_audit_proto_' + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
m = importlib.util.module_from_spec(_spec)
sys.modules[_name] = m
_spec.loader.exec_module(m)
PARAMETER = 'ray_extent'
DEPENDENCY = {
    'step_a':'Follow each boundary marker inward to its source bar, measure the gap, and infer the exact D4 template correspondence to each target bar.',
    'intermediate':'A per-marker ray plan: measured source gap, transformed contact port and outward normal for each matching bar.',
    'step_b':'Paint the oriented rays, using the measured source gap as their length in the source_length setting, clipped by the boundary or an original obstacle.',
    'why_b_depends_on_a':'Neither the port/normal nor the copied length is a fixed coordinate or color. Replacing the input-measured distance by one truncates the transferred rays and changes the final grid.'}



def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def check_binding(binding, root):
    root = Path(root).resolve()
    for row in binding['files']:
        path = root/row['path']
        if (path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root)
                or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']):
            raise ValueError('source drift: '+row['path'])


def finite_audit(seeds):
    if type(seeds) is not int or not 1 <= seeds <= 512:
        raise ValueError('seeds must be 1..512')
    failures=[]; episodes=0; pairs=0; rule_names=set(); source_inputs=set()
    for seed in range(seeds):
        streams=[]
        for setting in m.SETTINGS:
            ep = m.generate(seed, {PARAMETER:setting}, 6, 4)
            streams.append([p['input'] for p in ep['train']+ep['test']])
            all_pairs=ep['train']+ep['test']
            predictions=[m.rivals(p['input'],setting) for p in all_pairs]
            names=set(predictions[0]); rule_names |= names
            for p in all_pairs:
                source_inputs.add(hashlib.sha256(json.dumps(p['input']).encode()).hexdigest())
            for count in range(2,7):
                episodes += 1; pairs += count+4
                survivors={name for name in names if all(predictions[i][name] == ep['train'][i]['output'] for i in range(count))}
                wrong=sorted(name for name in survivors if any(predictions[6+i][name] != ep['test'][i]['output'] for i in range(4)))
                if wrong: failures.append({'seed':seed,'demos':count,'setting':setting,'rivals':wrong})
        if streams[0] != streams[1]: raise AssertionError('unmatched input streams')
    return {'status':'passed' if not failures else 'failed', 'seeds':seeds,
            'demo_counts':[2,3,4,5,6], 'settings':list(m.SETTINGS),
            'episodes':episodes, 'pair_exposures':pairs, 'distinct_inputs':len(source_inputs),
            'rivals':sorted(rule_names), 'query_changing_survivors':failures,
            'limits':'Finite declared rivals and bounded seeds; counts include nested lesson prefixes, not independent fresh samples. No universal identifiability or measured training gain.'}


def evidence(preflight, out, seeds):
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from reviewer_support import public_challenge_bytes, public_challenge_id
    preflight=Path(preflight).resolve(); out=Path(out).resolve()
    if out.exists(): raise FileExistsError('choose a new evidence directory')
    receipt=json.loads(preflight.read_text())
    if receipt['task_id'] != HOME.name or receipt['status'] != 'passed':
        raise ValueError('wrong or failed preflight')
    check_binding(receipt['source_binding'],ROOT)
    for filename,digest in receipt['evidence_sha256'].items():
        if hashlib.sha256((preflight.parent/filename).read_bytes()).hexdigest() != digest:
            raise ValueError('preflight evidence drift')
    report=finite_audit(seeds)
    if report['status'] != 'passed':
        out.mkdir(parents=True); write(out/'self-review.json',report)
        raise AssertionError('finite rival survivor; retained report requires repair')
    executed=json.loads((preflight.parent/'execution.json').read_text())
    selected=next(e for e in executed['episodes'] if e['settings'][PARAMETER] == 'source_length')
    inp=selected['test'][3]['input']; program=selected['program_solution']
    needle='(distance (first source-data))'
    assert program.count(needle) == 1
    cf=program.replace(needle,'(distance 1)')
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    labels=0; maximum=[]
    try:
        for setting in m.SETTINGS:
            ep=m.generate(109,{PARAMETER:setting},6,4)
            for p in ep['train']+ep['test']:
                actual=apply(ep['program_solution'],p['input']); labels += 1
                if actual != p['output']: raise AssertionError('maximum lesson Racket label mismatch')
            maximum.append({'settings':{PARAMETER:setting},'seed':109,'demos':6,'queries':4,'labels':10})
        actual=apply(program,inp); wrong=apply(cf,inp); labels += 2
        assert actual == selected['test'][3]['output'] and actual != wrong
    finally:
        bridge.close()
    _,ray_plan=m.base.plans(inp)
    intermediate=[{k:p[k] for k in ('color','source_index','target_index','source_gap','code','contact','normal')} for p in ray_plan]
    witness={'schema':'arcpuzzles-sequential-dependency-witness-v1',
        'source_binding':receipt['source_binding'],'racket':{'backend':'racket','protected':True},
        **DEPENDENCY,'cases':[{'input':inp,'settings':selected['settings'],
        'intermediate_value':intermediate,'program':program,'output':actual,
        'counterfactual_program':cf,'counterfactual_output':wrong,'ablation':'wrong_intermediate'}]}
    encoded=json.dumps(witness).encode()
    validate_sequential_witness({'sequential_dependency':{**DEPENDENCY,'witness_path':'witness.json'}},receipt,lambda _:encoded)
    replay=replay_witness(ROOT,witness)
    # The shared low-level replay uses an owner label even in a reviewer process.
    # Correct this context label; execution facts and runtime identity are retained.
    replay['status']='reviewer_replayed'
    replay['owner_accepted']=False
    out.mkdir(parents=True)
    write(out/'self-review.json',report)
    write(out/'witness.json',witness)
    write(out/'replay.json',replay)
    write(out/'maximum-labels.json',{'status':'passed','racket':identity,'evaluations':labels,
          'maximum_jobs':maximum,'witness_evaluations':2,'owner_accepted':False})
    public=out/'public'; public.mkdir()
    views={}; timeline=[]; invariance=0
    first_indices=set()
    for ei,ep in enumerate(executed['episodes']):
        timeline_ep=m.present(ep,ei+317,4)
        assert m.present(ep,ei+317,1)['views'][0] == timeline_ep['views'][0]
        altered=deepcopy(ep); altered['seed']=-992; altered['settings']={'hidden':'changed'}; altered['program_solution']='changed'
        for p in altered['test']: p['output']=[[9]]
        assert m.present(altered,ei+317,4)['views'] == timeline_ep['views']; invariance += 1
        first=timeline_ep['private']['source_indices'][0]
        later=next(j for j in range(4) if j != first)
        altered['test'][later]['input']=[[5]]
        assert m.present(altered,ei+317,1)['views'] == timeline_ep['views'][:1]; invariance += 1
        ids=[]
        for view in timeline_ep['views']:
            pid=public_challenge_id(view)
            if pid in views: raise AssertionError('duplicate visible challenge')
            views[pid]=public_challenge_bytes(view); ids.append(pid)
        timeline.append({'episode':ei,'source_indices':timeline_ep['private']['source_indices'],'view_ids':ids})
        for seed in range(16): first_indices.add(m.present(ep,seed,1)['private']['source_indices'][0])
    assert len(first_indices) > 1
    for pid,raw in sorted(views.items()): (public/(pid+'.json')).write_bytes(raw)
    write(out/'presentation.private.json',{'schema':'task-authoring-sequential-views-v1',
        'controller_only':True,'timeline':timeline,'public_ids_sorted':sorted(views),
        'model_instruction':'Deliver one public file at a time. Do not expose the listing, mapping, answers or final-turn hints.'})
    write(out/'public-export-check.json',{'status':'passed','files':len(views),'private_mutation_checks':invariance,
        'first_query_indices_seen':sorted(first_indices),'first_turn_prefix_invariant':True,
        'source_binding':receipt['source_binding'],'limits':'One query per view; this entire bundle is private controller data.'})
    check_binding(receipt['source_binding'],ROOT)
    return {'status':'passed','episodes':report['episodes'],'racket_evaluations':labels+replay['evaluations'],
            'public_files':len(views),'causal_changed_cells':sum(a!=b for ra,rb in zip(actual,wrong) for a,b in zip(ra,rb)),
            'owner_accepted':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preflight',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,default=32)
    args=p.parse_args()
    print(json.dumps(evidence(args.preflight,args.out,args.seeds),sort_keys=True))


if __name__ == '__main__': main()
