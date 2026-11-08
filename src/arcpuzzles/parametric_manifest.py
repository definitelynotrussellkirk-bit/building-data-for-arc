"""Build a task-local author-reported inventory without executing its code."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .catalog import Catalog
from .parametric_promotion import CONTRACT, settings_space
from .review import _lock

SCHEMA = 'arcpuzzles-parametric-prototype-evidence-v1'
_CACHES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.git'}


def _safe(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('Symlink in manifest input/output: ' + str(part))
    return path


def _path(root, value, *, home=None):
    if not isinstance(value, (str, os.PathLike)):
        raise ValueError('Manifest paths must be strings or paths')
    raw = str(value)
    path = Path(value)
    if '\\' in raw or '\0' in raw or '..' in path.parts:
        raise ValueError('Unsafe manifest path: ' + raw)
    path = _safe(path if path.is_absolute() else root / path)
    if home is not None and not path.resolve().is_relative_to(home.resolve()):
        raise ValueError('Manifest inputs must stay inside their task home: ' + raw)
    return path


def _files(directory, *, skip_parts=(), exclude=()):
    _safe(directory)
    if not directory.is_dir():
        raise ValueError('Evidence/include directory is missing: ' + str(directory))
    found = []
    for path in sorted(directory.rglob('*')):
        if any(part in _CACHES | set(skip_parts) for part in path.relative_to(directory).parts):
            continue
        _safe(path)
        if path in exclude:
            continue
        if path.is_file():
            found.append(path)
        elif not path.is_dir():
            raise ValueError('Special files cannot form manifest evidence: ' + str(path))
    return found


def _sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _identifier_hold(home):
    path = _safe(home / 'workspace/parametric/evidence/manifest.json')
    if not path.exists():return {}
    if not path.is_file():raise ValueError('The current prototype manifest must be a regular file')
    raw = path.read_bytes();current = json.loads(raw)
    if isinstance(current, dict) and current.get('public_identifier_status') == 'external_correction_pending':
        return {'public_identifier_status': 'external_correction_pending'}
    return {}


def _contract(root, home):
    prototype = home / 'workspace/parametric'
    path = _path(root, prototype / 'promotion.json', home=home)
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict) or value.get('schema') != CONTRACT:
        raise ValueError('A finite promotion.json adapter contract is required')
    settings_space(value)
    if not isinstance(value.get('limits'), dict):
        raise ValueError('Contract count limits must name demos and queries')
    for name in ['demos', 'queries']:
        limits = value.get('limits', {}).get(name)
        if (not isinstance(limits, list) or len(limits) != 2
                or any(type(x) is not int for x in limits) or not 1 <= limits[0] <= limits[1] <= 32):
            raise ValueError('Contract count limits must be exact integers in1..32')
    name = value.get('adapter')
    prefix = prototype.relative_to(root).as_posix() + '/'
    if not isinstance(name, str) or not name.startswith(prefix) or not name.endswith('.py'):
        raise ValueError('Contract adapter must name a library-relative task-local Python source')
    adapter = _path(root, name, home=prototype)
    resources = value.get('resources', [])
    if (not isinstance(resources, list)
            or any(not isinstance(x, str) or not x.startswith(prefix) for x in resources)):
        raise ValueError('Contract resources must be library-relative task-local paths')
    selected = [path, adapter, *[_path(root, name, home=prototype) for name in resources]]
    if any(not p.is_file() for p in selected):
        raise ValueError('A declared adapter/resource source is missing')
    return value, selected


def _snapshot(root, tid, evidence, include, reported_checks, *, exclude=()):
    catalog = Catalog(root)
    row = catalog.describe(tid)
    tid = row['id'];home = root / 'generators' / tid
    if not row.get('generator') or not row.get('rule_hash'):
        raise ValueError('A current generator and unique canonical rule are required')
    authority = row.get('rule_task_id', tid)
    programs = [v.get('program_solution') for v in catalog._variants().get(authority, [])]
    if (not programs or any(type(p) is not str or not p.strip() for p in programs)
            or len(set(programs)) != 1):
        raise ValueError('A unique exact canonical authority is required')
    contract, selected = _contract(root, home)
    source = _path(root, row['generator'], home=home)
    selected.append(source)
    prototype = home / 'workspace/parametric'
    selected.extend(p for p in _files(prototype, skip_parts={'evidence', 'examples'})
                    if p.suffix in {'.py', '.rkt', '.json'})
    evidence = _path(root, evidence, home=home)
    proof = _files(evidence, exclude=exclude)
    if not proof or not any(p.stat().st_size for p in proof):
        raise ValueError('At least one nonempty task-local evidence file is required')
    for name in include:
        path = _path(root, name, home=home)
        if path.is_file():
            selected.append(path)
        elif path.is_dir():
            extra = _files(path, exclude=exclude)
            if not extra:raise ValueError('Included evidence directory is empty')
            selected.extend(extra)
        else:
            raise ValueError('Included task-local source/evidence is missing')
    sources = set(selected)
    files = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': _sha(p)}
             for p in sorted(sources | set(proof))]
    result = {'schema': SCHEMA, 'task_id': tid, 'generator_sha256': row['generator_sha256'],
        'canonical_rule_hash': row['rule_hash'], 'rule_task_id': authority,
        'canonical_program_sha256': hashlib.sha256(programs[0].encode()).hexdigest(),
        'parameters': contract['parameters'], 'default': contract['default'], 'limits': contract['limits'],
        'verification_status': 'reviewer_reported', 'reported_checks': reported_checks,
        'builder_executed_checks': False, 'variant_approved': False,
        'production_parametric_api': False, 'training_admitted': False,
        'evidence_root': evidence.relative_to(root).as_posix(), 'files': files,
        'scope': 'Author-reported task-local inventory. Current hashes are not execution, qualification, acceptance or training admission.',
        **_identifier_hold(home)}
    return result, sources


def _existing(output, wanted):
    _safe(output)
    if wanted is not None and (type(wanted) is not str or not re.fullmatch('[0-9a-f]{64}', wanted)):
        raise ValueError('Replacement requires the exact prior lowercase SHA256 hash')
    if output.exists():
        if not output.is_file():raise ValueError('Manifest output must be a regular file')
        observed = _sha(output)
        if wanted is None:
            raise FileExistsError(f'Manifest exists at {output}; compare the current report before using --replace {observed}')
        if observed != wanted:raise ValueError('Existing manifest hash changed; observed ' + observed)
        return wanted
    if wanted is not None:raise ValueError('Cannot replace a missing manifest output')
    return None


def build_manifest(catalog, task_id, *, evidence, reported_checks, include=None,
                   output=None, replace_sha256=None):
    """Write a fresh report; replacing one never copies its old passing claims."""
    if type(reported_checks) is not str or not reported_checks.strip() or len(reported_checks) > 4000:
        raise ValueError('Explicit author-reported checks text is required (1..4000characters)')
    if include is None:include = []
    if not isinstance(include, (list, tuple)):raise ValueError('Include must be a list of task-local paths')
    root = catalog.root;tid = catalog.describe(task_id)['id']
    home = root / 'generators' / tid
    destination = _path(Path.cwd(), output) if output is not None else home / 'workspace/parametric/evidence/manifest.json'
    if destination.is_relative_to(root) and not any(destination.is_relative_to(folder)
            for folder in (home, root/'var', root/'build')):
        raise ValueError('Library manifest outputs must stay in this task or ignored scratch')
    if destination.suffix != '.json':
        raise ValueError('Manifest output must be a JSON file')
    _safe(destination);_safe(root/'REVIEW')
    with _lock(root/'REVIEW'):
        value, sources = _snapshot(root, tid, evidence, include, reported_checks.strip(), exclude={destination})
        if destination in sources:raise ValueError('Manifest output overlaps a declared source')
        previous = _existing(destination, replace_sha256)
        raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.manifest-', suffix='.tmp', dir=destination.parent)
        pending = Path(name)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
            fresh, _ = _snapshot(root, tid, evidence, include, reported_checks.strip(), exclude={destination, pending})
            if fresh != value:raise ValueError('Source/evidence changed while building the manifest')
            _existing(destination, previous)
            if previous is None:
                os.link(pending, destination)
            else:
                os.replace(pending, destination)
        finally:
            pending.unlink(missing_ok=True)
    return {'manifest': str(destination), 'sha256': hashlib.sha256(raw).hexdigest(),
            'files': len(value['files']), 'verification_status': 'reviewer_reported',
            'builder_executed_checks': False, 'training_admitted': False,
            **({'replaced_sha256': previous} if previous is not None else {})}
