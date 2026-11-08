"""Bounded, passive comparison of the temporary model/storage observations."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from . import review_evidence_bundle as bundles

STUDY = 'model-storage-20261023'
PATH = 'checks/storage-observations.jsonl'
STAGES = ['before_extract', 'after_extract', 'after_setup', 'before_package']
MAX_RETURNS = 16
MAX_BYTES = 65536


def study_policy(review_root: Path, *, today: str | None = None) -> dict | None:
    today = today or datetime.now(timezone.utc).date().isoformat()
    path = review_root / 'storage-study.json'
    try:
        count = len(json.loads(path.read_text())['returns']) if path.exists() else 0
    except (OSError, ValueError, KeyError, TypeError):
        return None  # A broken optional study never prevents building a packet.
    if today >= '2026-10-30' or count >= MAX_RETURNS:
        return None
    return dict(id=STUDY, expires_utc='2026-10-30', max_returns=MAX_RETURNS,
                max_observations_per_return=4, path=PATH, stages=STAGES,
                blocking=False, capacity_gate=False, cleanup_authorized=False)


def _read(archive):
    names = set(archive.namelist())
    if PATH in names:
        if archive.getinfo(PATH).file_size > MAX_BYTES:
            raise ValueError('Storage observations exceed 64 KiB')
        return archive.read(PATH)
    if bundles.MANIFEST not in names:
        return None
    manifest = bundles.read_manifest(archive.read(bundles.MANIFEST))
    row = next((row for row in manifest['files'] if row['path'] == PATH), None)
    if row is None:
        return None
    if row['bytes'] > MAX_BYTES:
        raise ValueError('Storage observations exceed 64 KiB')
    bundles.check_budget(manifest, [(info.filename, info.file_size) for info in archive.infolist()
                                   if info.filename != bundles.ARCHIVE])
    return bundles.verify(archive.read(bundles.ARCHIVE), manifest, retain={PATH})[PATH]


def _rows(raw: bytes, packet_sha: str) -> list[dict]:
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not 1 <= len(rows) <= 4:
        raise ValueError('Expected one to four observed checkpoints; missing stages stay missing')
    stages = set()
    for row in rows:
        if (not isinstance(row, dict) or row.get('schema') != 'arcpuzzles-storage-observation-v1'
                or row.get('study_id') != STUDY or row.get('stage') not in STAGES
                or row['stage'] in stages or row.get('freshness') not in {'fresh', 'continued', 'unknown'}
                or not isinstance(row.get('model'), str) or not 1 <= len(row['model']) <= 120
                or row.get('archive', {}).get('sha256') != packet_sha):
            raise ValueError('Invalid study identity, checkpoint, model label or packet hash')
        stages.add(row['stage'])
        stamp = datetime.fromisoformat(row['observed_utc'])
        if stamp.tzinfo is None:
            raise ValueError('Storage timestamp must include timezone')
        filesystems = row.get('filesystems')
        if not isinstance(filesystems, list) or not 1 <= len(filesystems) <= 8:
            raise ValueError('Expected bounded filesystem counters')
        for fs in filesystems:
            if not isinstance(fs, dict) or not isinstance(fs.get('path'), str) or len(fs['path']) > 4096:
                raise ValueError('Invalid filesystem path')
            if 'error' in fs:
                continue
            for key in ['device_id', 'total_bytes', 'free_bytes', 'available_bytes']:
                if type(fs.get(key)) is not int or fs[key] < 0:
                    raise ValueError('Invalid byte counter')
            if not fs['available_bytes'] <= fs['free_bytes'] <= fs['total_bytes']:
                raise ValueError('Incoherent byte counters')
            values = [fs.get(key) for key in ['total_inodes', 'free_inodes', 'available_inodes']]
            if values != [None, None, None] and (
                    any(type(value) is not int or value < 0 for value in values)
                    or not values[2] <= values[1] <= values[0]):
                raise ValueError('Invalid inode counters')
        # Keep counters needed for comparison, not directory names or diagnostics.
        for key in list(row):
            if key not in {'schema', 'study_id', 'stage', 'model', 'freshness', 'observed_utc',
                           'archive', 'mount_namespace', 'filesystems'}:
                del row[key]
    if len({(row['model'], row['freshness']) for row in rows}) != 1:
        raise ValueError('Model/freshness changed between checkpoints')
    return sorted(rows, key=lambda row: STAGES.index(row['stage']))


def retain_observations(review_root, archive, *, return_sha, packet_sha):
    """Called under the native collector lock; never executes reviewer code."""
    try:
        raw = _read(archive)
        if raw is None:
            return None
        rows = _rows(raw, packet_sha)
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeError) as exc:
        return dict(status='invalid', reason=str(exc), admission_changed=False)
    path = review_root / 'storage-study.json'
    state = json.loads(path.read_text()) if path.exists() else dict(
        schema='arcpuzzles-storage-study-v1', id=STUDY, expires_utc='2026-10-30',
        returns=[], startup_by_model=[], evidence_basis='reviewer_reported',
        interpretation='Compare fresh startup for the same ZIP; no model-specific quota or cleanup conclusion yet.')
    existing = next((row for row in state['returns'] if row['return_sha256'] == return_sha), None)
    observed_sha = hashlib.sha256(raw).hexdigest()
    if not existing and any(row['observations_sha256'] == observed_sha for row in state['returns']):
        return dict(status='duplicate_observations', admission_changed=False)
    if not existing and len(state['returns']) >= MAX_RETURNS:
        return dict(status='study_full', admission_changed=False)
    deltas = []
    for before, after in zip(rows, rows[1:]):
        if not before.get('mount_namespace') or before['mount_namespace'] != after.get('mount_namespace'):
            continue
        old = {fs['path']: fs for fs in before['filesystems'] if 'error' not in fs}
        for fs in after['filesystems']:
            prior = old.get(fs['path'])
            if 'error' in fs or not prior or prior['device_id'] != fs['device_id']:
                continue
            change = dict(path=fs['path'], before=before['stage'], after=after['stage'],
                          available_bytes_change=fs['available_bytes'] - prior['available_bytes'])
            if fs['available_inodes'] is not None and prior['available_inodes'] is not None:
                change['available_inodes_change'] = fs['available_inodes'] - prior['available_inodes']
            deltas.append(change)
    entry = dict(return_sha256=return_sha, packet_zip_sha256=packet_sha,
                 observations_sha256=observed_sha, observations=rows,
                 missing_stages=[stage for stage in STAGES if stage not in {row['stage'] for row in rows}],
                 deltas=deltas)
    if existing:
        if existing != entry:
            return dict(status='invalid', reason='Existing return has different observations', admission_changed=False)
    else:
        state['returns'].append(entry)
    state['startup_by_model'] = [dict(return_sha256=item['return_sha256'], packet_zip_sha256=item['packet_zip_sha256'],
                                    model=row['model'], filesystems=row['filesystems'])
                                for item in state['returns'] for row in item['observations']
                                if row['stage'] == 'before_extract' and row['freshness'] == 'fresh']
    review_root.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.writing.json')
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)
    return dict(status='recorded', path='REVIEW/storage-study.json', checkpoints=len(rows),
                missing_stages=entry['missing_stages'], admission_changed=False)
