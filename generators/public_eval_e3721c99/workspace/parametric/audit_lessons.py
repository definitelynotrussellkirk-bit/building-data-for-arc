"""Bounded, repeatable adversarial audit. Run from the library via review.py run.

Writes only private evidence; public views contain one masked query each.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import random

def load():
    p=Path(__file__).with_name('adapter.py');s=importlib.util.spec_from_file_location('_e372_audit_adapter',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def audit(seeds):
    m=load();failures=[];episodes=stress=diff=0;harmful=[];holes_seen=set();areas_seen=set();legend_sides=set()
    rivals=('hole_area','eight_connected','bbox_zero_regions','color_order','reverse_color_order','legend_position_rank','keep_unmatched','cap_at_one','nearest_upper')
    for seed in range(seeds):
        for demos in (2,3,6):
            canonical=m.generate(seed,{'lookup':'exact'},demos,4)
            for lookup in m.SETTINGS:
                ep=m.generate(seed,{'lookup':lookup},demos,4);episodes+=1
                for split in ('train','test'):
                    for p,q in zip(ep[split],canonical[split]):
                        if p['input']!=q['input']:failures.append([seed,demos,lookup,'unmatched_input'])
                        diff+=p['output']!=q['output']
                        legend,payload,prototypes=m.parse(p['input'])
                        for cells in payload:
                            regions=m.holes(cells);holes_seen.add(len(regions));areas_seen.update(map(len,regions))
                stress+=len(ep['test'][-1]['input'])==len(ep['test'][-1]['input'][0])==30
                if len({json.dumps(p['input']) for sp in ('train','test') for p in ep[sp]})!=demos+4:
                    failures.append([seed,demos,lookup,'duplicate_input'])
                for rival in rivals:
                    if all(m.solve(p['input'],lookup,rival=rival)==p['output'] for p in ep['train']):
                        if any(m.solve(p['input'],lookup,rival=rival)!=p['output'] for p in ep['test']):
                            harmful.append([seed,demos,lookup,rival])
                for n in (1,2,3):
                    if m.generate(seed,{'lookup':lookup},demos,n)['test']!=ep['test'][:n]:
                        failures.append([seed,demos,lookup,'unstable_query_prefix'])
    return {'schema':'e372-bounded-audit-v1','seeds':seeds,'episodes':episodes,'stress_30x30_pairs':stress,
            'setting_answer_differences':diff,'observed_payload_hole_counts':sorted(holes_seen),'observed_hole_areas':sorted(areas_seen),
            'rivals':list(rivals),'harmful_survivors':harmful,'failures':failures,
            'scope':'Finite sampler and declared-rival checks, not universal uniqueness or learning benefit.'}

def postflight(preflight_dir,out):
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes,public_challenge_id
    m=load();root=Path(__file__).resolve().parents[4]
    preflight_dir=Path(preflight_dir);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((preflight_dir/'preflight.json').read_text())
    for row in receipt['source_binding']['files']:
        if hashlib.sha256((root/row['path']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Stale source binding')
    execution=json.loads((preflight_dir/'execution.json').read_text())
    selected=next(ep for ep in execution['episodes'] if ep['settings']['lookup']=='nearest_lower')
    p=selected['test'][0];program=selected['program_solution']
    counter=program.replace('(define n (length regions))','(define n (for/sum ([z regions]) (obj-size z)))')
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    try:
        actual=apply(program,p['input']);cf=apply(counter,p['input'])
        assert actual==p['output'] and actual!=cf
    finally:bridge.close()
    names={'step_a':'Flood-fill background inside each object bounding box and discard every region connected to its boundary.',
           'intermediate':'The count of enclosed four-connected cavities for each gray component, plus the measured legend count-to-color map.',
           'step_b':'Use the measured count to choose the exact or greatest-lower legend key, then recolor or erase the gray component.',
           'why_b_depends_on_a':'Neither component size nor total empty area supplies the number of enclosed regions; changing that count selects a different legend color.'}
    witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':receipt['source_binding'],**names,
             'racket':{'backend':'racket','protected':True},'runtime_identity':identity,'cases':[{'input':p['input'],'settings':selected['settings'],
             'intermediate_value':{'legend':m.parse(p['input'])[0],'payload':[{'origin':min(cs),'cavity_count':len(m.holes(cs)),'cavity_area':sum(map(len,m.holes(cs)))} for cs in m.parse(p['input'])[1]]},
             'program':program,'output':actual,'counterfactual_program':counter,'counterfactual_output':cf,'ablation':'wrong_intermediate'}]}
    (out/'witness.json').write_text(json.dumps(witness,sort_keys=True,indent=2)+'\n')
    public=out/'public';public.mkdir();rows=[];seen=set();first_indices=set()
    for ep in execution['episodes']:
        ps=1000+ep['seed'];order=list(range(4));random.Random(ps).shuffle(order)
        views=m.public_views(ep,presentation_seed=ps)
        assert m.public_views(ep,presentation_seed=ps,limit=1)==views[:1]
        private=json.loads(json.dumps(ep));private['seed']=123456;private['settings']={'hidden':'changed'};private['program_solution']='changed'
        for pair in private['test']:pair['output']=[[9]]
        assert m.public_views(private,presentation_seed=ps)==views
        for i,v in enumerate(views):
            content=public_challenge_bytes(v);ident=public_challenge_id(v)
            assert ident not in seen;seen.add(ident)
            assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
            (public/f'{ident}.json').write_bytes(content)
            rows.append({'id':ident,'source_seed':ep['seed'],'settings':ep['settings'],'presentation_seed':ps,'source_index':order[i]})
        first_indices.add(order[0])
    # Independently check the mechanism over many presentation seeds, not just two source seeds.
    firsts={json.dumps(m.public_views(selected,presentation_seed=i,limit=1)[0]['test']) for i in range(32)}
    assert len(firsts)==4
    report={'schema':'e372-public-audit-v1','views':len(rows),'rows':rows,'distinct_first_queries_over_32_presentation_seeds':len(firsts),
            'private_metadata_invariance':True,'first_turn_prefix_stable':True,'public_id_basis':'sha256(exact visible challenge bytes)',
            'source_binding':receipt['source_binding'],'owner_accepted':False,'training_admitted':False}
    (out/'public-audit.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    return names

def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--preflight',type=Path);p.add_argument('--postflight-out',type=Path)
    a=p.parse_args()
    if not 1<=a.seeds<=1024:raise ValueError('Bounded seed count 1..1024 required')
    r=audit(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n')
    if r['failures'] or r['harmful_survivors']:raise SystemExit('Audit failed; inspect report')
    if a.preflight:postflight(a.preflight,a.postflight_out)
    print(json.dumps(r))
if __name__=='__main__':main()
