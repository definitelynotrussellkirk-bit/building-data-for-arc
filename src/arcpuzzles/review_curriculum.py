"""Optional reviewer observations, bound to bytes; never an approval or coverage gate."""
from __future__ import annotations

import hashlib
from pathlib import Path

AXES = ('multi_rule_interaction', 'sequential_state', 'contextual_gating', 'task_defined_symbols')
SUPPORT_SCOPES = ('production_lesson', 'generated_input', 'canonical_only', 'validator_only', 'proposed', 'unknown')


def bind_curriculum(value, *, task_id: str, generator: bytes, canonical: bytes,
                    rule_task_id: str, evidence: dict[str, str]) -> dict:
    """Normalize advisory claims. Unsupported present claims stay unknown, not fatal."""
    source = value if isinstance(value, dict) else {}
    supplied = source.get('axes', {})
    supplied = supplied if isinstance(supplied, dict) else {}
    axes, warnings, bound_evidence = {}, [], {}
    for name in AXES:
        raw = supplied.get(name, {})
        raw = raw if isinstance(raw, dict) else {}
        claimed = raw.get('status', 'unknown')
        status = claimed if claimed in ('present', 'not_applicable', 'unknown') else 'unknown'
        witness = raw.get('witness', '')
        rival = raw.get('rival', '')
        if status == 'present' and not all(isinstance(s, str) and s.strip() for s in (witness, rival)):
            status = 'unknown'
            warnings.append(f'{name}: present needs a concrete witness and rival; retained as unknown')
        paths = raw.get('evidence', [])
        paths = paths if isinstance(paths, list) else []
        for path in paths:
            if isinstance(path, str) and path in evidence:
                bound_evidence[path] = evidence[path]
            else:
                status = 'unknown'
                warnings.append(f'{name}: evidence not packaged: {path!r}; retained as unknown')
        scope = raw.get('support_scope', 'unknown')
        scope = scope if scope in SUPPORT_SCOPES else 'unknown'
        axes[name] = {'status': status, 'reported_status': claimed, 'support_scope': scope,
                      'witness': witness, 'rival': rival, 'evidence': paths}
    return {'schema': 'arcpuzzles-curriculum-annotation-v1', 'task_id': task_id,
            'generator_sha256': hashlib.sha256(generator).hexdigest(),
            'canonical_sha256': hashlib.sha256(canonical).hexdigest(), 'rule_task_id': rule_task_id,
            'axes': axes, 'notes': source.get('notes', ''), 'warnings': warnings,
            'evidence_sha256': bound_evidence, 'verification_status': 'reviewer_reported',
            'training_admitted': False}


def retained_curriculum(receipt: dict, root: Path) -> dict | None:
    """Keep old observations visible but label byte drift; absence means unreviewed."""
    annotation = (receipt.get('intake_summary') or {}).get('curriculum')
    if not isinstance(annotation, dict) or annotation.get('schema') != 'arcpuzzles-curriculum-annotation-v1':
        return None
    task_id = receipt['task_id']
    generator = root / 'generators' / task_id / 'generator.py'
    canonical = root / 'shared/data/canonical/puzzles.jsonl'
    matches = annotation.get('task_id') == task_id and all(
        path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == annotation.get(key)
        for path, key in ((generator, 'generator_sha256'), (canonical, 'canonical_sha256')))
    return {**annotation, 'source_status': 'current' if matches else 'stale',
            'return_id': f"{receipt['assignment_id']}:v{receipt['version']:04d}",
            'packet_id': receipt['packet_id'], 'return_zip_sha256': receipt['zip_sha256'],
            'verification_status': 'reviewer_reported', 'training_admitted': False}
