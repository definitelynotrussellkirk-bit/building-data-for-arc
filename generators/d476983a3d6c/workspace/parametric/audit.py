"""Reusable finite lesson audit with independent semantics and protected Racket.

Run from the same checkout through review.py run. JSON is compact by design;
full counterexample grids are retained only for findings and authored controls.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HOME.parents[1]
TASK = 'd476983a3d6c'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R = load(HERE/'rivals.py', 'd476983a3d6c_audit_rivals')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sources():
    paths = [HOME/'generator.py', *HERE.glob('*.py'), *HERE.glob('*.rkt'), HERE/'promotion.json', * (HOME/'tests').glob('test_parametric*.py')]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths)) if p.is_file()}


def stress():
    pairs = [((0,3),(29,25)),((2,28),(27,1)),((4,0),(25,29)),((6,24),(23,5)),((8,2),(21,27)),((10,29),(19,0)),((12,12),(17,17))]
    result = []
    for index, command in enumerate((1,2)):
        grid = [[9 if ((r*17+c*13)%5 < 2 if index == 0 else r%5 == 0 or c%4 == 0) else 0
                 for c in range(30)] for r in range(30)]
        grid[0][0] = command
        colors = [c for c in range(1,9) if c != command]
        for color, endpoints in zip(colors,pairs):
            for r,c in endpoints: grid[r][c] = color
        result.append(grid)
    return result


def lesson(episode, mode, counters):
    pairs = episode['train'] + episode['test']
    findings = []
    for split in ('train','test'):
        for i,pair in enumerate(episode[split]):
            expected = R.intended(pair['input'],mode)
            counters['python_label_comparisons'] += 1
            if expected != pair['output']:
                findings.append({'kind':'incorrect_label','split':split,'index':i,'input':pair['input'],'actual':pair['output'],'expected':expected})
    refutations = {}; survivors = []
    for name,predict in R.bank(mode).items():
        counters['rival_lesson_combinations'] += 1
        for index,pair in enumerate(episode['train']):
            counters['rival_demo_evaluations'] += 1
            if predict(pair['input']) != pair['output']:
                refutations[name] = index
                break
        else:
            survivors.append(name)
            for index,pair in enumerate(episode['test']):
                counters['rival_query_evaluations'] += 1
                wrong = predict(pair['input'])
                if wrong != pair['output']:
                    findings.append({'kind':'surviving_rival_query_disagreement','rival':name,'query_index':index,
                                     'train':episode['train'],'query':pair,'rival_output':wrong})
                    break
    return {'refutations':refutations,'survivors':survivors,'findings':findings,
            'input_ids':[digest(p['input']) for p in pairs],
            'pair_ids':[digest(p) for p in pairs]}


def run(args):
    before = sources()
    prototype = load(HERE/'prototype.py','d476983a3d6c_audit_prototype')
    counters = {k:0 for k in ['episodes','python_label_comparisons','determinism_checks','matching_input_checks','prefix_checks','distinct_input_checks',
                             'rival_lesson_combinations','rival_demo_evaluations','rival_query_evaluations']}
    jobs=[]; issues=[]; episodes={}; lesson_records={}
    for seed in args.seeds:
        for demos in args.demos:
            for mode in R.MODES:
                key=(seed,demos,mode); settings={'routing_mode':mode}
                try:
                    episode=prototype.generate(seed,settings,demos=demos,queries=4)
                    repeated=prototype.generate(seed,settings,demos=demos,queries=4)
                    assert episode == repeated, 'non-deterministic generation'
                    counters['determinism_checks']+=1
                    assert len(episode['train'])==demos and len(episode['test'])==4
                    assert episode['program_solution']==prototype.program(settings)
                    rec=lesson(episode,mode,counters)
                    assert len(set(rec['input_ids']))==demos+4,'duplicate input in lesson'
                    counters['distinct_input_checks']+=1
                    episodes[key]=episode; lesson_records[key]=rec
                    counters['episodes']+=1
                    jobs.append({'seed':seed,'demos':demos,'mode':mode,**rec})
                    issues.extend({'seed':seed,'demos':demos,'mode':mode,**f} for f in rec['findings'])
                except Exception as e:
                    issues.append({'kind':'generation_or_python_error','seed':seed,'demos':demos,'mode':mode,'error':repr(e)})
        for demos in args.demos:
            left=episodes.get((seed,demos,'command'));right=episodes.get((seed,demos,'avoid_painted'))
            if left and right:
                assert [p['input'] for split in ('train','test') for p in left[split]] == [p['input'] for split in ('train','test') for p in right[split]]
                counters['matching_input_checks']+=2
        for mode in R.MODES:
            for a,b in zip(args.demos,args.demos[1:]):
                left=episodes.get((seed,a,mode));right=episodes.get((seed,b,mode))
                if left and right:
                    assert left['train']==right['train'][:a] and left['test']==right['test']
                    counters['prefix_checks']+=1
    canonical=next(json.loads(line) for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
                   if json.loads(line).get('task_id')==TASK)
    exact_default=prototype.program({'routing_mode':'command'})==canonical['program_solution']
    canonical_rows=[]
    for split in ('train','test'):
        for i,pair in enumerate(canonical[split]):
            canonical_rows.append({'split':split,'index':i,'python_matches':R.intended(pair['input'],'command')==pair['output'],'input_sha256':digest(pair['input'])})
    protected={'ran':False}; controls=[]; stress_rows=[]
    if not args.python_only:
        from arcpuzzles.parametric_worker import _real_evaluator
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        cache={}; native_counts={'actual_executions':0,'cache_hits':0,'generated_label_checks':0,'rival_parity_checks':0,'stress_intended_checks':0,'stress_rival_checks':0}
        def execute(program,grid):
            key=(hashlib.sha256(program.encode()).hexdigest(),digest(grid))
            if key in cache:native_counts['cache_hits']+=1;return cache[key]
            output=apply(program,grid);native_counts['actual_executions']+=1;cache[key]=output;return output
        native_rows=[]
        try:
            for seed in args.protected_seeds:
                for demos in [args.demos[0],args.demos[-1]]:
                    for mode in R.MODES:
                        key=(seed,demos,mode)
                        if key not in episodes:continue
                        episode=episodes[key];rec=lesson_records[key];program=prototype.program({'routing_mode':mode})
                        row={'seed':seed,'demos':demos,'mode':mode,'label_checks':[],'rivals':{}}
                        for split in ('train','test'):
                            for i,pair in enumerate(episode[split]):
                                native_counts['generated_label_checks']+=1
                                actual=execute(program,pair['input']);ok=actual==pair['output']==R.intended(pair['input'],mode)
                                row['label_checks'].append({'split':split,'index':i,'ok':ok,'output_sha256':digest(actual)})
                                if not ok:issues.append({'kind':'protected_label_mismatch','seed':seed,'demos':demos,'mode':mode,'split':split,'index':i,'pair':pair,'actual':actual})
                        for name,idx in rec['refutations'].items():
                            pair=episode['train'][idx];expected=R.bank(mode)[name](pair['input']);actual=execute(R.racket(mode,name),pair['input'])
                            native_counts['rival_parity_checks']+=1;ok=actual==expected and actual!=pair['output']
                            row['rivals'][name]={'refuting_demo':idx,'ok':ok,'rival_output_sha256':digest(actual)}
                            if not ok:issues.append({'kind':'protected_rival_mismatch','mode':mode,'rival':name,'input':pair['input'],'actual':actual,'expected':expected})
                        native_rows.append(row)
            for row in canonical_rows:
                pair=canonical[row['split']][row['index']]
                row['protected_matches']=execute(prototype.program({'routing_mode':'command'}),pair['input'])==pair['output']
            for i,grid in enumerate(stress()):
                for mode in R.MODES:
                    intended=R.intended(grid,mode);actual=execute(prototype.program({'routing_mode':mode}),grid)
                    native_counts['stress_intended_checks']+=1
                    row={'scene':i,'mode':mode,'input':grid,'input_sha256':digest(grid),'output_sha256':digest(actual),
                         'features':R.feature_summary(grid,mode),'intended_matches':actual==intended,'rivals':{}}
                    if actual!=intended:issues.append({'kind':'stress_intended_mismatch','scene':i,'mode':mode,'actual':actual,'expected':intended})
                    for name,predict in R.bank(mode).items():
                        got=execute(R.racket(mode,name),grid);expect=predict(grid);ok=got==expect
                        native_counts['stress_rival_checks']+=1
                        row['rivals'][name]={'parity':ok,'differs_from_intended':got!=intended,'output_sha256':digest(got)}
                        if not ok:issues.append({'kind':'stress_rival_mismatch','mode':mode,'rival':name,'scene':i,'actual':got,'expected':expect})
                    stress_rows.append(row)
            for label in ('sequential_cmd1','sequential_cmd2'):
                grid=R.fixtures()[label]
                intended=execute(prototype.program({'routing_mode':'avoid_painted'}),grid)
                wrong=execute(R.racket('avoid_painted','original_canvas_costs'),grid)
                controls.append({'kind':'wrong_intermediate','input':grid,'intended':intended,'wrong_original_canvas':wrong,
                                 'changes_output':intended!=wrong,'features':R.feature_summary(grid,'avoid_painted')})
            protected={'ran':True,'identity':identity,'counts':native_counts,'episodes':native_rows}
        finally:bridge.close()
    after=sources()
    passed=not issues and exact_default and before==after and all(row['python_matches'] and row.get('protected_matches',True) for row in canonical_rows) and all(row['changes_output'] for row in controls)
    result={'schema':'d476983a3d6c-independent-parametric-audit-v1','passed':passed,'task_id':TASK,
            'source_hashes_before':before,'source_hashes_after':after,'source_unchanged':before==after,
            'scope':{'seeds':args.seeds,'demo_counts':args.demos,'queries':4,'rival_entries':{mode:len(R.bank(mode)) for mode in R.MODES},'equivalences':R.EQUIVALENCES},
            'counts':counters,'jobs':jobs,'issues':issues,'exact_canonical_default':exact_default,'canonical_pairs':canonical_rows,
            'protected':protected,'stress':stress_rows,'causal_controls':controls,
            'limitations':['Finite named rival and seed evidence, not universal uniqueness or success.','Rival query checks are performed only after all visible demonstrations fit.','The inherited production sampler and its unresolved audit remain unchanged.','Protected checks overlap the Python census; counts are not independent statistical samples.']}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    parser.add_argument('--seeds',default='0,1,2,7,17,31,97,255')
    parser.add_argument('--demos',default='2,3,6')
    parser.add_argument('--protected-seeds',default='0,17')
    parser.add_argument('--python-only',action='store_true')
    args=parser.parse_args()
    for name in ('seeds','demos','protected_seeds'):
        setattr(args,name,sorted(set(int(x) for x in getattr(args,name).split(','))))
    result=run(args)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise ValueError('Use a fresh evidence path')
    out.write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False)+'\n')
    print(json.dumps({'passed':result['passed'],'counts':result['counts'],'native':result['protected'].get('counts'),'issues':len(result['issues']),'source_unchanged':result['source_unchanged'],'out':str(out)},indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
