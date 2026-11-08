#!/usr/bin/env python3
"""Execute task tests in an actual disposable runtime, not the library layout.

Example (through the packet's run_with_racket.py wrapper):
  python3 generators/98a65dc7fcb1/workspace/run_portable_tests.py \
    --task a16cf9241d71 \
    --test generators/a16cf9241d71/tests/test_generator_a16cf9241d71.py \
    --out ../checks/audit_a16_portable
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task',required=True)
    parser.add_argument('--test',required=True,help='test file relative to repo')
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    test=(REPO/args.test).resolve()
    if not test.is_relative_to(REPO/'generators'/args.task) or not test.is_file():
        parser.error('--test must be an existing regular file under the selected task')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime,run_process
    with tempfile.TemporaryDirectory(prefix='task-portable-pytest-') as temporary:
        runtime=Path(temporary)
        manifest=prepare_runtime(Catalog(REPO),runtime,task_id=args.task)
        target=runtime/'review_tests'/test.name
        target.parent.mkdir();shutil.copy2(test,target)
        argv=[sys.executable,'-m','pytest','-q',str(target.relative_to(runtime))]
        result=run_process(argv,runtime,timeout=120)
        (out/'stdout.log').write_text(result.get('stdout',''))
        (out/'stderr.log').write_text(result.get('stderr',''))
        report={'schema':'task-portable-pytest-v1','task_id':args.task,
            'actual_runtime_directory':str(runtime),'argv':argv,
            'test_source':args.test,'test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),
            'generator_sha256':Catalog(REPO).describe(args.task)['generator_sha256'],
            'runtime_manifest_sha256':hashlib.sha256((runtime/'RUNTIME_MANIFEST.json').read_bytes()).hexdigest(),
            'execution':result}
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(result.get('stdout',''));print(result.get('stderr',''),file=sys.stderr)
        code=result.get('returncode',result.get('exit_code',1))
        return code if isinstance(code,int) else 1

if __name__=='__main__':raise SystemExit(main())
