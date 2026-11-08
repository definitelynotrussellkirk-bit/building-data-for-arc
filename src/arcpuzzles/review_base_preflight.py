"""Explicit research checks for built bases; never grants source approval.

The native approval gate stays unchanged. This separate authoring route reuses
its source/contract validation and protected worker, then returns a different
receipt which native acceptance rejects. No catalog or approval file is edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .catalog import Catalog
from . import parametric_promotion as native

SCHEMA = 'arcpuzzles-base-parametric-authoring-preflight-v1'
POLICY = {'schema': 'arcpuzzles-built-base-review-v1',
          'pool': 'implemented_unambiguous_reference_without_accepted_parametric',
          'base_approval_required_at_draw': False,
          'base_review': 'check_repair_then_full_parametric_build',
          'owner_admission': 'base_source_review_then_native_qualification_and_acceptance'}


def eligible_ids(generators, accepted, *, include_unapproved):
    return sorted(tid for tid, row in generators.items() if tid not in accepted
                  and (include_unapproved or row['approved']))


def completed_base_review(contract, report):
    """Only validated whole-pool ready returns count as a base safety review.

    Call after packet validation and accepted source integration. This permits
    an unchanged base to earn a review; it does not itself approve any bytes.
    """
    return (contract.get('base_review_policy') == POLICY
            and report.get('parametric_work', {}).get('status') == 'ready'
            and report.get('outcome') in {'prototype', 'repaired', 'unchanged'}
            and report.get('remaining_failures') == [])


def source_ready(root, tid):
    """Read native source binding for research, explicitly outside its approval gate.

    The view changes one returned dictionary in memory. It cannot approve a
    Catalog, qualify through the public native API, or write an acceptance.
    All other native source, inventory, reference and contract checks still run.
    """
    catalog = Catalog(root)
    row = catalog.describe(tid)
    if row.get('semantic_veto'):
        raise ValueError('Resolve the explicit semantic veto before authoring preflight')
    if not row.get('generator') or not row.get('rule_hash') or 'ambiguous_canonical_rule' in row.get('approval_reasons', []):
        raise ValueError('Authoring needs an implemented base and one unambiguous reference')
    class SourceView:
        root = catalog.root
        def describe(self, selected):
            if selected != tid:
                raise ValueError('Authoring source view is scoped to one task')
            return {**catalog.describe(selected), 'approved': True}
        def _variants(self):
            return catalog._variants()
    try:
        return native._ready(SourceView(), tid)
    except ValueError as exc:
        if 'Prototype is not current/ready' not in str(exc):
            raise
        home = f'generators/{tid}/workspace/parametric/evidence'
        path = catalog.root/home/'manifest.json'
        replacement = (' --replace '+hashlib.sha256(path.read_bytes()).hexdigest()) if path.is_file() and not path.is_symlink() else ''
        raise ValueError(f'{exc}. Required inventory: {home}/manifest.json. '
            'Retain an actual focused-test or audit receipt in that evidence directory, then from WORK/repo run: '
            f'python3 -m arcpuzzles parametric manifest {tid} --evidence {home} '
            f'--reported-checks "ACTUAL_CHECK_NAMES_AND_RESULTS"{replacement}. '
            'The builder records your claims; it does not execute checks.') from exc


def _records(catalog, tid):
    row = catalog.describe(tid)
    return catalog._variants().get(row.get('rule_task_id', tid), [])


def _records_hash(catalog, tid):
    return hashlib.sha256(native._raw(_records(catalog, tid))).hexdigest()


def _base_checks(catalog, tid):
    from .parametric_worker import _local_imports, _real_evaluator, _grid
    row = catalog.describe(tid)
    records = _records(catalog, tid)
    programs = {r['program_solution'] for r in records}
    if len(programs) != 1:
        raise ValueError('Base review needs one exact canonical program')
    pairs = []
    with _local_imports(catalog.root/'shared/runtime', catalog.root/'generators'/tid):
        apply, identity, bridge = _real_evaluator(catalog.root/'shared/runtime')
        try:
            for variant, record in enumerate(records):
                for split in ('train', 'test'):
                    collection = record.get(split, [])
                    # Match canonical_pairs' legacy singleton format without
                    # changing the raw records used by _records_hash.
                    if isinstance(collection, dict):
                        collection = [collection]
                    for index, pair in enumerate(collection):
                        if 'output' not in pair:
                            continue
                        grid = lambda g: _grid([[int(c) for c in line] for line in g]) if g and isinstance(g[0], str) else _grid(g)
                        actual = _grid(apply(record['program_solution'], grid(pair['input'])))
                        if actual != grid(pair['output']):
                            raise ValueError(f'Original label mismatch: variant {variant} {split}[{index}]')
                        pairs.append({'variant': variant, 'split': split, 'index': index,
                                      'input': grid(pair['input']), 'output': actual})
        finally:
            bridge.close()
    if not pairs:
        raise ValueError('Base review needs labelled original pairs')
    # Existing staged generation supports all mapped legacy imports. Its explicit
    # research option retains unapproved status while executing reference labels.
    draws = [catalog.generate(tid, count=1, seed=seed, difficulty=difficulty,
                              n_train=2, n_test=1, allow_unapproved=True)
             for seed, difficulty in ((17, None), (43, 'medium'))]
    return {'status': 'passed', 'canonical_records_sha256': _records_hash(catalog, tid),
            'pairs': pairs, 'generation': draws, 'racket': identity,
            'base_approved_before': row['approved']}


def preflight(root, tid, out, *, demos=None, timeout=180):
    root = Path(root).resolve(); out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    catalog = Catalog(root)
    contract, binding = source_ready(root, tid)
    from .review_parametric_admission import qualification_demo_count
    demos = qualification_demo_count(contract, demos)
    if not 2 <= demos <= 6:
        raise ValueError('Declare a teachable count within 2..6 demonstrations')
    jobs = [job for setting in native.settings_space(contract) for seed in (0, 17)
            for job in native._jobs(contract, seed=seed, count=1, demos=demos,
                                    queries=4, settings=setting)]
    base = _base_checks(catalog, tid)
    execution = native._execute(catalog, tid, contract, jobs, timeout)
    programs = native._check_execution(execution, jobs, binding, contract)
    execution['base_review'] = base
    for episode in execution['episodes']:
        episode['reference'] = 'unapproved_authoring_preflight'
    if source_ready(root, tid) != (contract, binding) or _records_hash(Catalog(root), tid) != base.get('canonical_records_sha256', _records_hash(catalog, tid)):
        raise ValueError('Source changed during authoring preflight')
    out.mkdir(parents=True, exist_ok=False)
    native._write(out/'execution.json', execution)
    report = {'schema': SCHEMA, 'status': 'passed', 'task_id': tid,
              'verification_status': 'authoring_preflight_not_owner_qualification',
              'owner_accepted': False, 'training_admitted': False,
              'source_binding': binding, 'contract': contract, 'jobs': jobs,
              'programs': programs, 'execution': {'path': 'execution.json',
                  'sha256': hashlib.sha256((out/'execution.json').read_bytes()).hexdigest()},
              'limits': 'Finite base/reference and parametric checks. Adversarial self-review still required; owner source review and native admission remain separate.'}
    native._write(out/'qualification.json', report)
    return {**report, 'receipt': str((out/'qualification.json').resolve())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task_id')
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True, metavar='NEW_DIR',
                        help='output directory must not exist (even empty); writes qualification.json and execution.json')
    parser.add_argument('--demos', type=int)
    args = parser.parse_args()
    report = preflight(args.root, args.task_id, args.out, demos=args.demos)
    execution_path = Path(report['receipt']).parent / report['execution']['path']
    execution_bytes = execution_path.read_bytes()
    if hashlib.sha256(execution_bytes).hexdigest() != report['execution']['sha256']:
        raise ValueError('Authoring execution changed before summary')
    execution = json.loads(execution_bytes)
    print(json.dumps({
        **{k: report[k] for k in ('status', 'verification_status', 'owner_accepted',
                                  'training_admitted', 'receipt')},
        'job_count': len(report['jobs']),
        'settings_count': len(report['programs']),
        'parametric_labelled_pairs': sum(len(e['train']) + len(e['test'])
                                        for e in execution['episodes']),
        'base_canonical_pairs': len(execution['base_review']['pairs']),
        'protected_racket': execution['racket']['protected'],
        'racket_evaluations': execution['racket_evaluations'],
    }))


if __name__ == '__main__':
    main()
