"""Versioned repair-target normalization shared by packet producers and consumers."""
from __future__ import annotations

from pathlib import PurePosixPath
import re
from .review_public_creation import PUBLIC_WORK_POLICY, PUBLIC_LEGACY_WORK_POLICY, PUBLIC_WORK_SCHEMA

MULTI_SCHEMA = 'arcpuzzles-full-assignment-v3'
POLICY_SCHEMA = 'arcpuzzles-repair-target-policy-v1'
MAIN_WORK_SCHEMA = 'arcpuzzles-parametric-main-two-checks-v1'
MAIN_WORK_POLICY = {'schema': MAIN_WORK_SCHEMA, 'effort_percent': [70, 15, 15],
               'roles': ['parametric_main', 'robustness_check', 'robustness_check'],
               'demonstration_range': [2, 6], 'training_queries': 4,
               'query_visibility': 'sequential_without_total_count_hint'}
WORK_SCHEMA = 'arcpuzzles-three-parametric-targets-v1'
WORK_POLICY = {'schema': WORK_SCHEMA, 'roles': ['parametric', 'parametric', 'parametric'],
               'demonstration_range': [2, 6], 'training_queries': 4,
               'query_visibility': 'sequential_without_total_count_hint'}

ADMISSION_WORK_SCHEMA = 'arcpuzzles-parametric-main-admission-v1'
ADMISSION_WORK_POLICY = {'schema': ADMISSION_WORK_SCHEMA,
    'roles': ['parametric_main', 'adversarial_check', 'adversarial_check'],
    'priority': 'finish_main_then_peers_with_remaining_time',
    'peer_work': 'optional_unverified_help', 'peer_integration': 'owner_checked_only',
    'completion': 'native_owner_accepted', 'demonstration_range': [2, 6],
    'training_queries': 4, 'query_visibility': 'sequential_without_total_count_hint'}

TWO_WORK_SCHEMA = 'arcpuzzles-two-parametric-admissions-v1'
TWO_WORK_POLICY = {'schema': TWO_WORK_SCHEMA, 'roles': ['parametric', 'parametric'],
    'priority': 'finish_and_self_review_each_before_next', 'peer_work': 'none',
    'completion': 'both_native_owner_accepted', 'demonstration_range': [2, 6],
    'training_queries': 4, 'query_visibility': 'sequential_without_total_count_hint'}
ONE_WORK_SCHEMA = 'arcpuzzles-one-parametric-admission-v1'
ONE_WORK_POLICY = {'schema': ONE_WORK_SCHEMA, 'roles': ['parametric'],
    'priority': 'build_then_deep_adversarial_repair', 'peer_work': 'none',
    'completion': 'native_owner_accepted', 'demonstration_range': [2, 6],
    'training_queries': 4, 'query_visibility': 'sequential_without_total_count_hint'}
NATIVE_WORK_SCHEMAS = {ADMISSION_WORK_SCHEMA, TWO_WORK_SCHEMA, ONE_WORK_SCHEMA}


def validate_work_policy(contract: dict, manifest: dict) -> None:
    from .review_base_preflight import POLICY as BASE_REVIEW_POLICY
    base = manifest.get('base_review_policy')
    if (contract.get('base_review_policy') != base
            or base is not None and base != BASE_REVIEW_POLICY):
        raise ValueError('Assignment base review policy differs from packet')
    expected = manifest.get('work_policy')
    if (contract.get('work_policy') != expected
            or expected is not None and expected not in (MAIN_WORK_POLICY, WORK_POLICY, ADMISSION_WORK_POLICY, TWO_WORK_POLICY, ONE_WORK_POLICY, PUBLIC_WORK_POLICY, PUBLIC_LEGACY_WORK_POLICY)):
        raise ValueError('Assignment work policy differs from packet')


def parametric_target_ids(contract: dict) -> list[str]:
    """Frozen work roles, independent of legacy primary/secondary draw naming."""
    schema = contract.get('work_policy', {}).get('schema')
    if schema in {WORK_SCHEMA, TWO_WORK_SCHEMA, ONE_WORK_SCHEMA, PUBLIC_WORK_SCHEMA}:
        return target_ids(contract)
    if schema in {MAIN_WORK_SCHEMA, ADMISSION_WORK_SCHEMA}:
        return target_ids(contract)[:1]
    return []


