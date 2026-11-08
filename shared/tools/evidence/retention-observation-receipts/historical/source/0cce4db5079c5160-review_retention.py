"""Extract useful current state, then retire managed reviewer transports.

A processed ZIP is temporary transport. Current notes, active audits, source-bound
approvals, proposals and authored examples are the retained product. No historical
intake ledger is written. Preview is read-only; apply verifies before deleting.
"""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import io
import json
from functools import lru_cache
from pathlib import Path, PurePosixPath
import re
import shutil
import zipfile
import zlib

from .catalog import jsonl, local_path, sha256
from .review_full_packet import canonical_json
from .review_notes import (audit_state, compact_suggestions, compact_task_state,
                           index_path, read_index, suggestion_events, append_suggestions,
                           validate_proposal_assets)
from .review_solve import digest
from .review_feedback import feedback_items

_CORE = {'ASSIGNMENT.json', 'AUDIT.md', 'AUDIT_ASSIGNMENT.json',
         'BLIND_ASSIGNMENT.json', 'DECISIONS.md', 'FEEDBACK_TO_CODEX.md',
         'INTAKE.json', 'QUESTION_ANSWER.md', 'RESULTS.json', 'REVIEW.md',
         'EVIDENCE-BUNDLE.json', 'EVIDENCE-BUNDLE.tar.gz'}
_PROCESSED = {'accepted', 'implemented', 'deferred', 'needs_evidence', 'rejected'}


@lru_cache(maxsize=4)
def _packet_rule_table(path: Path) -> dict[str, bytes]:
    from .review_full_packet import packet_member
    rows: dict[str, list[bytes]] = {}
    with zipfile.ZipFile(path) as packet:
        for line in packet_member(packet, 'repo/shared/data/canonical/puzzles.jsonl').splitlines():
            task = json.loads(line)['task_id']
            rows.setdefault(task, []).append(line + b'\n')
    return {task: b''.join(lines) for task, lines in rows.items()}


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(canonical_json(value) + b'\n')
    temporary.replace(path)


def _copy(owner: Path, relative: str, raw: bytes) -> dict:
    target = local_path(owner, relative)
    if target.exists() and target.read_bytes() != raw:
        raise ValueError(f'Conflicting extracted evidence: {relative}')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    if sha256(target) != digest(raw):
        raise ValueError(f'Extracted evidence hash differs: {relative}')
    return {'path': relative, 'sha256': digest(raw), 'bytes': len(raw)}


def _curate_report(raw: bytes, name: str) -> tuple[bytes, dict]:
    """Known census schemas: keep counts, failures and minimal successful witnesses.

    Unknown formats stay byte-exact. A derived selection is labelled with its
    original hash; it never claims a fresh run or the retained full sample corpus.
    """
    if not name.endswith('.json'):
        return raw, {}
    try:
        value = json.loads(raw)
    except ValueError:
        return raw, {}
    if not isinstance(value, dict):
        return raw, {}
    selected = dict(value)
    selection = {}
    runtime = value.get('runtime_manifest')
    if (value.get('schema') == 'arcpuzzles-check-v1' and isinstance(runtime, dict)
            and isinstance(runtime.get('files'), (dict, list)) and isinstance(value.get('task_id'), str)):
        task = value['task_id']
        files = runtime['files']
        if isinstance(files, dict):
            kept = {path: binding for path, binding in files.items() if task in path}
        elif all(isinstance(item, dict) and any(isinstance(item.get(key), str)
                    for key in ('library_path', 'runtime_path', 'path')) for item in files):
            kept = [item for item in files if any(task in item.get(key, '')
                    for key in ('library_path', 'runtime_path', 'path') if isinstance(item.get(key), str))]
        else:
            return raw, {}
        if kept == files:
            return raw, {}
        selected['runtime_manifest'] = {**runtime, 'files': kept}
        selection = {'policy': 'retain check results and task bindings; omit unrelated copied runtime inventory',
                     'original_runtime_files': len(files), 'retained_runtime_files': len(kept),
                     'runtime_inventory_sha256': digest(canonical_json(files))}
    elif value.get('schema') == 'arcpuzzles-lesson-census-v1':
        if len(raw) < 128_000:
            return raw, {}
        lessons = value.get('lessons', [])
        seen_bands, kept = set(), []
        for lesson in lessons:
            failure = lesson.get('ambiguous') or lesson.get('errors') or lesson.get('warnings') or any(
                rotation.get('ambiguous') or rotation.get('errors') for rotation in lesson.get('rotations', []))
            band = lesson.get('band')
            if failure or band not in seen_bands:
                kept.append(lesson)
                if not failure:
                    seen_bands.add(band)
        selected['lessons'] = kept
        selection = {'policy':'aggregate counts, all failing lessons, one complete successful lesson per band',
                     'original_lessons':len(lessons),'retained_lessons':len(kept)}
    elif value.get('schema_version') == 3 and 'axis_domains' in value and 'cases' in value:
        if len(raw) < 128_000:
            return raw, {}
        cases = value['cases']
        kept = [case for case in cases if case.get('errors') or case.get('finding_count')]
        selected['cases'] = kept
        selection = {'policy':'aggregate counts, representative findings and all failing override cases',
                     'original_cases':len(cases),'retained_cases':len(kept)}
    else:
        return raw, {}
    if value.get('schema') != 'arcpuzzles-check-v1':
        selected.pop('runtime_manifest', None)
    metadata = {'source_member_sha256':digest(raw),'selection':selection}
    selected['retention_selection'] = metadata
    return canonical_json(selected) + b'\n', metadata


