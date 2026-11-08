#!/usr/bin/env python3
"""Official fresh patch replay and portable task tests in a private namespace.

Only OUR original ZIP, return ZIP, issued controller, source tree, vendor and
verified Racket cache are used. Fresh patched code comes exclusively from the
official replay-return operation. A fresh Python venv inherits numpy/Pillow and
installs pytest into private tmpfs. Unchanged fresh review.py run executes the
recorded portable task test directory. Existing Racket bytes are a read-only
OverlayFS lower: the official setup chmod copies its binary privately, leaving
our cache untouched. No protected official code is modified.
"""
from __future__ import annotations
import argparse
import base64
import ctypes
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import time
import zipfile
sys.dont_write_bytecode=True
from build_return_full import regular,iter_files,run_record,exclusive_copy
from build_return_overlay import manifest_files,bind_readonly,drop_owned_zip_cache,restore_zip_members
from support_sparse_packet import canonical,file_digest,no_symlinks,safe_name


def verify_toolchain(work):
    vendor=work/'vendor'
    archives=sorted(vendor.glob('*.tar.gz'))+sorted(vendor.glob('*.tgz'))
    if len(archives)!=1:
        raise ValueError('Expected exactly one original Racket vendor archive')
    archive=archives[0]
    installed=work/'.review/racket-runtime'
    regular(installed/'racket/bin/racket')
    files=0;total=0;inventory=hashlib.sha256();issued=set()
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            safe_name(member.name)
            if member.isdir():continue
            if not member.isfile() or not member.name.startswith('racket/'):
                raise ValueError('Unexpected nonregular Racket vendor entry')
            path=installed/member.name
            regular(path)
            expected=hashlib.file_digest(tar.extractfile(member),'sha256').hexdigest()
            if file_digest(path)!=expected:
                raise ValueError(f'Our Racket cache differs from issued vendor archive: {member.name}')
            inventory.update(canonical({'path':member.name,'sha256':expected,'bytes':member.size})+b'\n')
            files+=1;total+=member.size;issued.add(member.name)
    extras=[path.relative_to(installed).as_posix() for path in iter_files(installed)
            if path.relative_to(installed).as_posix() not in issued]
    return {'unissued_runtime_files_hidden_privately':len(extras),'archive':str(archive),'archive_sha256':file_digest(archive),'verified_files':files,
            'verified_bytes':total,'inventory_sha256':inventory.hexdigest(),
            'racket_binary_sha256':file_digest(installed/'racket/bin/racket')},extras


