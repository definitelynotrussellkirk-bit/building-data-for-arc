"""Owner-only current maintenance counter; no scheduler or reviewer duty."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from .review import _lock

NAME = 'packet-maintenance.json'


def content_digest(archive: Path) -> str:
    """Ignore ZIP container timestamps/order/compression; bind every member."""
    with zipfile.ZipFile(archive) as source:
        rows = [(i.filename, hashlib.sha256(source.read(i)).hexdigest())
                for i in source.infolist() if not i.is_dir()]
    return hashlib.sha256(json.dumps(sorted(rows), separators=(',', ':')).encode()).hexdigest()


def _write(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    try:
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def record_accepted(review_root: Path, returned: dict) -> dict:
    """Called under the intake lock only AFTER successful native collection validation."""
    path = review_root / NAME
    if not path.exists():
        return {'status': 'not_initialized', 'maintenance_due': False}
    if returned.get('validation_status') != 'accepted':
        raise ValueError('Only accepted returns can advance maintenance')
    state = json.loads(path.read_text())
    archive = Path(returned['archive_path'])
    if returned.get('zip_sha256') and hashlib.sha256(archive.read_bytes()).hexdigest() != returned['zip_sha256']:
        raise ValueError('Accepted return archive hash changed')
    digest = content_digest(archive)
    if digest not in state['accepted_content_sha256']:
        state['accepted_content_sha256'] = sorted([*state['accepted_content_sha256'], digest])
        state['accepted_since_pass'] += 1
        state['maintenance_due'] = state['accepted_since_pass'] >= state['interval']
        _write(path, state)
    return {k: state[k] for k in ('accepted_since_pass', 'interval', 'maintenance_due')}


def notify_accepted(review_root: Path, returned: dict) -> dict:
    # A counter write failure must not misreport a completed collection as failed.
    try:
        return record_accepted(review_root, returned)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        return {'status': 'counter_update_failed', 'error': str(exc),
                'action': 'Repair current counter and replay this accepted receipt before next intake.'}


def start(review_root: Path) -> dict:
    path = review_root / NAME
    state = json.loads(path.read_text())
    if 'pass_checkpoint' in state:
        raise ValueError('Maintenance pass already started; keep its original checkpoint')
    state['pass_checkpoint'] = state['accepted_since_pass']
    _write(path, state)
    return state


def complete(review_root: Path, evidence: str) -> dict:
    """Owner attestation after an actual completed maintenance pass, not at launch."""
    evidence_path = Path(evidence).resolve()
    if not evidence_path.is_file() or not evidence_path.stat().st_size:
        raise ValueError('Completed pass requires a nonempty outcome/evidence file')
    path = review_root / NAME
    previous = json.loads(path.read_text()) if path.exists() else {}
    if previous and 'pass_checkpoint' not in previous:
        raise ValueError('Run start before maintenance; complete preserves later arrivals')
    remaining = previous.get('accepted_since_pass', 0) - previous.get('pass_checkpoint', 0)
    state = dict(schema='arcpuzzles-packet-maintenance-v1', owner_only=True, interval=25,
                 accepted_since_pass=remaining, maintenance_due=remaining >= 25,
                 accepted_content_sha256=previous.get('accepted_content_sha256', []),
                 last_completed_pass={'evidence_path': str(evidence_path),
                                      'sha256': hashlib.sha256(evidence_path.read_bytes()).hexdigest()},
                 baseline='Prospective distinct validated owner returns only; no historic count inferred.')
    _write(path, state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-root', type=Path, default=Path('REVIEW'))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('start')
    done = commands.add_parser('complete')
    done.add_argument('--evidence', required=True)
    replay = commands.add_parser('replay-accepted')
    replay.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    root = args.review_root.resolve()
    with _lock(root):
        if args.command == 'complete':
            result = complete(root, args.evidence)
        elif args.command == 'start':
            result = start(root)
        elif args.command == 'replay-accepted':
            returned = json.loads(args.receipt.read_text())
            if not args.receipt.resolve().is_relative_to(root / 'assignments'):
                raise ValueError('Replay requires an owner intake receipt under REVIEW/assignments')
            result = record_accepted(root, returned)
        else:
            path = root / NAME
            result = (json.loads(path.read_text()) if path.exists() else
                      {'status': 'not_initialized', 'maintenance_due': False,
                       'action': 'Complete the initial verified maintenance pass to arm the counter.'})
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
