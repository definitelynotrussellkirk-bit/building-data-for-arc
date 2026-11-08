#!/usr/bin/env python3
"""Validate a review delta, apply it to a fresh original packet, run task tests.

Requires the original packet ZIP, the delta ZIP, git and pytest. The original
packet and working tree are never modified. No hidden solve labels are read.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'src'))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unpack(archive: zipfile.ZipFile, destination: Path) -> None:
    infos=archive.infolist()
    if sum(info.file_size for info in infos)>1_000_000_000:
        raise ValueError('packet exceeds 1 GB unpacked size limit')
    seen=set()
    for info in infos:
        p=PurePosixPath(info.filename)
        if (p.is_absolute() or '..' in p.parts or '\\' in info.filename
                or info.filename in seen
                or stat.S_ISLNK(info.external_attr >> 16)):
            raise ValueError(f'unsafe or duplicate ZIP path: {info.filename!r}')
        seen.add(info.filename)
    archive.extractall(destination)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',required=True)
    parser.add_argument('--delta',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    if not shutil.which('git'):parser.error('git is required to check and apply the patch')
    packet=Path(args.packet).resolve();delta=Path(args.delta).resolve()
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    from arcpuzzles.review_full_return import validate_full_return
    from arcpuzzles.runtime import run_process
    with zipfile.ZipFile(packet) as source,zipfile.ZipFile(delta) as review:
        manifest=json.loads(source.read('PACKET-MANIFEST.json'))
        validated=validate_full_return(review,manifest)
        contract=json.loads(review.read('ASSIGNMENT.json'))
        tid=contract['task_id']
        patch=review.read('patches/source.patch')
        report={'schema':'fresh-packet-delta-replay-v1','packet_sha256':sha(packet.read_bytes()),
            'candidate_delta_sha256':sha(delta.read_bytes()),'patch_sha256':sha(patch),
            'validation':validated,'task_id':tid,'verification_scope':'static validator, clean patch application, task-local Python tests; not a fresh full Racket battery',
            'commands':[]}
        with tempfile.TemporaryDirectory(prefix='fresh-review-delta-') as temporary:
            runtime=Path(temporary);report['actual_replay_directory']=str(runtime)
            unpack(source,runtime)
            patch_path=runtime/'returned.patch';patch_path.write_bytes(patch)
            for argv in (['git','apply','--check','returned.patch'],['git','apply','returned.patch'],
                         [sys.executable,'-m','pytest','-q',f'repo/generators/{tid}/tests']):
                result=run_process(argv,runtime,timeout=120)
                report['commands'].append({'argv':argv,'cwd':str(runtime),**result})
                if result['exit_code'] != 0:
                    report['status']='FAIL'
                    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
                    print(result['stdout']);print(result['stderr'],file=sys.stderr)
                    return result['exit_code'] or 1
            restored=runtime/f'repo/generators/{tid}/generator.py'
            report['restored_generator_sha256']=sha(restored.read_bytes())
            frozen=review.read('solve/source/generator.py')
            if restored.read_bytes()!=frozen:
                raise ValueError('patched generator does not match the solved source snapshot')
            # Scope validation is the official validator's responsibility; this
            # identity check also proves the delivered task tests used this source.
            report['status']='PASS'
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({k:report[k] for k in ('status','task_id','patch_sha256','restored_generator_sha256','actual_replay_directory')},indent=2))
            print(report['commands'][-1]['stdout'])
    return 0

if __name__=='__main__':raise SystemExit(main())
