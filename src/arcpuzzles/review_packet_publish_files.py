"""Stage local release files and restore the previous pair on ordinary failure."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

from .review_replay import _no_symlinks


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_receipt(path, value):
    pending = path.with_name('.' + path.name + '.tmp')
    pending.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(pending, path)


def publish_files(pairs, out, receipt, *, before_commit=None):
    """Pairs are (source, destination, expected_sha256, previous_sha256); all staged copies precede replacement.

    The journal and backups remain on incomplete rollback. This is rollback for
    synchronous errors, not an atomic multi-file filesystem transaction.
    """
    rows = []
    try:
        for index, (source, destination, wanted, expected_previous) in enumerate(pairs):
            _no_symlinks(destination);destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and not destination.is_file():raise ValueError('Nonregular destination: ' + str(destination))
            if sha(source) != wanted:raise ValueError('Publication source hash changed: ' + str(source))
            previous = sha(destination) if destination.exists() else None
            if previous != expected_previous:raise ValueError('Destination changed while staging: ' + str(destination))
            if wanted == previous:continue
            stage = destination.with_name('.' + destination.name + '.' + uuid.uuid4().hex + '.pending')
            backup = out / f'previous-{index}' if previous is not None else None
            row = {'destination':str(destination),'staged':str(stage),'sha256':wanted,
                   'previous_sha256':previous,'backup':str(backup) if backup else None}
            rows.append(row)
            if backup:
                try:os.link(destination, backup)
                except OSError:shutil.copy2(destination, backup)
                if sha(backup) != previous:raise ValueError('Previous destination changed during backup')
            shutil.copy2(source, stage)
            if sha(stage) != wanted:raise ValueError('Staged copy differs from source')
        receipt.update(status='prepared', files=rows)
        write_receipt(out / 'publication.json', receipt)
        for row in rows:
            path = Path(row['destination']);_no_symlinks(path)
            actual = sha(path) if path.exists() else None
            if actual != row['previous_sha256']:raise ValueError('Destination changed before publication: ' + str(path))
        if before_commit is not None:before_commit()
        for row in rows:os.replace(row['staged'], row['destination'])
    except BaseException:
        failures = []
        for row in reversed(rows):
            path = Path(row['destination'])
            try:
                _no_symlinks(path);actual = sha(path) if path.exists() else None
                if actual == row['previous_sha256']:continue
                if actual != row['sha256']:raise RuntimeError('Destination changed externally; recovery backup retained')
                if row['backup']:os.replace(row['backup'], path)
                else:path.unlink()
            except BaseException as error:failures.append(str(error))
        receipt.update(previous_ready_restored=not failures, rollback_errors=failures)
        raise
    finally:
        for row in rows:
            pending = Path(row['staged'])
            if pending.is_file() and not pending.is_symlink():pending.unlink()
    # The original cached packet and verification are never removed. Backups
    # belong to this transaction and no longer serve recovery after success.
    for row in rows:
        if row['backup']:
            try:Path(row['backup']).unlink(missing_ok=True)
            except OSError as error:receipt.setdefault('cleanup_warnings', []).append(str(error))
