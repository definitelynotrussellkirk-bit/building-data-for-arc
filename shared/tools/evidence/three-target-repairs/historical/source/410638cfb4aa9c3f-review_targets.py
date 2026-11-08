"""Versioned repair-target normalization shared by packet producers and consumers."""
from __future__ import annotations

from pathlib import PurePosixPath
import re

MULTI_SCHEMA = 'arcpuzzles-full-assignment-v3'
POLICY_SCHEMA = 'arcpuzzles-repair-target-policy-v1'


def assignment_targets(contract: dict) -> list[dict]:
    """Return ordered target records; v3 is exactly three, primary first."""
    primary = {'task_id': contract.get('task_id'), 'generator': contract.get('generator')}
    if contract.get('schema') != MULTI_SCHEMA:
        return [primary]
    rows = contract.get('repair_targets')
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError('Three-target assignment requires exactly three repair_targets')
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'task_id', 'generator'}
                or not isinstance(row['task_id'], str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]*', row['task_id'])
                or not isinstance(row['generator'], dict)):
            raise ValueError('Invalid repair target record')
    if len({row['task_id'] for row in rows}) != 3 or rows[0] != primary:
        raise ValueError('Repair targets must be unique with the primary first')
    return rows


def target_ids(contract: dict) -> list[str]:
    return [row['task_id'] for row in assignment_targets(contract)]


def rule_task_ids(contract: dict) -> list[str]:
    return list(dict.fromkeys(row['generator']['rule_task_id'] for row in assignment_targets(contract)))


def target_for_path(path: str, contract: dict) -> dict | None:
    """Identify an assigned task home, without granting edit permission."""
    if not isinstance(path, str) or '\\' in path or '..' in PurePosixPath(path).parts:
        return None
    for row in assignment_targets(contract):
        if path.startswith(f"repo/generators/{row['task_id']}/"):
            return row
    return None


def validate_target_outcomes(contract: dict, results: dict) -> list[dict]:
    """Validate v3 target reports and return them in assignment order."""
    if contract.get('schema') != MULTI_SCHEMA:
        return []
    ids = target_ids(contract)
    rows = results.get('repair_targets')
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError('Results require exactly three repair target outcomes')
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or row.get('task_id') not in ids or row['task_id'] in by_id:
            raise ValueError('Invalid or duplicate repair outcome task')
        if not isinstance(row.get('outcome'), str) or row['outcome'] not in {'repaired', 'prototype', 'unchanged', 'blocked'}:
            raise ValueError('Invalid repair target outcome')
        if not isinstance(row.get('summary'), str) or not row['summary'].strip():
            raise ValueError('Repair outcome requires a nonempty summary')
        components = row.get('changed_components')
        if (not isinstance(components, list) or any(not isinstance(x, str) for x in components)
                or len(set(components)) != len(components)
                or set(components) - {'generator', 'racket', 'tests_notes'}):
            raise ValueError('Invalid repair changed_components')
        for name in ('evidence_paths', 'remaining_failures'):
            if not isinstance(row.get(name), list) or any(not isinstance(x, str) for x in row[name]):
                raise ValueError(f'Invalid repair {name}')
        by_id[row['task_id']] = row
    return [by_id[tid] for tid in ids]
