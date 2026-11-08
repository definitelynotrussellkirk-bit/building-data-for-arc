"""Reproducible protected-Racket rival audit, sampler sweep and private exporter.

Run via review.py run; all labels/rival results are actual protected Racket values.
--preflight additionally creates a source-bound counterfactual witness from its jobs.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, sys
from pathlib import Path

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/runtime').is_dir())
TASK=HOME.name

def load(name):
    spec=importlib.util.spec_from_file_location(TASK+'_'+name,BASE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def binding():
    return {'task_id':TASK,'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sorted(HOME.rglob('*')) if p.is_file() and (p.suffix in {'.py','.rkt'} or p.name in {'promotion.json','public-parent.json'}) and '__pycache__' not in p.parts]}

def audit(out: Path, preflight: Path|None=None):
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    if out.exists():raise ValueError('Use a fresh output directory')
    out.mkdir(parents=True)
    a,r,p=load('adapter'),load('rivals'),load('presentation')
    source=binding(); modes=a.P.SETTINGS
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    cache={};evaluations=0;lessons=[];failures=[]
    def execute(program,g):
        nonlocal evaluations
        key=(program,json.dumps(g,separators=(',',':')))
        if key not in cache:
            cache[key]=_grid(apply(program,copy.deepcopy(g)));evaluations+=1
        return cache[key]
    try:
        for mode in modes:
            candidates=r.programs(mode)
            for seed in (0,17,43,101):
                e=a.generate(seed,{'finish_rule':mode},2,4)
                for pair in e['train']+e['test']:
                    assert execute(e['program_solution'],pair['input'])==pair['output'],'Selected label mismatch'
                refuted=[];harmless=[]
                for name,program in candidates.items():
                    # Execute all visible demos. Never count a crash as a rejection.
                    matches=[execute(program,x['input'])==x['output'] for x in e['train']]
                    if not all(matches):refuted.append(name);continue
                    disagreements=[j for j,x in enumerate(e['test']) if execute(program,x['input'])!=x['output']]
                    if disagreements:
                        failures.append({'mode':mode,'seed':seed,'rival':name,'program':program,'episode':e,'query_indices':disagreements})
                    else:harmless.append(name)
                lessons.append({'mode':mode,'seed':seed,'demos':2,'queries':4,'refuted':refuted,'query_equivalent_survivors':harmless})
        dump(out/'rival-programs.json',{mode:r.programs(mode) for mode in modes})
        sweep=0;requests=0;unique=set();maxima=[]
        for seed in range(64):
            base=a.generate(seed,{'finish_rule':modes[0]},6,4)
            other=a.generate(seed,{'finish_rule':modes[1]},6,4)
            assert [x['input'] for s in ('train','test') for x in base[s]]==[x['input'] for s in ('train','test') for x in other[s]]
            for split in ('train','test'):
                for x in base[split]:
                    a.P.checked_grid(x['input']);a.P.checked_grid(x['output']);sweep+=1
                    unique.add(json.dumps(x['input'],separators=(',',':')))
                    sizes=sorted(map(len,a.P.components(x['output'])),reverse=True)
                    assert len(sizes)>1 and sizes[0]>sizes[1],('nonunique maximum',seed,split,sizes)
            if seed<8:
                for d in range(2,7):
                    for q in range(1,5):
                        e=a.generate(seed,{'finish_rule':modes[0]},d,q);requests+=1
                        assert e['train']==base['train'][:d] and e['test']==base['test'][:q]
            assert len(set(json.dumps(x['input']) for s in ('train','test') for x in base[s]))==10
        report={'status':'passed' if not failures else 'failed','task_id':TASK,'source_binding':source,'racket':identity,'racket_evaluations':evaluations,
          'lessons':lessons,'harmful_survivors':failures,'sampler_scenes':sweep,'unique_scenes':len(unique),'count_prefix_requests':requests,
          'scope':'Finite declared competitors and listed seeds only; no universal uniqueness claim. All rival errors are fatal.'}
        dump(out/'audit.json',report)
        if failures:raise AssertionError(f'{len(failures)} harmful rivals; see audit.json')
        if preflight:
            pf=json.loads(preflight.read_text());ex=json.loads((preflight.parent/'execution.json').read_text())
            for row in pf['source_binding']['files']:
                assert sha(ROOT/row['path'])==row['sha256'],'Preflight source drift'
            ep=next(e for e in ex['episodes'] if e['settings']['finish_rule']==modes[1]);x=ep['test'][3]
            cf=r.programs(modes[1])['raw_geometry']
            actual=execute(ep['program_solution'],x['input']);counter=execute(cf,x['input'])
            assert actual==x['output'] and actual!=counter
            descriptions={
                'step_a':'Remove legend anchors and expand target codes into the geometric 4x4 symbols.',
                'intermediate':'Complete decoded grid and its multicolor 8-connected occupied-cell components.',
                'step_b':'Select the largest decoded component by occupied-cell count and recolor exactly its cells to 9.',
                'why_b_depends_on_a':'Marker count, raw exemplar connectivity, and decoded occupied-cell mass can select different groups; the consumer needs the expanded geometry.'}
            groups=a.P.components(a.P.solve(x['input']));best=max(groups,key=len)
            witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':TASK,'source_binding':pf['source_binding'],**descriptions,'racket':{'backend':'racket','protected':True},
                'cases':[{'input':x['input'],'settings':ep['settings'],'program':ep['program_solution'],'output':actual,
                 'intermediate_value':{'component_sizes':list(map(len,groups)),'selected_cells':best},'counterfactual_program':cf,
                 'counterfactual_output':counter,'ablation':'wrong_intermediate'}]}
            dump(out/'causal-witness.json',witness)
            from arcpuzzles.review_parametric_admission import validate_sequential_witness
            from arcpuzzles.review_public_admission import _strict_programs
            validate_sequential_witness({'sequential_dependency':{**descriptions,'witness_path':str(out/'causal-witness.json')}},pf,lambda f:Path(f).read_bytes())
            _strict_programs(ROOT,[ep['program_solution'],cf])
            # Fresh execution (not the memoization cache) replays both labels.
            assert _grid(apply(ep['program_solution'],x['input']))==actual
            assert _grid(apply(cf,x['input']))==counter
            dump(out/'causal-replay.json',{'status':'passed','racket':identity,'witness_sha256':sha(out/'causal-witness.json'),
                 'changed_cells':sum(u!=v for row1,row2 in zip(actual,counter) for u,v in zip(row1,row2)),
                 'replay_evaluations':2,'source_binding':pf['source_binding'],'owner_accepted':False})
            exports=[]
            for e in ex['episodes']:
                bank=p.prepare(e,13)
                assert p.prepare(e,13,limit=1)['views']==bank['views'][:1]
                mutated=copy.deepcopy(e);mutated['settings']={'secret':'changed'};mutated['program_solution']='private'
                assert p.prepare(mutated,13)['views']==bank['views']
                firstindex=bank['source_indices'][0]
                for j in range(4):
                    if j!=firstindex:mutated['test'][j]={'input':[[9]],'output':[[8]]}
                assert p.prepare(mutated,13,limit=1)['views']==bank['views'][:1]
                exports.append(bank)
            p.write_views({'views':[v for bank in exports for v in bank['views']]},out/'public')
            dump(out/'presentation.private.json',{'controller_only':True,'episodes':exports})
            dump(out/'public-check.json',{'status':'passed','episodes':len(exports),'views':sum(len(b['views']) for b in exports),'first_turn_equal_to_single_query':True,
               'future_query_and_metadata_invariant':True,'all_ids_visible_bytes_only':True,'query_total_hint':False,'training_admitted':False})
        print(json.dumps({'status':'passed','task_id':TASK,'racket_evaluations':evaluations,'audit_episodes':len(lessons),'sampler_scenes':sweep,'count_prefix_requests':requests}))
    finally:bridge.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--preflight',type=Path)
    args=parser.parse_args();audit(args.out,args.preflight)