def _mentioned(name: str, text: str) -> bool:
    """Match a path, not its prefix inside a different filename or directory."""
    return re.search(r'(?<![\w/.-])' + re.escape(name) + r'(?![\w/-]|\.[A-Za-z0-9_])', text) is not None


def _cited_members(names: set[str], text: str, *, relative_names: set[str] | None = None) -> set[str]:
    cited = {name for name in names if _mentioned(name, text)}
    explicit = set(cited)
    for reference in re.findall(r'`([^`\n]+)`', text):
        if reference in names or reference.endswith('/') or any(c.isspace() for c in reference):
            continue
        if not PurePosixPath(reference).suffix:
            continue
        # A maintainer can clarify an immutable reviewer basename using an
        # exact path in the current disposition. Never infer that choice.
        clarified = {name for name in explicit if name.endswith('/' + reference)}
        if clarified:
            continue
        matches = {name for name in (names if relative_names is None else relative_names)
                   if name.endswith('/' + reference)}
        if relative_names is not None and not matches and any(name.endswith('/' + reference) for name in names):
            raise ValueError(f'Review evidence citation {reference!r} resolves only outside this task scope; '
                             'use a full checks/ path to identify the intended evidence.')
        if len(matches) > 1:
            raise ValueError(f'Ambiguous review evidence citation {reference!r}; use a full checks/ path: '
                             + ', '.join(sorted(matches)))
        cited |= matches
    return cited


def _runtime_copy(name: str) -> bool:
    parts = PurePosixPath(name).parts
    return (parts[-1] == 'RUNTIME_MANIFEST.json' or any(
        part in {'__pycache__', 'site-packages', 'src', 'repo', 'lib', 'puzzle_generators', 'arc_repl'}
        or part.startswith(('.venv', 'runtime')) for part in parts[:-1]))


def _compressed_dependencies(selected: set[str], names: set[str], read) -> tuple[set[str], list[dict]]:
    """Follow the supplied, explicit gzip evidence-index contracts.

    Return the expanded selection without executing a reviewer restore helper.
    Bundle members can be fetched after discovery, before payload verification.
    """
    from .review_evidence_bundle import _safe_path
    expanded, entries = set(selected), []
    for name in sorted(selected):
        if not name.endswith('.json'):
            continue
        try:
            manifest = json.loads(read(name))
        except (ValueError, UnicodeError):
            continue
        if not isinstance(manifest, dict):
            continue
        schema = manifest.get('schema')
        if schema not in {'arc-review-evidence-archive-v1', 'review-large-evidence-v1',
                          'arcpuzzles-evidence-gzip-v1'}:
            continue
        def invalid(reason):
            return ValueError(f'Compressed evidence index {name}: {reason}')
        # Some observer receipts reuse the gzip-index schema. Their reported
        # success is not evidence: require a real index and verify its closure.
        if (schema == 'arcpuzzles-evidence-gzip-v1' and 'files' not in manifest
                and 'expanded_members' in manifest):
            members = manifest['expanded_members']
            count = manifest.get('native_reader_verified_archives')
            if (not isinstance(members, list) or not members
                    or any(not isinstance(m, str) or not m.startswith('checks/')
                           or not _safe_path(m) or _runtime_copy(m) or m not in names
                           for m in members)
                    or len(set(members)) != len(members)
                    or type(count) is not int or count < 1):
                raise invalid('invalid observation receipt dependency inventory')
            indexes = [m for m in members if m.endswith('.json')]
            if len(indexes) != 1 or indexes[0] == name:
                raise invalid('observation receipt requires one real index')
            try:
                index = json.loads(read(indexes[0]))
            except (ValueError, UnicodeError):
                raise invalid('observation receipt references an invalid index')
            if (not isinstance(index, dict)
                    or index.get('schema') != 'arcpuzzles-evidence-gzip-v1'
                    or not isinstance(index.get('files'), list) or not index['files']):
                raise invalid('observation receipt cannot substitute for an index')
            closure, dependencies = _compressed_dependencies({indexes[0]}, names, read)
            if closure != set(members) or len(dependencies) != count:
                raise invalid('observation receipt differs from actual index closure')
            expanded |= closure
            entries.extend(dependencies)
            continue
        rows = manifest.get('entries' if schema == 'arc-review-evidence-archive-v1' else 'files')
        if not isinstance(rows, list):
            raise invalid('entries must be a list')
        native_gzip = schema == 'arcpuzzles-evidence-gzip-v1'
        if native_gzip and not rows:
            raise invalid('files must not be empty')
        seen = set()
        originals = set()
        for row in rows:
            if not isinstance(row, dict):
                raise invalid('entry must be an object')
            if native_gzip:
                # This tool's paths are relative to its MANIFEST.json, not the
                # transport root. Validate them before joining; never resolve
                # a same-named payload in another bundle or outside checks/.
                for key in ('path', 'compressed_path'):
                    path = row.get(key)
                    if not isinstance(path, str) or not _safe_path('checks/' + path):
                        raise invalid(f'invalid relative {key}: {path!r}')
                if row['compressed_path'] != row['path'] + '.gz':
                    raise invalid('compressed_path must be path plus .gz')
                base = PurePosixPath(name).parent
                row = {'original_path': (base / row['path']).as_posix(),
                       'compressed_path': (base / row['compressed_path']).as_posix(),
                       'original_bytes': row.get('raw_size'), 'original_sha256': row.get('raw_sha256'),
                       'compressed_bytes': row.get('compressed_size'),
                       'compressed_sha256': row.get('compressed_sha256')}
            for key in ('original_path', 'compressed_path'):
                path = row.get(key)
                if not isinstance(path, str) or not _safe_path(path) or _runtime_copy(path):
                    raise invalid(f'invalid {key}: {path!r}')
            compressed = row['compressed_path']
            if (not compressed.endswith('.gz') or compressed == row['original_path']
                    or compressed in seen):
                raise invalid(f'duplicate or invalid gzip path: {compressed}')
            seen.add(compressed)
            originals.add(row['original_path'])
            if compressed not in names:
                raise invalid(f'missing dependency: {compressed}')
            for prefix in ('original', 'compressed'):
                size, sha = row.get(prefix + '_bytes'), row.get(prefix + '_sha256')
                if type(size) is not int or size < 0:
                    raise invalid(f'invalid {prefix} byte count')
                if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha):
                    raise invalid(f'invalid {prefix} SHA-256')
            fields = ('original_path', 'compressed_path', 'original_bytes', 'compressed_bytes',
                      'original_sha256', 'compressed_sha256')
            entries.append({key: row[key] for key in fields})
            expanded.add(compressed)
        if native_gzip:
            # Match the supplied tool's file/directory collision contract for
            # restored files and bundle files, including the index itself.
            for paths in (originals, seen | {name}):
                for path in paths:
                    if any(parent.as_posix() in paths for parent in PurePosixPath(path).parents):
                        raise invalid(f'file/directory path collision: {path}')
        if schema == 'review-large-evidence-v1':
            if manifest.get('compression') != 'gzip':
                raise invalid('compression must be gzip')
            totals = {'count': len(rows), 'original_bytes': sum(r['original_bytes'] for r in rows),
                      'compressed_bytes': sum(r['compressed_bytes'] for r in rows)}
            for key, total in totals.items():
                if type(manifest.get(key)) is not int or manifest[key] != total:
                    raise invalid(f'{key} does not match entries')
    return expanded, entries


