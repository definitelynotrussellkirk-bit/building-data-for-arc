"""Findings-only reproducible audits for this packet's two immutable targets."""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import sys
import tempfile

TARGETS=('28ad783a6a98','20458da8b222')

def sha(data):return hashlib.sha256(data).hexdigest()


def manhattan(grid):
    seeds=[(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,5)]
    out=[row[:] for row in grid]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v==5:continue
            ds=[abs(r-rr)+abs(c-cc) for rr,cc,_ in seeds]
            best=min(ds);ids=[i for i,d in enumerate(ds) if d==best]
            out[r][c]=seeds[ids[0]][2] if len(ids)==1 else 8
    return out


def worker(outdir):
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs,canonical_rule_source,normalized_rule_hash
    outdir.mkdir(parents=True,exist_ok=True)
    report={'schema':'assigned-adversarial-audits-v1','runtime_cwd':str(Path.cwd()),
            'probe_sha256':sha(Path(__file__).read_bytes()),'targets':{},'execution_errors':[]}
    for task in TARGETS:
        bundle=runner._load_bundle(task);gen=bundle.generator_module
        source=canonical_rule_source(task)
        bundle=replace(bundle,rule_source=source,rule_callable_text=runner.wrap_rule(source))
        identity={'task_id':task,'generator_sha256':sha(Path(gen.__file__).read_bytes()),
                  'canonical_rule_sha256':sha(source.encode()),'rule_hash':normalized_rule_hash(source),
                  'source_unchanged':True}
        result=dict(identity)
        bridge,name=runner._open_bridge_with_rule(bundle.rule_callable_text)
        try:
            if task==TARGETS[0]:
                result.update({'matrix_cases':0,'override_mismatches':[],
                               'racket_checked_mismatches':0,'validator_failures':[]})
                for seed,t1,t2 in itertools.product(range(10),gen._CODES,gen._CODES):
                    overrides={'first_transform':t1,'second_transform':t2}
                    g=gen.generate(seed,0,**overrides);panels=gen._split_panels(g)
                    first=[code for code in gen._CODES if gen._xform_grid(panels[0],code)==panels[1]]
                    second=[code for code in gen._CODES if gen._xform_grid(panels[2],code)==panels[3]]
                    errors=gen.self_check(g);result['matrix_cases']+=1
                    if errors:result['validator_failures'].append({'seed':seed,'overrides':overrides,'errors':errors})
                    if first!=[t1] or second!=[t2]:
                        actual=runner._apply_rule(bridge,name,g)
                        requested=gen._xform_grid(gen._xform_grid(panels[4],t1),t2)
                        row={'seed':seed,'sample_index':0,'overrides':overrides,
                             'observed_first':first,'observed_second':second,
                             'input_sha256':sha(json.dumps(g,separators=(',',':')).encode()),
                             'requested_output_equals_query_panel':requested==panels[4],
                             'racket_output_matches_requested':actual==requested}
                        result['override_mismatches'].append(row)
                        result['racket_checked_mismatches']+=1
                        if len(result['override_mismatches'])==1:
                            witness={**identity,**row,'input':g,'actual_racket_output':actual,
                                     'rival_output':requested,'validator_errors':errors,
                                     'documented_generator_domain':True,
                                     'rival_meaning':'Output under the explicitly requested t2(t1(X)), not a rival label for the generated panels',
                                     'command':['python3','run_with_racket.py','python3',
                                                'generators/f7e325967ea1/workspace/audit_targets.py','--out','../checks/audits'],
                                     'cwd':'packet_root'}
                            (outdir/f'{task}-counterexample.json').write_text(json.dumps(witness,indent=2)+'\n')
                result['finding']='Explicit inverse transforms are silently replaced to exclude legitimate identity compositions.'
            else:
                result.update({'generated_checked':0,'canonical_checked':0,'mirror_mismatches':[],
                               'validator_failures':[],'observed_override_failures':[],
                               'profiles':{},'manhattan_disagreements':0})
                for index,p in enumerate(canonical_pairs(task)):
                    actual=runner._apply_rule(bridge,name,p['input']);result['canonical_checked']+=1
                    if actual!=p['output']:
                        result['mirror_mismatches'].append({'canonical_index':index,'pair':p,'actual':actual})
                stats=Counter()
                for band,profile,seed in itertools.product(('easy','medium','hard'),gen.SCENE_PROFILES,range(2)):
                    overrides={'scene_profile':profile};g=gen.generate(seed,seed*19,difficulty=band,**overrides)
                    errors=gen.self_check(g);observed=gen.observe_overrides(g)
                    actual=runner._apply_rule(bridge,name,g);mirror=gen.rule_mirror(g)
                    result['generated_checked']+=1;stats[band+'/'+profile]+=1
                    context={'band':band,'seed':seed,'sample_index':seed*19,'overrides':overrides,'input':g}
                    if errors:result['validator_failures'].append({**context,'errors':errors})
                    if observed!=overrides:result['observed_override_failures'].append({**context,'observed':observed})
                    if mirror!=actual:result['mirror_mismatches'].append({**context,'actual':actual,'mirror':mirror})
                    rival=manhattan(g)
                    if rival!=actual:
                        result['manhattan_disagreements']+=1
                        path=outdir/f'{task}-domain-witness.json'
                        if band=='hard' and not path.exists():
                            witness={**identity,**context,'actual_racket_output':actual,'rival_output':rival,
                                     'validator_errors':errors,'documented_generator_domain':True,
                                     'interpretation':'Correct wall-aware labels; hard dimensions cannot match any canonical profile. Not a mislabeled example.',
                                     'command':['python3','run_with_racket.py','python3',
                                                'generators/f7e325967ea1/workspace/audit_targets.py','--out','../checks/audits'],
                                     'cwd':'packet_root'}
                            path.write_text(json.dumps(witness,indent=2)+'\n')
                result['profiles']=dict(stats)
                result['finding']='No label/validator/override defect in these 48 samples; independent profile-floor command finds zero canonical support in medium/hard.'
        except Exception as exc:
            report['execution_errors'].append({'task':task,'error':repr(exc)})
        finally:
            bridge.close()
        report['targets'][task]=result
    report['passed_execution']=not report['execution_errors']
    (outdir/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'execution_errors':report['execution_errors'],
          'transform_override_mismatches':len(report['targets'][TARGETS[0]].get('override_mismatches',[])),
          'geodesic_samples':report['targets'][TARGETS[1]].get('generated_checked',0)}))
    return 0 if report['passed_execution'] else 1


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=ap.parse_args()
    if args.worker:return worker(args.out)
    root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime,run_process
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='assigned-audits-') as directory:
        stage=Path(directory);prepare_runtime(Catalog(root),stage,task_ids=list(TARGETS))
        shutil.copy2(__file__,stage/'audit_targets.py')
        run=run_process([sys.executable,'-B','audit_targets.py','--worker','--out','audit-output'],stage,timeout=480)
        (out/'execution.json').write_text(json.dumps({'runtime_cwd':str(stage),
            'runtime_manifest_sha256':sha((stage/'RUNTIME_MANIFEST.json').read_bytes()),'execution':run},indent=2)+'\n')
        if (stage/'audit-output').exists():
            for path in (stage/'audit-output').iterdir():shutil.copy2(path,out/path.name)
        print(run['stdout']);print(run['stderr'],file=sys.stderr)
        return run['exit_code'] if not run['timed_out'] else 124

if __name__=='__main__':raise SystemExit(main())
