"""Reviewed exact-text proposals and explicit selected-copy application.

This is deliberately not a Racket semantic-equivalence checker. Only a restricted
reader subset with identical tokens after whitespace/line-comment removal is
eligible. Strings, escaped symbols, character literals and reader extensions
require manual review. Canonical and archival sources are never rewritten.
"""
from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import uuid

from .catalog import Catalog, local_path


def _sha(blob: bytes | str) -> str:
    return hashlib.sha256(blob.encode('utf-8') if isinstance(blob, str) else blob).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _decode(text):
    return json.loads(text, object_pairs_hook=_object)


def _tokens(source: str) -> list[str]:
    # Keep delimiters and quote tokens distinct. A semicolon consumes only its
    # actual line, so moving a newline across a comment cannot hide rule edits.
    if any((ord(char) < 32 and char not in '\t\r\n') or ord(char) > 126 for char in source):
        raise ValueError('Unsupported Racket reader character; review manually')
    tokens = []
    for line in source.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        code = line.partition(';')[0]
        if any(char in code for char in ('"', '|', '\\', '`', ',')):
            raise ValueError('Unsupported Racket lexical construct; review manually')
        for token in re.findall(r"[()\[\]{}']|[^\s()\[\]{}']+", code):
            if '#' in token and not (token in ('#t', '#f') or re.fullmatch(r'#[\:][A-Za-z][A-Za-z0-9_-]*', token)):
                raise ValueError('Unsupported Racket reader construct; review manually')
            tokens.append(token)
    return tokens


def _checked_path(root: Path, name: str) -> Path:
    path = local_path(root, name)
    # Even internal links can change the meaning of a repository-relative patch.
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise ValueError(f'Symlinked authority path requires manual review: {name}')
    return path


def _read(root: Path, name: str) -> bytes:
    return _checked_path(root, name).read_bytes()


def _replace_target(text: str, old: str, new: str) -> str:
    pattern = r'"target_code"\s*:\s*("(?:\\.|[^"\\])*")'
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1 or _decode(matches[0][1]) != old:
        raise ValueError('Selected target_code encoding is not unique; review manually')
    start, end = matches[0].span(1)
    return text[:start] + json.dumps(new) + text[end:]


def _diff(name: str, before: str, after: str) -> str:
    result = [f'diff --git a/{name} b/{name}\n']
    for line in difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                   fromfile=f'a/{name}', tofile=f'b/{name}', n=3):
        result.append(line)
        if not line.endswith('\n'):
            result.append('\n\\ No newline at end of file\n')
    return ''.join(result)