def _verify_compressed_dependencies(entries: list[dict], read) -> None:
    """Verify compressed bytes and streamed originals before disposing transport."""
    verified = {}
    for row in entries:
        name = row['compressed_path']
        if name in verified:
            if verified[name] != row:
                raise ValueError(f'Compressed evidence has conflicting declarations: {name}')
            continue
        raw = read(name)
        if len(raw) != row['compressed_bytes'] or digest(raw) != row['compressed_sha256']:
            raise ValueError(f'Compressed evidence bytes differ: {name}')
        sha, size = hashlib.sha256(), 0
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                while chunk := stream.read(1024 * 1024):
                    size += len(chunk)
                    if size > row['original_bytes']:
                        raise ValueError(f'Compressed evidence original size differs: {name}')
                    sha.update(chunk)
        except (OSError, EOFError, zlib.error) as exc:
            raise ValueError(f'Compressed evidence cannot be decompressed: {name}') from exc
        if size != row['original_bytes'] or sha.hexdigest() != row['original_sha256']:
            raise ValueError(f'Compressed evidence original bytes differ: {name}')
        verified[name] = row


def _feedback_members(names: set[str], text: str) -> set[str]:
    """Keep cited evidence and authored prototype folders, without runtime copies."""
    names = {name for name in names if name.startswith('checks/') and not _runtime_copy(name)}
    cited = _cited_members(names, text)
    prototypes = set()
    folders = set()
    for name in names:
        parts = PurePosixPath(name).parts
        if len(parts) < 3:
            continue
        if parts[1] == 'tooling' and len(parts) == 3:
            # A basename citation names one flat prototype, not every other
            # tool in checks/tooling/. Nested proposal-folder behavior is kept.
            continue
        prototypes.add(name)
        minimum = 3 if parts[1] == 'tooling' else 2
        parent = PurePosixPath(name).parent.as_posix() + '/'
        if name in cited and (parts[1] in {'proposals', 'optional-tools', 'tooling'}
                              or PurePosixPath(name).suffix in {'.py', '.patch', '.rkt', '.sh'}):
            folders.add(parent)
        for length in range(minimum, len(parts)):
            folder = '/'.join(parts[:length]) + '/'
            if _mentioned(folder, text):
                folders.add(folder)
    return cited | {name for name in prototypes if any(name.startswith(folder) for folder in folders)}


