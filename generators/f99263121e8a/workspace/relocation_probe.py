"""Copy then relocate a portable runtime; verify labels in an isolated child.

Invoke from packet root through run_with_racket.py. No repository source import
is allowed in the child; the verified Racket executable is an explicit dependency.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT/'src'))
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime

CHILD = r'''
import hashlib, importlib.util, json, os, pathlib, sys
root = pathlib.Path.cwd()
sys.path.insert(0, str(root))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.runner import wrap_rule
path = root/'puzzle_generators/per_puzzle/f99263121e8a/generator.py'
spec = importlib.util.spec_from_file_location('relocated_subject', path)
gen = importlib.util.module_from_spec(spec); sys.modules[spec.name]=gen; spec.loader.exec_module(gen)
record = next(json.loads(line) for line in (root/'data/canonical/puzzles.jsonl').open()
              if json.loads(line).get('task_id')=='f99263121e8a')
bridge=RacketBridge(timeout=20)
rows=[]
try:
    for band in ('easy','medium','hard'):
        for seed in range(17,23):
            g=gen.generate(seed,seed-17,difficulty=band)
            literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in g)+')'
            actual=bridge.eval_text(f'({wrap_rule(record["program_solution"])} {literal})')
            rows.append({'band':band,'seed':seed,'sample_index':seed-17,
                         'selfcheck_clean':not gen.self_check(g,difficulty=band),
                         'racket_match':actual==gen.rule_mirror(g),
                         'input_sha256':hashlib.sha256(json.dumps(g).encode()).hexdigest()})
finally:
    bridge.shutdown()
forbidden=sys.argv[1]
modules={name:str(pathlib.Path(m.__file__).resolve()) for name,m in tuple(sys.modules.items())
         if getattr(m,'__file__',None) and not str(m.__file__).startswith('<')}
leaks={k:v for k,v in modules.items() if v.startswith(forbidden+os.sep)}
report={'cwd':str(root), 'isolated_python':bool(sys.flags.isolated),
        'generator_path':str(path),'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_import_leaks':leaks,'seed_range':[17,22],'sample_index':'seed-17','cases':rows,
        'passed':not leaks and all(r['selfcheck_clean'] and r['racket_match'] for r in rows)}
print(json.dumps(report))
sys.exit(0 if report['passed'] else 1)
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): parser.error('refusing to overwrite evidence')
    with tempfile.TemporaryDirectory(prefix='f99263121e8a-relocation-') as name:
        base=Path(name); original=base/'before-move'; relocated=base/'after-move'
        manifest=prepare_runtime(Catalog(ROOT),original,'f99263121e8a')
        shutil.move(str(original),str(relocated))
        env=dict(os.environ); env.pop('PYTHONPATH',None); env['PYTHONNOUSERSITE']='1'
        argv=[sys.executable,'-I','-c',CHILD,str(ROOT.resolve())]
        completed=subprocess.run(argv,cwd=relocated,env=env,capture_output=True,text=True,timeout=120)
        child=json.loads(completed.stdout) if completed.stdout.strip() else None
        report={'schema':'f99263121e8a-relocation-v1',
                'source_generator_sha256':hashlib.sha256((HOME/'generator.py').read_bytes()).hexdigest(),
                'original_stage':str(original),'actual_runtime_cwd':str(relocated),
                'original_stage_removed':not original.exists(),'runtime_files':len(manifest.get('files',{})),
                'child_argv':argv,'child_exit_code':completed.returncode,'child_stderr':completed.stderr,
                'child':child,'passed':completed.returncode==0 and bool(child and child['passed'])}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(args.out),'passed':report['passed']}))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
