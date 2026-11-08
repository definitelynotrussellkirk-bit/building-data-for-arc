"""Read-only parametric authoring priority from supplied ARC task provenance.

An original-task relationship is ancestry, not current rule equivalence, source
approval or training admission. No generator or Racket program is executed here.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
from .catalog import Catalog, jsonl, local_path, sha256

SCHEMA = 'arcpuzzles-parametric-priority-v1'


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def _challenge(row):
    """Public challenge identity: demos and query inputs, never query answers."""
    def grid(value):
        if value and all(isinstance(r, str) for r in value):
            return [[int(c) for c in r] for r in value]
        return value
    tests = row.get('test', [])
    tests = [tests] if isinstance(tests, dict) else tests
    return {'train': [{'input': grid(p['input']), 'output': grid(p['output'])}
                      for p in row.get('train', [])],
            'test': [{'input': grid(p['input'])} for p in tests]}


def _prototype(root: Path, row: dict) -> dict:
    home = root / 'generators' / row['id']
    path = home / 'workspace/parametric/evidence/manifest.json'
    if not path.is_file():
        return {'status': 'missing'}
    try:
        if path.is_symlink():
            raise ValueError('symlink manifest')
        value = json.loads(path.read_text())
        if (value.get('task_id') != row['id']
                or value.get('generator_sha256') != row['generator_sha256']
                or value.get('canonical_rule_hash') != row['rule_hash']):
            raise ValueError('source_or_rule_changed')
        if value.get('verification_status') not in {'reviewer_reported', 'independently_checked'}:
            raise ValueError('unqualified_evidence')
        parameters = value.get('parameters')
        if (parameters is not None and (not isinstance(parameters, dict) or not parameters
                or any(not isinstance(v, list) or len(v) < 2 for v in parameters.values()))):
            raise ValueError('missing_bounded_alternatives')
        files = value.get('files')
        if not isinstance(files, list) or not files:
            raise ValueError('missing_evidence_inventory')
        for item in files:
            source = local_path(root, item['path'])
            if (not source.resolve().is_relative_to(home.resolve()) or source.is_symlink()
                    or not source.is_file() or sha256(source) != item['sha256']):
                raise ValueError('evidence_changed_or_missing')
        pending = value.get('public_identifier_status') == 'external_correction_pending'
        return {'status': 'needs_followup' if pending else 'current',
                **({'reason': 'public_identifier_correction_pending'} if pending else {}),
                'manifest': path.relative_to(root).as_posix(),
                'manifest_sha256': sha256(path), 'verification_status': value['verification_status'],
                'parameter_declaration': 'manifest' if parameters is not None else 'retained_evidence',
                'variant_approved': False}
    except (ValueError, KeyError, TypeError, OSError) as error:
        return {'status': 'stale', 'reason': str(error)}


def build_parametric_priority(catalog: Catalog, *, rows: list[dict] | None = None) -> dict:
    """Prefer reviewed original families needing a small rule prototype.

    Direct identity is checked against the supplied public challenge bytes.
    Reviewed lineage can establish an inspired variant; an old generator hash
    does not erase ancestry or grant semantic equivalence to its new source.
    """
    root = catalog.root
    rows = catalog.query() if rows is None else rows
    by_id = {r['id']: r for r in rows if r.get('generator')}
    supplied = {}
    by_challenge = {}
    source_files = {}
    split_counts = {}
    for split in ('training', 'evaluation'):
        relative = f'shared/data/raw/arc-agi_{split}_challenges.json'
        path = root / relative
        if not path.is_file():
            split_counts[split] = 0
            continue
        raw = json.loads(path.read_text())
        split_counts[split] = len(raw)
        source_files[relative] = sha256(path)
        for original, challenge in raw.items():
            if not re.fullmatch(r'[0-9a-f]{8}', original):
                raise ValueError(f'Invalid supplied task ID: {original}')
            digest = _digest(_challenge(challenge))
            origin = {'source_split': split, 'source_task_id': original,
                      'challenge_sha256': digest}
            supplied[(split, original)] = origin
            by_challenge.setdefault(digest, []).append(origin)
    canonical = root / 'shared/data/canonical/puzzles.jsonl'
    source_files['shared/data/canonical/puzzles.jsonl'] = sha256(canonical)
    source_files['catalog/puzzles.jsonl'] = sha256(root / 'catalog/puzzles.jsonl')
    origins = {}
    for value in jsonl(canonical):
        tid = value['task_id']
        if tid not in by_id:
            continue
        for origin in by_challenge.get(_digest(_challenge(value)), []):
            key = (origin['source_split'], origin['source_task_id'])
            origins.setdefault(tid, {})[key] = {**origin, 'basis': 'exact_public_challenge'}
    relative = 'shared/data/derived/official_generator_lineage.jsonl'
    lineage_path = root / relative
    rejected_lineage = []
    if lineage_path.is_file():
        source_files[relative] = sha256(lineage_path)
        for lineage in jsonl(lineage_path):
            tid = lineage.get('generator_id')
            if tid not in by_id or lineage.get('mapping_status') != 'verified':
                continue
            key = (lineage.get('source_split'), lineage.get('source_task_id'))
            original = supplied.get(key)
            if (original is None or lineage.get('source_hashes', {}).get('challenge_sha256')
                    != original['challenge_sha256']):
                rejected_lineage.append({'generator_id': tid, 'reason': 'supplied_challenge_not_bound'})
                continue
            origins.setdefault(tid, {}).setdefault(key, {
                **original, 'basis': 'reviewed_lineage',
                'relationship': lineage.get('relationship'),
                'lineage_path': relative,
                'current_generator_matches_lineage': lineage.get('source_hashes', {}).get('generator_sha256')
                                                     == by_id[tid]['generator_sha256']})
    related = {}
    tiers = {'approved_originals_need_parameters': [],
             'originals_need_repair_and_parameters': [], 'other_unapproved': []}
    normal = []
    blocked = []
    for tid, row in sorted(by_id.items()):
        eligible = (row.get('rule_hash') is not None
                    and 'ambiguous_canonical_rule' not in row.get('approval_reasons', []))
        if eligible and not row['approved']:
            normal.append(tid)
        if tid not in origins:
            continue
        prototype = _prototype(root, row)
        related[tid] = {'origins': [v for _, v in sorted(origins[tid].items())],
                        'generator_sha256': row['generator_sha256'], 'rule_hash': row['rule_hash'],
                        'approved': row['approved'], 'prototype': prototype,
                        'ancestry_only': True, 'training_admitted': False}
        if not eligible:
            blocked.append({'generator_id': tid, 'reason': 'unambiguous_canonical_rule_required'})
        if eligible and prototype['status'] != 'current':
            tier = ('approved_originals_need_parameters' if row['approved']
                    else 'originals_need_repair_and_parameters')
            tiers[tier].append(tid)
    prioritized = set(tiers['approved_originals_need_parameters'] + tiers['originals_need_repair_and_parameters'])
    tiers['other_unapproved'] = [tid for tid in normal if tid not in prioritized]
    selected = next((name for name, pool in tiers.items() if pool), 'other_unapproved')
    covered = {(v['source_split'], v['source_task_id']) for values in origins.values() for v in values.values()}
    missing = [{'source_split': s, 'source_task_id': t} for s, t in sorted(set(supplied) - covered)]
    # Choose the public parent before its descendants, so unmapped tasks and
    # families with fewer implementations still receive authoring attention.
    evaluation_anchors = []
    for (split, original), origin in sorted(supplied.items()):
        if split != 'evaluation':
            continue
        candidates = [tid for tid, rel in related.items()
                      if (split, original) in origins[tid] and by_id[tid].get('rule_hash') is not None
                      and 'ambiguous_canonical_rule' not in by_id[tid].get('approval_reasons', [])]
        pools = {
            'approved_need_parameters': [tid for tid in candidates if related[tid]['approved']
                                        and related[tid]['prototype']['status'] != 'current'],
            'need_repair_and_parameters': [tid for tid in candidates if not related[tid]['approved']
                                          and related[tid]['prototype']['status'] != 'current'],
            'related_improvement': candidates,
        }
        tier = next((name for name, pool in pools.items() if pool), 'inspired_extension')
        evaluation_anchors.append({**origin,
            'source_path': 'shared/data/raw/arc-agi_evaluation_challenges.json',
            'selected_tier': tier, 'main_ids': pools.get(tier, [])})
    evaluation_focus = {
        'schema': 'arcpuzzles-evaluation-focus-v1',
        'probability': {'numerator': 1, 'denominator': 10},
        'anchors': evaluation_anchors,
        'provided_tasks': len(evaluation_anchors),
        'mapped_tasks': sum(('evaluation', anchor['source_task_id']) in covered
                            for anchor in evaluation_anchors),
        'eligible_related_generators': len({tid for anchor in evaluation_anchors for tid in anchor['main_ids']}),
        'fallback': 'inspired_extension_on_normal_priority_target',
        'scope': 'Authoring focus only; proposed inspiration is not verified lineage, difficulty calibration or training admission.',
    }
    return {'schema': SCHEMA, 'policy': 'supplied_original_families_first',
            'selected_tier': selected, 'main_ids': tiers[selected], 'tiers': tiers,
            'provided_tasks': split_counts, 'provided_task_count': len(supplied),
            'covered_original_tasks': len(covered), 'unmapped_original_tasks': missing,
            'related_generators': related, 'rejected_lineage': rejected_lineage,
            'blocked_originals': blocked,
            'evaluation_focus': evaluation_focus,
            'counts': {'related_generators': len(related),
                       'current_prototypes': sum(r['prototype']['status'] == 'current' for r in related.values()),
                       **{name: len(pool) for name, pool in tiers.items()}},
            'source_files': source_files,
            'scope': 'Parametric authoring priority only. Ancestry is not current semantic equivalence, safety approval, rule-variant approval or training admission.'}
