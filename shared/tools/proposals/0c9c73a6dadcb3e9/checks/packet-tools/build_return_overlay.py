#!/usr/bin/env python3
"""Low-memory full official ARCpuzzles verification/package via a private cache overlay.

An existing cache supplies ONLY a read-only OverlayFS lower repository. Every
issued path is streamed against OUR original manifest, all differences restored
from OUR SHA-bound original ZIP, and all extra repository files hidden privately.
No other reviewer's reports, checks, solves, assignments, or private data are read.
Our bootstrap, evidence and immutable baseline are separately read-only bound.
Unchanged official review.py verify runs before authored source is installed;
unchanged official review.py package validates and builds the exact output.
Requires Linux user/mount namespaces, tmpfs, OverlayFS userxattr, and sibling
build_return_full.py/support_sparse_packet.py. Does not modify any cache owner.
"""
from __future__ import annotations
import argparse
import ctypes
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import zlib
sys.dont_write_bytecode = True
from support_sparse_packet import canonical, file_digest, no_symlinks, safe_name
from build_return_full import regular, iter_files, run_record, exclusive_copy, REQUIRED, OPTIONAL

PAIR = re.compile(r'("(?:[^"\\]|\\.)*"):("(?:[^"\\]|\\.)*")([,}])')


def manifest_files(path):
    """Canonical files-object iterator; bounded buffer, no 100k-entry dict."""
    with path.open(encoding='utf-8') as stream:
        buffer = ''
        while '"files":{' not in buffer:
            chunk = stream.read(65536)
            if not chunk:
                raise ValueError('Missing manifest files object')
            buffer = (buffer + chunk)[-131072:]
        buffer = buffer.split('"files":{', 1)[1]
        previous = ''
        while True:
            match = PAIR.match(buffer)
            while match is None:
                chunk = stream.read(65536)
                if not chunk:
                    raise ValueError('Malformed canonical files object')
                buffer += chunk
                if len(buffer) > 262144:
                    raise ValueError('Oversized manifest record')
                match = PAIR.match(buffer)
            name, digest = map(json.loads, match.group(1, 2))
            safe_name(name)
            if name <= previous or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('Unsorted or invalid manifest file binding')
            previous = name
            buffer = buffer[match.end():]
            yield name, digest
            if match.group(3) == '}':
                return


def layout_entries(path):
    with path.open(encoding='utf-8') as stream:
        buffer = ''
        while '"layout":{' not in buffer:
            chunk = stream.read(65536)
            if not chunk:
                raise ValueError('Missing layout')
            buffer = (buffer + chunk)[-131072:]
        buffer = '{' + buffer.split('"layout":{', 1)[1]
        try:
            value, _ = json.JSONDecoder().raw_decode(buffer)
        except json.JSONDecodeError:
            buffer += stream.read(65536)
            value, _ = json.JSONDecoder().raw_decode(buffer)
        if value.get('workspace') != 'WORK' or set(value.get('entry_files', {})) != {'review.py', 'START-HERE.md'}:
            raise ValueError('Invalid outer packet layout')
        return value['entry_files']


def sorted_tree_files(root, prefix='repo/'):
    """Yield path names only, globally sorted; never follow cache symlinks."""
    with os.scandir(root) as scan:
        children = sorted(scan, key=lambda e: e.name + ('/' if e.is_dir(follow_symlinks=False) else ''))
    for item in children:
        name = prefix + item.name
        if item.is_dir(follow_symlinks=False):
            yield from sorted_tree_files(Path(item.path), name + '/')
        else:
            yield name


