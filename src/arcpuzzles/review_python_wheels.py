"""Pinned offline pytest wheels; NumPy/Pillow and pip are explicitly not bundled."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

WHEELS = {
  "colorama-0.4.6-py2.py3-none-any.whl": {
    "sha256": "4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6",
    "bytes": 25335,
    "requirement": "colorama==0.4.6"
  },
  "iniconfig-2.3.0-py3-none-any.whl": {
    "sha256": "f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12",
    "bytes": 7484,
    "requirement": "iniconfig==2.3.0"
  },
  "packaging-25.0-py3-none-any.whl": {
    "sha256": "29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484",
    "bytes": 66469,
    "requirement": "packaging==25.0"
  },
  "pluggy-1.6.0-py3-none-any.whl": {
    "sha256": "e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746",
    "bytes": 20538,
    "requirement": "pluggy==1.6.0"
  },
  "pygments-2.19.2-py3-none-any.whl": {
    "sha256": "86540386c03d588bb81d44bc3928634ff26449851e99741617ecb9037ee5ec0b",
    "bytes": 1225217,
    "requirement": "pygments==2.19.2"
  },
  "pytest-9.0.2-py3-none-any.whl": {
    "sha256": "711ffd45bf766d5264d487b917733b453d917afd2b0ad65223959f59089f875b",
    "bytes": 374801,
    "requirement": "pytest==9.0.2"
  }
}


def verified_files(cache):
    cache = Path(cache)
    files = {}
    for name, pin in WHEELS.items():
        path = cache / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Missing regular pinned pytest wheel: {path}')
        if path.stat().st_size != pin['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError(f'Pinned pytest wheel SHA/size differs: {path}')
        files['vendor/python/' + name] = path
    return files


def install(cache):
    if sys.version_info < (3, 12):
        raise ValueError('Python3.12+ is required')
    if sys.prefix == sys.base_prefix:
        raise ValueError('Use a packet-local venv: python3 -m venv --system-site-packages WORK/.venv; then WORK/.venv/bin/python review.py python-install-tests')
    files = verified_files(cache)
    command = [sys.executable, '-m', 'pip', '--isolated', 'install', '--no-index',
               '--no-deps', '--ignore-installed', '--no-cache-dir', '--disable-pip-version-check',
               *map(str, files.values())]
    result = subprocess.run(command, timeout=120)
    if result.returncode:
        raise ValueError(f'Offline pytest installation failed with exit{result.returncode}; this venv needs pip (python -m ensurepip).')
    return {'pytest_installed': True, 'numpy_pillow_bundled': False,
            'next': 'Run this same interpreter with review.py python-check'}


def fetch(cache):
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, '-m', 'pip', '--isolated', 'download',
        '--only-binary=:all:', '--no-deps', '--index-url', 'https://pypi.org/simple',
        '--dest', str(cache), *[p['requirement'] for p in WHEELS.values()]], timeout=120)
    if result.returncode:
        raise ValueError('Pinned wheel retrieval failed; preserve any completed cache files and retry')
    verified_files(cache)
    return {'cache': str(cache.resolve()), 'files': len(WHEELS), 'bytes': sum(p['bytes'] for p in WHEELS.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['fetch', 'verify'])
    parser.add_argument('--cache', type=Path, default=Path('var/review/python-wheels'))
    args = parser.parse_args()
    try:
        result = fetch(args.cache) if args.action == 'fetch' else {'files': list(verified_files(args.cache))}
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
