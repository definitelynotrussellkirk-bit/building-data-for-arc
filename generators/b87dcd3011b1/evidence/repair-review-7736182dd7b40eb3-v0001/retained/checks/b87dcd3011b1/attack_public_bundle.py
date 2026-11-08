#!/usr/bin/env python3
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path('/mnt/data/arcpuzzles_work_134417')
SOURCE = ROOT / 'WORK/checks/b87dcd3011b1/preview'
OUT = ROOT / 'WORK/checks/b87dcd3011b1/public-verifier-attacks.json'


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(bundle: Path):
    proc = subprocess.run(
        ['python3', str(ROOT/'review.py'), 'preview-public', 'verify', '--bundle', str(bundle)],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
    )
    return {
        'exit_code': proc.returncode,
        'stdout_tail': proc.stdout[-1200:],
        'stderr_tail': proc.stderr[-1200:],
        'rejected': proc.returncode != 0,
    }


def first_public(bundle):
    return sorted((bundle/'public').glob('*.json'))[0]


def mutate_hidden_output(bundle: Path):
    """Leak a query answer while making public filename and private manifest self-consistent."""
    old = first_public(bundle)
    value = json.loads(old.read_bytes())
    value['test'][0]['output'] = [[9]]
    payload = raw(value)
    new_id = sha(payload)
    new = old.with_name(new_id + '.json')
    old_id = old.stem
    old.unlink()
    new.write_bytes(payload)
    manifest_path = bundle/'private/manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    for row in manifest['public_files']:
        if row['sha256'] == old_id:
            row.update(path=f'public/{new_id}.json', sha256=new_id)
    for episode in manifest['episodes']:
        episode['view_ids'] = [new_id if x == old_id else x for x in episode['view_ids']]
    manifest_path.write_bytes(raw(manifest))


def mutate_forged_manifest(bundle: Path):
    path = bundle/'private/manifest.json'
    value = json.loads(path.read_bytes())
    value['source_binding']['files'][0]['sha256'] = '0' * 64
    path.write_bytes(raw(value))


def mutate_stale_program(bundle: Path):
    epath = bundle/'private/execution.json'
    qpath = bundle/'private/qualification.json'
    mpath = bundle/'private/manifest.json'
    execution = json.loads(epath.read_bytes())
    episode = execution['episodes'][2]
    episode['program'] += '\n; stale receipt mutation\n'
    episode['program_sha256'] = sha(episode['program'].encode())
    ebytes = raw(execution)
    epath.write_bytes(ebytes)

    qualification = json.loads(qpath.read_bytes())
    qualification['execution']['sha256'] = sha(ebytes)
    qbytes = raw(qualification)
    qpath.write_bytes(qbytes)

    manifest = json.loads(mpath.read_bytes())
    manifest['execution']['sha256'] = sha(ebytes)
    manifest['qualification']['sha256'] = sha(qbytes)
    mpath.write_bytes(raw(manifest))


def mutate_unexpected_file(bundle: Path):
    (bundle/'public/unexpected.json').write_text('{}\n')


def main():
    attacks = [
        ('hidden_query_answer_with_forged_hashes', mutate_hidden_output),
        ('forged_private_manifest_source_binding', mutate_forged_manifest),
        ('stale_program_receipt_with_rehashed_envelope', mutate_stale_program),
        ('unexpected_public_file', mutate_unexpected_file),
    ]
    rows = []
    baseline = verify(SOURCE)
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-public-attacks-') as td:
        td = Path(td)
        for name, mutate in attacks:
            target = td/name
            shutil.copytree(SOURCE, target)
            mutate(target)
            result = verify(target)
            rows.append({'attack': name, **result})
    report = {
        'schema': 'arcpuzzles-public-verifier-adversarial-review-v1',
        'task_id': 'b87dcd3011b1',
        'baseline': baseline,
        'attacks': rows,
        'attacks_run': len(rows),
        'attacks_rejected': sum(r['rejected'] for r in rows),
        'status': 'passed' if baseline['exit_code'] == 0 and all(r['rejected'] for r in rows) else 'failed',
        'limits': 'Four finite mutation attacks against copied bundles. This does not prove cryptographic authenticity of editable receipts or exhaust all leakage channels.'
    }
    OUT.write_bytes(raw(report))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['status'] == 'passed' else 1

if __name__ == '__main__':
    raise SystemExit(main())
