"""New-policy return binding and mandatory native owner admission.

Reviewer qualification is input evidence, never an acceptance authority. The
owner replays the existing native qualification/acceptance path on live bytes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

from .catalog import Catalog, sha256
from .review_public_creation import PUBLIC_WORK_SCHEMA
from .review_targets import ADMISSION_WORK_SCHEMA, TWO_WORK_SCHEMA, NATIVE_WORK_SCHEMAS, assignment_targets
from . import review_evidence_bundle as bundles


def evidence_reader(archive, paths):
    """Read only requested, hash-verified evidence, including compact bundles."""
    names = set(archive.namelist())
    retained = {}
    if bundles.MANIFEST in names:
        manifest = bundles.read_manifest(archive.read(bundles.MANIFEST))
        selected = set(paths) & {r['path'] for r in manifest['files']}
        retained = bundles.verify(archive.read(bundles.ARCHIVE), manifest, retain=selected) or {}
    return lambda name: retained[name] if name in retained else archive.read(name)


def validate_ready_evidence(contract, progress, read, inventory):
    """Bind ready metadata to real packaged native qualification and source names.

    Static validation does not execute patched code. Exact source bytes are
    compared again on the integrated live tree before native owner execution.
    """
    tid = contract['task_id']
    for name in ('promotion_path', 'inventory_path'):
        if progress[name] not in inventory:
            raise ValueError('Native deliverable absent from bound source: ' + progress[name])
    q = json.loads(read(progress['qualification_path']))
    if not isinstance(q, dict):
        raise ValueError('Native qualification must be an object')
    binding = q.get('source_binding', {})
    promotion = q.get('contract', {})
    if not isinstance(binding, dict) or not isinstance(promotion, dict):
        raise ValueError('Invalid native source binding or contract')
    adapter = promotion.get('adapter')
    from .review_base_preflight import SCHEMA as AUTHORING_SCHEMA, POLICY as BASE_REVIEW_POLICY
    authoring = q.get('schema') == AUTHORING_SCHEMA
    if authoring and (contract.get('base_review_policy') != BASE_REVIEW_POLICY
            or q.get('status') != 'passed' or q.get('owner_accepted') is not False
            or q.get('verification_status') != 'authoring_preflight_not_owner_qualification'):
        raise ValueError('Base authoring preflight requires explicit whole-pool assignment policy')
    if ((not authoring and (q.get('schema') != 'arcpuzzles-parametric-qualification-v1' or q.get('status') != 'qualified'))
            or q.get('task_id') != tid
            or binding.get('task_id') != tid
            or promotion.get('schema') != 'arcpuzzles-parametric-adapter-v1'
            or not isinstance(adapter, str)
            or not adapter.startswith(f'generators/{tid}/workspace/parametric/')
            or 'repo/' + adapter not in inventory):
        raise ValueError('Invalid native qualification or adapter source binding')
    files = binding.get('files')
    if not isinstance(files, list) or not files:
        raise ValueError('Native qualification lacks source inventory')
    for row in files:
        if not isinstance(row, dict):
            raise ValueError('Invalid native source inventory row')
        name = row.get('path')
        if (not isinstance(name, str) or 'repo/' + name not in inventory
                or '..' in PurePosixPath(name).parts or '\\' in name
                or not isinstance(row.get('sha256'), str) or len(row['sha256']) != 64):
            raise ValueError('Native qualification cites unbound source')
    paths = {r['path'] for r in files}
    if not {adapter, progress['promotion_path'].removeprefix('repo/')} <= paths:
        raise ValueError('Native qualification omits adapter or promotion source')
    execution = q.get('execution', {})
    if not isinstance(execution, dict) or execution.get('path') != 'execution.json':
        raise ValueError('Native qualification requires sibling execution.json')
    execution_path = str(PurePosixPath(progress['qualification_path']).parent / 'execution.json')
    if hashlib.sha256(read(execution_path)).hexdigest() != execution.get('sha256'):
        raise ValueError('Native qualification execution evidence hash differs')
    if authoring:
        base = json.loads(read(execution_path)).get('base_review', {})
        if base.get('status') != 'passed' or not base.get('pairs') or len(base.get('generation', [])) != 2:
            raise ValueError('Base authoring preflight requires original pairs and two ordinary generation checks')
    return q


def validate_sequential_witness(progress, qualification, read):
    """Bind reported causal evidence; this is not a universal depth proof."""
    dependency = progress['sequential_dependency']
    witness = json.loads(read(dependency['witness_path']))
    if (not isinstance(witness, dict)
            or witness.get('schema') != 'arcpuzzles-sequential-dependency-witness-v1'
            or witness.get('source_binding') != qualification['source_binding']
            or witness.get('racket') != {'backend': 'racket', 'protected': True}):
        raise ValueError('Sequential witness must bind exact qualified source and protected Racket evidence')
    for key in ('step_a', 'intermediate', 'step_b', 'why_b_depends_on_a'):
        if witness.get(key) != dependency[key]:
            raise ValueError('Sequential witness differs from the named dependency')
    cases = witness.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 16:
        raise ValueError('Sequential witness requires 1..16 bounded cases')
    for case in cases:
        if (not isinstance(case, dict) or any(key not in case for key in
                ('input', 'settings', 'intermediate_value', 'output', 'counterfactual_output'))
                or case.get('ablation') not in {'skip_a', 'wrong_intermediate', 'wrong_order'}
                or not case['output'] or not case['counterfactual_output']
                or case['output'] == case['counterfactual_output']
                or any(not isinstance(case.get(key), str) or not case[key].strip()
                       for key in ('program', 'counterfactual_program'))):
            raise ValueError('Sequential witness needs a Racket-backed counterfactual changing final output')
        setting_key = json.dumps(case['settings'], sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        if hashlib.sha256(case['program'].encode()).hexdigest() != qualification.get('programs', {}).get(setting_key):
            raise ValueError('Sequential witness program is not a qualified setting program')
    return {'status': 'source_bound_reviewer_reported', 'cases': len(cases),
            'witness_sha256': hashlib.sha256(read(dependency['witness_path'])).hexdigest(),
            'limits': 'Bounded authored causal cases; native qualification does not prove universal algorithmic depth.'}


def qualification_demo_count(native_contract, requested=None):
    """Use the family's declared count/minimum, or an explicit verified request."""
    bounds = native_contract.get('limits', {}).get('demos')
    if (type(bounds) is not list or len(bounds) != 2
            or any(type(v) is not int for v in bounds)
            or not 1 <= bounds[0] <= bounds[1] <= 32):
        raise ValueError('Native contract needs valid demonstration limits')
    count = native_contract.get('qualification_demos', bounds[0]) if requested is None else requested
    if type(count) is not int or not bounds[0] <= count <= bounds[1]:
        raise ValueError(f'Demonstrations must be an integer in {bounds[0]}..{bounds[1]}')
    return count


