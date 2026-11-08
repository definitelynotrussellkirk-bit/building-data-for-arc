#!/usr/bin/env python3
"""Run an argument vector with a private, bounded 512 MiB temporary filesystem.

Usage: python3 run_with_private_tmpfs.py -- COMMAND [ARG ...]
Persistent outputs must be outside TMPDIR. No shell is used for COMMAND.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PREFIX = 'arc-review-private-tmpfs-'
MOUNT_OPTIONS = 'size=512m,nodev,nosuid,mode=700'


def shell_status(code: int) -> int:
    return code if code >= 0 else 128 - code


def inside(mountpoint_text: str, command: list[str]) -> int:
    mountpoint = Path(mountpoint_text)
    if (not mountpoint.is_absolute() or mountpoint.parent != Path('/tmp')
            or not mountpoint.name.startswith(PREFIX) or mountpoint.is_symlink()
            or not mountpoint.is_dir() or any(mountpoint.iterdir())):
        raise RuntimeError('Refusing mount outside the new, empty owned /tmp directory')
    info = mountpoint.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError('Private mountpoint must be owned by this user with mode 0700')
    # unshare has already created a private user/mount namespace. This mount
    # affects only that namespace and never overlays an existing mount.
    mounted = subprocess.run(['mount', '-t', 'tmpfs', '-o', MOUNT_OPTIONS,
                              'tmpfs', str(mountpoint)], check=False)
    if mounted.returncode:
        return shell_status(mounted.returncode)
    environment = os.environ.copy()
    environment['TMPDIR'] = str(mountpoint)
    # Keep PATH, the selected interpreter/venv, cwd, and all other environment.
    os.execvpe(command[0], command, environment)
    return 127


def main(argv: list[str]) -> int:
    if argv and argv[0] == '--_inside':
        if len(argv) < 3:
            raise RuntimeError('Internal invocation needs a mountpoint and command')
        return inside(argv[1], argv[2:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command
    if command[:1] == ['--']:
        command = command[1:]
    if not command:
        parser.error('supply -- COMMAND [ARG ...]')
    if not shutil.which('unshare') or not shutil.which('mount'):
        parser.error('Linux unshare and mount are required')
    # The underlying directory is empty again when the private namespace exits.
    with tempfile.TemporaryDirectory(prefix=PREFIX, dir='/tmp') as directory:
        namespace_command = [
            'unshare', '--user', '--map-root-user', '--mount', '--fork',
            '--propagation', 'private', sys.executable, str(Path(__file__).resolve()),
            '--_inside', directory, *command,
        ]
        return shell_status(subprocess.run(namespace_command, check=False).returncode)


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(130)
    except (OSError, RuntimeError) as exc:
        print(f'private tmpfs: {exc}', file=sys.stderr)
        raise SystemExit(1)
