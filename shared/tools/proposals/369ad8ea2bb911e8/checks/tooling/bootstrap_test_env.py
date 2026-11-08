"""Offline isolated test environment from installed distributions; no network.

Run with the interpreter that can already import the named dependencies.
The destination must be new. Packages are copied, never symlinked to a previous
checkout or user site. Only Python's standard interpreter/stdlib are shared.
Normal connected setup remains: python -m venv ENV; ENV/bin/python -m pip
install 'numpy>=1.26' 'Pillow>=10' 'pytest>=8'.
"""
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import venv

PACKAGES = ('numpy', 'Pillow', 'pytest', 'iniconfig', 'packaging', 'pluggy', 'Pygments')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists() or args.receipt.exists():
        parser.error('destination and receipt must both be new')
    packages = [(name, metadata.distribution(name)) for name in PACKAGES]
    venv.EnvBuilder(with_pip=False, symlinks=True).create(destination)
    interpreter = destination / 'bin/python'
    site = Path(subprocess.check_output(
        [str(interpreter), '-I', '-c', 'import sysconfig;print(sysconfig.get_path("purelib"))'], text=True).strip())
    if not site.is_relative_to(destination):
        raise RuntimeError('refusing to write dependencies outside the new environment')
    rows = []
    for name, dist in packages:
        files = []
        for relative in dist.files or ():
            relative = Path(str(relative))
            if relative.is_absolute() or '..' in relative.parts or '__pycache__' in relative.parts:
                continue
            source = dist.locate_file(relative)
            if not source.is_file():
                continue
            target = site / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if digest != hashlib.sha256(source.read_bytes()).hexdigest():
                raise RuntimeError(f'copy hash mismatch: {relative}')
            files.append({'path': str(relative), 'sha256': digest, 'size': target.stat().st_size})
        rows.append({'distribution': name, 'version': dist.version, 'files': files})
    probe = subprocess.run([str(interpreter), '-I', '-c',
        'import sys,json,pytest,numpy,PIL;print(json.dumps({"python":sys.version,"executable":sys.executable,"pytest":pytest.__version__,"numpy":numpy.__version__,"Pillow":PIL.__version__,"module_paths":[pytest.__file__,numpy.__file__,PIL.__file__]}))'],
        text=True, capture_output=True)
    receipt = {'schema': 'offline-test-environment-v1', 'destination': str(destination),
               'invoked_with': sys.executable, 'packages': rows, 'probe_exit_code': probe.returncode,
               'probe_stdout': probe.stdout, 'probe_stderr': probe.stderr,
               'network_used': False, 'user_site_enabled_in_probe': False}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
    print(probe.stdout, end='')
    if probe.returncode:
        print(probe.stderr, file=sys.stderr)
    return probe.returncode


if __name__ == '__main__':
    raise SystemExit(main())
