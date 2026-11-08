"""Bounded, reproducible supplementary reviewer tickets; legacy audits opt out."""
from __future__ import annotations

import copy
import hashlib
import math
import json
from pathlib import Path, PurePosixPath

TICKET_POLICY = {
    'schema': 'arcpuzzles-supplementary-ticket-policy-v1',
    'count': 2,
    'weights': {'adversarial_witness': 35, 'audit_replay': 20, 'api_boundary': 15,
                'parameter_queries': 10, 'tool_reproduction': 10, 'allocation_quality': 10},
    'weight_basis': 'initial heuristics, not measured optimal allocation',
    'sampling': 'eligible types weighted without replacement; unavailable types excluded and weights renormalized',
    'budget': {'authoring_minutes': 10, 'targeted_probe_seconds': 120, 'targeted_probes': 1},
}
SAFETY_TYPES = {'adversarial_witness', 'audit_replay', 'api_boundary'}
CONSUMERS = {'adversarial_witness': 'target_current_audit', 'audit_replay': 'existing_audit_assessment',
             'api_boundary': 'target_current_audit', 'parameter_queries': 'task_support_or_prototype_followup',
             'tool_reproduction': 'existing_tool_request_disposition',
             'allocation_quality': 'bounded_owner_allocation_experiment_proposal',
             'nvarc_visual': 'dataset_current_assessment'}
INSTRUCTIONS = {
    'adversarial_witness': 'Inspect one plausible shortcut and retain one lawful witness or a bounded unknown; no full peer battery or census.',
    'audit_replay': 'Reproduce the pinned existing audit witness using its retained source/asset identity. Report whether that bounded claim reproduced; do not clear an audit automatically.',
    'api_boundary': 'Inspect one advertised API/override boundary; use one minimal valid/invalid call comparison and retain actual behavior.',
    'parameter_queries': 'Inspect the pinned parameter evidence or four-query support. Check one relevant setting/count/privacy boundary; keep support and variant approval separate.',
    'tool_reproduction': 'Inspect/reproduce the pinned tool request using its retained assets. Return evidence and a proposed request disposition; do not implement unrelated shared changes.',
    'allocation_quality': 'Use the ticket seed to sample up to three current records. Read TRAINING-CONTEXT.md as dated context and verify relevant source identities/freshness. Inspect actual draw pools/focus and catalog weights; compare representation, teachability, parameter/four-query coverage with review, Racket and deduplication cost. Inspect source-specific linter/rejection/repair/ambiguity/grammar evidence where present, including ARC-GEN or RE-ARC; provenance alone guarantees no quality. Compare one alternative allocation by estimated quality per cost and propose a bounded test/stopping rule; label estimates and coverage gaps. High loss alone is not a defect; proposed prototypes are separate from production capability.',
    'nvarc_visual': 'Review only the ONE pinned NVARC file: run python3 assignment.py nvarc prepare. See pairs 0–3 only, save prediction.json with a one-sentence rule and exact predicted_output for pair 4 BEFORE running python3 assignment.py nvarc reveal --prediction prediction.json. Compare pair 4, then skim pairs 5 through the actual end (13–30 total). Three authoring minutes; no heavy probe, Racket, source program or source edits. Give one verdict ok/ambiguous/inconsistent/trivial/broken, or blocked/uncertain under status blocked/unknown. Unknown is valid; do not turn uncertainty into invented ambiguity/noise. No catalog import, generator approval or training admission. Put the returned proof paths in evidence_paths and nvarc_review with exactly file, sha256, verdict, rule, predicted_ok, bad_pairs, minutes, note.',
}


def _policy_template(optional=False):
    policy = copy.deepcopy(TICKET_POLICY)
    if optional:
        policy['schema'] = 'arcpuzzles-supplementary-ticket-policy-v2'
        policy['weights']['nvarc_visual'] = 5
    return policy


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _asset(manifest, path, expected=None):
    # Audit indexes use a path plus a sibling hash; proposal rows use a
    # nested {path, sha256} binding. Neither shape may bypass the hash pin.
    if isinstance(path, dict):
        nested_hash = path.get('sha256')
        if not isinstance(nested_hash, str) or (expected and expected != nested_hash):
            return None
        expected, path = nested_hash, path.get('path')
    if not isinstance(path, str) or not path:
        return None
    path = path if path.startswith('repo/') else 'repo/' + path
    digest = manifest['files'].get(path)
    if not digest or (expected and digest != expected):
        return None
    return {'path': path, 'sha256': digest}


