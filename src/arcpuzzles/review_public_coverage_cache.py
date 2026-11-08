"""Owner-local fast packet allocation cache; never admission or fresh execution.

Every hit rehashes a conservative complete task home and current shared sources.
Authenticated cache records preserve a prior full verification result, not a new
qualification. No cache, key, or historical owner evidence is shipped to reviewers.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets

from .catalog import Catalog
from .review_public_creation import SOURCE, SOLUTIONS, digest, generator_id
from .review_public_admission import REGISTRY, _regular, verified_coverage

SCHEMA = 'arcpuzzles-fast-public-coverage-cache-v1'
_SKIP = {'__pycache__'}


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root, folder):
    """Inventory names as well as bytes; reject symlinks and special files."""
    folder = _regular_directory(root, folder)
    result = {}
    for current, dirs, files in os.walk(folder, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP)
        for name in dirs + sorted(files):
            path = Path(current)/name
            if path.is_symlink():
                raise ValueError('Symlink in cache closure')
            if path.is_dir():
                continue
            relative = path.relative_to(root).as_posix()
            result[relative] = _sha(_regular(root, relative))
    return result


def _regular_directory(root, folder):
    path = root/folder
    if (not path.is_dir() or path.is_symlink() or not path.resolve().is_relative_to(root)
            or any(p.is_symlink() for p in path.parents if p.is_relative_to(root))):
        raise ValueError('Invalid cache source directory')
    return path


def _key(path):
    if path.is_symlink():
        raise ValueError('Symlink cache key')
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raw = path.read_bytes()
        if len(raw) != 32:
            raise ValueError('Invalid cache key')
        return raw
    else:
        raw = secrets.token_bytes(32)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
        return raw


def _signature(key, row):
    return hmac.new(key, _raw(row), hashlib.sha256).hexdigest()




def _shared(root):
    import inspect
    files = {}
    for folder in ('shared/runtime', 'src/arcpuzzles'):
        files.update(_tree(root, folder))
    for name in (SOURCE, SOLUTIONS, 'shared/tools/comment_solutions.py'):
        files[name] = _sha(_regular(root, name))
    # Also bind the executing installed package, which can differ from root/src.
    for path in sorted(Path(inspect.getfile(Catalog)).parent.glob('*.py')):
        if path.is_symlink() or not path.is_file():
            raise ValueError('Invalid executing helper source')
        files['executing:' + str(path.resolve())] = _sha(path)
    files['cache_helper'] = _sha(Path(__file__))
    return files


def _identity(root, pid, entry, catalog, variants, shared_identity):
    tid = generator_id(pid)
    record = catalog._records[tid]
    files = _tree(root, 'generators/'+tid)
    # Explicit inventories may cite a file in an otherwise ignored bytecode
    # folder; bind those too. These schemas are prerequisites of native status.
    for relative in (f'generators/{tid}/parametric/accepted.json',
                     f'generators/{tid}/workspace/parametric/evidence/manifest.json'):
        inventory_path = root/relative
        if inventory_path.exists():
            inventory = json.loads(_regular(root, relative).read_text())
            rows = inventory.get('files', []) + inventory.get('source_binding', {}).get('files', [])
            for row in rows:
                name = row['path']
                files[name] = _sha(_regular(root, name))
    if record.get('generator'):
        files[record['generator']] = _sha(_regular(root, record['generator']))
    # Owner originals can live outside the task home. Bind every file
    # read by _verified_originals, including the containing receipt.
    proof_path = _regular(root, entry['owner_evidence']['path'])
    proof = json.loads(proof_path.read_text())
    receipt_path = _regular(root, proof['owner_preflight'])
    for path in (proof_path, receipt_path, receipt_path.parent/'original-pairs.json',
         receipt_path.parent/'execution.json'):
        name = path.relative_to(root).as_posix()
        files[name] = _sha(_regular(root, name))
    return digest({'schema': SCHEMA, 'entry': entry, 'shared': shared_identity,
               'catalog_record': record,
               'authority_variants': variants.get(record.get('rule_task_id', tid), []),
               'files': files})


def fast_coverage(root):
    """Return current covered IDs and a truthful allocation-only cache receipt."""
    root = Path(root).resolve()
    cache_dir = root/'var/review/public-coverage-cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Do not follow a substituted cache/key directory.
    _regular_directory(root, 'var/review/public-coverage-cache')
    key = _key(cache_dir/'owner.key')
    cache_path = cache_dir/'current.json'
    try:
        if cache_path.is_symlink():
            raise ValueError('Symlink cache')
        cached = json.loads(cache_path.read_text())
        cached = cached['entries'] if cached.get('schema') == SCHEMA else {}
        if type(cached) is not dict:
            cached = {}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        cached = {}
    try:
        registry = json.loads(_regular(root, REGISTRY).read_text())
        if (registry.get('schema') != 'arcpuzzles-public-eval-coverage-v1'
                or type(registry.get('parents')) is not dict):
            raise ValueError('Invalid coverage registry')
        catalog = Catalog(root)
        variants = catalog._variants()  # Validate/parse once, never a frozen-engine mutation.
        shared = _shared(root)
        shared_identity = digest(shared)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return verified_coverage(root), {'mode': 'full_fallback', 'cache_hits': 0,
                                        'basis': 'unchanged_full_verification'}
    identities = {}; hits = []; misses = []
    for pid, entry in registry['parents'].items():
        try:
            item = entry['public_creation']; tid = generator_id(pid)
            if item['task_id'] != tid or entry.get('status') != 'accepted':
                continue
            identity = _identity(root, pid, entry, catalog, variants, shared_identity)
            identities[pid] = identity
            row = cached.get(pid, {})
            payload = {'public_task_id': pid, 'identity': identity, 'covered': True}
            if (type(row) is dict and row.get('payload') == payload
                    and type(row.get('signature')) is str
                    and hmac.compare_digest(row['signature'], _signature(key, payload))):
                hits.append(pid)
            else:
                misses.append(pid)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            misses.append(pid)
    verified = verified_coverage(root, _candidate_ids=set(misses)) if misses else []
    covered = sorted(set(hits) | set(verified))
    # A miss can spend minutes in native verification. Never authenticate an
    # identity sampled before that call if its sources changed in the meantime.
    if misses:
        fresh_catalog = Catalog(root)
        fresh_variants = fresh_catalog._variants()
        fresh_shared = _shared(root)
        fresh_registry = json.loads(_regular(root, REGISTRY).read_text())
        retained = []
        for pid in covered:
            try:
                fresh = _identity(root, pid, fresh_registry['parents'][pid],
                                  fresh_catalog, fresh_variants, digest(fresh_shared))
                if fresh == identities.get(pid):
                    retained.append(pid)
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                pass
        covered = retained
    entries = {}
    for pid in covered:
        if pid in identities:
            payload = {'public_task_id': pid, 'identity': identities[pid], 'covered': True}
            entries[pid] = {'payload': payload, 'signature': _signature(key, payload)}
    pending = cache_dir/'current.tmp'
    if pending.is_symlink():
        raise ValueError('Symlink pending cache')
    pending.write_bytes(_raw({'schema': SCHEMA, 'entries': entries}) + b'\n')
    pending.replace(cache_path)
    return covered, {'mode': 'exact_content_cache', 'cache_hits': len(hits),
                     'native_verification_candidates': len(misses),
                     'basis': 'prior_full_verification_rebound_to_current_content',
                     'fresh_execution': False, 'training_admitted': False}
