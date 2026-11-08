"""Create a task-owned pytest environment from already installed package bytes.

Uses the base runtime's NumPy/Pillow and copies user-site test dependencies into
an independent venv. It does not enable user-site imports or download packages.
This is an offline fallback for a runtime whose pytest lives only in user-site.
"""
from __future__ import annotations
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    destination = args.out.resolve()
    if destination.exists():
        raise SystemExit('Refusing to overwrite an existing environment')
    venv.EnvBuilder(with_pip=False, system_site_packages=True, symlinks=False).create(destination)
    target = destination / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    copied = []
    for name in ('pytest', 'iniconfig', 'pluggy', 'pygments'):
        distribution = metadata.distribution(name)
        files = []
        for entry in distribution.files or ():
            relative = Path(str(entry))
            if relative.is_absolute() or '..' in relative.parts or '__pycache__' in relative.parts:
                continue
            source = Path(distribution.locate_file(entry))
            if not source.is_file():
                continue
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output)
            files.append({'path': relative.as_posix(), 'bytes': output.stat().st_size,
                          'sha256': hashlib.sha256(output.read_bytes()).hexdigest()})
        copied.append({'distribution': name, 'version': distribution.version,
                       'source': str(distribution.locate_file('')), 'files': files})
    environment = dict(os.environ, PYTHONNOUSERSITE='1')
    environment.pop('PYTHONPATH', None)
    environment.pop('PYTHONHOME', None)
    command = [str(destination/'bin/python3'), '-c',
               'import json,sys,pytest,numpy,PIL; print(json.dumps({"python":sys.version,"pytest":pytest.__version__,"numpy":numpy.__version__,"Pillow":PIL.__version__,"pytest_path":pytest.__file__}))']
    result = subprocess.run(command, cwd=destination, env=environment, text=True, capture_output=True)
    receipt = {'status': 'ready' if result.returncode == 0 else 'failed',
               'source_interpreter': sys.executable, 'environment': str(destination),
               'base_system_packages': True, 'user_site_enabled': False,
               'copied_distributions': copied, 'probe_argv': command,
               'probe_exit_code': result.returncode, 'probe_stdout': result.stdout,
               'probe_stderr': result.stderr}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k != 'copied_distributions'}))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