def build_ticket_policy(manifest: dict, source_files: dict[str, Path] | None = None) -> dict:
    """Bind candidates only to included bytes; pass projected logical source files."""
    source_files = source_files or {}
    candidates = {kind: [] for kind in TICKET_POLICY['weights']}
    def read_source(name):
        raw = source_files[name].read_bytes()
        if _hash(raw) != manifest['files'].get(name):
            raise ValueError(f'Ticket metadata source changed: {name}')
        return json.loads(raw)
    for tid in sorted(manifest['all_ids']):
        row = manifest['generators'][tid]
        source = _asset(manifest, row['generator'], row['generator_sha256'])
        if source is None:
            raise ValueError(f'Ticket generator source absent: {tid}')
        base = {'task_id': tid, 'generator_sha256': row['generator_sha256'],
                'rule_hash': row['rule_hash'], 'rule_task_id': row['rule_task_id'], 'source': source}
        for kind in ('adversarial_witness', 'api_boundary', 'allocation_quality'):
            candidates[kind].append(dict(base))
        index_path = f'repo/generators/{tid}/evidence/review_index.json'
        index = source_files.get(index_path)
        if index is not None:
            for audit in read_source(index_path).get('audits', []):
                if audit.get('resolution') in {'resolved', 'no_issue'}:
                    continue
                asset = _asset(manifest, audit.get('assets_manifest', ''), audit.get('assets_manifest_sha256'))
                if asset is not None:
                    candidates['audit_replay'].append({**base, 'audit_return_id': audit['return_id'],
                        'audited_generator_sha256': audit['source_sha256'],
                        'audit_record_sha256': _hash(_json(audit)), 'assets_manifest': asset,
                        'audit_index': _asset(manifest, index_path)})
        parameter_path = f'repo/generators/{tid}/workspace/parametric/evidence/manifest.json'
        parameter = source_files.get(parameter_path)
        if parameter is not None:
            value = read_source(parameter_path)
            if value.get('generator_sha256') == row['generator_sha256']:
                candidates['parameter_queries'].append({**base, 'evidence_manifest': _asset(manifest, parameter_path)})
    suggestions_path = 'repo/REVIEW/suggestions.json'
    suggestions = source_files.get(suggestions_path)
    if suggestions is not None:
        for request in read_source(suggestions_path).get('items', []):
            if request.get('status') in {'implemented', 'declined'}:
                continue
            asset = _asset(manifest, request.get('assets_manifest', ''), request.get('assets_manifest_sha256'))
            if asset is not None:
                item = {'request_id': request['request_id'],
                        'request_sha256': _hash(_json(request)), 'request_source': _asset(manifest, suggestions_path),
                        'assets_manifest': asset}
                tid = request.get('generator_id')
                if tid is not None:
                    if tid not in manifest['generators']:
                        continue
                    row = manifest['generators'][tid]
                    item.update(task_id=tid, generator_sha256=row['generator_sha256'],
                                rule_hash=row['rule_hash'], rule_task_id=row['rule_task_id'])
                candidates['tool_reproduction'].append(item)
    candidates = {k: v for k, v in candidates.items() if v}
    from .review_nvarc import ARCHIVE_PATH, ARCHIVE_SHA256, TYPE, archive_candidates
    optional = ARCHIVE_PATH in source_files
    if optional:
        if manifest['files'].get(ARCHIVE_PATH) != ARCHIVE_SHA256:
            raise ValueError('NVARC archive hash differs from pinned sample')
        candidates[TYPE] = archive_candidates(source_files[ARCHIVE_PATH])
    if len(candidates) < 2:
        raise ValueError('Supplementary tickets need at least two eligible types')
    return {**_policy_template(optional), 'candidates': candidates}


