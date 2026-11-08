"""Replay an exact source delta in a fresh original packet and verify it.

The original packet and a package_return.py-produced delta ZIP are required.
Creates a new directory; never overwrites an existing checkout or source file.
Runs isolated offline Racket setup, focused tests, and the task's full battery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

TASK='ce99418cc163'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,required=True)
    parser.add_argument('--delta',type=Path,required=True)
    parser.add_argument('--fresh-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    packet=Path.cwd().resolve()
    fresh=args.fresh_root.resolve(); out=args.out.resolve()
    if fresh.exists() or out.exists():
        parser.error('--fresh-root and --out must be new directories')
    if packet==fresh or packet in fresh.parents:
        parser.error('fresh checkout must be outside this packet; do not package duplicate trees')
    expected=sha(packet/f'repo/generators/{TASK}/generator.py')
    solve=json.loads((packet/'solve/summary.json').read_text())
    if solve['generator_hash']!=expected:
        raise ValueError('final solve is not bound to the checked generator')
    out.mkdir(parents=True)
    fresh.mkdir(parents=True)
    report={'task_id':TASK,'generator_sha256':expected,'original_zip_sha256':sha(args.original),
            'source_delta_zip_sha256':sha(args.delta),'fresh_root':str(fresh),'commands':[],
            'solve_generator_hash':solve['generator_hash'],'changed_file_sha256':{}}

    def save():
        (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')

    def run(name,argv,cwd):
        completed=subprocess.run(argv,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        log=out/(name+'.log'); log.write_text(completed.stdout)
        report['commands'].append({'argv':argv,'cwd':str(cwd),'exit_code':completed.returncode,
                                   'evidence_path':str(log.relative_to(packet))})
        save(); print(name,completed.returncode,flush=True)
        if completed.returncode:
            raise RuntimeError(f'{name} failed; see {log}')
        return completed.stdout

    with zipfile.ZipFile(args.original) as archive:
        for item in archive.infolist():
            p=PurePosixPath(item.filename)
            mode=item.external_attr>>16
            if p.is_absolute() or '..' in p.parts or '\\' in item.filename or stat.S_ISLNK(mode):
                raise ValueError('unsafe original archive member: '+item.filename)
        archive.extractall(fresh)
    with zipfile.ZipFile(args.delta) as delta:
        patch=delta.read('patches/source.patch')
    patch_path=out/'source.patch'; patch_path.write_bytes(patch)
    report['source_patch_sha256']=sha(patch_path)
    run('apply-check',['git','apply','--check',str(patch_path)],fresh)
    run('apply',['git','apply',str(patch_path)],fresh)
    changed=re.findall(r'^diff --git a/(repo/[^\s]+) b/\1$',patch.decode(),flags=re.M)
    if not changed:
        raise ValueError('no source changes in patch')
    for name in changed:
        expected_file=sha(packet/name); actual_file=sha(fresh/name)
        if expected_file!=actual_file:
            raise ValueError('replay bytes differ: '+name)
        report['changed_file_sha256'][name]=actual_file
    if sha(fresh/f'repo/generators/{TASK}/generator.py')!=expected:
        raise ValueError('fresh generator differs from tested source')
    run('setup-racket',[sys.executable,'setup_racket.py'],fresh)
    test_output=run('focused-tests',[sys.executable,'run_with_racket.py',sys.executable,'-m','pytest',f'generators/{TASK}/tests','-q'],fresh)
    test_match=re.search(r'(\d+) passed',test_output)
    if not test_match:
        raise ValueError('focused pytest did not report a passing test count')
    report['focused_test_count']=int(test_match.group(1))
    run('battery',[sys.executable,'run_with_racket.py',sys.executable,'-m','arcpuzzles','check',TASK,
                   '--battery','--timeout','4000','--phase','after','--out',str(out/'battery')],fresh)
    battery=json.loads((out/'battery/checks'/f'{TASK}_after_battery_summary.json').read_text())
    if battery['generator_file_sha256']!=expected or battery['counts']['green']!=12:
        raise ValueError('fresh battery did not prove 12 final-source green stages')
    report.update(status='PASS',source_patch_sha256=sha(patch_path),fresh_battery_counts=battery['counts'],
                  unchanged_canonical_sha256=sha(fresh/'repo/shared/data/canonical/puzzles.jsonl'),
                  focused_tests=f"{report['focused_test_count']} passed; see focused-tests.log",
                  legacy_fixture='No selected-task frozen test fixture exists; not reported as a pass.')
    save()
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