def admit_main(catalog, contract, target_report, archive_path, *, withheld_paths=()):
    """Execute native admission only for the new policy, preserving honest failures."""
    if contract.get('work_policy', {}).get('schema') not in NATIVE_WORK_SCHEMAS:
        return None
    from . import parametric_promotion as promotion
    tid = contract['task_id']
    result = {'schema': 'arcpuzzles-review-parametric-admission-v1',
              'assignment_id': contract['assignment_id'], 'task_id': tid,
              'status': 'blocked', 'objective_met': False, 'training_admitted': False,
              'verification_status': 'owner_native_admission',
              'return_sha256': sha256(Path(archive_path))}
    progress = target_report.get('parametric_work', {})
    try:
        if progress.get('status') != 'ready':
            raise ValueError('Main not ready: ' + str(progress.get('summary', 'No deliverable')))
        if withheld_paths:
            raise ValueError('Main source paths withheld from integration: ' + ', '.join(withheld_paths))
        live = Catalog(catalog.root)
        native, binding = promotion._ready(live, tid)
        qpath = progress['qualification_path']
        epath = str(PurePosixPath(qpath).parent / 'execution.json')
        with zipfile.ZipFile(archive_path) as archive:
            read = evidence_reader(archive, [qpath, epath, progress['sequential_dependency']['witness_path']])
            # Every live binding file must also be in this exact native report.
            inventory = {'repo/' + r['path'] for r in binding['files']}
            inventory.add(progress['inventory_path'])
            reported = validate_ready_evidence(contract, progress, read, inventory)
            result['sequential_dependency'] = validate_sequential_witness(progress, reported, read)
            witness = json.loads(read(progress['sequential_dependency']['witness_path']))
        if reported['source_binding'] != binding or reported['contract'] != native:
            raise ValueError('Returned qualification differs from exact integrated live source binding')
        from .review_sequential_replay import replay_witness
        result['sequential_dependency']['owner_execution'] = replay_witness(catalog.root, witness)
        if promotion._ready(Catalog(catalog.root), tid)[1] != binding:
            raise ValueError('Main source changed during witness replay')
        # The inventory is executable readiness input, already checked by _ready.
        result['source_binding'] = binding
        base = catalog.root / 'var/review/main-parametric-admission'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=tid + '-', dir=base) as directory:
            counts = {job['demos'] for job in reported['jobs']}
            if len(counts) != 1:
                raise ValueError('Returned native qualification must declare one verified demo count')
            demos = qualification_demo_count(native, next(iter(counts)))
            if not 2 <= demos <= 6:
                raise ValueError('New MAIN admission requires a supported demo count within 2..6')
            qualified = promotion.qualify(live, tid, Path(directory) / 'qualification', demos=demos)
            if qualified['source_binding'] != binding:
                raise ValueError('Main source changed after witness replay')
            if reported.get('programs') != qualified['programs']:
                raise ValueError('Returned program map differs from fresh native qualification')
            accepted = promotion.accept(live, tid, Path(qualified['receipt']),
                                        reason='New-policy main deliverable: owner qualification and fresh acceptance replay')
        current = promotion.status(Catalog(catalog.root), tid)
        if accepted.get('status') != 'accepted' or current.get('status') != 'accepted':
            raise ValueError('Native acceptance did not remain current')
        result.update(status='accepted', objective_met=True,
                      acceptance_sha256=current['acceptance_sha256'])
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        result.update(blocker=f'{type(exc).__name__}: {exc}',
                      next_action='Repair this main native deliverable on its current source, rerun qualification, and retry owner admission; objective remains unmet.')
    path = catalog.root / f'generators/{tid}/evidence/parametric-admission-current.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    temporary.replace(path)
    return {**result, 'evidence_path': str(path)}


