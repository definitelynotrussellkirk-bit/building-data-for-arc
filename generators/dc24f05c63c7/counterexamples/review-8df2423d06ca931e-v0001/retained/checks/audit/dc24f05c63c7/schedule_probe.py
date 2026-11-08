#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from copy import deepcopy
from pathlib import Path

TASK='dc24f05c63c7'
ROOT=Path(__file__).resolve().parents[3]
GEN=ROOT/'repo/generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_dc_gen',GEN); gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

def info(g):
    x,e=gen._analyse(g)
    if e: raise AssertionError(e)
    return x

def kind_bbox(kind, quadrant):
    su,sv=gen._QUADRANT_SIGNS[quadrant]
    pts=tuple((su*u,sv*v) for u,v in gen._MOTIF_PATTERNS[kind])
    return gen._bbox_points(pts)

def adaptive_rival(demos, query):
    first=info(demos[0]['input'])
    delta=(gen._MOTIF_KINDS.index(first['motif_kind'])-gen._QUADRANTS.index(first['motif_quadrant']))%4
    for pair in demos:
        x=info(pair['input'])
        assert (gen._MOTIF_KINDS.index(x['motif_kind'])-gen._QUADRANTS.index(x['motif_quadrant']))%4==delta
    q=info(query)
    predicted=gen._MOTIF_KINDS[(gen._QUADRANTS.index(q['motif_quadrant'])+delta)%4]
    out=deepcopy(query); target=q['target_frame']
    for u,v in kind_bbox(predicted,q['motif_quadrant']):
        r,c=gen._glob(target[0],target[1],target[2],u,v); out[r][c]=8
    return out,predicted,delta

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['prepare','finish'],required=True); ap.add_argument('--ordinary-racket',type=Path); ap.add_argument('--counter-racket',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    base=a.out.parent
    if a.mode=='prepare':
        total=matches=hook_accepts=0; samples=[]
        for band in ('easy','medium','hard'):
            for seed in range(20):
                for start in range(8):
                    demos=[]
                    for idx in range(start,start+4):
                        g=gen.generate(seed,idx,difficulty=band); demos.append({'input':g,'output':gen.rule_mirror(g)})
                    q=gen.generate(seed,start+4,difficulty=band); intended=gen.rule_mirror(q)
                    rival,predicted,delta=adaptive_rival(demos,q)
                    total+=1; matches+=rival==intended
                    hook_accepts+=gen.lesson_identifiable(demos,{'input':q,'output':intended})==[]
                    if len(samples)<64:
                        samples.append({'band':band,'seed':seed,'start':start,'input':q,'rival_output':rival,'predicted_kind':predicted,'delta':delta})
        # Make a legal exact-override query that breaks the ordinary within-seed pairing.
        seed=0; start=0; band='medium'
        demos=[]
        for idx in range(start,start+4):
            g=gen.generate(seed,idx,difficulty=band); demos.append({'input':g,'output':gen.rule_mirror(g)})
        normal=gen.generate(seed,start+4,difficulty=band); ni=info(normal)
        normal_bbox=(ni['bbox_h'],ni['bbox_w'])
        alternatives=[k for k in gen._MOTIF_KINDS if (len({u for u,v in kind_bbox(k,ni['motif_quadrant'])}),len({v for u,v in kind_bbox(k,ni['motif_quadrant'])}))!=normal_bbox]
        alt=alternatives[0]
        counter=gen.generate(seed,start+4,difficulty=band,motif_kind=alt)
        rival,predicted,delta=adaptive_rival(demos,counter)
        pre={'schema':'audit_dc_schedule_prepare/1','task_id':TASK,'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),'lesson_sample':{'denominator':total,'adaptive_rival_matches':matches,'lesson_hook_accepts':hook_accepts,'bands':['easy','medium','hard'],'seeds':'0..19','starts':'0..7'},'ordinary_cases':samples,'counterexample':{'seed':seed,'start':start,'query_sample_index':start+4,'difficulty':band,'override':{'motif_kind':alt},'input':counter,'self_check':gen.self_check(counter),'observed':gen.observe_overrides(counter),'normal_scheduled_kind':ni['motif_kind'],'adaptive_predicted_kind':predicted,'delta':delta,'rival_output':rival,'python_authority_output':gen.rule_mirror(counter),'disagrees':rival!=gen.rule_mirror(counter)}}
        (base/'ordinary_inputs.json').write_text(json.dumps({'inputs':[x['input'] for x in samples]},indent=2)+'\n')
        (base/'counter_input.json').write_text(json.dumps(counter,indent=2)+'\n')
        a.out.write_text(json.dumps(pre,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'lessons':total,'matches':matches,'hook_accepts':hook_accepts,'ordinary_racket_cases':len(samples),'counterexample_disagrees':pre['counterexample']['disagrees'],'alternative_kind':alt,'out':str(a.out)}))
        return
    pre=json.loads((base/'schedule_prepare.json').read_text()); ordinary=json.loads(a.ordinary_racket.read_text()); counter=json.loads(a.counter_racket.read_text())
    oracle_matches=sum(case['rival_output']==res['output'] for case,res in zip(pre['ordinary_cases'],ordinary['results']))
    c=pre['counterexample']; c_actual=counter['results'][0]['output']
    report={'schema':'audit_dc24f05c63c7/1','task_id':TASK,'generator_sha256':pre['generator_sha256'],'rule_hash':counter['executed_rule_hash'],'rule_text_sha256':counter['rule_text_sha256'],'lesson_sample':pre['lesson_sample'],'racket_spot_check':{'denominator':len(ordinary['results']),'adaptive_rival_matches_racket':oracle_matches},'counterexample':{**c,'racket_output':c_actual,'rival_disagrees_with_racket':c['rival_output']!=c_actual,'input_sha256':counter['results'][0]['input_sha256'],'output_sha256':counter['results'][0]['output_sha256']},'finding':'Within a seed, motif_quadrant and motif_kind advance in lockstep with a constant offset. A demo-fitted quadrant-to-kind mapping predicts every ordinary query while ignoring its color-8 motif geometry; an exact motif_kind override breaks the shortcut.'}
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps({'lesson_matches':report['lesson_sample']['adaptive_rival_matches'],'lesson_total':report['lesson_sample']['denominator'],'racket_matches':oracle_matches,'racket_total':len(ordinary['results']),'counterexample_disagrees':report['counterexample']['rival_disagrees_with_racket'],'out':str(a.out)}))
if __name__=='__main__': main()