def supplementary_contract(manifest: dict, packet_id: str, main: dict,
                           seed: bytes, blind_id: str | None = None) -> dict:
    if not isinstance(seed, bytes) or len(seed) != 32:
        raise ValueError('Ticket seed must be exactly 32 bytes')
    policy = manifest.get('supplementary_ticket_policy', {})
    template = _policy_template(policy.get('schema') == 'arcpuzzles-supplementary-ticket-policy-v2')
    if any(policy.get(key) != value for key, value in template.items()):
        raise ValueError('Unknown supplementary ticket policy')
    # Main work may already have changed its generator/prototype bytes. Peer
    # tickets use untouched pinned sources and must not reassign that work.
    excluded = {tid for tid in (blind_id, main.get('task_id')) if tid is not None}
    candidates = {kind: [row for row in rows if row.get('task_id') not in excluded]
                  for kind, rows in policy['candidates'].items() if kind in template['weights']}
    candidates = {kind: rows for kind, rows in candidates.items() if rows}
    if len(candidates) < 2:
        raise ValueError('Too few eligible ticket types after excluding blind task')
    # A first target must leave a distinct target available for a different
    # type. This prevents old-source audit replay and current-source API work
    # from collapsing into one task's conflicting source identity at intake.
    def compatible(left, right):
        return left.get('task_id') is None or right.get('task_id') is None or left['task_id'] != right['task_id']
    feasible = {kind: [row for row in rows if any(
        compatible(row, other) for other_kind, others in candidates.items()
        if other_kind != kind for other in others)] for kind, rows in candidates.items()}
    candidates = {kind: rows for kind, rows in feasible.items() if rows}
    if len(candidates) < 2:
        raise ValueError('Two supplementary tickets need distinct peer target identities')
    eligible = {kind: template['weights'][kind] for kind in template['weights'] if kind in candidates}
    weights = dict(eligible)
    tickets = []
    for slot in range(2):
        used_targets = {ticket['task_id'] for ticket in tickets if ticket.get('task_id') is not None}
        available = {kind: [row for row in candidates[kind] if row.get('task_id') not in used_targets]
                     for kind in weights}
        weights = {kind: weight for kind, weight in weights.items() if available[kind]}
        if not weights:
            raise ValueError('Two supplementary tickets need distinct peer target identities')
        roll = int.from_bytes(hashlib.sha256(seed + f':ticket-type:{slot}'.encode()).digest(), 'big') % sum(weights.values())
        for kind, weight in weights.items():
            if roll < weight:
                break
            roll -= weight
        rows = available[kind]
        index = int.from_bytes(hashlib.sha256(seed + f':ticket-target:{slot}'.encode()).digest(), 'big') % len(rows)
        selected = dict(rows[index])
        ticket_seed = _hash(seed + f':ticket-probe:{slot}'.encode())
        ticket = {**selected, 'type': kind, 'seed': ticket_seed, 'consumer': CONSUMERS[kind],
                  'budget': dict(TICKET_POLICY['budget'])}
        if kind == 'nvarc_visual':
            from .review_nvarc import BUDGET
            ticket['budget'] = dict(BUDGET)
        ticket['ticket_id'] = 'ticket-' + _hash(_json({'packet_id': packet_id,
            'assignment_id': main['assignment_id'], 'slot': slot, **ticket}))[:16]
        tickets.append(ticket)
        del weights[kind]
    return {'schema': 'arcpuzzles-full-audit-v4', 'packet_id': packet_id,
            'assignment_id': main['assignment_id'], 'seed': seed.hex(), 'tickets': tickets,
            'eligible_weights': eligible, 'eligible_weight_total': sum(eligible.values()),
            'targets': [{'task_id': t['task_id'], 'generator_sha256': t.get('audited_generator_sha256', t['generator_sha256'])}
                        for t in tickets if t['type'] in SAFETY_TYPES]}


