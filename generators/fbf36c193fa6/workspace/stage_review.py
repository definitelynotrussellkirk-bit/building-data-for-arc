#!/usr/bin/env python3
"""Stage this task and ALL its local tests/probes into an independent runtime.

Usage from repository root:
  python generators/fbf36c193fa6/workspace/stage_review.py --out var/ray-review
The output directory must be new/empty. No source tree is modified. This extends
normal runtime staging to include new task-local tests absent from the frozen
runtime map, and hashes every extra copied file for reproducibility.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    home=Path(__file__).resolve().parents[1]
    repo=home.parents[1]
    sys.path.insert(0,str(repo/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    destination=args.out.resolve()
    receipt=prepare_runtime(Catalog(repo),destination,home.name)
    extras=[]
    files=[(p,Path('tests')/p.name) for p in sorted((home/'tests').glob('test_*.py'))]
    files.append((home/'workspace/coverage_probe.py',Path('review_probe.py')))
    for source,relative in files:
        target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        extras.append({'source':str(source.relative_to(repo)), 'target':str(relative),
                       'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    result={'schema':'arcpuzzles-task-review-staging-v1','task_id':home.name,
            'runtime_directory':str(destination),'extra_files':extras,
            'runtime_manifest_sha256':hashlib.sha256((destination/'RUNTIME_MANIFEST.json').read_bytes()).hexdigest()}
    (destination/'REVIEW_RUNTIME_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
