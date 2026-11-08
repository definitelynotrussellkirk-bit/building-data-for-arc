"""Build a portable approved-generator library, independent of reviewer draws."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile
from arcpuzzles import Catalog
from arcpuzzles.review import _lock
from arcpuzzles.review_packet_selection import choose_selection, project_library
from arcpuzzles.review_full_packet import RACKET_ARCHIVE_NAME, RACKET_ARCHIVE_SHA256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--racket-archive', type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    if args.out.exists():
        raise FileExistsError(args.out)
    runtime = args.racket_archive.resolve()
    if hashlib.sha256(runtime.read_bytes()).hexdigest() != RACKET_ARCHIVE_SHA256:
        raise ValueError('Racket archive differs from pinned release')
    with _lock(root / 'REVIEW'):
        catalog = Catalog(root)
        approved = [r['id'] for r in catalog.query(approved=True)]
        selection, _ = choose_selection(catalog, root / 'REVIEW',
            size=catalog.stats()['generators'], task_ids=approved)
        files, projection = project_library(root, root / 'REVIEW', selection, fast=True)
        # The accepted-family index is useful navigation, not an approval override.
        files['REVIEW/parametric-families-current.json'] = root / 'REVIEW/parametric-families-current.json'
        index = json.loads(files['REVIEW/parametric-families-current.json'].read_text())
        tracked = set(subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0'))
        # Temporary intake receipts are not part of the distributable library.
        files = {name: path for name, path in files.items()
                 if name in tracked or name == 'REVIEW/packet-projection.json'}
        required = {}
        for family in index['families']:
            tid = family['task_id']
            acceptance = json.loads((root / family['acceptance_path']).read_text())
            evidence = json.loads((root / 'generators' / tid / 'workspace/parametric/evidence/manifest.json').read_text())
            for record in evidence['files'] + acceptance['files'] + acceptance['source_binding']['files']:
                prior = required.setdefault(record['path'], record['sha256'])
                if prior != record['sha256']:
                    raise ValueError('Conflicting required source: ' + record['path'])
        for name, expected in required.items():
            # Explicit readiness dependencies take precedence over generic
            # packet pruning (for example, a retained progress.log).
            if name not in files and name in tracked:
                files[name] = root / name
            if name not in files or hashlib.sha256(files[name].read_bytes()).hexdigest() != expected:
                raise ValueError('Required accepted-family dependency missing or changed: ' + name)
        source_commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD']).decode().strip()
        members = {'library/' + name: path for name, path in files.items()}
        members['vendor/' + RACKET_ARCHIVE_NAME] = runtime
        manifest = {'schema': 'arcpuzzles-generator-handoff-v1',
            'source_commit': source_commit, 'approved_generators': len(approved),
            'accepted_families': index['accepted_families'],
            'accepted_settings': index['accepted_settings'],
            'selected_ids': selection['selected_ids'],
            'dependency_ids': selection['dependency_ids'],
            'runtime': {'platform': 'Linux x86_64', 'archive': 'vendor/' + RACKET_ARCHIVE_NAME,
                        'sha256': RACKET_ARCHIVE_SHA256},
            'python': '>=3.12', 'dependencies': ['numpy>=1.26', 'Pillow>=10'],
            'training_admitted': False,
            'scope': 'Current approved sources and accepted parametric families. Projected tables retain approval boundaries; historical evidence graph is not re-audited.',
            'files': {name: {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
                      for name, path in sorted(members.items())}}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.out, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for name, path in sorted(members.items()):
                z.write(path, name)
            z.writestr('BUNDLE.json', json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        sha = hashlib.sha256(args.out.read_bytes()).hexdigest()
        args.out.with_suffix('.sha256').write_text(sha + '  ' + args.out.name + '\n')
        args.out.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'archive': str(args.out), 'sha256': sha, 'bytes': args.out.stat().st_size,
                         'approved_generators': len(approved), 'accepted_families': index['accepted_families'],
                         'accepted_settings': index['accepted_settings'], 'files': len(members)}))


if __name__ == '__main__':
    main()