def validate_ticket_reports(contract: dict, reports: object, names: set[str], *, read_member=None) -> list[dict]:
    if not isinstance(reports, list) or len(reports) != 2:
        raise ValueError('Exactly two supplementary ticket reports are required')
    tickets = {ticket['ticket_id']: ticket for ticket in contract['tickets']}
    seen = set()
    for report in reports:
        if not isinstance(report, dict) or report.get('ticket_id') not in tickets or report['ticket_id'] in seen:
            raise ValueError('Unknown or repeated supplementary ticket report')
        ticket = tickets[report['ticket_id']]
        seen.add(report['ticket_id'])
        if (report.get('type') != ticket['type'] or report.get('status') not in {'completed', 'finding', 'blocked', 'unknown'}
                or not isinstance(report.get('summary'), str) or not report['summary'].strip()):
            raise ValueError('Invalid supplementary ticket report')
        if report['status'] == 'finding' and ticket['type'] not in SAFETY_TYPES:
            raise ValueError('Non-safety ticket cannot create a safety audit')
        paths = report.get('evidence_paths')
        if not isinstance(paths, list) or any(not isinstance(path, str) or path not in names for path in paths):
            raise ValueError('Supplementary ticket evidence is not packaged')
        elapsed = report.get('elapsed_minutes')
        if elapsed is not None and (type(elapsed) not in {int, float} or elapsed < 0 or not math.isfinite(elapsed)):
            raise ValueError('Invalid ticket elapsed time; use null when unknown')
        if ticket['type'] == 'nvarc_visual':
            from .review_nvarc import validate_report
            validate_report(ticket, report, names, read_member)
    return reports


def ticket_safety_targets(contract: dict, reports: list[dict]) -> list[dict]:
    findings = {r['ticket_id'] for r in reports if r.get('status') == 'finding'}
    return list({t['task_id']: {'task_id': t['task_id'], 'generator_sha256': t.get('audited_generator_sha256', t['generator_sha256'])}
                 for t in contract['tickets'] if t['ticket_id'] in findings and t['type'] in SAFETY_TYPES}.values())


def ticket_report_rows(contract: dict, reports: list[dict]) -> list[dict]:
    by_id = {r['ticket_id']: r for r in reports}
    return [{'ticket': ticket, 'report': by_id[ticket['ticket_id']],
             'verification_status': 'reviewer_reported', 'automatic_policy_change': False}
            for ticket in contract['tickets']]


def ticket_duties(contract: dict) -> str:
    lines = ['# Two bounded supplementary tickets', '',
             'Work only these two selected tickets. Use each pinned budget; ordinary tickets allow at most ten authoring minutes and one targeted probe of up to 120 seconds. NVARC allows three minutes and no heavy probe.',
             'Blocked or unknown is valid; record the reason. No peer battery, large census or model job is required.',
             'Keep timings unknown (null) unless actually measured/reported. Do not fabricate a no-issue safety record.', '']
    for ticket in contract['tickets']:
        lines += [f"## {ticket['ticket_id']} — {ticket['type']}",
                  f"Consumer: `{ticket['consumer']}`. Probe seed: `{ticket['seed']}`.",
                  INSTRUCTIONS[ticket['type']], 'Pinned identity: `' + json.dumps(ticket, sort_keys=True) + '`', '']
    lines += ['Write exactly these two rows in `RESULTS.json` under `supplementary_tickets`: each row has `ticket_id`, `type`, `status` (completed/finding/blocked/unknown), `summary`, `evidence_paths`, and `elapsed_minutes` (number or null).',
              'The structured rows retain each ticket outcome for its stated consumer. General `FEEDBACK_TO_CODEX.md` is optional; add substantive extra feedback rather than repeating the rows. Only an actual peer safety finding uses status `finding` and a `## TASK_ID` section in `AUDIT.md`; otherwise omit that file. Evidence stays under `checks/tickets/TICKET_ID/`. Findings remain source-bound and unverified until maintainer assessment.']
    return '\n'.join(lines) + '\n'


def copied_transport_path(name: str) -> bool:
    """New returns carry deltas/evidence, never a copied distribution/runtime."""
    path = PurePosixPath(name)
    parts = path.parts
    return (path.name in {'RUNTIME_MANIFEST.json', 'request.zip', 'original.zip', 'PACKET-MANIFEST.json'}
            or path.name.startswith(('SEND-THIS-', 'racket-minimal-'))
            or any(part in {'repo', 'WORK', 'site-packages', 'puzzle_generators', 'arc_repl', 'vendor', '.git'}
                   or part.startswith(('.venv', 'runtime')) for part in parts[:-1]))