def admit_assignment(catalog, contract, outcomes, archive_path, *, withheld_paths=None,
                     selected_targets=None):
    """Admit each required native build; partial acceptance never completes a pair."""
    withheld = withheld_paths or {}
    schema = contract.get('work_policy', {}).get('schema')
    if schema not in NATIVE_WORK_SCHEMAS | {PUBLIC_WORK_SCHEMA}:
        return None
    def unselected(tid):
        return {'task_id': tid, 'status': 'not_selected', 'objective_met': False,
                'training_admitted': False,
                'blocker': 'Owner withheld this target for separate reconciliation; existing accepted source is unchanged.'}
    if schema not in {TWO_WORK_SCHEMA, PUBLIC_WORK_SCHEMA}:
        if selected_targets is not None and contract['task_id'] not in selected_targets:
            return unselected(contract['task_id'])
        return admit_main(catalog, contract, outcomes[contract['task_id']], archive_path,
                          withheld_paths=withheld.get(contract['task_id'], ()))
    results = []
    for target in assignment_targets(contract):
        if selected_targets is not None and target['task_id'] not in selected_targets:
            results.append(unselected(target['task_id']))
            continue
        scoped = {**contract, **target}
        if schema == PUBLIC_WORK_SCHEMA:
            from .review_public_admission import admit_public_creation
            admit = admit_public_creation
        else:
            admit = admit_main
        results.append(admit(catalog, scoped, outcomes[target['task_id']], archive_path,
                            withheld_paths=withheld.get(target['task_id'], ())))
    complete = len(results) == 2 and all(
        r is not None and r.get('status') == 'accepted' and r.get('objective_met') is True
        for r in results)
    return {'schema': 'arcpuzzles-review-two-parametric-admissions-v1',
            'assignment_id': contract['assignment_id'], 'required_count': 2,
            'status': 'accepted' if complete else 'blocked', 'objective_met': complete,
            'training_admitted': False, 'targets': results}
