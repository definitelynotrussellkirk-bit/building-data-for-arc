"""Owner-only compatibility for old public returns missing safe reference metadata.

This module edits only one RULE_TASK_ID declaration. It does not approve source,
register catalog data, alter programs/resources, or replace actual owner execution.
Original reviewer receipts and witnesses remain unchanged.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from .review import _lock
from .review_public_creation import generator_id, reference_id

SCHEMA = 'arcpuzzles-public-reference-compatibility-v1'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _identity(root, tid, pid):
    if tid != generator_id(pid):
        raise ValueError('Compatibility repair requires the exact public generator namespace')
    raw = Path(root).absolute()
    if any(p.is_symlink() for p in (raw, *raw.parents)):
        raise ValueError('Compatibility root cannot contain symlinks')
    return raw.resolve(), f'generators/{tid}/generator.py', reference_id(pid)


def _safe(root, relative, *, file=False):
    name = Path(relative)
    if name.is_absolute() or '..' in name.parts or '\\' in str(relative):
        raise ValueError('Compatibility path must be library-relative')
    path = root / name
    if not path.resolve().is_relative_to(root):
        raise ValueError('Compatibility path escapes its checkout')
    if any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
        raise ValueError('Compatibility paths cannot contain symlinks')
    if file and not path.is_file():
        raise ValueError('Compatibility source/proof must be a regular file: ' + str(relative))
    return path


def _plan(raw, tid, rid):
    """Return one reversible metadata edit, or None for an already valid literal."""
    try:
        text = raw.decode('utf-8-sig')
        tree = ast.parse(text)
        compile(raw, '<public-generator-compatibility>', 'exec')
    except (UnicodeError, SyntaxError) as error:
        raise ValueError('Compatibility source must be valid UTF-8 Python') from error
    declarations = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            names = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            names = [statement.target]
        else:
            continue
        if any(isinstance(name, ast.Name) and name.id == 'RULE_TASK_ID' for name in names):
            if len(names) != 1 or not isinstance(names[0], ast.Name):
                raise ValueError('Compatibility cannot change a multi-target declaration')
            declarations.append(statement)
    stores = [node for node in ast.walk(tree) if isinstance(node, ast.Name)
              and node.id == 'RULE_TASK_ID' and isinstance(node.ctx, (ast.Store, ast.Del))]
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.alias)
               and (node.asname or node.name) == 'RULE_TASK_ID']
    definitions = [node for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                   and node.name == 'RULE_TASK_ID']
    if len(declarations) > 1 or len(stores) != len(declarations) or imports or definitions:
        raise ValueError('Compatibility requires one simple literal or a missing declaration')
    bom = 3 if raw.startswith(b'\xef\xbb\xbf') else 0
    lines = raw[bom:].splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    if declarations:
        value = declarations[0].value
        if not isinstance(value, ast.Constant) or type(value.value) is not str:
            raise ValueError('Compatibility refuses computed RULE_TASK_ID declarations')
        if value.value == rid:
            return None
        if value.value != tid:
            raise ValueError('Compatibility refuses a different RULE_TASK_ID authority')
        start = bom + offsets[value.lineno - 1] + value.col_offset
        end = bom + offsets[value.end_lineno - 1] + value.end_col_offset
        old, new = raw[start:end], repr(rid).encode()
        kind = 'replace_descriptive_literal'
    else:
        # Preserve module docstrings, encoding/shebang lines and future imports.
        headers = []
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and type(tree.body[0].value.value) is str:
            headers.append(tree.body[0])
        headers.extend(node for node in tree.body if isinstance(node, ast.ImportFrom) and node.module == '__future__')
        if headers:
            start = bom + offsets[max(node.end_lineno for node in headers)]
        elif tree.body:
            first = tree.body[0]
            line = min([first.lineno, *[d.lineno for d in getattr(first, 'decorator_list', [])]])
            start = bom + offsets[line - 1]
        else:
            start = len(raw)
        newline = b'\r\n' if b'\r\n' in raw else b'\n'
        boundary = newline if start > bom and raw[start-1:start] not in (b'\n', b'\r') else b''
        old = b''
        new = boundary + b'RULE_TASK_ID = ' + repr(rid).encode() + newline
        kind = 'insert_missing_literal'
    result = raw[:start] + new + raw[start + len(old):]
    compile(result, '<public-generator-compatibility>', 'exec')
    return {'kind': kind, 'offset': start, 'before': old.decode(), 'after': new.decode()}, result


def _raw(record):
    return (json.dumps(record, sort_keys=True, indent=2) + '\n').encode()


def _atomic(path, raw, mode=0o644):
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-compat-', dir=path.parent)
    pending = Path(name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        os.replace(pending, path)
    finally:
        pending.unlink(missing_ok=True)


def repair_reference_id(root, tid, pid):
    """Repair only missing/descriptive literals; accepted source is never edited."""
    root, relative, rid = _identity(root, tid, pid)
    _safe(root, 'REVIEW')
    with _lock(root / 'REVIEW'):
        path = _safe(root, relative, file=True)
        before = path.read_bytes()
        plan = _plan(before, tid, rid)
        if plan is None:
            return None
        accepted = _safe(root, f'generators/{tid}/parametric/accepted.json')
        if accepted.exists():
            raise ValueError('Compatibility cannot edit a generator with an accepted artifact')
        edit, after = plan
        receipt_name = f'generators/{tid}/evidence/owner-reference-compatibility/{_sha(before)}.json'
        receipt = _safe(root, receipt_name)
        record = {'schema': SCHEMA, 'task_id': tid, 'public_task_id': pid,
                  'reference_id': rid, 'generator_path': relative,
                  'before_sha256': _sha(before), 'after_sha256': _sha(after),
                  'edit': edit, 'receipt_path': receipt_name,
                  'scope': 'Reference identifier metadata only; owner/native execution still required.',
                  'approval_granted': False, 'training_admitted': False}
        payload = _raw(record)
        if receipt.exists() and (not receipt.is_file() or receipt.read_bytes() != payload):
            raise ValueError('Existing compatibility proof differs; explicit owner retry required')
        receipt.parent.mkdir(parents=True, exist_ok=True)
        _safe(root, receipt_name)
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.read_bytes() != before:
            raise ValueError('Generator changed during compatibility planning')
        _atomic(path, after, mode)
        try:
            if not receipt.exists():
                _atomic(receipt, payload)
        except Exception:
            if path.read_bytes() == after:
                _atomic(path, before, mode)
            raise
        return {**record, 'receipt_sha256': _sha(payload)}


def rebind_source_binding(root, tid, pid, binding, repair=None):
    """Return a copy changing only the proven generator digest; never edit a receipt.

    An idempotent retry can recover the exact deterministic task-local proof.
    Every other supplied bound source must still have its original digest.
    """
    root, relative, rid = _identity(root, tid, pid)
    if type(binding) is not dict or binding.get('task_id') != tid or type(binding.get('files')) is not list:
        raise ValueError('Compatibility needs this task\'s reported source binding')
    result = copy.deepcopy(binding)
    files = result['files']; seen = set(); selected = None
    for row in files:
        if type(row) is not dict or type(row.get('path')) is not str or row['path'] in seen:
            raise ValueError('Compatibility refuses malformed or duplicate source bindings')
        seen.add(row['path'])
        if type(row.get('sha256')) is not str or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('Compatibility source hashes must be exact SHA-256 values')
        current = _safe(root, row['path'], file=True).read_bytes()
        if row['path'] == relative:
            selected = row
        elif _sha(current) != row['sha256']:
            raise ValueError('A non-generator bound source changed; explicit owner retry required')
    if selected is None:
        raise ValueError('Reported binding does not include the selected generator')
    after = _safe(root, relative, file=True).read_bytes()
    if _plan(after, tid, rid) is not None:
        raise ValueError('Apply the narrow reference metadata repair before rebinding')
    if selected['sha256'] == _sha(after):
        return result
    name = f"generators/{tid}/evidence/owner-reference-compatibility/{selected['sha256']}.json"
    path = _safe(root, name, file=True)
    raw = path.read_bytes(); proof = json.loads(raw)
    if type(proof) is not dict:
        raise ValueError('Malformed retained compatibility proof')
    if repair is not None and (repair.get('receipt_path') != name or repair.get('receipt_sha256') != _sha(raw)):
        raise ValueError('Supplied compatibility receipt differs from retained proof')
    if (proof.get('schema') != SCHEMA or proof.get('task_id') != tid or proof.get('public_task_id') != pid
            or proof.get('reference_id') != rid or proof.get('generator_path') != relative
            or proof.get('receipt_path') != name or proof.get('before_sha256') != selected['sha256']
            or proof.get('after_sha256') != _sha(after) or proof.get('approval_granted') is not False
            or proof.get('training_admitted') is not False):
        raise ValueError('Compatibility proof does not bind the current exact source')
    edit = proof.get('edit', {})
    if type(edit) is not dict:
        raise ValueError('Malformed compatibility edit proof')
    offset = edit.get('offset')
    if (type(offset) is not int or not 0 <= offset <= len(after)
            or type(edit.get('before')) is not str or type(edit.get('after')) is not str):
        raise ValueError('Malformed compatibility edit proof')
    old, new = edit['before'].encode(), edit['after'].encode()
    if not new or after[offset:offset + len(new)] != new:
        raise ValueError('Compatibility edit cannot be reversed against current source')
    before = after[:offset] + old + after[offset + len(new):]
    if _sha(before) != selected['sha256'] or _plan(before, tid, rid) != (edit, after):
        raise ValueError('Compatibility proof is not the exact allowed metadata-only delta')
    selected['sha256'] = _sha(after)
    return result
