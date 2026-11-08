#!/usr/bin/env python3
"""Install host-available pure-Python pytest packages into an isolated venv.

For offline reviewers whose pytest is only in the Python user site. NumPy and
Pillow must already be installed in the base interpreter's system site. Rebuilds
small standard wheels from installed distributions, then installs them through
pip with --no-index. Does not disable PYTHONNOUSERSITE or alter host packages.
The target venv and temporary wheels are runtime artifacts, not return contents.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.metadata as metadata
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv
from zipfile import ZipFile, ZIP_DEFLATED


def make_wheel(name, destination):
    distribution = metadata.distribution(name)
    root = Path(distribution.locate_file("")).resolve()
    files = distribution.files or []
    wheel_record = next(p for p in files if str(p).endswith('.dist-info/WHEEL'))
    info = str(wheel_record).rsplit('/', 1)[0]
    wheel_text = distribution.locate_file(wheel_record).read_text()
    if 'Root-Is-Purelib: true' not in wheel_text:
        raise ValueError(f'{name}: only pure-Python distributions are supported')
    tags = [line.split(': ', 1)[1] for line in wheel_text.splitlines() if line.startswith('Tag: ')]
    tag = next((value for value in tags if value == 'py3-none-any'), tags[0])
    filename = info.removesuffix('.dist-info') + '-' + tag + '.whl'
    output = destination / filename
    records = []
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for relative in files:
            path = Path(str(relative))
            if path.is_absolute() or '..' in path.parts or '__pycache__' in path.parts:
                continue
            if path.suffix == '.pyc' or path.name in ('RECORD', 'INSTALLER', 'REQUESTED', 'direct_url.json'):
                continue
            source = Path(distribution.locate_file(relative)).resolve()
            if not source.is_relative_to(root) or not source.is_file():
                raise ValueError(f'{name}: missing or escaping package member {relative}')
            data = source.read_bytes()
            archive.writestr(path.as_posix(), data)
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
            records.append((path.as_posix(), 'sha256=' + digest, str(len(data))))
        record_name = info + '/RECORD'
        records.append((record_name, '', ''))
        text = io.StringIO(newline='')
        csv.writer(text, lineterminator='\n').writerows(records)
        archive.writestr(record_name, text.getvalue())
    return output, distribution.version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--venv', type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        raise SystemExit('Python 3.12+ is required')
    target = args.venv.resolve()
    if target.exists():
        raise SystemExit(f'Refusing to replace existing venv: {target}')
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(target)
    executable = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    env = dict(os.environ, PYTHONNOUSERSITE='1')
    with tempfile.TemporaryDirectory(prefix='review-pytest-wheels-') as temporary:
        directory = Path(temporary)
        packages = [make_wheel(name, directory) for name in ('pytest', 'pluggy', 'iniconfig', 'pygments', 'packaging')]
        subprocess.run([str(executable), '-m', 'pip', 'install', '--no-index', '--no-deps',
                        *[str(path) for path, _ in packages]], check=True, env=env)
        versions = {path.name: version for path, version in packages}
    subprocess.run([str(executable), '-c',
                    'import pytest,numpy,PIL; print("isolated prerequisites",pytest.__version__,numpy.__version__,PIL.__version__)'],
                   check=True, env=env)
    print(json.dumps({'status': 'ready', 'python': str(executable),
                      'python_no_user_site': True, 'installed': versions}, sort_keys=True))


if __name__ == '__main__':
    main()
