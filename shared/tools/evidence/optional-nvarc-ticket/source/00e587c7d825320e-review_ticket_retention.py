"""Archive-independent current consumers for the two bounded reviewer tickets.

Planning only: the caller owns the review lock, applies immutable files before
mutable pointers, and runs the native disposal gate. No submitted code executes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from .catalog import local_path
from .review_tickets import CONSUMERS, copied_transport_path, validate_ticket_reports

ALLOCATION_REQUEST_ID = 'owner:allocation-data-quality-assessment'
_START = '<!-- arcpuzzles-current-supplementary:start -->'
_END = '<!-- arcpuzzles-current-supplementary:end -->'


def _raw(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _checked_file(owner, row, staged=None):
    path = local_path(owner, row['path'])
    if staged is not None and path in staged:
        raw = staged[path]
        if _sha(raw) != row['sha256']:
            raise ValueError(f'Changed staged supplementary dependency: {row["path"]}')
        return raw
    if path.is_symlink() or not path.is_file() or _sha(path.read_bytes()) != row['sha256']:
        raise ValueError(f'Missing or changed supplementary dependency: {row["path"]}')
    return path.read_bytes()


def _dataset_verdict_rows(owner, pointer, staged):
    """Rebuild the training consumer from current externally checked reports."""
    from .review_nvarc import DATASET, TYPE, validate_report
    rows = []
    for digest, link in pointer['assessments'].items():
        body = json.loads(_checked_file(owner, link, staged))
        ticket, report = body['ticket'], body['report']
        if (ticket.get('type') != TYPE or ticket.get('dataset_id') != DATASET
                or ticket.get('sha256') != digest or body.get('verification_status') != 'reviewer_reported'):
            raise ValueError('Invalid current NVARC consumer assessment')
        members = {f['source_member']: _checked_file(owner, f, staged) for f in body['files']}
        validate_report(ticket, report, set(members), members.__getitem__)
        if report['status'] == 'completed':
            rows.append(report['nvarc_review'])
    rows.sort(key=lambda row: (row['file'], row['sha256']))
    return b''.join((json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode() for row in rows)


def ticket_evidence_names(rows: list[dict], names: set[str]) -> set[str]:
    """Initial wanted set, before the caller expands gzip dependencies."""
    selected = set()
    for row in rows:
        for name in row['report'].get('evidence_paths', []):
            path = PurePosixPath(name)
            if (name not in names or path.is_absolute() or '..' in path.parts
                    or copied_transport_path(name)):
                raise ValueError(f'Invalid supplementary ticket evidence path: {name}')
            if not name.startswith('checks/') and name not in {'REVIEW.md', 'DECISIONS.md', 'FEEDBACK_TO_CODEX.md', 'QUESTION_ANSWER.md'}:
                raise ValueError(f'Ticket evidence must be compact authored evidence: {name}')
            selected.add(name)
    return selected


def merge_ticket_notes(text: str, task_id: str, pointer: str) -> str:
    section = (_START + '\n## Current supplementary checks\n\n'
        f'Current source-bound ticket observations: `{pointer}`. '
        'Results are reviewer-reported; blocked or unknown stays explicit. '
        'These observations do not approve a generator or variant, resolve audits, '
        'or admit data to training.\n' + _END)
    if _START in text:
        if _END not in text:
            raise ValueError('Incomplete current supplementary notes marker')
        before, rest = text.split(_START, 1)
        _, after = rest.split(_END, 1)
        return before + section + after
    return text.rstrip() + '\n\n' + section + '\n'


def _request_manifest(owner, request, request_id, staged):
    base = 'shared/tools/proposals/' + _sha(request_id.encode())[:16]
    path = local_path(owner, base + '/manifest.json')
    link = request.get('assets_manifest') if request else None
    if link:
        if not isinstance(link, dict) or link.get('path') != base + '/manifest.json':
            raise ValueError('Invalid existing tool request asset manifest path')
        # The owner's current request can still point to the on-disk version;
        # prior plans in this same compaction are a separately checked overlay.
        original = _checked_file(owner, link)
    else:
        original = None
    if path in staged:
        manifest = json.loads(staged[path])
    elif original is not None:
        manifest = json.loads(original)
    else:
        return base, {'schema': 'arcpuzzles-tool-proposal-assets-v1',
                      'request_id': request_id, 'runtime_approved': False, 'files': []}
    if (manifest.get('schema') != 'arcpuzzles-tool-proposal-assets-v1'
            or manifest.get('request_id') != request_id or manifest.get('runtime_approved') is not False
            or not isinstance(manifest.get('files'), list) or not manifest['files']):
        raise ValueError('Invalid existing tool request asset manifest identity')
    for file in manifest['files']:
        if not file['path'].startswith(base + '/'):
            raise ValueError('Existing tool asset outside its request home')
        _checked_file(owner, file, staged)
    return base, manifest


def prepare_ticket_retention(owner: Path, receipt: dict, rows: list[dict],
                             names: set[str], read_member, *,
                             staged_plans: dict[Path, bytes] | None = None) -> dict:
    """Prepare retained reports and current consumers without changing owner state.

    Call after ``ticket_evidence_names`` has joined the native wanted/expanded
    sets, so ``read_member`` can supply declared evidence and its gzip closure.
    """
    owner = Path(owner).resolve()
    staged = {(Path(path) if Path(path).is_absolute() else owner / path): raw
              for path, raw in (staged_plans or {}).items()}
    from .review_retention import _compressed_dependencies, _verify_compressed_dependencies, _runtime_copy
    if receipt.get('validation_status') != 'accepted':
        raise ValueError('Supplementary retention requires a validated return')
    validate_ticket_reports({'tickets': [r['ticket'] for r in rows]}, [r['report'] for r in rows], names,
                            read_member=read_member)
    requests_path = owner / 'REVIEW/suggestions.json'
    current = json.loads(requests_path.read_text()) if requests_path.is_file() else {'items': []}
    requests = {r['request_id']: r for r in current['items']}
    result = {'plans': [], 'selected_files': [], 'suggestion_events': [],
              'notes_updates': {}, 'selected_names': set()}
    pointers = {}
    dataset_pointer = None
    for row in rows:
        ticket, report = row['ticket'], row['report']
        kind = ticket['type']
        if ticket.get('consumer') != CONSUMERS[kind]:
            raise ValueError('Supplementary ticket consumer differs from its type')
        initial = ticket_evidence_names([row], names)
        selected, dependencies = _compressed_dependencies(initial, names, read_member)
        if any(_runtime_copy(name) or copied_transport_path(name) for name in selected):
            raise ValueError('Supplementary evidence closure contains a copied runtime')
        _verify_compressed_dependencies(dependencies, read_member)
        result['selected_names'].update(selected)
        evidence = [(name, read_member(name)) for name in sorted(selected)]
        body = {'schema': 'arcpuzzles-supplementary-assessment-v1', 'ticket': ticket,
                'report': report, 'return_id': f"{receipt['assignment_id']}:v{receipt['version']:04d}",
                'return_sha256': receipt['zip_sha256'], 'verification_status': 'reviewer_reported',
                'automatic_policy_change': False, 'training_admitted': False,
                'variant_approved': False, 'audit_resolution_changed': False,
                'evidence': [{'source_member': name, 'sha256': _sha(data), 'bytes': len(data)} for name, data in evidence]}
        tool_kind = kind in {'tool_reproduction', 'allocation_quality'}
        dataset_kind = kind == 'nvarc_visual'
        if dataset_kind:
            from .review_nvarc import DATASET
            if ticket.get('dataset_id') != DATASET or not re.fullmatch(r'[0-9a-f]{64}', ticket.get('sha256', '')):
                raise ValueError('Dataset ticket needs its pinned file identity')
            assessment_base = f'REVIEW/dataset-reviews/{DATASET}/assessments'
        elif tool_kind:
            request_id = ticket.get('request_id') if kind == 'tool_reproduction' else ALLOCATION_REQUEST_ID
            if not isinstance(request_id, str) or not request_id:
                raise ValueError('Tool reproduction needs its existing request identity')
            request = requests.get(request_id)
            if kind == 'tool_reproduction' and request is None:
                raise ValueError('Cannot retain a tool reproduction without its existing request')
            base, proposal = _request_manifest(owner, request, request_id, staged)
            assessment_base = base + '/supplementary'
        else:
            tid = ticket.get('task_id')
            if not isinstance(tid, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', tid):
                raise ValueError('Generator ticket needs its pinned task identity')
            if not re.fullmatch(r'[0-9a-f]{64}', ticket.get('generator_sha256', '')):
                raise ValueError('Generator ticket needs its source hash')
            assessment_base = f'generators/{tid}/evidence/supplementary'
            generator = local_path(owner, f'generators/{tid}/generator.py')
            current_hash = _sha(generator.read_bytes()) if generator.is_file() else None
            body.update(current_generator_sha256=current_hash,
                        source_status='current' if current_hash == ticket['generator_sha256'] else 'historical',
                        current_rule_reverified=False)
        assessment_id = _sha(_raw(body))
        home = assessment_base + '/' + assessment_id
        files = []
        for name, data in evidence:
            destination = home + '/evidence/' + name
            result['selected_files'].append((destination, data))
            files.append({'path': destination, 'source_member': name, 'sha256': _sha(data), 'bytes': len(data)})
        body['files'] = files
        relative = home + '/manifest.json';raw = _raw(body)
        result['selected_files'].append((relative, raw))
        link = {'path': relative, 'sha256': _sha(raw), 'bytes': len(raw)}
        if dataset_kind:
            pointer = f'REVIEW/dataset-reviews/{DATASET}/current.json'
            path = local_path(owner, pointer)
            if dataset_pointer is None:
                if path in staged or path.is_file():
                    dataset_pointer = json.loads(staged[path] if path in staged else path.read_bytes())
                    if (dataset_pointer.get('schema') != 'arcpuzzles-current-dataset-reviews-v1'
                            or dataset_pointer.get('dataset_id') != DATASET):
                        raise ValueError('Invalid current dataset review identity')
                    for prior in dataset_pointer.get('files', []):
                        _checked_file(owner, prior, staged)
                else:
                    dataset_pointer = {'schema': 'arcpuzzles-current-dataset-reviews-v1',
                                       'dataset_id': DATASET, 'assessments': {}, 'files': []}
            dataset_pointer['assessments'][ticket['sha256']] = link
            dataset_pointer['files'] = [dataset_pointer['assessments'][k] for k in sorted(dataset_pointer['assessments'])]
        elif tool_kind:
            # Original tool files remain exact. Replace only the prior current
            # ticket assessment in its native proposal inventory.
            previous = proposal.get('supplementary_assessment')
            previous_home = (str(PurePosixPath(previous['path']).parent) + '/'
                             if isinstance(previous, dict) and isinstance(previous.get('path'), str)
                             and previous['path'].startswith(base + '/supplementary/') else None)
            originals = [f for f in proposal['files']
                         if previous_home is None or not f['path'].startswith(previous_home)]
            proposal = {**proposal, 'files': originals + files + [link],
                        'supplementary_assessment': link, 'runtime_approved': False}
            proposal_raw = _raw(proposal);proposal_path = base + '/manifest.json'
            result['plans'].append((local_path(owner, proposal_path), proposal_raw))
            event = {'event': 'suggestion', 'request_id': request_id,
                     'assets_manifest': {'path': proposal_path, 'sha256': _sha(proposal_raw)}}
            if request is None:
                event['text'] = 'Assess review allocation and expected data quality per cost using bounded source-bound observations; changes require an owner decision.'
            result['suggestion_events'].append(event)
        else:
            pointer = f'generators/{tid}/evidence/supplementary-current.json'
            if tid not in pointers:
                path = local_path(owner, pointer)
                if path in staged or path.is_file():
                    value = json.loads(staged[path] if path in staged else path.read_bytes())
                    if value.get('schema') != 'arcpuzzles-current-supplementary-v1' or value.get('task_id') != tid:
                        raise ValueError('Invalid current supplementary pointer identity')
                    for file in value.get('files', []):
                        _checked_file(owner, file, staged)
                    pointers[tid] = value
                else:
                    pointers[tid] = {'schema': 'arcpuzzles-current-supplementary-v1',
                                     'task_id': tid, 'assessments': {}, 'files': []}
            pointers[tid]['assessments'][kind] = link
            pointers[tid]['files'] = [pointers[tid]['assessments'][key] for key in sorted(pointers[tid]['assessments'])]
            result['notes_updates'][local_path(owner, f'generators/{tid}/notes.md')] = {'task_id': tid, 'pointer': pointer}
    for tid, value in pointers.items():
        result['plans'].append((local_path(owner, f'generators/{tid}/evidence/supplementary-current.json'), _raw(value)))
    if dataset_pointer is None:
        from .review_nvarc import DATASET
        path = local_path(owner, f'REVIEW/dataset-reviews/{DATASET}/current.json')
        if path in staged or path.is_file():
            dataset_pointer = json.loads(staged[path] if path in staged else path.read_bytes())
            if (dataset_pointer.get('schema') != 'arcpuzzles-current-dataset-reviews-v1'
                    or dataset_pointer.get('dataset_id') != DATASET):
                raise ValueError('Invalid current dataset review identity')
    if dataset_pointer is not None:
        result['plans'].append((local_path(owner, f'REVIEW/dataset-reviews/{DATASET}/current.json'), _raw(dataset_pointer)))
        overlay = {**staged, **{local_path(owner, path): raw for path, raw in result['selected_files']}}
        result['plans'].append((owner / 'var/review/nvarc-check/verdicts.jsonl',
                                _dataset_verdict_rows(owner, dataset_pointer, overlay)))
    return result


def validate_current_ticket_assessments(owner: Path) -> set[str]:
    """Verify all current generator consumers without opening any return archive."""
    owner = Path(owner).resolve()
    from .review_retention import _compressed_dependencies, _verify_compressed_dependencies
    retained = set()
    for pointer in (owner / 'generators').glob('*/evidence/supplementary-current.json'):
        value = json.loads(pointer.read_text());tid = pointer.parent.parent.name
        if (pointer.is_symlink() or value.get('schema') != 'arcpuzzles-current-supplementary-v1'
                or value.get('task_id') != tid or value.get('files') != [value['assessments'][key] for key in sorted(value.get('assessments', {}))]):
            raise ValueError('Invalid current supplementary assessment pointer')
        retained.add(pointer.relative_to(owner).as_posix())
        for link in value['files']:
            body = json.loads(_checked_file(owner, link));home = str(PurePosixPath(link['path']).parent) + '/'
            if (body.get('schema') != 'arcpuzzles-supplementary-assessment-v1'
                    or body.get('ticket', {}).get('task_id') != tid
                    or not home.startswith(f'generators/{tid}/evidence/supplementary/')):
                raise ValueError('Invalid source-bound supplementary assessment')
            retained.add(link['path']);members = {}
            for file in body['files']:
                if not file['path'].startswith(home):
                    raise ValueError('Supplementary asset outside its assessment')
                raw = _checked_file(owner, file);retained.add(file['path']);members[file['source_member']] = raw
            _, dependencies = _compressed_dependencies(set(members), set(members), members.__getitem__)
            _verify_compressed_dependencies(dependencies, members.__getitem__)
    from .review_nvarc import DATASET, TYPE, validate_report
    pointer = owner / f'REVIEW/dataset-reviews/{DATASET}/current.json'
    if pointer.exists():
        value = json.loads(pointer.read_bytes())
        if (pointer.is_symlink() or value.get('schema') != 'arcpuzzles-current-dataset-reviews-v1'
                or value.get('dataset_id') != DATASET
                or value.get('files') != [value['assessments'][k] for k in sorted(value.get('assessments', {}))]):
            raise ValueError('Invalid current dataset review pointer')
        retained.add(pointer.relative_to(owner).as_posix())
        for digest, link in value['assessments'].items():
            body = json.loads(_checked_file(owner, link));home = str(PurePosixPath(link['path']).parent) + '/'
            ticket = body.get('ticket', {})
            if (body.get('schema') != 'arcpuzzles-supplementary-assessment-v1' or ticket.get('type') != TYPE
                    or ticket.get('sha256') != digest or ticket.get('dataset_id') != DATASET
                    or not home.startswith(f'REVIEW/dataset-reviews/{DATASET}/assessments/')):
                raise ValueError('Invalid source-bound dataset assessment')
            retained.add(link['path']);members = {}
            for file in body['files']:
                if not file['path'].startswith(home):
                    raise ValueError('Dataset review asset outside its assessment')
                members[file['source_member']] = _checked_file(owner, file)
                retained.add(file['path'])
            validate_report(ticket, body['report'], set(members), members.__getitem__)
    return retained


def ticket_feedback_only(text: str, rows: list[dict]) -> bool:
    """Recognize only the exact generated ticket-outcome placeholder feedback."""
    expected = 'Ticket outcomes ' + ' '.join(
        f"{row['ticket']['ticket_id']}: {row['report']['summary']}" for row in rows)
    return ' '.join(text.split()) == ' '.join(expected.split())
