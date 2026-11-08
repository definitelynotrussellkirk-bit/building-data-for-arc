#!/usr/bin/env python3
"""Reproduce the unrelated API bootstrap test in untouched uploaded sources."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-zip', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='arc-pristine-test-') as temp:
        root = Path(temp)
        with ZipFile(args.source_zip) as archive:
            for member in archive.infolist():
                if not (member.filename.startswith(('repo/src/', 'repo/tests/')) or
                        member.filename in ('repo/pyproject.toml', 'repo/README.md')):
                    continue
                destination = (root / member.filename).resolve()
                if not destination.is_relative_to(root) or ((member.external_attr >> 16) & 0o170000) == 0o120000:
                    raise ValueError('unsafe archive member: ' + member.filename)
                archive.extract(member, root)
        env = dict(os.environ, PYTHONPATH='src')
        cmd = [sys.executable, '-m', 'pytest', '-q',
               'tests/test_review_solve.py::test_duties_solve_preparation_runs_from_packet_root']
        result = subprocess.run(cmd, cwd=root/'repo', env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        (args.out/'pytest.log').write_text(result.stdout)
        (args.out/'result.json').write_text(json.dumps({
            'source_zip': args.source_zip.name, 'argv': cmd, 'cwd': str(root/'repo'),
            'env_subset': {'PYTHONPATH': 'src'}, 'exit_code': result.returncode,
            'source': 'Unmodified src/tests/pyproject/README from the supplied ZIP',
        }, indent=2)+'\n')
        print(result.stdout)
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