def _audit_members(names: set[str], task: str, text: str) -> set[str]:
    """Keep cited witnesses and audit probes; never keep copied runtime trees."""
    names = {name for name in names if name.startswith('checks/') and not _runtime_copy(name)}
    safe = {name for name in names if 'data' not in PurePosixPath(name).parts and not any(
        len(part) == 12 and all(c in '0123456789abcdef' for c in part) and part != task
        for part in PurePosixPath(name).parts)}
    target_names = {name for name in safe if task in name}
    relative_names = target_names or safe
    source_path = f'repo/generators/{task}/generator.py'
    if (_mentioned(source_path, text)
            and not any(name.endswith('/generator.py') for name in relative_names)):
        # Clarify source-code prose without selecting another task's snapshot.
        # Task-local evidence with this basename still needs an explicit path.
        text = text.replace('`generator.py`', f'`{source_path}`')
    selected = _cited_members(names, text, relative_names=relative_names)
    for name in names:
        if not name.startswith('checks/'):
            continue
        parts = PurePosixPath(name).parts
        # An explicit citation is evidence, even when the author placed it in
        # data/ or used a compressed/nonstandard filename.
        if name in selected:
            continue
        if name not in safe:
            continue
        if parts[-1] == 'RUNTIME_MANIFEST.json':
            continue
        # Files naming a different assigned target are not this task's witness.
        target_specific = task in name
        other_target = any(
                len(p) == 12 and all(c in '0123456789abcdef' for c in p) and p != task for p in parts)
        useful = any(word in parts[-1].lower() for word in
                     ('witness', 'counterexample', 'probe', 'rival', 'repro', 'input', 'output', 'receipt',
                      'summary', 'result', 'parity', 'finding', 'racket', 'verif', 'feasibility', 'sampling', 'screening', 'episode'))
        shared_audit_file = len(parts) == 3 and parts[1] in {'audit', 'audits'}
        if (target_specific or shared_audit_file) and not other_target and useful:
            # Repeated green stage logs and copied runner inventories add no
            # counterexample. Keep a cited failure log when it is the evidence.
            if name.endswith(('.json', '.py', '.rkt')):
                selected.add(name)
    return selected


def _approval_snapshots(owner: Path, catalog: dict, *, apply: bool) -> dict:
    selected = {r.get('approval_receipt') for r in catalog.values() if r.get('approval_receipt')}
    counts = Counter()
    for path in sorted((owner / 'REVIEW/approvals').glob('*.json')):
        name = path.relative_to(owner).as_posix()
        if name not in selected:
            counts['obsolete_removed'] += 1
            if apply:
                path.unlink()
            continue
        old = json.loads(path.read_text())
        fields = ('schema', 'assignment_id', 'version', 'return_id', 'task_id', 'policy',
                  'generator_sha256', 'rule_hash', 'return_sha256', 'verification_status',
                  'reported_completion', 'reported_remaining_failures', 'reviewed_at', 'scope',
                  'trajectory_training_admitted')
        current = {k: old[k] for k in fields if k in old}
        # Approval is a selected identity, not an old narrative/integration ledger.
        current['trajectory_training_admitted'] = False
        check_path = owner / 'var/review/full-checks' / str(old.get('assignment_id')) / f"{old.get('version', 0):04d}/result.json"
        if old.get('verification_status') != 'reviewer_reported' and check_path.is_file():
            checked = json.loads(check_path.read_text())
            bound = checked.get('candidate_file_sha256', {}).get(f"repo/generators/{old['task_id']}/generator.py")
            if bound == old['generator_sha256']:
                current['check_evidence'] = {'source_receipt_sha256':sha256(check_path),
                    'status':checked['status'],'generator_sha256':bound,
                    'checks':[{**{k:c[k] for k in ('kind','command','exit_code','timed_out') if k in c},
                               'stdout_sha256':digest(c.get('stdout','').encode()),
                               'stderr_sha256':digest(c.get('stderr','').encode())} for c in checked.get('checks',[])]}
        elif old.get('check_evidence'):
            current['check_evidence'] = old['check_evidence']
        if apply:
            _write(path, current)
        counts['current'] += 1
    return dict(counts)


def compact_reviews(owner: Path, *, apply: bool = False) -> dict:
    from .review import _lock
    with _lock(owner.resolve() / 'REVIEW'):
        return _compact_reviews(owner, apply=apply)


