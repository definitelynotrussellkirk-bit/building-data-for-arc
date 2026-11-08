"""Reproducible generated-lesson audit and honest original-label diagnostics.

Execute via review.py run. The diagnostic is deliberately NOT named preflight,
qualification or acceptance. A failing supplied gold label remains a blocker.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import tempfile

TASK='public_eval_d8e07eb2'
ROOT=Path(__file__).resolve().parents[4]


def load():
    p=Path(__file__).with_name('adapter.py')
    s=importlib.util.spec_from_file_location('_d8_audit_adapter',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(seeds):
    if type(seeds) is not int or not 1<=seeds<=1024:
        raise ValueError('Use a bounded exact integer seed count in 1..1024')
    binding=source_binding(ROOT)
    m=load();failures=[];harmful=[];episodes=labels=stress=differences=0
    backgrounds=set();board_sizes=set();statuses={mode:set() for mode in m.SETTINGS}
    for seed in range(seeds):
        for nd in (4,5,6):
            canonical=m.generate(seed,{'match':'color_shape'},nd,4)
            for mode in m.SETTINGS:
                ep=canonical if mode=='color_shape' else m.generate(seed,{'match':mode},nd,4)
                episodes+=1;labels+=nd+4
                for split in ('train','test'):
                    for p,q in zip(ep[split],canonical[split]):
                        if p['input']!=q['input']:failures.append([seed,nd,mode,'setting_dependent_input'])
                        differences+=p['output']!=q['output']
                        d=m.parse(p['input']);backgrounds.add(d['bg']);board_sizes.add((len(d['rows']),len(d['cols'])))
                        statuses[mode].add(p['output'][-1][0])
                stress+=any(len(p['input'])==len(p['input'][0])==30 for p in ep['test'])
                if len({json.dumps(p['input']) for sp in ('train','test') for p in ep[sp]})!=nd+4:
                    failures.append([seed,nd,mode,'duplicate_input'])
                for n in (1,2,3):
                    if m.generate(seed,{'match':mode},nd,n)['test']!=ep['test'][:n]:
                        failures.append([seed,nd,mode,'unstable_query_prefix'])
                if ep['test']!=m.generate(seed,{'match':mode},4,4)['test']:
                    failures.append([seed,nd,mode,'demo_query_coupling'])
                for rival in m.RIVALS:
                    if all(m.solve(p['input'],mode,rival=rival)==p['output'] for p in ep['train']):
                        if any(m.solve(p['input'],mode,rival=rival)!=p['output'] for p in ep['test']):
                            harmful.append([seed,nd,mode,rival])
    if source_binding(ROOT)!=binding:failures.append(['source_changed_during_audit'])
    return {'schema':'d8-bounded-generated-audit-v1','status':'passed_bounded_generated_checks' if not failures and not harmful else 'failed',
            'source_binding':binding,
            'seeds':seeds,'minimum_demos':4,'episodes':episodes,'labeled_pairs':labels,
            'stress_30x30_pairs':stress,'setting_answer_differences':differences,
            'backgrounds':sorted(backgrounds),'board_sizes':sorted(board_sizes),'observed_footer_colors':{k:sorted(v) for k,v in statuses.items()},
            'rivals':list(m.RIVALS),'harmful_survivors':harmful,'failures':failures,
            'scope':'Finite sampler and declared-rival evidence only. Does not waive any failing original label, prove universal uniqueness or grant admission.'}


def source_binding(root):
    home=root/'generators'/TASK
    sources=[p for p in home.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
             (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json'))]
    sources+=[p for p in (root/'shared/runtime').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.rkt')]
    # Pure Python audit works with only the task home; protected execution
    # still requires the explicitly selected checkout runtime.
    optional_tool=root/'shared/tools/comment_solutions.py'
    if optional_tool.is_file():
        sources.append(optional_tool)
    return {'task_id':TASK,'files':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in sorted(sources)]}


def execute(out):
    """Evaluate all original and generated labels; retain conflicts, never bless them."""
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    from arcpuzzles.review_programs import strict_programs
    from reviewer_support import public_challenge_bytes,public_challenge_id
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    out=Path(out)
    if out.exists():raise ValueError('Choose a fresh diagnostic output directory')
    m=load();root=ROOT;home=root/'generators'/TASK;binding=source_binding(root)
    data=root/'shared/data/raw';parent_path=data/'arc-agi_evaluation_challenges.json';gold_path=data/'arc-agi_evaluation_solutions.json'
    frozen_data={p.name:sha(p) for p in (parent_path,gold_path)}
    parent=json.loads(parent_path.read_text())['d8e07eb2'];gold=json.loads(gold_path.read_text())['d8e07eb2']
    syntax=strict_programs(root,[m.program({'match':mode}) for mode in m.SETTINGS])
    run,identity,bridge=_real_evaluator(root/'shared/runtime');calls=0
    def apply(program,g):
        nonlocal calls
        calls+=1
        return _grid(run(program,_grid(g)))
    originals=[];episodes=[];jobs=[];relocated=[];witness=None
    try:
        if identity.get('backend')!='racket' or identity.get('protected') is not True:
            raise AssertionError('Protected Racket is required')
        for split in ('train','test'):
            for index,pair in enumerate(parent[split]):
                g=[[int(c) for c in row] for row in pair['input']]
                want=[[int(c) for c in row] for row in pair.get('output',gold[index] if split=='test' else [])]
                actual=apply(m.program({'match':'color_shape'}),g)
                if actual!=m.solve(g,'color_shape'):raise AssertionError('Independent Racket and Python semantics disagree')
                diffs=[{'row':r,'col':c,'input':g[r][c],'predicted':actual[r][c],'supplied':want[r][c]}
                       for r in range(len(g)) for c in range(len(g[0])) if actual[r][c]!=want[r][c]]
                originals.append({'split':split,'index':index,'matched':not diffs,'differences':diffs,'input':g,'actual':actual,'supplied':want})
        for mode in m.SETTINGS:
            for seed in (17,43):
                ep=m.generate(seed,{'match':mode},4,4)
                for split in ('train','test'):
                    for pair in ep[split]:
                        if apply(ep['program_solution'],pair['input'])!=pair['output']:
                            raise AssertionError((mode,seed,split,'label mismatch'))
                survivors=[]
                for alternative in m.SETTINGS:
                    if all(apply(m.program({'match':alternative}),p['input'])==p['output'] for p in ep['train']):
                        survivors.append(alternative)
                if survivors!=[mode]:raise AssertionError(('Ambiguous lesson',mode,seed,survivors))
                episodes.append({'settings':{'match':mode},'seed':seed,**ep})
                jobs.append({'settings':{'match':mode},'seed':seed,'demos':4,'queries':4,'survivors':survivors})
        selected=next(e for e in episodes if e['settings']['match']=='color_shape')
        pair=selected['train'][2]  # Constructed near-line: color determines whether it is complete.
        d=m.parse(pair['input']);actual_positions=sorted(m.matched_positions(d,'color_shape'))
        false_positions=sorted(m.matched_positions(d,'shape_only'))
        program=selected['program_solution']
        start=program.index('  (define matched\n');end=program.index('  (define success',start)
        replacement='  (define matched (list '+ ' '.join(f'(list {r} {c})' for r,c in false_positions)+'))\n'
        counter=program[:start]+replacement+program[end:]
        strict_programs(root,[counter])
        actual=apply(program,pair['input']);cf=apply(counter,pair['input'])
        if actual!=pair['output'] or actual==cf or actual[-1][0]!=2 or cf[-1][0]!=3:
            raise AssertionError('The wrong matched-position set must change failure into success')
        names={'step_a':'Decode tight colored header masks and match them to board symbols.',
               'intermediate':'The set of matched (board row, board column) coordinates.',
               'step_b':'Test the matched coordinates for a complete row/column, then highlight slots and render the success/failure panels.',
               'why_b_depends_on_a':'A same-silhouette wrong-color decoy changes a near-line to a complete row only after matching; board dimensions or selected-symbol count cannot decide this status.'}
        witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':binding,**names,
                 'racket':{'backend':'racket','protected':True},'runtime_identity':identity,
                 'cases':[{'input':pair['input'],'settings':selected['settings'],
                           'intermediate_value':{'matched_positions':actual_positions,'counterfactual_positions':false_positions},
                           'program':program,'output':actual,'counterfactual_program':counter,'counterfactual_output':cf,
                           'ablation':'wrong_intermediate'}]}
        # This checks the witness's structural schema against this diagnostic's
        # source/program map. It DOES NOT turn the diagnostic into qualification.
        program_map={json.dumps({'match':mode},sort_keys=True,separators=(',',':')):hashlib.sha256(m.program({'match':mode}).encode()).hexdigest() for mode in m.SETTINGS}
        validate_sequential_witness({'sequential_dependency':{**names,'witness_path':'witness.json'}},
            {'source_binding':binding,'programs':program_map},lambda _:json.dumps(witness).encode())
        replay_actual=apply(program,pair['input']);replay_counter=apply(counter,pair['input'])
        if replay_actual!=actual or replay_counter!=cf:
            raise AssertionError('Diagnostic causal replay changed labels')
        with tempfile.TemporaryDirectory(prefix='d8-base-only-') as tmp:
            isolated=Path(tmp)/'generator.py';shutil.copyfile(home/'generator.py',isolated)
            spec=importlib.util.spec_from_file_location('_d8_base_only',isolated)
            base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
            for index in range(6):
                g=base.generate(29,index)
                if base.generate(29,index)!=g or base.self_check(g):raise AssertionError('Portable sampler failure')
                actual=apply(m.program({'match':'color_shape'}),g)
                if actual!=base.solve(g):raise AssertionError('Relocated base mismatch')
                relocated.append({'seed':29,'sample_index':index,'input':g,'output':actual})
    finally:bridge.close()
    for row in binding['files']:
        if sha(root/row['path'])!=row['sha256']:raise AssertionError('Source changed during execution')
    for p in (parent_path,gold_path):
        if sha(p)!=frozen_data[p.name]:raise AssertionError('Original data changed')
    out.mkdir(parents=True)
    write(out/'execution.json',{'schema':'d8-generated-diagnostic-execution-v1','source_binding':binding,'racket':identity,'program_syntax':syntax,'jobs':jobs,'episodes':episodes})
    write(out/'original-pairs.json',{'schema':'d8-original-parity-diagnostic-v1','source_binding':binding,'racket':identity,
                                   'status':'passed' if all(p['matched'] for p in originals) else 'failed',
                                   'matches':sum(p['matched'] for p in originals),'total':len(originals),'pairs':originals,'original_files_sha256':frozen_data})
    write(out/'witness.json',witness)
    write(out/'causal-replay.json',{'schema':'d8-blocked-prototype-causal-replay-v1',
        'status':'diagnostic_replayed_not_qualified','source_binding':binding,'racket':identity,
        'cases':1,'different_outputs':True,'official_preflight_passed':False,
        'limits':'Direct protected construction and replay; no successful official preflight, native qualification or owner acceptance.'})
    write(out/'relocated-base.json',{'source_binding':binding,'racket':identity,'pairs':relocated})
    public=out/'public';public.mkdir();rows=[];seen=set()
    for ep in episodes:
        ps=1000+ep['seed'];order=list(range(4));random.Random(ps).shuffle(order)
        views=m.public_views(ep,presentation_seed=ps)
        if m.public_views(ep,presentation_seed=ps,limit=1)!=views[:1]:raise AssertionError('First-turn mismatch')
        hidden=copy.deepcopy(ep);hidden['settings']={'private':'changed'};hidden['seed']=-1;hidden['program_solution']='changed'
        for p in hidden['test']:p['output']=[[9]]
        if m.public_views(hidden,presentation_seed=ps)!=views:raise AssertionError('Private metadata leak')
        future=copy.deepcopy(ep)
        for index,pair in enumerate(future['test']):
            if index!=order[0]:pair['input']=[[9]]
        if m.public_views(future,presentation_seed=ps,limit=1)!=views[:1]:
            raise AssertionError('Future input leaked into first turn')
        visible=copy.deepcopy(ep);visible['test'][order[0]]['input']=[[9]]
        if m.public_views(visible,presentation_seed=ps,limit=1)==views[:1]:
            raise AssertionError('First-turn positive control did not change')
        for index,v in enumerate(views):
            ident=public_challenge_id(v);blob=public_challenge_bytes(v)
            if ident in seen:raise AssertionError('Duplicate public view')
            seen.add(ident);(public/(ident+'.json')).write_bytes(blob)
            rows.append({'id':ident,'source_seed':ep['seed'],'settings':ep['settings'],'presentation_seed':ps,'source_index':order[index]})
    firsts={json.dumps(m.public_views(episodes[0],presentation_seed=i,limit=1)[0]['test']) for i in range(32)}
    if len(firsts)!=4:raise AssertionError('Query presentation is tied to a source ordinal')
    write(out/'public-audit.json',{'schema':'d8-public-projection-audit-v1','source_binding':binding,'views':len(rows),'rows':rows,
                                 'private_metadata_invariance':True,'future_query_invariance':True,
                                 'visible_query_positive_control':True,'first_turn_prefix_stable':True,'distinct_first_queries':len(firsts)})
    report={'schema':'d8-authoring-diagnostic-not-preflight-v1','task_id':TASK,
            'status':'blocked_original_labels' if not all(p['matched'] for p in originals) else 'passed_diagnostic_only',
            'source_binding':binding,'programs':program_map,'racket':identity,'racket_evaluations':calls,
            'original_labels_matched':sum(p['matched'] for p in originals),'original_labels_total':len(originals),
            'generated_labels_verified':sum(len(ep['train'])+len(ep['test']) for ep in episodes),
            'generated_jobs':len(jobs),'relocated_base_labels':len(relocated),'public_views':len(rows),
            'witness_changed_cells':sum(a!=b for r,s in zip(witness['cases'][0]['output'],witness['cases'][0]['counterfactual_output']) for a,b in zip(r,s)),
            'witness_status_change':[2,3],'owner_accepted':False,'training_admitted':False,
            'evidence_sha256':{p.name:sha(p) for p in sorted(out.glob('*.json'))},
            'limitation':'A diagnostic is not official preflight or qualification. One unresolved original-label mismatch blocks reference acceptance.'}
    write(out/'diagnostics.json',report)
    conflicts=[p for p in originals if not p['matched']]
    write(home/'workspace/original-label-conflict.json',{'schema':'d8-original-label-conflict-v1','source_binding':binding,
        'status':'requires_owner_interpretation_or_annotation_review','original_files_sha256':frozen_data,'cases':conflicts,
        'next_action':'Inspect the nine header cells in train[0]. Decide whether the inferred symbol-preserving rule is incomplete or the supplied label needs an explicitly authorized correction. Do not silently change the frozen parent or special-case this grid.'})
    write(home/'workspace/parametric/evidence/manifest.json',{'schema':'d8-unapproved-diagnostic-inventory-v1','task_id':TASK,
        'source_binding':binding,'owner_registration_required':True,'status':'blocked_original_labels'})
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--execute-out',type=Path)
    a=p.parse_args();result=audit(a.seeds);write(a.out,result)
    print(json.dumps({k:result[k] for k in ('status','seeds','episodes','labeled_pairs','stress_30x30_pairs','harmful_survivors','failures')}),flush=True)
    if result['failures'] or result['harmful_survivors']:raise SystemExit('Generated audit failed')
    if a.execute_out:
        report=execute(a.execute_out)
        print(json.dumps({k:report[k] for k in ('status','original_labels_matched','original_labels_total','generated_labels_verified','racket_evaluations','public_views','witness_changed_cells')}),flush=True)
        if report['status']=='blocked_original_labels':raise SystemExit(2)
if __name__=='__main__':main()
