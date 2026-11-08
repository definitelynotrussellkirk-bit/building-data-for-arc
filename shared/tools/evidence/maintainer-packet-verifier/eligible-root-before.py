"""Frozen, portable review-library projections and successful-build rotation.

The owner library is never edited or moved. Projected JSON is explicitly derived;
all source/rule/evidence bytes retain their owner hashes. No reviewer code runs.
"""
from __future__ import annotations

from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import re

from .catalog import Catalog, jsonl, local_path

SELECTION_SCHEMA = 'arcpuzzles-packet-selection-v1'
ROTATION_SCHEMA = 'arcpuzzles-packet-rotation-v1'
PROJECTION_SCHEMA = 'arcpuzzles-packet-projection-v1'
DEFAULT_SIZE = 500
_SKIP = {'.git', 'var', 'build', 'dist', '__pycache__', '.pytest_cache', '.mypy_cache',
         '.ruff_cache', '.venv', 'venv', 'secrets', 'credentials', 'weights', 'checkpoints',
         'incoming', '.superpowers', 'reviewer-solves'}
_HISTORY = {'history', 'historical', 'prior', 'provenance', 'archive', 'archives', 'session_logs'}
_HISTORICAL_MANIFEST_PREFIXES = ('prior-manifest-', 'initial-manifest-', 'reviewer-authored-manifest-')
_DIARY = re.compile(r'(?i)(?:^|[-_])(plan|progress|session|work[-_]?log|scratch|journal|transcript)(?:[-_.]|$)')


