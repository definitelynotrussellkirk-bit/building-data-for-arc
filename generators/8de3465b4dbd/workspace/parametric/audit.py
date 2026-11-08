"""Bounded task-local auditor. Run via review.py run from the packet root.

Claims are checked using protected Racket. Outputs are private except for each
single public/<visible-sha>.json selected by the caller; no turn controller.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def load_native():
    path = Path(__file__).with_name('native.py')
    spec = importlib.util.spec_from_file_location('audit_local_native',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def check_counts(m, seeds):
    from reviewer_support import public_challenge_bytes
    requests = pairs = matches = turns = 0
    seen = set()
    order_set = set()
    for seed in range(seeds):
        reference = m.generate(seed,{m.KEY:m.SETTINGS[0]},6,4)
        for setting in m.SETTINGS:
            whole = m.generate(seed,{m.KEY:setting},6,4)
            order_set.add(tuple(whole['private']['query_source_indices']))
            for pair in whole['train']+whole['test']:
                seen.add(hashlib.sha256(raw(pair['input'])).hexdigest())
            for demos in range(2,7):
                for queries in range(1,5):
                    ep = m.generate(seed,{m.KEY:setting},demos,queries)
                    assert ep['train'] == whole['train'][:demos]
                    assert ep['test'] == whole['test'][:queries]
                    all_pairs = ep['train']+ep['test']
                    assert len({raw(p['input']) for p in all_pairs}) == len(all_pairs)
                    assert [p['input'] for p in ep['train']] == [p['input'] for p in reference['train'][:demos]]
                    assert [p['input'] for p in ep['test']] == [p['input'] for p in reference['test'][:queries]]
                    if setting!=m.SETTINGS[0]: matches+=1
                    for i in range(queries):
                        view = m.public_turn(ep,i)
                        assert view == {'train':ep['train'],'test':[{'input':ep['test'][i]['input']}]} 
                        encoded = public_challenge_bytes(view)
                        mutated = copy.deepcopy(ep)
                        mutated['private'] = {'anything':'changed'}
                        mutated['program_solution'] = 'private mutation'
                        for p in mutated['test']: p['output'] = [[0]]
                        for j in range(i+1,queries): mutated['test'][j]['input'] = [[9]]
                        assert public_challenge_bytes(m.public_turn(mutated,i)) == encoded
                        turns+=1
                    requests+=1
                    pairs+=len(all_pairs)
    return {'seeds':seeds,'count_setting_requests':requests,'pair_instances':pairs,
            'distinct_inputs':len(seen),'matched_input_comparisons':matches,
            'public_turn_checks':turns,'distinct_query_permutations':len(order_set),'failures':0}


def protected_examples(m):
    from reviewer_support import find_root, public_challenge_bytes
    from arcpuzzles.parametric_worker import _real_evaluator
    from arc_repl import racket_bridge
    root = find_root(__file__)
    runtime = Path(racket_bridge.__file__).resolve().parents[1]
    assert runtime in (root,root/'shared/runtime')
    apply,identity,bridge = _real_evaluator(runtime)
    episodes,teachings,public = [],[],{}
    evaluations = 0
    try:
        for seed in (0,17):
            for setting in m.SETTINGS:
                ep = m.generate(seed,{m.KEY:setting},3,4)
                for pair in ep['train']+ep['test']:
                    actual = apply(ep['program_solution'],pair['input']); evaluations+=1
                    assert actual == pair['output'], ('selected Racket disagreement',seed,setting)
                    pair['output'] = actual
                episodes.append(ep)
                for i in range(4):
                    payload = public_challenge_bytes(m.public_turn(ep,i))
                    digest = hashlib.sha256(payload).hexdigest()
                    assert digest not in public
                    public[digest] = payload
        # A finite hypothesis test, using only the first two demonstrations.
        # Every rival is executed on all four queries too; runtime errors fail.
        for setting in m.SETTINGS:
            ep = m.generate(0,{m.KEY:setting},2,4)
            names = [m.SETTINGS[1]] if setting==m.SETTINGS[0] else list(m.RIVALS)
            for name in names:
                dm,qm,labels = [],[],[]
                source = m.rule_for(name)
                for split in ('train','test'):
                    for i,pair in enumerate(ep[split]):
                        actual = apply(source,pair['input']); evaluations+=1
                        assert actual == m.predict(pair['input'],name), ('rival mirror disagreement',name)
                        labels.append({'split':split,'index':i,'input':pair['input'],'output':actual})
                        if actual!=pair['output']: (dm if split=='train' else qm).append(i)
                assert dm, ('rival survived both demonstrations',setting,name,qm)
                teachings.append({'setting':setting,'rival':name,'program':source,'demo_mismatches':dm,
                                  'query_mismatches':qm,'labels':labels})
    finally: bridge.close()
    return episodes,teachings,public,{'racket':identity,'evaluations':evaluations}


def write_public(out, payloads):
    """Physical public order depends on visible IDs, never private episode order."""
    directory = out/'public'
    directory.mkdir()
    for digest,payload in sorted(payloads.items()):
        if hashlib.sha256(payload).hexdigest()!=digest: raise ValueError('public bytes/ID mismatch')
        (directory/f'{digest}.json').write_bytes(payload)


def run(out, seeds=20):
    if type(seeds) is not int or not 1<=seeds<=100: raise ValueError('seeds must be 1..100')
    out = Path(out)
    if out.exists(): raise FileExistsError('use a fresh evidence directory')
    m=load_native()
    sweep = check_counts(m,seeds)
    episodes,teachings,public,execution = protected_examples(m)
    out.mkdir(parents=True)
    (out/'private').mkdir()
    (out/'private/episodes.json').write_bytes(raw(episodes))
    (out/'private/teaching.json').write_bytes(raw(teachings))
    write_public(out,public)
    summary = {'task_id':m.TASK_ID,'status':'passed','scope':'finite self-review; no owner acceptance or training admission',
               'sweep':sweep,'execution':execution,'lessons':len(episodes),'rivals':len(teachings),
               'public_files':len(public),'training_admitted':False}
    (out/'summary.json').write_bytes(raw(summary))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--seeds',type=int,default=20)
    args=parser.parse_args()
    print(json.dumps(run(args.out,args.seeds),indent=2))