def propose_selected_sync(catalog: Catalog, task: str) -> dict:
    """Read one task's current source and emit a hash-bound patch, never apply it."""
    task = catalog.resolve(task)
    root = catalog.root
    canonical_name = 'shared/data/canonical/puzzles.jsonl'
    canonical_blob = _read(root, canonical_name)
    sources = []
    for number, line in enumerate(canonical_blob.decode('utf-8').splitlines(), 1):
        if line.strip():
            row = _decode(line)
            if not isinstance(row, dict):
                raise ValueError('Canonical ledger row must be an object')
            if row.get('task_id') == task:
                source = row.get('program_solution')
                if not isinstance(source, str) or not source.strip():
                    raise ValueError('Canonical program_solution must be nonempty text')
                sources.append((number, source))
    if len({source for _, source in sources}) != 1:
        raise ValueError('Need one exact canonical program_solution across task records')
    canonical = sources[0][1]
    mapping_name = 'catalog/authority_files.json'
    mapping_blob = _read(root, mapping_name)
    mapping = _decode(mapping_blob)
    if not isinstance(mapping, dict):
        raise ValueError('Authority catalog must be an object')
    names = sorted(name for name, owner in mapping.items() if owner == task)
    if not names:
        raise ValueError('No catalog-bound selected authority files for task')
    files, patches = [], []
    for name in names:
        path = PurePosixPath(name)
        if (str(path) != name or '..' in path.parts or path.is_absolute()
                or not name.startswith('data/base/solutions/') or not name.endswith('.json')
                or not re.fullmatch(r'[A-Za-z0-9_./-]+', name)):
            raise ValueError(f'Unsupported authority catalog path: {name!r}')
        name = 'shared/' + name
        blob = _read(root, name); text = blob.decode('utf-8'); row = _decode(text)
        if not isinstance(row, dict) or row.get('task_id') != task:
            raise ValueError(f'{name}: selected task identity mismatch')
        target = row.get('racket_target')
        if not isinstance(target, dict) or not isinstance(target.get('target_code'), str) or not target['target_code'].strip():
            raise ValueError(f'{name}: missing selected target_code')
        old = target['target_code']
        changed = old != canonical
        patched = text
        if changed:
            if _tokens(old) != _tokens(canonical):
                raise ValueError(f'{name}: rule tokens differ; semantic changes require manual review')
            patched = _replace_target(text, old, canonical)
            expected = copy.deepcopy(row); expected['racket_target']['target_code'] = canonical
            if _decode(patched) != expected:
                raise ValueError(f'{name}: proposal changed unrelated fields')
            patches.append(_diff(name, text, patched))
        files.append({'path': name, 'old_sha256': _sha(blob), 'new_sha256': _sha(patched),
                      'selected_source_sha256_before': _sha(old), 'selected_source_sha256_after': _sha(canonical),
                      'changed_json_pointers': ['/racket_target/target_code'] if changed else [],
                      'archival_raw_code_unchanged': True})
    patch = ''.join(patches)
    return {'schema': 'arcpuzzles-selected-authority-proposal-v1', 'task_id': task,
            'status': 'proposal' if patch else 'already_synchronized', 'applied': False,
            'roles': {'source': 'canonical program_solution', 'destination': 'selected racket_target.target_code',
                      'preserved': 'archival raw_code'}, 'files': files, 'patch': patch, 'patch_sha256': _sha(patch),
            'patch_path_base': 'repository root (shared/ paths); not the flattened checker --patch layout',
            'inspection_pins': {canonical_name: _sha(canonical_blob), mapping_name: _sha(mapping_blob)},
            'canonical_lines': [number for number, _ in sources], 'canonical_source_sha256': _sha(canonical),
            'canonical_rule_hash': _sha(' '.join(canonical.split()))[:12],
            'proof_scope': 'Identical tokens in a restricted Racket reader subset. No execution or general semantic-equivalence claim.',
            'next_steps': 'Review every file hash and the patch, then explicitly --apply this saved proposal. Recreate the proposal if sources change.',
            'verify_argv': [['arcpuzzles', 'check', task, '--stage', stage, '--out', 'NEW_' + stage.upper() + '_DIRECTORY']
                            for stage in ('authority_sync', 'rule_smoke')]}


