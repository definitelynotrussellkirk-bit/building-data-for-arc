"""One-file, prediction-before-reveal external dataset review; no admission."""
from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import zipfile

TYPE = 'nvarc_visual'
DATASET = 'NVARC-CHECK-001'
ARCHIVE_PATH = 'review-data/NVARC-CHECK-001.zip'
ARCHIVE_SHA256 = '8a6bf7e6ef629cd3a6a0da86f8fb43d95c441aa829bfcb2aae1cf42c21ac5a62'
BUDGET = {'authoring_minutes': 3, 'targeted_probe_seconds': 0, 'targeted_probes': 0}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _raw(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def _grid(value):
    return (isinstance(value, list) and bool(value) and isinstance(value[0], list)
            and bool(value[0]) and all(isinstance(row, list) and len(row) == len(value[0])
            and all(type(x) is int and 0 <= x <= 9 for x in row) for row in value))


def archive_candidates(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if path.is_symlink() or _sha(raw) != ARCHIVE_SHA256:
        raise ValueError('NVARC archive hash differs from pinned sample')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        manifest = json.loads(z.read('MANIFEST.json'))
        rows = manifest.get('files')
        if not isinstance(rows, list) or len(rows) != 100:
            raise ValueError('NVARC needs its pinned 100-file manifest')
        names = ['puzzles/' + r['file'] for r in rows]
        if len(set(names)) != 100 or set(z.namelist()) != set(names) | {'MANIFEST.json'}:
            raise ValueError('NVARC sample inventory differs from manifest')
        candidates = []
        for row in rows:
            name = row['file']; p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name:
                raise ValueError('Unsafe NVARC filename')
            source = z.read('puzzles/' + name)
            pairs = json.loads(source)
            if (_sha(source) != row['sha256'] or not isinstance(pairs, list)
                    or len(pairs) != row['pairs'] or not 13 <= len(pairs) <= 30
                    or any(not isinstance(pair, dict) or set(pair) != {'input', 'output'}
                           or not _grid(pair['input']) or not _grid(pair['output']) for pair in pairs)):
                raise ValueError('NVARC source file hash or pair format differs')
            candidates.append({**{k: row[k] for k in ('file', 'sha256', 'subset', 'seed_tasks', 'pairs')},
                'dataset_id': DATASET, 'archive': {'path': ARCHIVE_PATH, 'sha256': ARCHIVE_SHA256},
                'sample_seed': manifest.get('sample_seed')})
    return sorted(candidates, key=lambda r: r['file'])


def completed_review_sources(owner: Path) -> dict[str, str]:
    """Read current completed identities for allocation, without opening labels.

    Metadata hashes and declared proof membership are checked here. Native
    intake/retention owns full proof validation; this grants no quality claim
    and deliberately does not use or change training-consumer adjudications.
    """
    from .catalog import local_path
    from .review_ticket_retention import _checked_file
    owner = Path(owner)
    pointer = local_path(owner, f'REVIEW/dataset-reviews/{DATASET}/current.json')
    if pointer.is_symlink():
        raise ValueError('Invalid NVARC coverage pointer')
    if not pointer.exists():
        return {}
    value = json.loads(pointer.read_bytes())
    if (not isinstance(value, dict) or value.get('schema') != 'arcpuzzles-current-dataset-reviews-v1'
            or value.get('dataset_id') != DATASET or not isinstance(value.get('assessments'), dict)
            or value.get('files') != [value['assessments'][k] for k in sorted(value['assessments'])]):
        raise ValueError('Invalid NVARC coverage metadata')
    completed = {}
    for digest, link in value['assessments'].items():
        if (not re.fullmatch('[0-9a-f]{64}', digest) or not isinstance(link, dict)
                or not isinstance(link.get('path'), str)
                or not link['path'].startswith(f'REVIEW/dataset-reviews/{DATASET}/assessments/')):
            raise ValueError('Invalid NVARC coverage assessment identity')
        raw = _checked_file(owner, link)
        body = json.loads(raw)
        if type(link.get('bytes')) is not int or link['bytes'] != len(raw) or not isinstance(body, dict):
            raise ValueError('Invalid NVARC coverage assessment bytes')
        ticket, report = body.get('ticket', {}), body.get('report', {})
        if (body.get('schema') != 'arcpuzzles-supplementary-assessment-v1'
                or body.get('verification_status') != 'reviewer_reported'
                or ticket.get('type') != TYPE or ticket.get('dataset_id') != DATASET
                or ticket.get('sha256') != digest
                or ticket.get('archive') != {'path': ARCHIVE_PATH, 'sha256': ARCHIVE_SHA256}
                or type(ticket.get('pairs')) is not int or not 13 <= ticket['pairs'] <= 30
                or report.get('ticket_id') != ticket.get('ticket_id') or report.get('type') != TYPE
                or report.get('status') not in {'completed', 'blocked', 'unknown'}
                or not isinstance(body.get('files'), list)):
            raise ValueError('Invalid source-bound NVARC coverage assessment')
        names = {row['source_member'] for row in body['files']}
        validate_report(ticket, report, names)
        if report['status'] == 'completed':
            completed[digest] = ticket['file']
    return completed


def _selected(root):
    from .review_tickets import supplementary_contract
    manifest = json.loads((root / 'PACKET-MANIFEST.json').read_bytes())
    packet_id = _sha(json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())
    main = json.loads((root / 'ASSIGNMENT.json').read_bytes())
    audit = json.loads((root / 'AUDIT_ASSIGNMENT.json').read_bytes())
    blind = root / 'BLIND_ASSIGNMENT.json'
    blind_id = json.loads(blind.read_bytes())['task_id'] if blind.is_file() else None
    if audit != supplementary_contract(manifest, packet_id, main, bytes.fromhex(audit['seed']), blind_id):
        raise ValueError('NVARC ticket contract changed')
    tickets = [t for t in audit['tickets'] if t['type'] == TYPE]
    if len(tickets) != 1:
        raise ValueError('No NVARC ticket was selected; do only the two assigned tickets')
    ticket = tickets[0]
    source_path = root / ARCHIVE_PATH
    if ticket['archive'] != {'path': ARCHIVE_PATH, 'sha256': ARCHIVE_SHA256}:
        raise ValueError('NVARC archive binding changed')
    candidates = archive_candidates(source_path)
    if not any(all(ticket.get(k) == v for k, v in row.items()) for row in candidates):
        raise ValueError('NVARC selected file differs from pinned manifest')
    with zipfile.ZipFile(source_path) as z:
        source = z.read('puzzles/' + ticket['file'])
    return ticket, source


def _blind(ticket, pairs):
    return {'dataset_id': DATASET, 'ticket_id': ticket['ticket_id'], 'file': ticket['file'],
            'sha256': ticket['sha256'], 'subset': ticket['subset'], 'seed_tasks': ticket['seed_tasks'],
            'train': pairs[:4], 'test': [{'input': pairs[4]['input']}]}


def _write_once(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError('NVARC proof path cannot be a symlink')
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f'NVARC immutable proof changed: {path.name}')
    else:
        with path.open('xb') as f:
            f.write(raw)


def prepare(root: Path) -> dict:
    root = Path(root)
    ticket, source = _selected(root)
    base = f"checks/tickets/{ticket['ticket_id']}/nvarc"
    blind = _raw(_blind(ticket, json.loads(source)))
    result = {'ticket_id': ticket['ticket_id'], 'blind_path': base + '/blind.json', 'blind_sha256': _sha(blind)}
    _write_once(root / '.review/nvarc' / ticket['ticket_id'] / 'prepared.json', _raw(result))
    _write_once(root / result['blind_path'], blind)
    _write_once(root / base / 'README.md', (
        'Review only pairs 0–3 in blind.json. Before revealing, save prediction.json with '
        'one-sentence "rule" and exact integer-grid "predicted_output" for pair 4.\n'
        'Run python3 assignment.py nvarc reveal --prediction PATH. Then compare pair 4 and '
        'skim pairs 5 through the actual end. Budget: three authoring minutes, no heavy probe. '
        'Return ok/ambiguous/inconsistent/trivial/broken, or blocked/uncertain with status '
        'blocked/unknown. Unknown does not imply ambiguity or noise. No source program is required.\n').encode())
    return result


def reveal(root: Path, prediction_path: Path) -> dict:
    root = Path(root)
    ticket, source = _selected(root)
    base = f"checks/tickets/{ticket['ticket_id']}/nvarc"
    state = root / '.review/nvarc' / ticket['ticket_id']
    expected_blind = _raw(_blind(ticket, json.loads(source)))
    prepared = json.loads((state / 'prepared.json').read_bytes())
    blind_path = base + '/blind.json'
    if (prepared.get('blind_path') != blind_path or prepared.get('blind_sha256') != _sha(expected_blind)
            or (root / blind_path).is_symlink() or (root / blind_path).read_bytes() != expected_blind):
        raise ValueError('NVARC blind file changed before prediction')
    raw = Path(prediction_path).read_bytes(); prediction = json.loads(raw)
    if (not isinstance(prediction, dict) or not isinstance(prediction.get('rule'), str)
            or not prediction['rule'].strip() or not _grid(prediction.get('predicted_output'))):
        raise ValueError('Prediction needs a rule and exact predicted_output integer grid')
    locked = state / 'prediction.json'
    if locked.exists() and locked.read_bytes() != raw:
        raise ValueError('NVARC prediction changed after it was locked')
    # Persist both exact prediction bytes and their source/blind binding before any answer is written.
    _write_once(locked, raw)
    _write_once(root / base / 'prediction-locked.json', raw)
    lock = {'ticket_id': ticket['ticket_id'], 'file': ticket['file'], 'sha256': ticket['sha256'],
            'blind_sha256': _sha(expected_blind), 'prediction_sha256': _sha(raw)}
    _write_once(root / base / 'prediction-lock.json', _raw(lock))
    pairs = json.loads(source)
    exposed = {'ticket_id': ticket['ticket_id'], 'file': ticket['file'], 'sha256': ticket['sha256'],
               'prediction_sha256': _sha(raw), 'pair4': pairs[4], 'remaining_pairs': pairs[5:],
               'predicted_ok': prediction['predicted_output'] == pairs[4]['output']}
    _write_once(root / base / 'source.json', source)
    _write_once(root / base / 'reveal.json', _raw(exposed))
    return {'reveal_path': base + '/reveal.json', 'predicted_ok': exposed['predicted_ok'],
            'evidence_paths': [base + '/' + n for n in (
                'blind.json', 'prediction-locked.json', 'prediction-lock.json', 'source.json', 'reveal.json')]}


def validate_report(ticket, report, names, read_member=None):
    result = report.get('nvarc_review')
    completed = report['status'] == 'completed'
    if result is None and not completed:
        return
    if not isinstance(result, dict) or set(result) != {'file', 'sha256', 'verdict', 'rule', 'predicted_ok', 'bad_pairs', 'minutes', 'note'}:
        raise ValueError('NVARC outcome needs the exact nvarc_review fields')
    if (result['file'] != ticket['file'] or result['sha256'] != ticket['sha256']
            or result['verdict'] not in ({'ok', 'ambiguous', 'inconsistent', 'trivial', 'broken'} if completed else {'blocked', 'uncertain'})
            or not isinstance(result['rule'], str) or (completed and not result['rule'].strip())
            or not isinstance(result['note'], str) or type(result['predicted_ok']) not in ({bool} if completed else {bool, type(None)})
            or not isinstance(result['bad_pairs'], list) or any(type(i) is not int or not 0 <= i < ticket['pairs'] for i in result['bad_pairs'])
            or (result['minutes'] is not None and (type(result['minutes']) not in {int, float}
                or not math.isfinite(result['minutes']) or result['minutes'] < 0))):
        raise ValueError('NVARC outcome differs from its bound file or uncertainty status')
    if not completed:
        return
    base = f"checks/tickets/{ticket['ticket_id']}/nvarc/"
    required = {base + n for n in ('blind.json', 'prediction-locked.json', 'prediction-lock.json', 'source.json', 'reveal.json')}
    if not required <= names or not required <= set(report['evidence_paths']):
        raise ValueError('NVARC completed review needs declared prediction/reveal proof')
    if read_member is None:
        return
    source = read_member(base + 'source.json')
    if _sha(source) != ticket['sha256']:
        raise ValueError('NVARC revealed source hash differs')
    pairs = json.loads(source)
    blind = read_member(base + 'blind.json')
    prediction_raw = read_member(base + 'prediction-locked.json'); prediction = json.loads(prediction_raw)
    lock = json.loads(read_member(base + 'prediction-lock.json'))
    exposed = json.loads(read_member(base + 'reveal.json'))
    expected_lock = {'ticket_id': ticket['ticket_id'], 'file': ticket['file'], 'sha256': ticket['sha256'],
                     'blind_sha256': _sha(blind), 'prediction_sha256': _sha(prediction_raw)}
    expected_reveal = {'ticket_id': ticket['ticket_id'], 'file': ticket['file'], 'sha256': ticket['sha256'],
        'prediction_sha256': _sha(prediction_raw), 'pair4': pairs[4], 'remaining_pairs': pairs[5:],
        'predicted_ok': prediction.get('predicted_output') == pairs[4]['output']}
    if (json.loads(blind) != _blind(ticket, pairs) or lock != expected_lock or exposed != expected_reveal
            or result['rule'] != prediction.get('rule') or result['predicted_ok'] != exposed['predicted_ok']
            or not _grid(prediction.get('predicted_output'))):
        raise ValueError('NVARC prediction/reveal proof differs from outcome')


def main(root: Path, args: list[str]) -> int:
    if args == ['prepare']:
        print(json.dumps(prepare(root), indent=2)); return 0
    if len(args) == 3 and args[:2] == ['reveal', '--prediction']:
        print(json.dumps(reveal(root, Path(args[2])), indent=2)); return 0
    raise ValueError('Usage: assignment.py nvarc prepare | nvarc reveal --prediction PATH')
