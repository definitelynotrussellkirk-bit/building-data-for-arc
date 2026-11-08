#!/usr/bin/env python3
"""Run explicit argv in one private Linux tmpfs; export return/ before exit.

This is a storage workaround for trusted commands, not a security sandbox.
Only Python's standard library and Linux unshare/mount/umount are required.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

CHILD = r'''import json, os, shutil, stat, subprocess, sys
from pathlib import Path
p=json.loads(sys.argv[1]); target=Path(p['target']); output=Path(p['output'])
mounted=False; status=70
try:
    if (os.readlink('/proc/self/ns/mnt') == p['mount_ns'] or
            os.readlink('/proc/self/ns/user') == p['user_ns']):
        raise RuntimeError('private user and mount namespaces were not established')
    # Atomic creation refuses any preexisting target, including a dangling symlink.
    target.mkdir(mode=0o700)
    r=subprocess.run([p['mount'], '-t', 'tmpfs', '-o',
        'size='+str(p['size'])+'M,mode=0700,nosuid,nodev', 'tmpfs', str(target)],
        shell=False, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('private tmpfs mount failed: '+r.stderr.strip())
    mounted=True
    returns=target/'return'; returns.mkdir(mode=0o700)
    env=dict(os.environ, MEMORY_WORK_DIR=str(target), MEMORY_RETURN_DIR=str(returns),
             MEMORY_OUTPUT_DIR=str(output), PYTHONDONTWRITEBYTECODE='1')
    try:
        result=subprocess.run(p['command'], cwd=target, env=env, shell=False)
        status=result.returncode if result.returncode >= 0 else 128-result.returncode
    except OSError as exc:
        print('memory-workspace: command could not run: '+str(exc), file=sys.stderr)
        status=127
    # Copy only the command's explicit return tree, including failure evidence.
    if output.is_symlink() or not output.is_dir():
        raise RuntimeError('output directory was replaced')
    info=output.stat()
    if [info.st_dev, info.st_ino] != p['output_identity']:
        raise RuntimeError('output directory was replaced')
    if returns.is_symlink() or not returns.is_dir():
        raise RuntimeError('return directory must remain a real directory')
    for root, dirs, files in os.walk(returns, followlinks=False):
        for name in dirs+files:
            item=Path(root)/name; mode=item.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise RuntimeError('symlink exports are not allowed: '+str(item))
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise RuntimeError('special-file exports are not allowed: '+str(item))
    if any(output.iterdir()):
        raise RuntimeError('output directory is no longer empty; refusing overwrite')
    shutil.copytree(returns, output, dirs_exist_ok=True)
    # Flush exported ordinary files; filesystem/hardware durability is still external.
    for root, dirs, files in os.walk(output):
        for name in files:
            with open(Path(root)/name, 'rb') as handle: os.fsync(handle.fileno())
        fd=os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    print('memory-workspace: exported return/ to '+str(output), file=sys.stderr)
except (OSError, RuntimeError) as exc:
    print('memory-workspace: '+str(exc), file=sys.stderr)
    status=70
finally:
    if mounted:
        r=subprocess.run([p['umount'], str(target)], shell=False, capture_output=True, text=True)
        if r.returncode:
            print('memory-workspace: private unmount failed; stop background users: '+r.stderr.strip(), file=sys.stderr)
            status=70
sys.exit(status)
'''


def new_target(raw: str, label: str) -> Path:
    path=Path(raw)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError(label+' must be an absolute path without ..')
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(label+' must not contain a symlink')
    if path.exists():
        raise ValueError(label+' must not already exist (even when empty)')
    parent=path.parent
    if not parent.is_dir() or parent.stat().st_uid != os.geteuid():
        raise ValueError(label+' requires an existing parent owned by the current user')
    return path


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True, help='new absolute child directory for this private mount')
    parser.add_argument('--output-dir', required=True, help='new absolute directory outside work-dir; receives return/')
    parser.add_argument('--size-mib', type=int, default=256, help='tmpfs capacity limit, not reserved memory (default 256)')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='-- followed by explicit argv')
    args=parser.parse_args(argv)
    try:
        if sys.platform != 'linux':
            raise ValueError('Linux with enabled user namespaces is required')
        if not 1 <= args.size_mib <= 1048576:
            raise ValueError('--size-mib must be between 1 and 1048576')
        command=args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command:
            raise ValueError('an explicit command after -- is required')
        target=new_target(args.work_dir,'work directory')
        output=Path(args.output_dir)
        if target == output or target in output.parents or output in target.parents:
            raise ValueError('output directory must be outside the transient work directory')
        output=new_target(args.output_dir,'output directory')
        programs={name: shutil.which(name) for name in ('unshare','mount','umount')}
        if not all(programs.values()):
            raise ValueError('Linux unshare, mount and umount executables are required')
    except (ValueError,OSError) as exc:
        parser.error(str(exc))
    try:
        output.mkdir(mode=0o700)
        info=output.stat()
        payload=dict(target=str(target),output=str(output),size=args.size_mib,command=command,
            mount=programs['mount'],umount=programs['umount'],
            mount_ns=os.readlink('/proc/self/ns/mnt'),user_ns=os.readlink('/proc/self/ns/user'),
            output_identity=[info.st_dev,info.st_ino])
        print('memory-workspace: transient files vanish when its namespace exits; only return/ is exported.',file=sys.stderr)
        result=subprocess.run([programs['unshare'],'--user','--map-root-user','--mount',
            '--propagation','private',sys.executable,'-B','-c',CHILD,json.dumps(payload)],shell=False)
        if result.returncode:
            print('memory-workspace: command or namespace setup failed (status '+str(result.returncode)+'); inspect messages above.',file=sys.stderr)
        return result.returncode if result.returncode >= 0 else 128-result.returncode
    except OSError as exc:
        print('memory-workspace: setup failed: '+str(exc),file=sys.stderr)
        return 70

if __name__ == '__main__':
    raise SystemExit(main())