def assignment_targets(contract: dict) -> list[dict]:
    """Return frozen one-, two- or three-target native assignments."""
    primary = {'task_id': contract.get('task_id'), 'generator': contract.get('generator')}
    if contract.get('schema') != MULTI_SCHEMA:
        return [primary]
    rows = contract.get('repair_targets')
    schema = contract.get('work_policy', {}).get('schema')
    count = 1 if schema == ONE_WORK_SCHEMA else 2 if schema in {TWO_WORK_SCHEMA, PUBLIC_WORK_SCHEMA} else 3
    if not isinstance(rows, list) or len(rows) != count:
        name = {1: "one", 2: "two", 3: "three"}[count]
        raise ValueError(f"Assignment requires exactly {name} repair_targets")
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'task_id', 'generator'}
                or not isinstance(row['task_id'], str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]*', row['task_id'])
                or not isinstance(row['generator'], dict)):
            raise ValueError('Invalid repair target record')
    if len({row['task_id'] for row in rows}) != count or rows[0] != primary:
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
    if not isinstance(rows, list) or len(rows) != len(ids):
        raise ValueError(f'Results require exactly {len(ids)} repair target outcomes')
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
    ordered = [by_id[tid] for tid in ids]
    creation = contract.get('work_policy', {}).get('schema') == PUBLIC_WORK_SCHEMA
    admission = contract.get('work_policy', {}).get('schema') in NATIVE_WORK_SCHEMAS or creation
    parametric_ids = parametric_target_ids(contract)
    for row in ordered:
        if row['task_id'] not in parametric_ids:
            continue
        progress = row.get('parametric_work')
        if (not isinstance(progress, dict) or progress.get('status') not in ({'ready', 'blocked'} if admission else {'built', 'improved', 'blocked'})
                or not isinstance(progress.get('summary'), str) or not progress['summary'].strip()):
            required = "native ready/blocked status" if admission else "status"
            raise ValueError(f"Target {row['task_id']} parametric work requires a {required} and concrete summary")
        prototype = progress.get('prototype_path')
        if progress['status'] in {'built', 'improved', 'ready'}:
            home = f"repo/generators/{row['task_id']}/workspace/parametric/"
            if (not isinstance(prototype, str) or not prototype.startswith(home)
                    or '..' in PurePosixPath(prototype).parts or '\\' in prototype
                    or not row['evidence_paths']):
                raise ValueError('Parametric deliverable requires its task-local prototype and evidence')
        elif prototype is not None:
            raise ValueError('Blocked parametric work must not declare a completed prototype')
        if admission and progress['status'] == 'ready':
            for name, expected in (('promotion_path', home + 'promotion.json'),
                                   ('inventory_path', home + 'evidence/manifest.json')):
                if progress.get(name) != expected:
                    raise ValueError('Native ready deliverable requires task-local ' + name)
            evidence_key = 'preflight_path' if creation else 'qualification_path'
            path = progress.get(evidence_key)
            if (not isinstance(path, str) or not path.startswith('checks/')
                    or '..' in PurePosixPath(path).parts or '\\' in path
                    or not path.endswith('/preflight.json' if creation else '/qualification.json') or path not in row['evidence_paths']):
                raise ValueError('Native ready deliverable requires packaged qualification evidence')
        if admission and progress['status'] == 'ready':
            dependency = progress.get('sequential_dependency')
            if (not isinstance(dependency, dict) or any(
                    not isinstance(dependency.get(key), str) or not dependency[key].strip()
                    for key in ('step_a', 'intermediate', 'step_b', 'why_b_depends_on_a', 'witness_path'))):
                raise ValueError('Main requires a named sequential dependency A/intermediate/B and witness')
            witness = dependency['witness_path']
            if (not witness.startswith('checks/') or '..' in PurePosixPath(witness).parts
                    or '\\' in witness or not witness.endswith('.json') or witness not in row['evidence_paths']):
                raise ValueError('Main sequential dependency requires packaged witness evidence')
        if admission and results.get('completion_state') == 'complete' and progress['status'] != 'ready':
            raise ValueError('Complete return requires native ready main; blocked work leaves the objective unmet')
    if contract.get('work_policy', {}).get('schema') in {MAIN_WORK_SCHEMA, ADMISSION_WORK_SCHEMA}:
        if any('parametric_work' in row for row in ordered[1:]):
            raise ValueError('Secondary robustness checks must not report parametric work')
    return ordered
