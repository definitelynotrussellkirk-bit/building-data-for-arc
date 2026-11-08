"""Provision the review runner offline from already installed distributions.

Run from WORK with the interpreter that can import pytest. No user-site path is
added to the resulting runner; its pytest files are copied into its own venv.
System NumPy/Pillow remain ordinary environment dependencies. On a different
machine the standard alternative is a clean venv and pip install numpy Pillow
pytest. The venv is temporary and is not a return artifact.
"""
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import venv

work = Path.cwd()
target = work / '.venv-review'
venv.EnvBuilder(with_pip=True, system_site_packages=True).create(target)
python = target / 'bin/python'
purelib = Path(subprocess.check_output(
    [str(python), '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'],
    text=True).strip())
installed = []
for name in ('pytest', 'pluggy', 'iniconfig', 'Pygments'):
    dist = importlib.metadata.distribution(name)
    base = Path(dist.locate_file('')).resolve()
    copied = 0
    for relative in dist.files or ():
        source = Path(dist.locate_file(relative)).resolve()
        if not source.is_relative_to(base) or not source.is_file():
            continue
        destination = purelib / source.relative_to(base)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1
    installed.append({'name': name, 'version': dist.version, 'files_copied': copied})
probe = subprocess.run([str(python), '-s', '-c',
    'import sys,pytest,numpy,PIL; print(sys.executable); print(pytest.__version__,numpy.__version__,PIL.__version__)'],
    capture_output=True, text=True)
report = {'method': 'offline local distribution copies into isolated venv',
          'python': str(python), 'packages': installed, 'probe_exit_code': probe.returncode,
          'probe_stdout': probe.stdout, 'probe_stderr': probe.stderr}
report_path = work / 'checks/runtime/setup.json'
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
sys.exit(probe.returncode)
