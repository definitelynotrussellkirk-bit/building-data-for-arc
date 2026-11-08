#!/usr/bin/env python3
"""Stage, move, and execute the reviewed generator without source-tree imports."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = 'f9dd4cf0f344'
CHILD = r'''
import hashlib, importlib.util, json, os, sys
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root))
manifest=json.loads((root/'RUNTIME_MANIFEST.json').read_text())
gen_entry=next(r for r in manifest['files'] if r['library_path']=='generators/f9dd4cf0f344/generator.py')
path=root/gen_entry['runtime_path']
spec=importlib.util.spec_from_file_location('portable_generator',path)
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
import puzzle_generators.base as base
assert root in Path(base.__file__).parents
for imported in (path,Path(base.__file__)):
    assert root in imported.parents
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
canonical=next(r for r in manifest['files'] if r['library_path']=='shared/data/canonical/puzzles.jsonl')
row=next(json.loads(s) for s in (root/canonical['runtime_path']).open() if json.loads(s)['task_id']=='f9dd4cf0f344')
bridge=RacketBridge(prelude_path=str(root/'arc_repl/racket_prelude/arc-prelude.rkt'))
bridge.eval_text('(define portable_rule '+wrap_rule(row['program_solution'])+')')
count=0
try:
    for difficulty in ('easy','medium','hard'):
        for seed in range(32):
            g=gen.generate(seed,seed,difficulty=difficulty)
            assert g==gen.generate(seed,seed,difficulty=difficulty)
            assert not gen.self_check(g)
            out=[r[:] for r in g]
            for r in range(1,len(g)-1):
                for c in range(1,len(g[0])-1):
                    arms={g[r-1][c],g[r+1][c],g[r][c-1],g[r][c+1]}
                    if g[r][c]==0 and len(arms)==1 and 0 not in arms:
                        out[r][c]=next(iter(arms))
            bridge.define_grid('portable_input',g)
            assert bridge.eval_text('(portable_rule portable_input)')==out
            count+=1
finally:
    bridge.close()
print(json.dumps({'cwd':str(root),'generator_file':str(path),'base_file':str(Path(base.__file__)),
 'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'racket_comparisons':count,
 'seed_range':[0,31],'sample_index':'seed','bands':['easy','medium','hard'],
 'PYTHONPATH':os.environ.get('PYTHONPATH'),'sys_path':sys.path}))
'''

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    sys.path.insert(0,str(ROOT/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    report={'schema':'relocated-runtime-probe-v1','source_root':str(ROOT),'errors':[]}
    with tempfile.TemporaryDirectory(prefix='f9dd4-portable-') as temp:
        parent=Path(temp);stage=parent/'original';moved=parent/'different-parent'/'runtime'
        prepare_runtime(Catalog(ROOT),stage,TASK)
        moved.parent.mkdir();shutil.move(stage,moved)
        env=os.environ.copy();env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        result=subprocess.run([sys.executable,'-c',CHILD],cwd=moved,env=env,capture_output=True,text=True,timeout=120)
        report.update({'staged_path':str(stage),'runtime_path':str(moved),
            'original_stage_exists_during_run':stage.exists(),'exit_code':result.returncode,
            'stdout':result.stdout,'stderr':result.stderr,'runtime_retained':False})
        if result.returncode==0:
            report['child']=json.loads(result.stdout)
            if any(str(ROOT) in p for p in report['child']['sys_path']):
                report['errors'].append('source checkout leaked onto child sys.path')
        else:
            report['errors'].append('relocated child failed; see stderr')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(bool(report['errors']))

if __name__=='__main__':
    raise SystemExit(main())