def restore_zip_members(archive_path, wanted):
    """Read local ZIP records without building a 100k-member central index.

    Input is SHA-256 bound before this function. Selected regular files are
    decompressed in chunks and checked against our issued SHA and ZIP CRC.
    Unsupported streaming/encryption/ZIP64 layouts fail closed.
    """
    pending = dict(wanted)
    with archive_path.open('rb') as archive:
        while True:
            header = archive.read(30)
            if len(header) < 4 or header[:4] != b'PK\x03\x04':
                break
            if len(header) != 30:
                raise ValueError('Truncated local ZIP header')
            _, version, flags, method, _, _, crc, compressed, expanded, namesize, extrasize = struct.unpack('<IHHHHHIIIHH', header)
            if flags & 9 or compressed == 0xffffffff or expanded == 0xffffffff:
                raise ValueError('Encrypted, descriptor, or ZIP64 input is unsupported by bounded reader')
            name = archive.read(namesize).decode('utf-8' if flags & 0x800 else 'cp437')
            safe_name(name)
            archive.seek(extrasize, 1)
            if name not in pending:
                archive.seek(compressed, 1)
                continue
            expected, target = pending.pop(name)
            if method not in (0, 8):
                raise ValueError('Unsupported selected ZIP compression')
            decompressor = zlib.decompressobj(-15) if method == 8 else None
            digest = hashlib.sha256()
            actual_crc = total = 0
            output = None
            if target is not None:
                target.parent.mkdir(parents=True, exist_ok=True)
                no_symlinks(target)
                # Target is our own private overlay, never a cache source.
                if target.exists():
                    target.unlink()
                output = target.open('xb')
            try:
                remaining = compressed
                while remaining:
                    raw = archive.read(min(65536, remaining))
                    if not raw:
                        raise ValueError('Truncated selected ZIP member')
                    remaining -= len(raw)
                    data = decompressor.decompress(raw) if decompressor else raw
                    digest.update(data); actual_crc = zlib.crc32(data, actual_crc); total += len(data)
                    if output:
                        output.write(data)
                if decompressor:
                    tail = decompressor.flush()
                    digest.update(tail); actual_crc = zlib.crc32(tail, actual_crc); total += len(tail)
                    if output:
                        output.write(tail)
                    if not decompressor.eof:
                        raise ValueError('Incomplete deflate stream')
                if digest.hexdigest() != expected or total != expanded or actual_crc != crc:
                    raise ValueError(f'Selected original ZIP member failed SHA/CRC/size: {name}')
            finally:
                if output:
                    output.close()
            if target is not None:
                target.chmod(0o644)
    if pending:
        raise ValueError(f'Original ZIP members missing: {sorted(pending)}')


