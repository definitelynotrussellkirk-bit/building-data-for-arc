"""Create an isolated test venv from already installed pure-Python test packages.

No network access or changes to the base interpreter. NumPy/Pillow remain the
base interpreter's installed system packages. PYTHONNOUSERSITE stays enabled.
Only use with trusted installed distributions; this is local dependency reuse,
not a package authenticity or sandbox verifier.
"""
import argparse
import base64
import csv
import hashlib
import importlib.metadata as md
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import venv
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    root = args.destination.resolve()
    if root.exists():
        raise FileExistsError('Use a new environment directory: ' + str(root))
    if sys.version_info < (3, 12):
        raise RuntimeError('Python 3.12 or newer is required')
    venv.EnvBuilder(with_pip=False, system_site_packages=True).create(root)
    wheels = root / 'offline-wheels'
    wheels.mkdir()
    packages = []
    for name in ('pytest', 'pluggy', 'iniconfig', 'Pygments'):
        distribution = md.distribution(name)
        if 'Root-Is-Purelib: true' not in distribution.read_text('WHEEL'):
            raise ValueError('Only pure-Python distributions may be reused: ' + name)
        members = {}
        for entry in distribution.files:
            path = PurePosixPath(str(entry))
            if path.is_absolute() or '..' in path.parts or path.suffix == '.pyc':
                continue
            if path.name in {'RECORD', 'RECORD.jws', 'RECORD.p7s'}:
                continue
            source = distribution.locate_file(entry)
            if source.is_file():
                members[path.as_posix()] = source.read_bytes()
        info = next(n.rsplit('/', 1)[0] for n in members if n.endswith('.dist-info/METADATA'))
        records = io.StringIO(newline='')
        writer = csv.writer(records, lineterminator='\n')
        for path, data in sorted(members.items()):
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
            writer.writerow([path, 'sha256=' + digest, len(data)])
        writer.writerow([info + '/RECORD', '', ''])
        members[info + '/RECORD'] = records.getvalue().encode()
        wheel = wheels / (info.removesuffix('.dist-info') + '-py3-none-any.whl')
        with zipfile.ZipFile(wheel, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for path, data in sorted(members.items()):
                archive.writestr(path, data)
        packages.append({'name': name, 'version': distribution.version,
                         'wheel': str(wheel), 'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest()})
    python = root / 'bin/python'
    env = {**os.environ, 'PYTHONNOUSERSITE': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1'}
    subprocess.run([str(python), '-m', 'pip', 'install', '--no-index', '--no-deps', '--no-user',
                    *(row['wheel'] for row in packages)], env=env, check=True)
    probe = subprocess.run([str(python), '-c',
        'import json,site,sys,pytest,numpy,PIL; assert not site.ENABLE_USER_SITE; '
        'print(json.dumps({"python":sys.version,"pytest":pytest.__version__,"numpy":numpy.__version__,"Pillow":PIL.__version__,"user_site_enabled":site.ENABLE_USER_SITE}))'],
        env=env, check=True, capture_output=True, text=True)
    receipt = {'base_interpreter': sys.executable, 'venv_interpreter': str(python),
               'network_used': False, 'base_interpreter_modified': False,
               'packages_reused': packages, 'isolated_probe': json.loads(probe.stdout)}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