def _replace_file(path: Path, blob: bytes) -> None:
    """Replace one complete file; preserve its mode and avoid partial text writes."""
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, name = tempfile.mkstemp(prefix='.authority-sync-', dir=path.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(blob); handle.flush(); os.fsync(handle.fileno())
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def _save_receipt(path: Path, value: dict) -> None:
    staged = path.with_suffix('.tmp')
    with staged.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    os.replace(staged, path)


def apply_selected_sync(catalog: Catalog, task: str, proposal_path: Path) -> dict:
    """Apply exactly the reviewed proposal, retaining source-bound recovery data.

    Review writers cooperate through the existing review lock. Each file replace
    is atomic; the multi-file operation is not crash-atomic. Recovery snapshots
    are written before the first replace. Caught failures roll back only bytes
    still equal to this operation's proposed bytes, preserving external edits.
    """
    from .review import _lock

    task = catalog.resolve(task); root = catalog.root
    proposal_blob = proposal_path.read_bytes(); reviewed = _decode(proposal_blob.decode('utf-8'))
    if not isinstance(reviewed, dict) or reviewed.get('task_id') != task:
        raise ValueError('Reviewed proposal task mismatch')
    review_root = _checked_path(root, 'REVIEW')
    with _lock(review_root):
        fresh = propose_selected_sync(catalog, task)
        if reviewed != fresh:
            raise ValueError('Reviewed proposal is stale or altered; recreate and review it before apply')
        changed = [item for item in fresh['files'] if item['changed_json_pointers']]
        if not changed:
            return {'schema': 'arcpuzzles-selected-authority-apply-v1', 'task_id': task,
                    'status': 'already_synchronized', 'applied': False, 'files': [],
                    'canonical_rule_hash': fresh['canonical_rule_hash']}
        originals, desired = {}, {}
        canonical_rows = [_decode(line) for line in _read(root, 'shared/data/canonical/puzzles.jsonl').decode('utf-8').splitlines() if line.strip()]
        canonical = next(row['program_solution'] for row in canonical_rows if row['task_id'] == task)
        for item in changed:
            name = item['path']; original = _read(root, name)
            if _sha(original) != item['old_sha256']:
                raise ValueError('Reviewed proposal source changed before staging')
            old = _decode(original.decode('utf-8'))['racket_target']['target_code']
            replacement = _replace_target(original.decode('utf-8'), old, canonical).encode('utf-8')
            if _sha(replacement) != item['new_sha256']:
                raise ValueError('Reviewed proposal replacement hash mismatch')
            originals[name] = original; desired[name] = replacement
        directory = f'var/review/authority-sync/{task}-{uuid.uuid4().hex}'
        recovery = _checked_path(root, directory); recovery.mkdir(parents=True, exist_ok=False)
        for name, original in originals.items():
            snapshot = recovery / 'originals' / name; snapshot.parent.mkdir(parents=True, exist_ok=True)
            with snapshot.open('xb') as handle:
                handle.write(original); handle.flush(); os.fsync(handle.fileno())
        receipt_path = recovery / 'receipt.json'
        receipt = {'schema': 'arcpuzzles-selected-authority-apply-v1', 'task_id': task,
                   'status': 'prepared', 'applied': None, 'files': changed,
                   'proposal_sha256': _sha(proposal_blob), 'patch_sha256': fresh['patch_sha256'],
                   'inspection_pins': fresh['inspection_pins'], 'canonical_rule_hash': fresh['canonical_rule_hash'],
                   'recovery_directory': directory, 'receipt': directory + '/receipt.json',
                   'verify_argv': fresh['verify_argv'], 'conflicts': [],
                   'coordination': 'Existing REVIEW/.lock; uncoordinated editors must stop before apply.',
                   'recovery_scope': 'Per-file atomic replacement, not crash-atomic across files. Inspect original/proposed hashes before restoring snapshots.'}
        _save_receipt(receipt_path, receipt)
        attempted = []
        try:
            # Recheck the whole reviewed snapshot after staging, before any write.
            if propose_selected_sync(catalog, task) != fresh:
                raise ValueError('Reviewed proposal source changed before commit')
            for item in changed:
                name = item['path']
                for source, pin in fresh['inspection_pins'].items():
                    if _sha(_read(root, source)) != pin:
                        raise ValueError('Canonical/catalog source changed during apply')
                if _sha(_read(root, name)) != item['old_sha256']:
                    raise ValueError('Selected authority changed during apply')
                attempted.append(item)
                _replace_file(_checked_path(root, name), desired[name])
            for item in fresh['files']:
                if _sha(_read(root, item['path'])) != item['new_sha256']:
                    raise ValueError('Selected authority changed before final verification')
            for source, pin in fresh['inspection_pins'].items():
                if _sha(_read(root, source)) != pin:
                    raise ValueError('Canonical/catalog source changed before final verification')
            receipt.update(status='applied', applied=True)
            _save_receipt(receipt_path, receipt)
        except (Exception, KeyboardInterrupt) as exc:
            conflicts = []
            for item in reversed(attempted):
                name = item['path']
                try:
                    current = _read(root, name)
                    if _sha(current) == item['old_sha256']:
                        continue
                    if _sha(current) != item['new_sha256']:
                        conflicts.append(name); continue
                    _replace_file(_checked_path(root, name), originals[name])
                except (OSError, ValueError):
                    conflicts.append(name)
            receipt.update(status='recovery_required' if conflicts else 'rolled_back',
                           applied=False if not conflicts else None, conflicts=conflicts, error=str(exc))
            _save_receipt(receipt_path, receipt)
            raise RuntimeError(f"Authority apply {receipt['status']}: {exc}; inspect {receipt['receipt']}") from exc
        return receipt