def drop_owned_zip_cache(path):
    if hasattr(os, 'posix_fadvise') and hasattr(os, 'POSIX_FADV_DONTNEED'):
        with path.open('rb') as stream:
            os.posix_fadvise(stream.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
        return True
    return False


def bind_readonly(source, target, receipt):
    no_symlinks(source); no_symlinks(target)
    if source.is_dir():
        target.mkdir(parents=True, exist_ok=True)
    else:
        regular(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch(exist_ok=False)
    run_record(['mount', '--bind', source, target], Path.cwd(), receipt)
    run_record(['mount', '-o', 'remount,bind,ro', target], Path.cwd(), receipt)


def authored_overlay(work, staged, contract, receipt):
    source_paths = {}
    for path in iter_files(work / 'repo/generators' / contract['task_id']):
        source_paths[path.relative_to(work).as_posix()] = path
    for name in contract['baseline_sha256']:
        regular(work/name)
        source_paths[name] = work/name
    inventory = hashlib.sha256(); changed = 0
    for name, source in sorted(source_paths.items()):
        target = staged/name
        if source.stat().st_mode & 0o111:
            raise ValueError(f'Executable selected source: {name}')
        digest = file_digest(source)
        inventory.update(canonical({'path': name, 'sha256': digest}) + b'\n')
        if not target.is_file() or file_digest(target) != digest:
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as incoming, target.open('wb') as outgoing:
                while chunk := incoming.read(1048576):
                    outgoing.write(chunk)
            target.chmod(0o644)
            if file_digest(target) != digest or file_digest(source) != digest:
                raise ValueError(f'Authored source changed during copy: {name}')
            changed += 1
    for name in REQUIRED + OPTIONAL:
        if (work/name).exists():
            bind_readonly(work/name, staged/name, receipt)
    bind_readonly(work/'.review/baseline', staged/'.review/baseline', receipt)
    for directory in ('checks', 'solve', 'solve-blind'):
        if (work/directory).exists():
            bind_readonly(work/directory, staged/directory, receipt)
    for private in ('solve-private', 'solve-private-blind'):
        source = work/'.review'/private/'generator.py'
        if source.exists():
            bind_readonly(source, staged/'.review'/private/'generator.py', receipt)
    return {'authored_source_paths': len(source_paths), 'private_copyups': changed,
            'authored_source_inventory_sha256': inventory.hexdigest(),
            'evidence_and_baseline_transport': 'read_only_bind_of_our_own_work'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('zip', 'source-work', 'cache-root', 'mountpoint', 'out-dir'):
        p.add_argument('--'+arg, type=Path, required=True)
    p.add_argument('--source-sha256', required=True)
    p.add_argument('--name', default='review_response_review-58c6359b7db58ccc.zip')
    p.add_argument('--reserve-output-mib',type=int,default=12)
    args = p.parse_args()
    archive, work, cache, mount, out = (getattr(args,n).absolute() for n in ('zip','source_work','cache_root','mountpoint','out_dir'))
    safe_name(args.name)
    if '/' in args.name or not args.name.endswith('.zip'):
        raise ValueError('Output must be one ZIP filename')
    for path in (archive, work, cache, mount, out):
        no_symlinks(path)
    if mount.exists() and any(mount.iterdir()):
        raise ValueError('Private mountpoint must be empty')
    if any(mount == item or mount in item.parents or item in mount.parents for item in (work,cache,out)):
        raise ValueError('Private mountpoint must be disjoint from inputs and output')
    out.mkdir(parents=True, exist_ok=True)
    final = out/args.name; receipt_path = out/(args.name+'.build.json')
    if final.exists():
        raise FileExistsError(final)
    with receipt_path.open('x') as log:
        receipt = {'schema':'arcpuzzles-private-overlay-build-v1','status':'running','commands':[],
                   'cache_root':str(cache),'source_zip':str(archive),'official_tools_modified':False,
                   'cache_owner_modified':False,'other_review_private_data_read':False}
        initial = json.dumps(receipt)
        log.write(initial + ' '*max(0,262144-len(initial))); log.flush();os.fsync(log.fileno())
        mounted = False
        output_fd = None
        output_identity = None
        try:
            if args.reserve_output_mib < 1:
                raise ValueError('Output reservation must be positive')
            output_fd=os.open(final,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            identity=os.fstat(output_fd)
            output_identity=(identity.st_dev,identity.st_ino)
            reserve_bytes=args.reserve_output_mib*1024*1024
            os.posix_fallocate(output_fd,0,reserve_bytes)
            os.fsync(output_fd)
            receipt['output_reservation']={'bytes':reserve_bytes,'exclusive_file_identity':list(output_identity),
                'reserved_file_is_not_a_successful_zip_until_receipt_passes':True}
            if file_digest(archive) != args.source_sha256:
                raise ValueError('Original ZIP hash differs from explicitly verified input hash')
            receipt['owned_input_zip_read_cache_dropped_after_hash'] = drop_owned_zip_cache(archive)
            manifest = work/'PACKET-MANIFEST.json'
            packet_id = file_digest(manifest)
            if file_digest(cache/'WORK/PACKET-MANIFEST.json') != packet_id:
                raise ValueError('Cache manifest differs from our issued packet')
            contract = json.loads((work/'ASSIGNMENT.json').read_text())
            if contract['packet_id'] != packet_id:
                raise ValueError('Our assignment packet ID mismatch')
            for name in REQUIRED:
                regular(work/name)
            for name,digest in contract['baseline_sha256'].items():
                regular(work/'.review/baseline'/name)
                if file_digest(work/'.review/baseline'/name) != digest:
                    raise ValueError(f'Frozen baseline changed: {name}')
            receipt.update(packet_id=packet_id,assignment_id=contract['assignment_id'],task_id=contract['task_id'],source_zip_sha256=args.source_sha256)
            libc=ctypes.CDLL(None,use_errno=True)
            if libc.unshare(0x20000):
                raise OSError(ctypes.get_errno(),'Creating private mount namespace failed')
            run_record(['mount','--make-rprivate','/'],Path.cwd(),receipt)
            mount.mkdir(parents=True,exist_ok=True)
            run_record(['mount','-t','tmpfs','-o','size=512M,nr_inodes=30000,mode=0700,nodev,nosuid','arc-overlay-private',mount],Path.cwd(),receipt)
            mounted=True
            checkout=mount/'checkout'; staged=checkout/'WORK'
            for directory in (staged/'repo',mount/'upper',mount/'overlay-work'):
                directory.mkdir(parents=True,exist_ok=True)
            run_record(['mount','-t','overlay','overlay','-o',f'lowerdir={cache}/WORK/repo,upperdir={mount}/upper,workdir={mount}/overlay-work,userxattr',staged/'repo'],Path.cwd(),receipt)
            # Only the repository is borrowed; foreign .review/checks/solves and
            # assignment/report paths are outside this mount and never accessed.
            restores={'WORK/PACKET-MANIFEST.json':(packet_id,None)}
            repo_names=iter(sorted_tree_files(staged/'repo'))
            current=next(repo_names,None); checked=matching=hidden=0
            own_present={path.relative_to(work).as_posix():path for path in iter_files(work/'repo')}
            home=f"repo/generators/{contract['task_id']}/"
            for name,digest in manifest_files(manifest):
                if name in contract['baseline_sha256'] and contract['baseline_sha256'][name] != digest:
                    raise ValueError('Baseline binding differs from issued manifest')
                if name.startswith('repo/'):
                    while current is not None and current < name:
                        (staged/current).unlink();hidden+=1;current=next(repo_names,None)
                    target=staged/name
                    okay=False
                    try:
                        regular(target);okay=file_digest(target)==digest
                    except (FileNotFoundError,ValueError):
                        pass
                    checked+=1
                    if okay:matching+=1
                    else:restores['WORK/'+name]=(digest,target)
                    if current==name:current=next(repo_names,None)
                    if name in own_present and not name.startswith(home) and name not in contract['baseline_sha256']:
                        if file_digest(own_present.pop(name)) != digest:
                            raise ValueError(f'Changed protected own working source: {name}')
                    elif name in own_present:
                        own_present.pop(name)
                else:
                    source=work/name
                    if source.is_file() and not source.is_symlink() and file_digest(source)==digest:
                        bind_readonly(source,staged/name,receipt)
                    else:
                        restores['WORK/'+name]=(digest,staged/name)
            while current is not None:
                (staged/current).unlink();hidden+=1;current=next(repo_names,None)
            if any(not name.startswith(home) for name in own_present):
                raise ValueError('Undeclared protected own working sources')
            del own_present
            for name,digest in layout_entries(manifest).items():
                source=work.parent/name
                regular(source)
                if file_digest(source)!=digest:
                    raise ValueError('Our outer official entry changed')
                bind_readonly(source,checkout/name,receipt)
            bind_readonly(manifest,staged/'PACKET-MANIFEST.json',receipt)
            restore_zip_members(archive,restores)
            receipt['owned_input_zip_read_cache_dropped_after_restore'] = drop_owned_zip_cache(archive)
            receipt['issued_cache_validation']={'repo_paths_checked':checked,'matching_paths':matching,
                'restored_repo_paths':[n for n in sorted(restores) if n.startswith('WORK/repo/')],
                'restored_issued_members':len(restores)-1,'hidden_extra_repo_files':hidden}
            del restores;gc.collect()
            if hasattr(libc,'malloc_trim'):libc.malloc_trim(0)
            env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
            env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
            run_record([sys.executable,checkout/'review.py','verify'],checkout,receipt,env=env)
            receipt['full_official_verification_before_overlay']=True
            receipt['authored_overlay']=authored_overlay(work,staged,contract,receipt)
            packaged=mount/args.name
            run_record([sys.executable,checkout/'review.py','package','--bundle-evidence','--out',packaged],checkout,receipt,env=env)
            receipt['official_zip_sha256']=file_digest(packaged)
            receipt['official_zip_bytes']=packaged.stat().st_size
            size=packaged.stat().st_size
            if size>reserve_bytes:
                raise ValueError('Official ZIP exceeds preallocated output; retry with larger --reserve-output-mib')
            identity=final.stat(follow_symlinks=False)
            if (identity.st_dev,identity.st_ino)!=output_identity:
                raise ValueError('Reserved output identity changed')
            os.lseek(output_fd,0,os.SEEK_SET)
            with packaged.open('rb') as incoming:
                while chunk:=incoming.read(1048576):
                    view=memoryview(chunk)
                    while view:
                        written=os.write(output_fd,view)
                        if not written:raise OSError('Output reservation write made no progress')
                        view=view[written:]
            os.fsync(output_fd)
            os.ftruncate(output_fd,size)
            os.fsync(output_fd)
            receipt['exported_zip_sha256']=file_digest(final)
            if receipt['exported_zip_sha256']!=receipt['official_zip_sha256']:
                raise ValueError('Reserved output bytes differ from exact official ZIP')
            receipt['status']='passed'
        except BaseException as error:
            receipt.update(status='failed',error=f'{type(error).__name__}: {error}')
            raise
        finally:
            if mounted:
                try:
                    run_record(['umount','-R',mount],Path.cwd(),receipt)
                    receipt['private_mounts_unmounted']=True
                    receipt['mountpoint_empty_after_unmount']=not any(mount.iterdir())
                except BaseException as error:
                    receipt.update(status='failed',unmount_error=str(error))
            if output_fd is not None:
                if receipt['status']!='passed':
                    try:
                        identity=final.stat(follow_symlinks=False)
                        if (identity.st_dev,identity.st_ino)==output_identity:
                            final.unlink()
                            receipt['failed_output_reservation_removed']=True
                    except FileNotFoundError:
                        pass
                os.close(output_fd)
            log.seek(0);log.write(json.dumps(receipt,sort_keys=True,indent=2)+'\n');log.truncate();log.flush();os.fsync(log.fileno())
        if receipt['status']!='passed':
            raise RuntimeError('Private build cleanup failed')
    print(json.dumps({'status':'passed','zip':str(final),'receipt':str(receipt_path)}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(f'ERROR: {type(error).__name__}: {error}',file=sys.stderr);raise SystemExit(2)