def _compact_reviews(owner: Path, *, apply: bool = False) -> dict:
    """Retire fully triaged managed returns only after archive-independent checks.

    Unclassified archive members, untriaged returns, changed hashes and missing
    witnesses fail closed. Downloads and outstanding source packet caches are
    outside this command's deletion scope.
    """
    from .review_full_inbox import _receipts, _incoming_task_index, _merge_current
    from .review_evidence_bundle import read_manifest, verify, check_budget
    from .review_return import scan_zip
    from .review_solve_tracker import build_solve_tracker, retain_solve_examples

    owner = owner.resolve()
    review = owner / 'REVIEW'
    catalog = {row['id']: row for row in jsonl(owner / 'catalog/puzzles.jsonl')}
    receipts = _receipts(review)
    pending = [r for r in receipts if r.get('disposition_status') not in _PROCESSED]
    if pending:
        raise ValueError('Triage returns before compaction: ' + ', '.join(r['assignment_id'] for r in pending[:10]))
    paths = sorted((review / 'assignments').glob('*/returns/return-*.json'))
    raw_receipts = [(p, json.loads(p.read_text())) for p in paths]
    by_identity = {(r['assignment_id'], r['version']): r for r in receipts}
    records = {p.parent.parent.name: read_index(owner, p.parent.parent.name)
               for p in (owner / 'generators').glob('*/evidence/review_index.json')}
    for path in (review / 'task_indexes').glob('*.json'):
        records.setdefault(path.stem, read_index(owner, path.stem))
    # A validated single-return intake need not have rendered an inbox. Read
    # incoming audits before selecting evidence, rather than relying on that
    # unrelated command to have populated generator indexes. Preview stays
    # read-only, and the shared merge preserves explicit audit dispositions.
    for _, raw in raw_receipts:
        archive = local_path(owner, Path(raw['archive_path']).relative_to(owner).as_posix())
        if not archive.is_relative_to(owner / 'var/review/returns'):
            raise ValueError('Return is outside the managed transport directory')
        if sha256(archive) != raw['zip_sha256']:
            raise ValueError(f'Return bytes changed: {archive}')
    incoming_ids = set()
    for receipt in receipts:
        if receipt['validation_status'] == 'accepted':
            incoming_ids.add(receipt['task_id'])
            incoming_ids.update(receipt.get('audit_targets') or
                                ([receipt['audit_target']] if receipt.get('audit_target') else []))
    for tid in sorted(incoming_ids):
        base = records.setdefault(tid, read_index(owner, tid))
        incoming = _incoming_task_index(review, tid, receipts=receipts)
        merged = _merge_current(review, tid, incoming, catalog_records=catalog)
        # Preserve legacy decision prose until its requests are extracted below.
        records[tid] = {**base, 'audits': merged['audits']}
    current = {tid: compact_task_state(owner, tid, record, catalog_records=catalog)
               for tid, record in records.items()}
    selected_reviews = {}
    for row in catalog.values():
        name = row.get('approval_receipt')
        if name and local_path(owner, name).is_file():
            approval = json.loads(local_path(owner, name).read_text())
            if (approval.get('generator_sha256') == row.get('reviewed_generator_sha256')
                    and approval.get('generator_sha256') == sha256(local_path(owner, row['generator']))):
                selected_reviews[(approval.get('assignment_id'), approval.get('version'))] = row
    active = {(a['return_id'], tid): a for tid, r in current.items() for a in r['audits']}
    plans, selected_files, members, bytes_removed = [], [], 0, 0
    proposal_count = 0
    question_requests, notes_plans = [], {}
    for receipt_path, raw in raw_receipts:
        receipt = by_identity.get((raw['assignment_id'], raw['version']))
        if receipt is None:
            # Earlier statically rejected wrappers must match a subsequently
            # validated return. A genuinely unexamined rejection is not disposable.
            duplicates = [r for r in receipts if r['assignment_id'] == raw['assignment_id']]
            if raw.get('status') != 'rejected' or not duplicates:
                raise ValueError(f'Unclassified return: {receipt_path}')
            receipt = duplicates[-1]
        archive_path = local_path(owner, Path(raw['archive_path']).relative_to(owner).as_posix())
        if not archive_path.is_relative_to(owner / 'var/review/returns'):
            raise ValueError('Return is outside the managed transport directory')
        if sha256(archive_path) != raw['zip_sha256']:
            raise ValueError(f'Return bytes changed: {archive_path}')
        with zipfile.ZipFile(archive_path) as archive:
            infos = scan_zip(archive)
            names = {i.filename for i in infos if not i.is_dir()}
            if raw.get('schema') == 'arcpuzzles-review-return-v1':
                with zipfile.ZipFile(receipt['archive_path']) as replacement:
                    for name in ('AUDIT.md', 'FEEDBACK_TO_CODEX.md', 'QUESTION_ANSWER.md'):
                        if (name in names) != (name in replacement.namelist()) or name in names and archive.read(name) != replacement.read(name):
                            raise ValueError(f'Rejected wrapper has unique unclassified evidence: {archive_path}')
                    solve_names = {n for n in names if n.startswith(('solve/', 'solve-blind/'))}
                    replacement_names = {n for n in replacement.namelist() if n.startswith(('solve/', 'solve-blind/'))}
                    if solve_names != replacement_names or any(archive.read(n) != replacement.read(n) for n in solve_names):
                        raise ValueError(f'Rejected wrapper has unique unclassified solve data: {archive_path}')
            unknown = {n for n in names if n not in _CORE and not n.startswith(('checks/', 'patches/', 'solve/', 'solve-blind/'))}
            if unknown:
                raise ValueError(f'Unclassified transport members: {sorted(unknown)}')
            bundle = read_manifest(archive.read('EVIDENCE-BUNDLE.json')) if 'EVIDENCE-BUNDLE.json' in names else None
            bundled_names = {r['path'] for r in bundle['files']} if bundle else set()
            all_names = names | bundled_names
            key = f"{receipt['assignment_id']}:v{receipt['version']:04d}"
            targets = [(tid, a) for (rid, tid), a in active.items() if rid == key]
            selected_by_task = {tid: _audit_members(all_names, tid,
                (a.get('text') or '') + '\n' + (a.get('resolution_reason') or '')) for tid, a in targets}
            wanted = set().union(*selected_by_task.values()) if selected_by_task else set()
            feedback_assets = []
            feedback = archive.read('FEEDBACK_TO_CODEX.md').decode('utf-8')
            # The inbox may already have compacted away this decision's prose.
            # Recover every request from the checked transport before retiring
            # it; an asset-only event cannot preserve the request's meaning.
            contract = json.loads(archive.read('ASSIGNMENT.json'))
            question_requests.extend(suggestion_events({
                'task_id': receipt['task_id'],
                'decisions': [{'return_id': key,
                    'source_sha256': contract['generator']['generator_sha256'],
                    'feedback': feedback,
                    'feedback_dispositions': receipt.get('feedback_dispositions', {})}]}))
            for item in feedback_items(feedback):
                decisions = receipt.get('feedback_dispositions', {}).get(item['id'], [])
                reason = decisions[-1].get('reason', '') if decisions else ''
                cited = _feedback_members(all_names, item['text'] + '\n' + reason)
                if cited:
                    feedback_assets.append((item, sorted(cited)))
                    wanted |= cited
            question_members = set()
            if (receipt['assignment_id'], receipt['version']) in selected_reviews:
                question_members = {n for n in all_names if n.startswith('checks/')
                           and n in archive.read('QUESTION_ANSWER.md').decode('utf-8')
                           and not _runtime_copy(n)}
                wanted |= question_members
            bundled = {}
            if bundle:
                check_budget(bundle, [(i.filename, i.file_size) for i in infos if i.filename != 'EVIDENCE-BUNDLE.tar.gz'])
                bundled = verify(archive.read('EVIDENCE-BUNDLE.tar.gz'), bundle, retain=wanted & bundled_names) or {}
            def read(name):
                return bundled[name] if name in bundled_names else archive.read(name)
            dependencies = []
            def expand(selected):
                expanded, entries = _compressed_dependencies(set(selected), all_names, read)
                dependencies.extend(entries)
                return expanded
            selected_by_task = {tid: expand(selected) for tid, selected in selected_by_task.items()}
            feedback_assets = [(item, sorted(expand(cited))) for item, cited in feedback_assets]
            question_members = expand(question_members)
            expanded_wanted = set().union(question_members, *selected_by_task.values(),
                                          *(set(cited) for _, cited in feedback_assets))
            extra = (expanded_wanted - wanted) & bundled_names
            if extra:
                bundled.update(verify(archive.read('EVIDENCE-BUNDLE.tar.gz'), bundle, retain=extra) or {})
            _verify_compressed_dependencies(dependencies, read)
            for item, cited in feedback_assets:
                request_id = key + ':' + item['id']
                base = 'shared/tools/proposals/' + digest(request_id.encode())[:16]
                assets = []
                for name in cited:
                    data, metadata = _curate_report(read(name), name)
                    relative = base + '/' + name
                    selected_files.append((relative, data))
                    assets.append({'path':relative, 'source_member':name,
                                   'sha256':digest(data), 'bytes':len(data), **metadata})
                manifest = {'schema':'arcpuzzles-tool-proposal-assets-v1',
                    'request_id':request_id, 'generator_id':receipt['task_id'],
                    'return_sha256':raw['zip_sha256'], 'files':assets,
                    'runtime_approved':False, 'scope':'Source-bound reviewer proposal/evidence; not selected tooling.'}
                relative = base + '/manifest.json'
                manifest_bytes = canonical_json(manifest) + b'\n'
                plans.append((local_path(owner, relative), manifest_bytes))
                question_requests.append({'event':'suggestion', 'request_id':request_id,
                    'assets_manifest':{'path':relative, 'sha256':digest(manifest_bytes)}})
            for tid, audit in targets:
                relative = f"generators/{tid}/counterexamples/{key.replace(':v', '-v')}/audit_assets.json"
                target = local_path(owner, relative)
                old = json.loads(target.read_text()) if target.is_file() else None
                if old and (old['task_id'] != tid or old['return_id'] != key
                            or old['audited_generator_sha256'] != audit['source_sha256']):
                    raise ValueError(f'Audit asset binding differs: {relative}')
                files = list(old.get('files', [])) if old else []
                for item in files:
                    existing = local_path(owner, item['path'])
                    if not existing.is_file() or sha256(existing) != item['sha256']:
                        raise ValueError(f'Missing or changed retained witness: {existing}')
                originals = {i.get('original_member') for i in files}
                for name in sorted(selected_by_task[tid] - originals):
                    destination = f"generators/{tid}/counterexamples/{key.replace(':v', '-v')}/retained/{name}"
                    data, metadata = _curate_report(read(name), name)
                    selected_files.append((destination, data))
                    files.append({'path': destination, 'sha256': digest(data), 'bytes': len(data), 'original_member': name, **metadata})
                if audit['source_sha256'] != sha256(owner / f'generators/{tid}/generator.py'):
                    from .review_full_candidate import _packet
                    from .review_full_packet import packet_member
                    with zipfile.ZipFile(_packet(review, receipt['packet_id'])) as packet:
                        source = packet_member(packet, f'repo/generators/{tid}/generator.py')
                        if digest(source) != audit['source_sha256']:
                            raise ValueError(f'Audited source differs from packet: {tid}')
                        destination = f"generators/{tid}/counterexamples/{key.replace(':v', '-v')}/audited_source.py"
                        if not any(i['path'] == destination for i in files):
                            selected_files.append((destination, source))
                            files.append({'path':destination,'sha256':digest(source),'bytes':len(source),
                                          'original_member':f'packet:repo/generators/{tid}/generator.py'})
                        # Only this task's bound rule rows, not the entire old
                        # library/runtime, are needed to understand the witness.
                        rule_task = catalog[tid].get('rule_task_id') or tid
                        raw_rules = _packet_rule_table(_packet(review, receipt['packet_id'])).get(rule_task, b'')
                        if raw_rules:
                            destination = f"generators/{tid}/counterexamples/{key.replace(':v', '-v')}/audited_rule.jsonl"
                            if not any(i['path'] == destination for i in files):
                                selected_files.append((destination, raw_rules))
                                files.append({'path':destination,'sha256':digest(raw_rules),'bytes':len(raw_rules),
                                              'original_member':'packet:task-bound-rule-rows'})
                for item in files:
                    existing = local_path(owner, item['path'])
                    if existing.exists() and sha256(existing) != item['sha256']:
                        raise ValueError(f'Existing witness changed: {existing}')
                if files:
                    assets = old or {'schema': 'arcpuzzles-audit-assets-v1', 'task_id': tid, 'return_id': key,
                        'zip_sha256': receipt['zip_sha256'], 'audited_generator_sha256': audit['source_sha256'],
                        'verification_status': 'reviewer_reported'}
                    assets['files'] = files
                    raw_assets = canonical_json(assets) + b'\n'
                    # Existing derived probes and curated receipts remain unchanged.
                    plans.append((target, raw_assets))
                    audit['assets_manifest'] = relative
                    audit['assets_manifest_sha256'] = digest(raw_assets)
            task = receipt['task_id']
            if (raw.get('schema') == 'arcpuzzles-full-return-receipt-v2'
                    and (receipt['assignment_id'], receipt['version']) in selected_reviews):
                row = selected_reviews[(receipt['assignment_id'], receipt['version'])]
                decisions = archive.read('DECISIONS.md').decode('utf-8')
                decisions = '\n'.join(line.rstrip() for line in decisions.splitlines()).rstrip() + '\n'
                note = owner / f'generators/{task}/notes.md'
                text = note.read_text() if note.is_file() else f'# Working notes: {task}\n'
                marker = '\n## Current reviewer considerations\n'
                text = text.split(marker)[0].rstrip() + marker + '\nSource SHA-256: `' + row['reviewed_generator_sha256'] + '`.\n\n' + decisions
                notes_plans[note] = text.encode('utf-8')
                question = json.loads(archive.read('ASSIGNMENT.json')).get('question', {}).get('id')
                answer = archive.read('QUESTION_ANSWER.md').decode('utf-8')
                if question == 'generator-shortcuts':
                    relative = f'generators/{task}/counterexamples/current-shortcut.json'
                    witness = {'schema':'arcpuzzles-current-shortcut-v1','task_id':task,
                        'generator_sha256':row['reviewed_generator_sha256'],'text':answer,
                        'verification_status':'reviewer_reported'}
                    plans.append((local_path(owner, relative), canonical_json(witness) + b'\n'))
                    for name in sorted(question_members):
                        raw_member, metadata = _curate_report(read(name), name)
                        destination = f'generators/{task}/counterexamples/current-shortcut/{name}'
                        selected_files.append((destination, raw_member))
                        witness.setdefault('files', []).append({'path':destination,'sha256':digest(raw_member),'bytes':len(raw_member),**metadata})
                    plans[-1] = (local_path(owner, relative), canonical_json(witness) + b'\n')
                elif answer.strip():
                    question_requests.append({'event':'suggestion', 'request_id':f'question:{task}:{digest(answer.encode())[:16]}',
                        'generator_id':task,'source_sha256':row['reviewed_generator_sha256'], 'text':answer})
            superseded = any(r['assignment_id'] == receipt['assignment_id'] and r['version'] > receipt['version'] for r in receipts)
            distinct_rejected_patch = False
            if raw.get('schema') == 'arcpuzzles-review-return-v1' and 'patches/source.patch' in names:
                with zipfile.ZipFile(receipt['archive_path']) as replacement:
                    distinct_rejected_patch = archive.read('patches/source.patch') != replacement.read('patches/source.patch')
            proposal = receipt['disposition_status'] in {'deferred', 'needs_evidence'} and not superseded or distinct_rejected_patch
            if proposal:
                patch = archive.read('patches/source.patch') if 'patches/source.patch' in names else b''
                stem = digest(patch)
                base = f'generators/{task}/workspace/proposals/{stem}'
                selected_files.append((base + '.patch', patch))
                reason = next((r['reason'] for r in reversed(receipt.get('dispositions', []))
                               if r.get('kind') in {'generator', 'decision'}), receipt['disposition_status'])
                if distinct_rejected_patch:
                    reason = 'Unvalidated alternative patch from rejected wrapper: ' + raw.get('reason', 'identity mismatch')
                description = {'schema': 'arcpuzzles-generator-proposal-v1', 'task_id': task,
                    'status': 'needs_evidence' if distinct_rejected_patch else receipt['disposition_status'], 'reason': reason,
                    'baseline_generator_sha256': json.loads(archive.read('ASSIGNMENT.json'))['generator']['generator_sha256'],
                    'patch': {'path': base + '.patch', 'sha256': stem}, 'training_admitted': False}
                # A proposal report explains how to port its tests/rivals; it is
                # retained work, not another accepted-source history entry.
                selected_files.append((base + '.md', archive.read('REVIEW.md')))
                plans.append((local_path(owner, base + '.json'), canonical_json(description) + b'\n'))
                proposal_count += 1
            members += len(all_names)
            bytes_removed += archive_path.stat().st_size
    requests = compact_suggestions(review)
    validate_proposal_assets(owner, requests)
    approvals = _approval_snapshots(owner, catalog, apply=False)
    result = {'schema': 'arcpuzzles-review-compaction-v1', 'mode': 'apply' if apply else 'preview',
              'managed_returns': len(raw_receipts), 'transport_bytes': bytes_removed,
              'classified_members': members, 'current_task_records': len(current),
              'active_audits': len(active), 'tool_requests': len(requests['items']),
              'proposal_candidates': proposal_count, 'selected_evidence_files': len(selected_files),
              'selected_evidence_bytes': sum(len(data) for path, data in selected_files),
              'largest_selected': [{'path':p, 'bytes':len(data)} for p, data in sorted(selected_files, key=lambda x:len(x[1]), reverse=True)[:8]],
              'approval_snapshots': approvals, 'archives_deleted': 0}
    if not apply:
        return result
    feed = owner / 'var/review/solves'
    built = build_solve_tracker(review, feed)
    if built['counts']['errors']:
        raise ValueError('Cannot retire archives with solve extraction errors')
    result['authored_examples'] = retain_solve_examples(owner, feed)
    for relative, data in selected_files:
        _copy(owner, relative, data)
    for path, data in [*plans, *notes_plans.items()]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    append_suggestions(review, [e for r in records.values() for e in suggestion_events(r)] + question_requests)
    _approval_snapshots(owner, catalog, apply=True)
    for tid, record in current.items():
        compact_task_state(owner, tid, record, apply=True, catalog_records=catalog)
    compact_suggestions(review, apply=True)
    validate_proposal_assets(owner, compact_suggestions(review))
    # All retained bytes must be readable/hash-valid without archive readers.
    for relative, data in selected_files:
        if sha256(local_path(owner, relative)) != digest(data):
            raise ValueError(f'Extraction verification failed: {relative}')
    for tid in current:
        for audit in read_index(owner, tid)['audits']:
            if audit.get('assets_manifest'):
                path = local_path(owner, audit['assets_manifest'])
                if sha256(path) != audit['assets_manifest_sha256']:
                    raise ValueError(f'Audit manifest verification failed: {path}')
                for item in json.loads(path.read_text())['files']:
                    if sha256(local_path(owner, item['path'])) != item['sha256']:
                        raise ValueError(f'Audit asset verification failed: {item["path"]}')
    # Mask receipts before exercising the independent reader. A failed check
    # restores receipts; no raw ZIP is removed until the gate passes.
    originals = {p: p.read_bytes() for p, r in raw_receipts}
    try:
        for path, r in raw_receipts:
            _write(path, {**r, 'retention_status': 'extracted'})
        rebuilt = build_solve_tracker(review, owner / 'var/review/compact-verify')
        expected = {k: built['counts'][k] for k in ('questions', 'attempts', 'verified_good', 'verified_bad', 'unverified')}
        if any(rebuilt['counts'][k] != n for k, n in expected.items()) or rebuilt['counts']['errors']:
            raise ValueError('Archive-independent authored data differs')
        from .review_full_inbox import build_full_inbox
        checked = build_full_inbox(review, owner / 'var/review/full-inbox')
        # Unmapped returns were never selected for disposal. They remain in
        # the inbox, with their exact raw transports, while mapped processed
        # receipts must disappear from the archive-dependent reader.
        if checked['counts']['returns'] != checked['counts']['invalid']:
            raise ValueError('Inbox still requires processed return transports')
    except Exception:
        for path, data in originals.items():
            path.write_bytes(data)
        raise
    # Recheck original ZIP identity immediately before removal.
    if set((review / 'assignments').glob('*/returns/return-*.json')) != set(originals):
        raise ValueError('New intake arrived during compaction; review it before disposal')
    for tid, record in current.items():
        if sha256(owner / f'generators/{tid}/generator.py') != record['current_source_sha256']:
            raise ValueError(f'Generator changed during compaction: {tid}')
    for path, r in raw_receipts:
        archive = Path(r['archive_path'])
        if sha256(archive) != r['zip_sha256']:
            raise ValueError(f'Transport changed before disposal: {archive}')
    assignments = {p.parent.parent for p, r in raw_receipts}
    archive_dirs = {Path(r['archive_path']).parent for p, r in raw_receipts}
    assignment_trees = []
    for parent in ('full-candidates', 'full-checks', 'solve-checks'):
        for assignment in assignments:
            tree = owner / 'var/review' / parent / assignment.name
            if tree.parent.is_symlink() or tree.is_symlink():
                raise ValueError(f'Symlink processed workspace: {tree}')
            if tree.is_dir():
                assignment_trees.append(tree)
    for directory in archive_dirs:
        shutil.rmtree(directory)
    for directory in assignments:
        # This is exactly the processed assignment workspace, not another task.
        shutil.rmtree(directory)
    for tree in assignment_trees:
        shutil.rmtree(tree)
    retired_hashes = {r['zip_sha256'] for p, r in raw_receipts}
    duplicates = 0
    for path in (owner / 'var/review').rglob('*.zip'):
        if not path.is_file() or path.is_symlink() or path.name.startswith('SEND-THIS-') or 'full-packets' in path.parts:
            continue
        if sha256(path) in retired_hashes:
            path.unlink()
            duplicates += 1
    for path in (review / 'task_indexes').glob('*.json'):
        path.unlink()
    for tid in records:
        for path in (owner / f'generators/{tid}/evidence').glob('review-review-*.json'):
            path.unlink()
    for path in [*review.glob('intake-*.md'), *review.glob('intake-*.json')]:
        path.unlink()
    result['archives_deleted'] = len(raw_receipts)
    result['redundant_zip_copies_deleted'] = duplicates
    result['processed_assignment_trees_deleted'] = len(assignment_trees)
    result['archive_independent_validation'] = 'passed'
    _write(owner / 'var/review/compaction-current.json', result)
    shutil.rmtree(owner / 'var/review/compact-verify')
    return result