def validate_controller(work):
    paths={path.relative_to(work).as_posix():path for path in iter_files(work/'repo/src/arcpuzzles')}
    paths.update({path.relative_to(work).as_posix():path for path in iter_files(work/'vendor')})
    for name,digest in manifest_files(work/'PACKET-MANIFEST.json'):
        if name in paths:
            if file_digest(paths.pop(name))!=digest:
                raise ValueError(f'Changed issued controller: {name}')
    if paths:
        raise ValueError('Undeclared controller source files')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source-zip','return-zip','compare-work','mountpoint','out-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-sha256',required=True)
    p.add_argument('--return-sha256',help='optional expected candidate/final ZIP hash')
    p.add_argument('--python',type=Path,default=Path(sys.executable))
    p.add_argument('--pytest-spec',default='pytest>=8')
    p.add_argument('--tests-json',type=Path,required=True,
        help='recorded Python argument arrays, restricted to -m pytest selected-task/tests')
    p.add_argument('--reserved-receipt',type=Path,help='reuse our preallocated receipt inode without releasing its reserved bytes')
    p.add_argument('--embedded-exports',action='store_true',help='retain replay inventory and test logs inside the one reserved JSON receipt')
    p.add_argument('--replay-only',action='store_true',help='official replay and hashes only; no toolchain or tests')
    args=p.parse_args()
    source,returned,work,mount,out=(getattr(args,n).absolute() for n in ('source_zip','return_zip','compare_work','mountpoint','out_dir'))
    for path in (source,returned,work,mount,out):no_symlinks(path)
    if mount.exists() and any(mount.iterdir()):raise ValueError('Private mountpoint must be empty')
    if any(mount==item or mount in item.parents or item in mount.parents for item in (source,returned,work,out)):
        raise ValueError('Private mountpoint must be disjoint from input and output')
    regular(source);regular(returned)
    tests=json.loads(args.tests_json.read_text())
    contract=json.loads((work/'ASSIGNMENT.json').read_text())
    task=contract['task_id'];expected_path=f'generators/{task}/tests'
    if not isinstance(tests,list) or not tests or any(command[:3]!=['-m','pytest',expected_path]
            or any(not isinstance(arg,str) or not arg or '\0' in arg for arg in command)
            for command in tests):
        raise ValueError('Only recorded portable selected-task test directory commands are accepted')
    out.mkdir(parents=True,exist_ok=True)
    receipt_path=out/(returned.name+'.fresh-validation.json')
    if args.reserved_receipt:
        reservation=args.reserved_receipt.absolute()
        regular(reservation)
        reserved_bytes=reservation.stat().st_size
        if reserved_bytes<262144:raise ValueError('Receipt reservation is too small')
        os.link(reservation,receipt_path)
        reservation.unlink()
        receipt_stream=receipt_path.open('r+')
    else:
        reserved_bytes=262144
        receipt_stream=receipt_path.open('x')
    with receipt_stream as stream:
        receipt={'schema':'arcpuzzles-private-fresh-validation-v1','status':'running','commands':[],
                 'source_zip':str(source),'return_zip':str(returned),'task_id':task,
                 'official_tools_modified':False,'foreign_review_state_used':False,
                 'recorded_test_commands':tests,'training_admitted':False}
        initial=json.dumps(receipt);stream.write(initial)
        remaining=max(0,reserved_bytes-len(initial))
        while remaining:
            chunk=' '*min(65536,remaining);stream.write(chunk);remaining-=len(chunk)
        stream.flush();os.fsync(stream.fileno())
        mounted=False
        try:
            if file_digest(source)!=args.source_sha256:raise ValueError('Original ZIP SHA mismatch')
            drop_owned_zip_cache(source)
            returned_sha=file_digest(returned)
            if args.return_sha256 and returned_sha!=args.return_sha256:raise ValueError('Return ZIP SHA mismatch')
            receipt.update(source_zip_sha256=args.source_sha256,return_zip_sha256=returned_sha)
            manifest_sha=file_digest(work/'PACKET-MANIFEST.json')
            if manifest_sha!=contract['packet_id']:raise ValueError('Our assignment manifest hash mismatch')
            restore_zip_members(source,{'WORK/PACKET-MANIFEST.json':(manifest_sha,None)})
            drop_owned_zip_cache(source)
            validate_controller(work)
            if not args.replay_only:
                receipt['toolchain_verification'],unissued_native_paths=verify_toolchain(work)
            libc=ctypes.CDLL(None,use_errno=True)
            if libc.unshare(0x20000):raise OSError(ctypes.get_errno(),'Private namespace creation failed')
            run_record(['mount','--make-rprivate','/'],Path.cwd(),receipt)
            mount.mkdir(parents=True,exist_ok=True)
            run_record(['mount','-t','tmpfs','-o','size=512M,nr_inodes=30000,mode=0700,nodev,nosuid','arc-fresh-validation',mount],Path.cwd(),receipt)
            mounted=True
            env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','VIRTUAL_ENV'}}
            env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',TMPDIR=str(mount))
            replay=mount/'replay'
            replay_env=dict(env,PYTHONPATH=os.pathsep.join((str(work/'repo/src'),str(work/'repo/shared/runtime'))),ARCPUZZLES_HOME=str(work/'repo'))
            gc.collect()
            if hasattr(libc,'malloc_trim'):libc.malloc_trim(0)
            run_record([sys.executable,'-m','arcpuzzles','--library',work/'repo','review','replay-return',
                '--source-zip',source,'--return-zip',returned,'--compare-work',work,'--out',replay,'--runtime-closure'],
                work/'repo',receipt,env=replay_env)
            drop_owned_zip_cache(source)
            replay_receipt=json.loads((replay/'replay.json').read_text())
            if replay_receipt.get('status')!='patch_replay_passed_tests_pending':
                raise ValueError('Official replay did not pass exact patch/hash checks')
            if replay_receipt.get('return_zip_sha256')!=returned_sha:
                raise ValueError('Replay receipt return SHA mismatch')
            receipt['official_replay']={key:replay_receipt.get(key) for key in
                ('status','packet_id','assignment_id','task_id','generator_sha256','patch_sha256',
                 'changed_files','full_original_packet_extracted','extracted_files','original_files')}
            fresh=replay/'checkout';freshwork=fresh/'WORK'
            # The official replay already hash-checked this original vendor
            # copy. Replace only our new copy with OUR issued read-only bind.
            copied_vendor=freshwork/'vendor'
            if copied_vendor.exists():shutil.rmtree(copied_vendor)
            bind_readonly(work/'vendor',copied_vendor,receipt)
            for filename in ('replay.json','extraction-manifest.json.gz'):
                if args.embedded_exports:
                    content=(replay/filename).read_bytes()
                    receipt.setdefault('embedded_exports',{})[filename]={'sha256':hashlib.sha256(content).hexdigest(),
                        'encoding':'base64' if filename.endswith('.gz') else 'utf-8',
                        'content':base64.b64encode(content).decode() if filename.endswith('.gz') else content.decode()}
                else:
                    dest=out/(returned.name+'.'+filename)
                    exclusive_copy(replay/filename,dest)
                    receipt.setdefault('exports',[]).append({'path':str(dest),'sha256':file_digest(dest)})
            if not args.replay_only:
                # Overlay only OUR verified native toolchain. Official setup
                # can chmod its private binary without modifying the lower.
                native=freshwork/'.review/racket-runtime'
                for directory in (native,mount/'racket-upper',mount/'racket-work'):
                    directory.mkdir(parents=True,exist_ok=True)
                run_record(['mount','-t','overlay','overlay','-o',
                    f'lowerdir={work}/.review/racket-runtime,upperdir={mount}/racket-upper,workdir={mount}/racket-work,userxattr',native],
                    Path.cwd(),receipt)
                for relative in unissued_native_paths:
                    (native/relative).unlink()
                venv=mount/'test-venv';python=venv/'bin/python'
                run_record([args.python.absolute(),'-m','venv','--system-site-packages',venv],mount,receipt,env=env)
                run_record([python,'-m','pip','install','--no-cache-dir',args.pytest_spec],mount,receipt,env=env)
                probe='import sys,pytest,numpy,PIL; print(sys.executable); print("pytest",pytest.__version__,pytest.__file__); print("numpy",numpy.__version__,numpy.__file__); print("Pillow",PIL.__version__,PIL.__file__)'
                run_record([python,'-c',probe],mount,receipt,env=env)
                for index,command in enumerate(tests,1):
                    record=run_record([python,fresh/'review.py','run',python,*command],fresh,receipt,env=env)
                    content=record['stdout']+'\nSTDERR:\n'+record['stderr']
                    if args.embedded_exports:
                        receipt.setdefault('test_logs',[]).append({'name':f'fresh-test-{index:02d}.log',
                            'content':content,'sha256':hashlib.sha256(content.encode()).hexdigest(),'exit_code':record['exit_code']})
                    else:
                        log=out/(returned.name+f'.fresh-test-{index:02d}.log')
                        with log.open('x') as output:output.write(content)
                        receipt.setdefault('test_logs',[]).append({'path':str(log),'sha256':file_digest(log),'exit_code':record['exit_code']})
                if file_digest(work/'.review/racket-runtime/racket/bin/racket')!=receipt['toolchain_verification']['racket_binary_sha256']:
                    raise ValueError('Our toolchain lower changed during validation')
                receipt['fresh_tests_passed']=True
                receipt['fresh_environment']={'venv_created_here':True,'system_site_packages':True,
                    'native_toolchain':'our_vendor_verified_read_only_overlay_lower_with_private_chmod_copyup',
                    'vendor':'our_issued_read_only_bind','code':'official_fresh_patch_replay_checkout'}
            if file_digest(returned)!=returned_sha:raise ValueError('Return ZIP changed during validation')
            receipt['status']='passed'
        except BaseException as error:
            receipt.update(status='failed',error=f'{type(error).__name__}: {error}');raise
        finally:
            if mounted:
                try:
                    run_record(['umount','-R',mount],Path.cwd(),receipt)
                    receipt['private_mounts_unmounted']=True
                    receipt['mountpoint_empty_after_unmount']=not any(mount.iterdir())
                except BaseException as error:receipt.update(status='failed',unmount_error=str(error))
            stream.seek(0);stream.write(json.dumps(receipt,sort_keys=True,indent=2)+'\n');stream.truncate();stream.flush();os.fsync(stream.fileno())
        if receipt['status']!='passed':raise RuntimeError('Private validation cleanup failed')
    print(json.dumps({'status':'passed','receipt':str(receipt_path)}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(f'ERROR: {type(error).__name__}: {error}',file=sys.stderr);raise SystemExit(2)