def _raw(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode() + b'\n'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _read(path):
    return json.loads(path.read_text())


def rotation_state(review_root: Path) -> dict:
    path = review_root / 'packet-rotation.json'
    value = _read(path) if path.is_file() else {'schema': ROTATION_SCHEMA, 'round': 0, 'last_selected': {}}
    if (value.get('schema') != ROTATION_SCHEMA or type(value.get('round')) is not int
            or value['round'] < 0 or not isinstance(value.get('last_selected'), dict)
            or any(not isinstance(t, str) or type(n) is not int or n < 0
                   for t, n in value['last_selected'].items())):
        raise ValueError('Invalid packet rotation current state')
    pending = value.get('pending_focus', [])
    if (not isinstance(pending, list) or any(not isinstance(t, str)
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', t) for t in pending)
            or len(set(pending)) != len(pending)):
        raise ValueError('Invalid pending packet focus IDs')
    return value


def queue_review_focus(review_root: Path, ids: list[str]) -> dict:
    """Merge current intake focus without advancing successful-build coverage."""
    from .review import _lock
    if not isinstance(ids, (list, tuple, set)) or any(not isinstance(t, str)
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', t) for t in ids):
        raise ValueError('Packet focus IDs must be library task identifiers')
    with _lock(review_root):
        state = rotation_state(review_root)
        after = {**state, 'pending_focus': sorted(set(state.get('pending_focus', [])) | set(ids))}
        if after != state:
            path = review_root/'packet-rotation.json';path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix('.json.tmp');temporary.write_bytes(_raw(after));temporary.replace(path)
        return after


def queue_receipt_focus(review_root: Path, receipt: dict) -> dict:
    """Use accepted contract targets, never arbitrary feedback/report text."""
    if receipt.get('validation_status') != 'accepted':
        return rotation_state(review_root)
    ids = [receipt.get('task_id')]
    for target in receipt.get('audit_targets', []):
        ids.append(target.get('task_id') if isinstance(target, dict) else target)
    for row in receipt.get('supplementary_tickets', []):
        ticket = row.get('ticket', {})
        ids.append(ticket.get('task_id'))
        ids.extend(ticket.get('task_ids', []))
    return queue_review_focus(review_root, [tid for tid in ids if tid is not None])


def commit_rotation(review_root: Path, selection: dict, state: dict) -> None:
    """Called under the review lock only after the output ZIP succeeds."""
    if _sha(_raw(rotation_state(review_root))) != selection['rotation']['before_sha256']:
        raise RuntimeError('Packet rotation state changed during build')
    if _sha(_raw(state)) != selection['rotation']['after_sha256']:
        raise ValueError('Packet rotation result differs from frozen selection')
    path = review_root / 'packet-rotation.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_bytes(_raw(state)); temporary.replace(path)


def choose_selection(catalog: Catalog, review_root: Path, *, size: int = DEFAULT_SIZE,
                     focus_ids: list[str] | None = None, task_ids: list[str] | None = None) -> tuple[dict, dict]:
    """Prefer recent returns and unfinished original families, reserving coverage.

    Quotas count root candidates; their transitive dependencies consume the same
    total generator budget. Selection is read-only until commit_rotation.
    """
    from .parametric_priority import build_parametric_priority
    if type(size) is not int or size < 1:
        raise ValueError('Packet selection size must be a positive integer')
    rows = catalog.query(); by_id = {r['id']: r for r in rows if r.get('generator')}
    available = sorted(by_id)
    if not available:
        raise ValueError('Packet selection requires generators')
    budget = min(size, len(available)); state = rotation_state(review_root)
    def resolve(tid):
        try:
            value = catalog.resolve(tid)
        except KeyError as error:
            raise ValueError(f'Unknown packet focus/dependency: {tid}') from error
        if value not in by_id:
            raise ValueError(f'Packet dependency has no generator: {tid}')
        return value
    def closure(tid):
        pending = [tid]; found = set()
        while pending:
            current = pending.pop()
            if current in found:
                continue
            found.add(current)
            dependencies = by_id[current].get('runtime_dependencies', [])
            if not isinstance(dependencies, list) or any(not isinstance(v, str) or not v for v in dependencies):
                raise ValueError(f'Invalid runtime dependency declaration: {current}')
            pending.extend(resolve(v) for v in dependencies)
        return found
    # Validate all declarations before selecting, rather than hiding a broken
    # dependency behind a particular rotation draw.
    closures = {tid: closure(tid) for tid in available}
    last = state['last_selected']
    order = lambda ids: sorted(set(ids), key=lambda tid: (last.get(tid, -1), tid))
    chosen = set(); reasons = {}; dependency_ids = set()
    def add(tid, reason, limit=budget):
        needed = closures[tid] - chosen
        if len(chosen) + len(needed) > limit:
            return False
        chosen.update(needed)
        reasons.setdefault(tid, [])
        if reason not in reasons[tid]: reasons[tid].append(reason)
        for dep in closures[tid] - {tid}:
            dependency_ids.add(dep)
            why = 'runtime_dependency:' + tid
            if why not in reasons.setdefault(dep, []): reasons[dep].append(why)
        return True
    focus = list(focus_ids if focus_ids is not None else state.get('pending_focus', []))
    if focus_ids is None and task_ids is None:
        # The current handoff points to one current intake receipt, not a
        # cumulative history scan. Explicit caller focus always takes precedence.
        current = review_root/'full-packet-current.json'
        receipt = (_read(current).get('current_intake', {}).get('source_receipt')
                   if current.is_file() else None)
        if isinstance(receipt, str):
            path = Path(receipt)
            if not path.is_absolute(): path = catalog.root/path
            if path.resolve().is_relative_to(catalog.root/'var') and path.is_file():
                intake = _read(path)
                records = intake.get('returns', [])
                if 'recent_focus_assignment_ids' in intake:
                    current_ids = intake['recent_focus_assignment_ids']
                    known = {item.get('assignment', {}).get('assignment_id') for item in records}
                    if (not isinstance(current_ids, list)
                            or any(not isinstance(aid, str) or not aid for aid in current_ids)
                            or len(set(current_ids)) != len(current_ids)
                            or not set(current_ids) <= known):
                        raise ValueError('Invalid current intake focus assignment IDs')
                    records = [item for item in records
                               if item.get('assignment', {}).get('assignment_id') in set(current_ids)]
                for item in records:
                    tid = item.get('assignment', {}).get('task_id')
                    if tid in by_id: focus.append(tid)
                    for audit in item.get('intake', {}).get('audit_targets', []):
                        if audit.get('task_id') in by_id: focus.append(audit['task_id'])
    focus = order(resolve(t) for t in focus)
    if task_ids is not None:
        roots = order(resolve(t) for t in task_ids)
        if not roots:
            raise ValueError('Explicit packet task_ids cannot be empty')
        for tid in roots:
            if not add(tid, 'explicit'):
                raise ValueError('Explicit packet dependency closure exceeds selection budget')
    elif budget == len(available):
        for tid in available: add(tid, 'coverage')
        for tid in focus: add(tid, 'recent_return')
    else:
        coverage_reserve = max(1, budget * 3 // 10) if budget > 1 else 0
        focus_quota = min(60, max(1, budget // 5))
        priority_quota = min(150, budget // 2)
        priority = build_parametric_priority(catalog, rows=rows)
        # Keep mapped public-evaluation families represented in every projection.
        # Parent coverage is least-recent first; one descendant per parent is
        # considered before a second, so large descendant banks cannot dominate.
        evaluation_quota = max(1, budget // 10)
        parents = [anchor for anchor in priority['evaluation_focus']['anchors']
                   if any(tid in by_id for tid in anchor['main_ids'])]
        parents.sort(key=lambda anchor: (
            max((last.get(tid, -1) for tid in anchor['main_ids']), default=-1),
            anchor['source_task_id']))
        parent_pools = [order(tid for tid in anchor['main_ids'] if tid in by_id) for anchor in parents]
        evaluation_roots = 0
        for depth in range(max((len(pool) for pool in parent_pools), default=0)):
            for pool in parent_pools:
                if evaluation_roots >= evaluation_quota: break
                if depth < len(pool) and add(pool[depth], 'public_evaluation_coverage', budget - coverage_reserve):
                    evaluation_roots += 1
        roots_added = 0
        for tid in focus:
            if roots_added >= focus_quota: break
            if add(tid, 'recent_return', budget - coverage_reserve): roots_added += 1
        priority_ids = priority['tiers']['approved_originals_need_parameters']
        roots_added = 0
        for tid in order(priority_ids):
            if roots_added >= priority_quota: break
            if tid not in chosen and add(tid, 'unfinished_approved_original', budget - coverage_reserve): roots_added += 1
        for tid in order(available):
            if len(chosen) >= budget: break
            if tid not in chosen: add(tid, 'coverage')
    after = deepcopy(state)
    if len(chosen) < len(available):
        after['round'] += 1
        for tid in chosen: after['last_selected'][tid] = after['round']
    if 'pending_focus' in after:
        after['pending_focus'] = [tid for tid in after['pending_focus'] if tid not in chosen]
    selection = {'schema': SELECTION_SCHEMA, 'policy': 'recent_returns_original_priority_coverage',
                 'target_size': size, 'owner_generator_count': len(available),
                 'selected_ids': sorted(chosen), 'dependency_ids': sorted(dependency_ids),
                 'reasons': {tid: reasons[tid] for tid in sorted(chosen)},
                 'quotas': {'recent_focus_roots': min(60, max(1, budget // 5)),
                            'unfinished_original_roots': min(150, budget // 2),
                            'public_evaluation_roots': max(1, budget // 10),
                            'coverage_reserved_slots': max(1, budget * 3 // 10) if budget > 1 else 0},
                 'rotation': {'round': after['round'], 'before_sha256': _sha(_raw(state)),
                              'after_sha256': _sha(_raw(after))}}
    return selection, after


def _allowed(relative: str, *, forced=False) -> bool:
    path = Path(relative)
    if any(p in _SKIP or p.startswith('.env') or p.endswith('.egg-info') for p in path.parts):
        return False
    if not forced:
        if path.name.startswith(_HISTORICAL_MANIFEST_PREFIXES): return False
        if len(path.parts) >= 4 and path.parts[0] == 'generators' and path.parts[2:4] == ('evidence', 'supplementary'): return False
        if 'workspace' in path.parts and 'proposals' in path.parts: return False
        if any(p in _HISTORY for p in path.parts): return False
        if 'workspace' in path.parts and _DIARY.search(path.name): return False
        if path.suffix in {'.pyc', '.pyo', '.zip', '.tar', '.zst', '.safetensors', '.pt', '.pth'}: return False
    return True


def project_library(root: Path, review_root: Path, selection: dict) -> tuple[dict[str, Path], dict]:
    """Return logical library members backed by owner bytes or explicit projection.

    Reusing a manifest's selection never reads or advances rotation. Filtered
    tables are written under ignored var/, with owner and projected hashes.
    """
    from .review_notes import compact_suggestions, validate_index, validate_proposal_assets
    root = root.resolve(); review_root = review_root.resolve()
    if selection.get('schema') != SELECTION_SCHEMA:
        raise ValueError('Unknown packet selection schema')
    ids = selection.get('selected_ids')
    if (not isinstance(ids, list) or not ids or len(set(ids)) != len(ids)
            or any(not isinstance(t, str) for t in ids)):
        raise ValueError('Malformed frozen packet selection')
    catalog = Catalog(root); chosen = set(ids)
    records = [r for r in jsonl(root/'catalog/puzzles.jsonl') if r['id'] in chosen]
    if {r['id'] for r in records} != chosen:
        raise ValueError('Frozen packet selection has missing catalog tasks')
    for row in records:
        deps = row.get('runtime_dependencies', [])
        if not isinstance(deps, list) or any(catalog.resolve(dep) not in chosen for dep in deps):
            raise ValueError(f'Frozen selection misses runtime dependency: {row["id"]}')
    rule_ids = {row.get('rule_task_id', row['id']) for row in records} | chosen
    files = {}; transformed = {}; bindings = []; evidence_drifts = []
    superseded_trees = set()
    for tid in ids:
        home = root/'generators'/tid
        current_generator = _sha((home/'generator.py').read_bytes())
        for proof in (home/'evidence').glob('*/manifest.json'):
            try: value = _read(proof)
            except (ValueError, UnicodeError): continue
            target = value.get('resolves_manifest')
            if (value.get('status') != 'resolved_reported_correction'
                    or value.get('generator_sha256') != current_generator
                    or not isinstance(target, str)
                    or not target.startswith(f'generators/{tid}/evidence/')):
                continue
            resolved = local_path(root, target)
            if resolved.is_file(): superseded_trees.add(resolved.parent.relative_to(root).as_posix())

    def put(name, *, force=False):
        if not _allowed(name, forced=force):
            if force: raise ValueError(f'Forbidden evidence dependency: {name}')
            return
        path = local_path(root, name)
        parts = Path(name).parts
        if any((root/Path(*parts[:i])).is_symlink() for i in range(1, len(parts) + 1)):
            raise ValueError(f'Symlink packet dependency: {name}')
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError(f'Missing regular packet runtime/evidence dependency: {name}')
        files[name] = path
    def tree(folder):
        base = root/folder
        if not base.exists(): return
        for path in sorted(base.rglob('*')):
            name = path.relative_to(root).as_posix()
            if any(name == prefix or name.startswith(prefix + '/') for prefix in superseded_trees): continue
            if path.is_symlink():
                if _allowed(name): raise ValueError(f'Symlink packet source: {name}')
            elif path.is_file() and _allowed(name): put(name)
    from .review_full_packet import ROOT_FILES, SELECTED_DOCS
    for name in (*ROOT_FILES, *SELECTED_DOCS):
        if (root/name).is_file(): put(name)
    for path in sorted((review_root/'questions').glob('*.json')):
        put('REVIEW/questions/' + path.name)
    # Do not traverse the 4k generator tree or all proposed shared tools.
    for folder in ('GUIDE', 'src', 'tests', 'tools', 'shared/runtime', 'shared/data/raw'):
        tree(folder)
    tools = root/'shared/tools'
    if tools.exists():
        for path in sorted(tools.rglob('*')):
            name = path.relative_to(root).as_posix()
            if len(path.relative_to(tools).parts) > 1 and path.relative_to(tools).parts[0] in {'proposals', 'evidence'}: continue
            if path.is_file() and _allowed(name): put(name)
    for tid in ids:
        home = root/'generators'/tid
        if home.is_symlink(): raise ValueError(f'Symlink task home: {tid}')
        tree(f'generators/{tid}')
    # Active indexes, including legacy input, retain their exact linked evidence.
    for tid in ids:
        candidates = [root/f'generators/{tid}/evidence/review_index.json', review_root/f'task_indexes/{tid}.json']
        seen = None
        for path in candidates:
            if not path.is_file(): continue
            record = _read(path); validate_index(record, tid)
            if seen is not None and path.read_bytes() != seen:
                raise ValueError(f'Conflicting task index: {tid}; migrate before packaging')
            seen = path.read_bytes()
            target = f'generators/{tid}/evidence/review_index.json'
            if path == root/target: put(target, force=True)
            else: transformed[target] = path.read_bytes()
    suggestions = compact_suggestions(review_root)
    requests = {**suggestions, 'items': [row for row in suggestions['items']
                 if row.get('generator_id') in chosen and row.get('status') not in {'rejected', 'implemented'}]}
    proposal_files = validate_proposal_assets(root, requests)
    for name in proposal_files: put(name, force=True)
    for row in requests['items']:
        if row.get('assets_manifest'): put(row['assets_manifest']['path'], force=True)
    transformed['REVIEW/suggestions.json'] = _raw(requests)
    # Every metadata projection is labelled in the projection receipt below.
    transformed['catalog/puzzles.jsonl'] = b''.join(_raw(row) for row in records)
    aliases = root/'catalog/aliases.json'
    if aliases.is_file():
        projected = {a: [tid for tid in targets if tid in chosen] for a, targets in _read(aliases).items()}
        transformed['catalog/aliases.json'] = _raw({a: v for a, v in projected.items() if v})
    authorities = _read(root/'catalog/authority_files.json')
    selected_authorities = {path: tid for path, tid in authorities.items() if tid in rule_ids}
    transformed['catalog/authority_files.json'] = _raw(selected_authorities)
    mappings = []
    for item in _read(root/'catalog/runtime_files.json'):
        name, target = item['path'], item['target']
        if name.startswith('generators/') and Path(name).parts[1] not in chosen: continue
        if target.startswith('data/base/solutions/') and authorities.get(target) not in rule_ids: continue
        mappings.append(item)
        # Tables below are projected; all other mapped source stays exact.
        if not name.startswith(('shared/data/canonical/', 'shared/data/derived/')) and name != 'shared/data/base/manifest.json': put(name, force=True)
    transformed['catalog/runtime_files.json'] = _raw(mappings)
    for path in sorted((root/'shared/data/canonical').glob('*.jsonl')):
        # Filtering preserves each owner line byte-for-byte; Racket strings,
        # row order, duplicates and unrelated-task formatting stay untouched.
        lines = [line for line in path.read_bytes().splitlines(keepends=True)
                 if line.strip() and json.loads(line).get('task_id') in rule_ids]
        transformed[path.relative_to(root).as_posix()] = b''.join(lines)
    for path in sorted((root/'shared/data/derived').glob('*')):
        if not path.is_file(): continue
        name = path.relative_to(root).as_posix()
        if path.suffix == '.jsonl':
            values = jsonl(path)
            values = [v for v in values if not any(k in v for k in ('generator_id', 'task_id', 'id'))
                      or v.get('generator_id', v.get('task_id', v.get('id'))) in chosen]
            transformed[name] = b''.join(_raw(v) for v in values)
        elif path.name == 'generator_weights.json':
            transformed[name] = _raw({t: v for t, v in _read(path).items() if t in chosen})
        elif path.name == 'generator_blacklist.txt':
            transformed[name] = ('\n'.join(line for line in path.read_text().splitlines() if line.split('#',1)[0].strip() in chosen)+'\n').encode()
        else: put(name)
    base_manifest = root/'shared/data/base/manifest.json'
    if base_manifest.is_file():
        base = _read(base_manifest)
        base['solutions'] = [v for v in base.get('solutions', []) if v.get('task_id', v.get('content_hash')) in rule_ids
                             or selected_authorities.get(v.get('solution_relpath')) in rule_ids]
        base['counts'] = {'projected_solutions': len(base['solutions'])}
        transformed['shared/data/base/manifest.json'] = _raw(base)
    # Include current compact approvals referenced by selected catalog records.
    for row in records:
        link = row.get('approval_receipt')
        if link: put(link, force=True)
    # Root authority/docs and current questions are added by the packet builder.
    # Follow explicit inventories recursively; do not silently drop cited ZIPs,
    # old source witnesses, or source-bound prototype originals to save space.
    observed_inputs = set()
    for name, path in files.items():
        if not name.endswith('/manifest.json') or 'supplementary' not in Path(name).parts:
            continue
        try: assessment = json.loads(path.read_bytes())
        except (ValueError, UnicodeError): continue
        if (not isinstance(assessment, dict)
                or assessment.get('schema') != 'arcpuzzles-supplementary-assessment-v1'):
            continue
        prefix = (Path(name).parent/'evidence').as_posix() + '/'
        for item in assessment.get('files', []):
            if not isinstance(item, dict): continue
            target = item.get('path')
            if not isinstance(target, str) or not target.startswith(prefix): continue
            source = local_path(root, target)
            if source.is_file() and _sha(source.read_bytes()) == item.get('sha256'):
                observed_inputs.add(target)
    pending = list(files)
    inspected = set(); outer_bound = set()
    def resolve_reference(value, parent):
        if not isinstance(value, str): return None
        value = value.removeprefix('repo/')
        parts = Path(parent).parts
        candidates = [value, (Path(parent).parent/value).as_posix()]
        if 'checks' in parts:
            candidates.append((Path(*parts[:parts.index('checks')])/value).as_posix())
        for name in dict.fromkeys(candidates):
            try: path = local_path(root, name)
            except ValueError: continue
            if path.is_file(): return name
        return None
    while pending:
        name = pending.pop()
        if name in inspected or not name.endswith('.json'): continue
        inspected.add(name)
        try: data = json.loads(files[name].read_bytes())
        except (ValueError, UnicodeError): continue
        if not isinstance(data, dict): continue
        refs = []
        # A bound old receipt is passive provenance, not a demand that current
        # source still equals its earlier bytes. The outer current inventory
        # pins that receipt and its retained source snapshots exactly.
        passive = (any(part in _HISTORY or part in {'reviewer-original', 'reviewer-reported'}
                       for part in Path(name).parts) or 'reviewer-original' in Path(name).name
                   or (Path(name).name.startswith(_HISTORICAL_MANIFEST_PREFIXES) and name in outer_bound))
        if isinstance(data.get('files'), list) and not passive:
            for item in data['files']:
                if not isinstance(item, dict) or not isinstance(item.get('sha256'), str): continue
                value = item.get('path')
                # Runtime inventories are observations, not repository-file
                # closures. Exact explicit repository inventories are binding.
                if not isinstance(value, str) or not value.startswith(('generators/', 'shared/', 'src/', 'tests/', 'catalog/', 'REVIEW/')): continue
                refs.append((value, item['sha256']))
        for audit in data.get('audits', []):
            if isinstance(audit, dict) and audit.get('assets_manifest'):
                refs.append((audit['assets_manifest'], audit.get('assets_manifest_sha256')))
        for key in ('assets_manifest',):
            value = data.get(key)
            # Authored ticket observations name the manifest read at probe time.
            # Its native assessment pins the report bytes; the current request
            # independently pins today's inventory. Merging that inventory must
            # not rewrite or requalify a historical observation's input binding.
            if name not in observed_inputs and isinstance(value, dict) and value.get('path'):
                refs.append((value['path'], value.get('sha256')))
        for value, expected in refs:
            target = resolve_reference(value, name)
            if target is None: raise FileNotFoundError(f'Missing evidence inventory dependency: {value} from {name}')
            actual = _sha((root/target).read_bytes())
            if expected and actual != expected:
                raise ValueError(f'Missing or changed retained witness/evidence inventory: {target}')
            outer_bound.add(target)
            if target not in files:
                put(target, force=True); pending.append(target)
        # Native gzip indexes carry compressed and restored identities. Resolve
        # their local transport paths without executing restoration programs.
        schema = data.get('schema')
        if schema in {'arc-review-evidence-archive-v1', 'review-large-evidence-v1', 'arcpuzzles-evidence-gzip-v1'}:
            entries = data.get('entries' if schema == 'arc-review-evidence-archive-v1' else 'files', [])
            for item in entries:
                if not isinstance(item, dict) or not item.get('compressed_path'): continue
                target = resolve_reference(item['compressed_path'], name)
                if target is None: raise FileNotFoundError(f'Missing compressed evidence dependency: {name}: {item["compressed_path"]}')
                blob=(root/target).read_bytes()
                expected=item.get('compressed_sha256');raw_hash=item.get('raw_sha256', item.get('original_sha256'))
                if expected and _sha(blob)!=expected: raise ValueError(f'Changed compressed evidence: {target}')
                if raw_hash and _sha(gzip.decompress(blob))!=raw_hash: raise ValueError(f'Changed restored evidence: {target}')
                if target not in files: put(target, force=True); pending.append(target)
    # Exact copied bytes and derived tables have separate receipts. Content-keyed
    # paths let frozen re-projection return real local Paths without a live cache.
    material = {name: _sha(raw) for name, raw in sorted(transformed.items())}
    key = _sha(_raw({'ids': sorted(chosen), 'tables': material,
                     'exact_sources': {name: _sha(path.read_bytes()) for name, path in sorted(files.items())}}))
    projection = root/'var/review/packet-projections'/key
    for name, raw in transformed.items():
        path = projection/name;path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_bytes()!=raw: path.write_bytes(raw)
        files[name] = path
    def purpose(name):
        parts = Path(name).parts
        if name in transformed: return 'selected_metadata'
        if name.startswith('generators/'):
            if '/evidence/supplementary' in name: return 'current_supplementary_ticket_evidence'
            if '/workspace/parametric/' in name: return 'parameter_prototype_and_evidence'
            if '/counterexamples/' in name: return 'counterexamples_and_audit_evidence'
            if '/tests/' in name: return 'generator_regressions'
            if name.endswith('/evidence/review_index.json'): return 'current_generator_review_state'
            if '/evidence/' in name: return 'source_bound_generator_evidence'
            return 'generator_source_notes_and_helpers'
        if name.startswith('shared/tools/proposals/'): return 'selected_actionable_tool_proposals'
        if name.startswith('shared/runtime/'): return 'reference_runtime_and_generation_helpers'
        if name.startswith('shared/tools/'): return 'review_and_validation_tools'
        if name.startswith('shared/data/raw/'): return 'supplied_reference_datasets'
        if name.startswith('shared/data/'): return 'canonical_and_runtime_data'
        if name.startswith('src/'): return 'public_api_and_review_engine'
        if name.startswith('tests/'): return 'shared_regression_tests'
        if name.startswith('tools/'): return 'local_build_tools'
        if name.startswith('GUIDE/'): return 'racket_dsl_guide'
        if name.startswith('REVIEW/approvals/'): return 'selected_source_approvals'
        if name.startswith('REVIEW/questions/'): return 'current_review_questions'
        return 'installation_and_owner_guidance'
    purpose_counts = {}
    for name, path in sorted(files.items()):
        category = purpose(name)
        count = purpose_counts.setdefault(category, {'files': 0, 'bytes': 0})
        count['files'] += 1; count['bytes'] += path.stat().st_size
        owner = root/name
        bindings.append({'path': name, 'packet_path': 'repo/' + name, 'projected_path': name, 'purpose': category, 'mode': 'projection' if name in transformed else 'exact_copy',
                         'owner_sha256': _sha(owner.read_bytes()) if owner.is_file() else None,
                         'projected_sha256': _sha(path.read_bytes())})
    receipt = {'schema': PROJECTION_SCHEMA, 'selected_ids': sorted(chosen), 'files': bindings,
               'stale_evidence_bindings': evidence_drifts, 'purpose_counts': purpose_counts,
               'superseded_limit_trees_omitted_unless_currently_cited': sorted(superseded_trees),
               'scope': 'Projected metadata is derived from owner tables; source, rules and cited evidence remain exact. No safety or training admission is granted.'}
    # A projected Catalog must itself be independently usable; copy exact
    # selected dependencies too, never symlink back into the owner checkout.
    expected_projection = {item['path']: item['projected_sha256'] for item in bindings}
    for name, source in list(files.items()):
        destination = projection/name
        if destination != source:
            destination.parent.mkdir(parents=True, exist_ok=True)
            raw = source.read_bytes()
            if _sha(raw) != expected_projection[name]:
                raise RuntimeError(f'Source changed during packet projection: {name}')
            if not destination.is_file() or destination.read_bytes() != raw:
                destination.write_bytes(raw)
            files[name] = destination
    receipt_path = projection/'PACKET-PROJECTION.json';receipt_path.write_bytes(_raw(receipt))
    files['REVIEW/packet-projection.json'] = receipt_path
    return files, receipt
