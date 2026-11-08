"""Offline fallback: copy installed review dependencies into a fresh venv.

Use the SAME host Python that already has these distributions. This is a
same-machine replay aid, not a dependency installer or a portable wheel bundle.
It refuses an existing destination, excludes user-site leakage in its import
check, and records actual versions. Normal managed environments need not use it.
"""
from __future__ import annotations

import argparse
from importlib import metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    destination = args.env.resolve()
    if destination.exists() or args.out.exists():
        parser.error('environment and report destinations must both be new')
    names = ('pytest', 'pluggy', 'iniconfig', 'pygments', 'packaging', 'numpy', 'pillow')
    distributions = [(name, metadata.distribution(name)) for name in names]
    venv.EnvBuilder(with_pip=False, system_site_packages=False).create(destination)
    python = destination / 'bin' / 'python'
    purelib = Path(subprocess.check_output(
        [str(python), '-I', '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'],
        text=True).strip())
    records = []
    for name, dist in distributions:
        count = 0
        for member in dist.files or ():
            relative = Path(str(member))
            if relative.is_absolute() or '..' in relative.parts or '__pycache__' in relative.parts:
                continue
            source = Path(dist.locate_file(member))
            if source.is_file():
                target = purelib / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                count += 1
        records.append({'name': name, 'version': dist.version, 'files_copied': count})
    command = [str(python), '-I', '-c',
               'import pytest, pluggy, iniconfig, pygments, packaging, numpy, PIL; print("isolated imports passed")']
    checked = subprocess.run(command, capture_output=True, text=True)
    report = {'schema': 'offline-review-env-v1', 'host_python': sys.executable,
              'host_version': sys.version, 'environment': str(destination),
              'system_site_packages': False, 'packages': records,
              'verification_command': command, 'exit_code': checked.returncode,
              'stdout': checked.stdout, 'stderr': checked.stderr,
              'limitation': 'copies already installed distributions on this machine; no network, pip, or wheel resolution'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(args.out), 'exit_code': checked.returncode, 'packages': len(records)}))
    return checked.returncode


if __name__ == '__main__':
    raise SystemExit(main())
