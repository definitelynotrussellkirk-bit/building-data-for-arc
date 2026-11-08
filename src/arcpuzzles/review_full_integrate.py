"""Explicit component integration and conflict-aware full-return combinations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from .review_full_packet import packet_member, packet_names
from .catalog import Catalog, local_path, sha256
from .review import _lock
from .review_full_candidate import _receipt, assess_full_candidate
from .review_full_return import _canonical_only_task
from .review_full_return import validate_full_return
from .runtime import run_process
from .review_public_creation import PUBLIC_WORK_SCHEMA
from .review_targets import MULTI_SCHEMA, assignment_targets, target_ids, rule_task_ids, target_for_path, validate_target_outcomes


COMPONENTS = {"generator", "racket", "tests_notes"}


def _component(path: str, task_id: str) -> str:
    home = f"repo/generators/{task_id}/"
    if path == home + "generator.py":
        return "generator"
    if path == home + "reference.rkt":
        return "racket"
    if path.startswith("repo/shared/data/canonical/") or path.startswith("repo/shared/data/base/"):
        return "racket"
    if path.startswith(home) and (path in {home + "notes.md", home + "SUMMARY.md"}
                                  or path.startswith((home + "workspace/", home + "tests/", home + "counterexamples/"))):
        return "tests_notes"
    raise ValueError(f"Unknown integration path: {path}")


def _checked(review_root: Path, assignment_id: str, version: int) -> tuple[dict, dict, Path]:
    returned = _receipt(review_root, assignment_id, version)
    if returned["validation_status"] != "accepted":
        raise ValueError("Return failed static validation")
    path = review_root.parent / "var/review/full-checks" / assignment_id / f"{version:04d}/result.json"
    if not path.is_file():
        raise ValueError("Candidate needs a check")
    check = json.loads(path.read_text())
    if check.get("status") != "passed":
        raise ValueError("Candidate did not pass checks")
    candidate = Path(check["candidate_path"])
    for item in check.get("paths", []):
        target = candidate / item
        if target.is_symlink() or not target.is_file() or sha256(target) != check["candidate_file_sha256"].get(item):
            raise ValueError(f"Checked candidate changed: {item}")
    return returned, check, candidate


def _merge_rule(baseline: bytes, proposed: bytes, current: bytes, task_id: str) -> bytes:
    _canonical_only_task(baseline, proposed, task_id)
    allowed = {task_id} if isinstance(task_id, str) else set(task_id)
    before, after, now = baseline.splitlines(), proposed.splitlines(), current.splitlines()
    # A rotating packet contains only its selected tasks. Match the complete
    # selected task's row sequence, preserving every other owner-library row.
    selected = lambda rows: [row for row in rows if json.loads(row).get("task_id") in allowed]
    if selected(now) != selected(before):
        raise ValueError("Canonical task row drift or collision; manual rebase required")
    merged = list(now)
    replacements = iter(selected(after))
    for index, old in enumerate(now):
        if json.loads(old).get("task_id") in allowed:
            merged[index] = next(replacements)
    return b"\n".join(merged) + b"\n"



def _merge_placeholder_notes(relative, baseline, proposed, current):
    """Append disjoint sections only when the shared base had no authored notes."""
    match = re.fullmatch(r'generators/([A-Za-z0-9_-]+)/notes[.]md', relative)
    if not match or any(not isinstance(v, bytes) for v in (baseline, proposed, current)):
        raise ValueError('Only existing task notes can use placeholder reconciliation')
    title = '# Working notes: ' + match.group(1)
    placeholder = 'Record design decisions, hypotheses, review findings, and unresolved questions here.'
    imported = 'Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.'
    base, incoming, live = (v.decode('utf-8') for v in (baseline, proposed, current))
    if [line.strip() for line in base.splitlines() if line.strip()] != [title, placeholder, imported]:
        raise ValueError('Notes baseline is not the exact empty placeholder template')

    def sections(text):
        headings = list(re.finditer(r'^## ([^\n]+)\n', text, re.M))
        if not headings:
            raise ValueError('Notes reconciliation requires authored ## sections')
        prefix = [line.strip() for line in text[:headings[0].start()].splitlines() if line.strip()]
        if not prefix or prefix[0] != title or any(line not in {title, placeholder, imported} for line in prefix):
            raise ValueError('Notes preamble changed beyond placeholder removal')
        names = [m.group(1).strip().casefold() for m in headings]
        if len(names) != len(set(names)):
            raise ValueError('Repeated notes heading')
        return set(names), text[headings[0].start():]

    live_names, _ = sections(live)
    incoming_names, additions = sections(incoming)
    if live_names & incoming_names:
        raise ValueError('Overlapping notes headings require explicit rebase')
    merged = current + (b'\n' if current.endswith(b'\n') else b'\n\n') + additions.encode('utf-8')
    receipt = {'policy': 'empty-placeholder-disjoint-notes-v1', 'path': relative,
               'appended_headings': sorted(incoming_names),
               **{name + '_sha256': hashlib.sha256(raw).hexdigest() for name, raw in
                  [('base', baseline), ('current', current), ('proposed', proposed), ('merged', merged)]}}
    return merged, receipt


def _reported(review_root: Path, assignment_id: str, version: int) -> tuple[dict, dict, Path]:
    """Prepare only changed files; accept reviewer evidence without executing it."""
    returned = _receipt(review_root, assignment_id, version)
    if returned["validation_status"] != "accepted":
        raise ValueError("Return failed static validation")
    candidate = review_root.parent / "var/review/reported-candidates" / assignment_id / f"{version:04d}"
    try:
        candidate.mkdir(parents=True)
    except FileExistsError:
        # A failed integration may leave useful exact-source staging evidence.
        # Never reuse or mutate it; successful integration is guarded upstream.
        candidate = Path(tempfile.mkdtemp(prefix=f"{version:04d}-attempt-", dir=candidate.parent))
    packet_path = review_root.parent / "var/review/full-packets" / returned["packet_id"] / "request.zip"
    with zipfile.ZipFile(packet_path) as packet, zipfile.ZipFile(returned["archive_path"]) as archive:
        manifest = json.loads(packet_member(packet, "PACKET-MANIFEST.json"))
        checked = validate_full_return(archive, manifest)
        paths = checked["patch_paths"]
        for name in paths:
            if name in manifest["files"]:
                raw = packet_member(packet, name)
                if hashlib.sha256(raw).hexdigest() != manifest["files"][name]:
                    raise ValueError(f"Packet source hash differs: {name}")
                target = candidate / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        initialized = run_process(["git", "init", "-q"], candidate, timeout=10)
        if initialized["exit_code"] != 0:
            raise ValueError("Cannot initialize patch root")
        for index, name in enumerate(sorted(n for n in archive.namelist() if n.startswith("patches/"))):
            patch = candidate / f"patch-{index:03d}.patch"
            patch.write_bytes(archive.read(name))
            result = run_process(["git", "apply", str(patch)], candidate, timeout=15)
            if result["exit_code"] != 0 or result["timed_out"]:
                raise ValueError(f"Patch does not apply: {result['stderr'][:500]}")
    for name in paths:
        target = candidate / name
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"Unsafe candidate file: {name}")
    report = {"schema": "arcpuzzles-reported-acceptance-v1", "assignment_id": assignment_id,
              "version": version, "status": "reviewer_reported", "paths": paths,
              "candidate_file_sha256": {name: sha256(candidate / name) for name in paths},
              "candidate_path": str(candidate), "verification_status": "reviewer_reported",
              "training_admitted": False, "checks": [], "receipt_path": str(candidate / "ACCEPTANCE.json")}
    Path(report["receipt_path"]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return returned, report, candidate


def _integrate_targets(catalog, review_root, assignment_id, version, components,
                       reviewer_reported, contract, selected_targets=None):
    """Apply one validated delta atomically, retaining a disposition per target."""
    targets = assignment_targets(contract)
    public_creation = contract.get('work_policy', {}).get('schema') == PUBLIC_WORK_SCHEMA
    if public_creation:
        from .review_public_creation import generator_id
        for row in targets:
            source = row['generator'].get('public_creation', {})
            if (row['generator'].get('job_kind') != 'public_eval_creation'
                    or generator_id(source.get('public_task_id', '')) != row['task_id']
                    or source.get('task_id') != row['task_id']):
                raise ValueError('Public creation target identity differs from frozen assignment')
    if selected_targets is not None and (
            not selected_targets or not set(selected_targets) <= {r['task_id'] for r in targets}):
        raise ValueError('Owner target selection must be nonempty and assigned')
    returned = _receipt(review_root, assignment_id, version)
    if returned['validation_status'] != 'accepted':
        raise ValueError('Return failed static validation')
    if sha256(Path(returned['archive_path'])) != returned['zip_sha256']:
        raise ValueError('Retained return hash changed')
    with zipfile.ZipFile(returned['archive_path']) as archive:
        if archive.read('ASSIGNMENT.json') != (review_root/'assignments'/assignment_id/'ASSIGNMENT.json').read_bytes():
            raise ValueError('Retained assignment differs from return')
        outcomes = {row['task_id']: row for row in validate_target_outcomes(
            contract, json.loads(archive.read('RESULTS.json')))}
        has_patch = any(n.startswith('patches/') for n in archive.namelist())
    evidence_paths = {row['task_id']: catalog.root/'generators'/row['task_id']/'evidence'/
        f'review-{assignment_id}-v{version:04d}.json' for row in targets}
    if any(path.exists() for path in evidence_paths.values()):
        raise FileExistsError('This return already has target integration evidence')
    if has_patch and not components:
        raise ValueError('Patched return needs explicit component disposition')
    if has_patch:
        returned, check, candidate = (_reported if reviewer_reported else _checked)(
            review_root, assignment_id, version)
        if not reviewer_reported and set(check.get('checked_task_ids', [])) != set(target_ids(contract)):
            raise ValueError('Three-target acceptance requires checks covering every assigned target')
    else:
        check, candidate = {'paths': [], 'receipt_path': None}, None
    canonical = 'repo/shared/data/canonical/puzzles.jsonl'
    packet_path = review_root.parent/'var/review/full-packets'/returned['packet_id']/'request.zip'
    desired, originals, owners, proposed_components = {}, {}, {}, {tid: set() for tid in outcomes}
    integrated = {tid: {} for tid in outcomes}
    selected_components = {tid: set() for tid in outcomes}
    withheld = {tid: [] for tid in outcomes}
    reconciliations = {}
    with zipfile.ZipFile(packet_path) as packet:
        mapping = json.loads(packet_member(packet, 'repo/catalog/runtime_files.json'))
        authorities = json.loads(packet_member(packet, 'repo/catalog/authority_files.json'))
        for item in check['paths']:
            relative = item.removeprefix('repo/')
            before = packet_member(packet, item) if item in packet_names(packet) else None
            proposed = (candidate/item).read_bytes()
            home = target_for_path(item, contract)
            if home:
                affected = {home['task_id']}
                component = _component(item, home['task_id'])
            elif item == canonical:
                _canonical_only_task(before, proposed, rule_task_ids(contract))
                changed_rules = {json.loads(a)['task_id'] for a, b in zip(before.splitlines(), proposed.splitlines()) if a != b}
                affected = {row['task_id'] for row in targets if row['generator']['rule_task_id'] in changed_rules}
                component = 'racket'
            else:
                bound = {authorities.get(entry['target']) for entry in mapping
                         if 'repo/' + entry['path'] == item and entry['target'].startswith('data/base/solutions/')}
                affected = {row['task_id'] for row in targets
                            if bound & {row['task_id'], row['generator']['rule_task_id']}}
                component = 'racket'
            if not affected:
                raise ValueError(f'Changed path has no assigned owner: {item}')
            for tid in affected:
                proposed_components[tid].add(component)
            accepted = {tid for tid in affected if component in components and
                        (component == 'tests_notes' or outcomes[tid]['outcome'] == 'repaired'
                         or public_creation and outcomes[tid]['outcome'] == 'prototype')}
            if (reviewer_reported and contract.get('work_policy', {}).get('schema')
                    == 'arcpuzzles-parametric-main-admission-v1'):
                accepted &= {contract['task_id']}  # Optional unverified peer work is proposal-only.
            if selected_targets is not None:
                accepted &= set(selected_targets)
            if item != canonical and accepted != affected:
                accepted = set()  # A shared authority cannot be partially applied.
            for tid in affected - accepted:
                withheld[tid].append(item)
            if not accepted:
                continue
            target = local_path(catalog.root, relative)
            if target.is_symlink():
                raise ValueError(f'Authoritative symlink: {relative}')
            current = target.read_bytes() if target.is_file() else None
            if item == canonical:
                accepted_rules = {row['generator']['rule_task_id'] for row in targets if row['task_id'] in accepted}
                # One shared row cannot be accepted for one alias and withheld for another.
                rejected_rules = {row['generator']['rule_task_id'] for row in targets if row['task_id'] in affected - accepted}
                if accepted_rules & rejected_rules:
                    raise ValueError('Conflicting target outcomes share a changed canonical rule')
                projected = b'\n'.join(b if json.loads(a)['task_id'] in accepted_rules else a
                    for a, b in zip(before.splitlines(), proposed.splitlines())) + b'\n'
                desired[relative] = _merge_rule(before, projected, current, accepted_rules)
            else:
                if current != before:
                    try:
                        merged, reconciliation = _merge_placeholder_notes(relative, before, proposed, current)
                    except ValueError as exc:
                        raise ValueError(f'Source drift or collision at {relative}; manual rebase required: {exc}') from exc
                    desired[relative] = merged
                    reconciliations[relative] = reconciliation
                else:
                    desired[relative] = proposed
            originals[target] = current
            owners[relative] = accepted
            for tid in accepted:
                selected_components[tid].add(component)
        if public_creation:
            # Immutable assignment provenance is not part of the reviewer delta.
            # Copy exact packet bytes into a new home in the same transaction.
            for row in targets:
                tid = row['task_id']
                if selected_targets is not None and tid not in selected_targets:
                    continue
                item = f'repo/generators/{tid}/workspace/public-parent.json'
                relative = item.removeprefix('repo/')
                raw = packet_member(packet, item)
                if hashlib.sha256(raw).hexdigest() != contract['baseline_sha256'].get(item):
                    raise ValueError('Public parent baseline hash differs from assignment')
                target = local_path(catalog.root, relative)
                current = target.read_bytes() if target.is_file() else None
                if target.is_symlink():
                    raise ValueError('Public parent provenance collides with live source')
                if current not in (None, raw):
                    old_parent, new_parent = json.loads(current), json.loads(raw)
                    if (type(old_parent.get('needs_creation')) is not bool
                            or type(new_parent.get('needs_creation')) is not bool
                            or {k: v for k, v in old_parent.items() if k != 'needs_creation'}
                            != {k: v for k, v in new_parent.items() if k != 'needs_creation'}):
                        raise ValueError('Public parent provenance collides with live source')
                if current != raw:
                    desired[relative] = raw
                    originals[target] = current
                    owners[relative] = {tid}
    # Do not infer reviewer scope from the selected component flags. Bind it to
    # the actual delta after resolving shared authority ownership from the packet.
    for tid, actual in proposed_components.items():
        if actual != set(outcomes[tid]['changed_components']):
            raise ValueError(f'Reported components differ from actual delta for {tid}')
    live = Catalog(catalog.root)
    for row in targets:
        tid = row['task_id']
        if not public_creation and selected_components[tid] & {'generator', 'racket'}:
            if live.describe(tid)['rule_hash'] != row['generator']['rule_hash']:
                raise ValueError(f'Assigned rule has source drift for {tid}; manual rebase required')
    if components - set().union(*proposed_components.values()):
        raise ValueError('Selected component has no returned change')
    stage = review_root.parent/'var/review/integration-staging'/assignment_id/f'{version:04d}'
    stage.mkdir(parents=True, exist_ok=True)
    for relative, raw in desired.items():
        path = stage/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    written, evidence_written = [], []
    try:
        for relative in desired:
            target = local_path(catalog.root, relative)
            if (target.read_bytes() if target.is_file() else None) != originals[target]:
                raise ValueError(f'Source changed during integration: {relative}')
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage/relative, target)
            written.append(target)
            for tid in owners[relative]:
                integrated[tid][relative] = sha256(target)
        fresh = Catalog(catalog.root)
        reports = []
        for row in targets:
            tid = row['task_id']
            disposition = 'needs_evidence' if withheld[tid] else ('accepted' if integrated[tid] else 'no_changes')
            evidence = {'schema': 'arcpuzzles-full-integration-v3', 'assignment_id': assignment_id,
                'version': version, 'packet_id': returned['packet_id'], 'task_id': tid,
                'repair_outcome': outcomes[tid]['outcome'], 'target_report': outcomes[tid],
                'components': sorted(selected_components[tid]), 'proposed_components': sorted(proposed_components[tid]),
                'integrated_files': integrated[tid], 'withheld_paths': withheld[tid],
                'check_receipt': check['receipt_path'] if not reviewer_reported else None,
                'reported_acceptance_receipt': check['receipt_path'] if reviewer_reported else None,
                'verification_status': ('reviewer_reported' if reviewer_reported else
                                        'independently_checked' if has_patch else 'not_run'),
                'rule_hash_at_integration': (
                    hashlib.sha256((catalog.root/f'generators/{tid}/reference.rkt').read_bytes()).hexdigest()[:12]
                    if public_creation and (catalog.root/f'generators/{tid}/reference.rkt').is_file()
                    else None if public_creation else fresh.describe(tid)['rule_hash']),
                'source_hashes_at_assignment': contract['baseline_sha256'], 'disposition': disposition}
            relevant_reconciliations = [r for name, r in reconciliations.items() if tid in owners[name]]
            if relevant_reconciliations:
                evidence['source_reconciliations'] = relevant_reconciliations
            path = evidence_paths[tid]
            path.parent.mkdir(parents=True, exist_ok=True)
            evidence_written.append(path)
            path.write_text(json.dumps(evidence, sort_keys=True, indent=2)+'\n')
            reports.append({'task_id': tid, 'disposition': disposition, 'repair_outcome': outcomes[tid]['outcome'],
                            'components': evidence['components'], 'evidence_path': str(path)})
    except Exception:
        for target in written:
            if originals[target] is None: target.unlink(missing_ok=True)
            else: target.write_bytes(originals[target])
        for path in evidence_written: path.unlink(missing_ok=True)
        raise
    from .review_approval import approve_reviews
    result = {'status': 'integrated' if desired else 'no_changes', 'files': sorted(desired),
            'components': sorted(components), 'targets': reports,
            'evidence_path': str(evidence_paths[contract['task_id']]),
            'approval': ({'status': 'pending_public_registration', 'approved': [], 'training_admitted': False}
                         if public_creation else approve_reviews(catalog, review_root, assignment_id=assignment_id, version=version))}
    from .review_parametric_admission import admit_assignment
    admission = admit_assignment(catalog, contract, outcomes,
                                 Path(returned['archive_path']), withheld_paths=withheld,
                                 selected_targets=selected_targets)
    if selected_targets is not None:
        result['owner_selected_targets'] = sorted(selected_targets)
    if admission is not None:
        result['parametric_admission'] = admission
        if 'targets' in admission:
            result['parametric_admissions'] = admission['targets']
        elif contract.get('work_policy', {}).get('schema') == 'arcpuzzles-one-parametric-admission-v1':
            result['parametric_admissions'] = [admission]
        result['objective_met'] = admission['objective_met']
        result['completion_status'] = 'accepted' if admission['objective_met'] else 'repair_needed'
    return result


def integrate_full_candidate(catalog: Catalog, review_root: Path, assignment_id: str,
                             version: int, components: set[str], *, reviewer_reported: bool = False,
                             selected_targets: set[str] | None = None) -> dict:
    if not components <= COMPONENTS:
        raise ValueError(f"Unknown components: {sorted(components - COMPONENTS)}")
    review_root = review_root.resolve()
    with _lock(review_root):
        contract_path = review_root/'assignments'/assignment_id/'ASSIGNMENT.json'
        if contract_path.is_file():
            contract = json.loads(contract_path.read_text())
            if contract.get('schema') == MULTI_SCHEMA:
                return _integrate_targets(catalog, review_root, assignment_id, version, components,
                                          reviewer_reported, contract, selected_targets)
        if selected_targets is not None:
            raise ValueError('Owner target selection requires a multi-target return')
        if not components:
            returned = _receipt(review_root, assignment_id, version)
            if returned["validation_status"] != "accepted":
                raise ValueError("Return failed static validation")
            with zipfile.ZipFile(returned["archive_path"]) as archive:
                results = json.loads(archive.read("RESULTS.json"))
            if any(item.get("kind") == "patch" for item in results["artifacts"]):
                raise ValueError("Patched return needs explicit component disposition")
            tid = returned["task_id"]
            evidence_path = catalog.root / "generators" / tid / "evidence" / f"review-{assignment_id}-v{version:04d}.json"
            if evidence_path.exists():
                raise FileExistsError("This return already has integration evidence")
            evidence = {"schema": "arcpuzzles-full-integration-v2", "assignment_id": assignment_id,
                        "version": version, "packet_id": returned["packet_id"], "components": [],
                        "integrated_files": {}, "disposition": "no_changes",
                        "stopping_reason": results.get("stopping_reason", "")}
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
            return {"status": "no_changes", "files": [], "components": [],
                    "evidence_path": str(evidence_path)}
        returned, check, candidate = (_reported if reviewer_reported else _checked)(review_root, assignment_id, version)
        contract = json.loads((review_root / "assignments" / assignment_id / "ASSIGNMENT.json").read_text())
        tid = contract["task_id"]
        paths = [path for path in check["paths"] if _component(path, tid) in components]
        if components - {_component(path, tid) for path in paths}:
            raise ValueError("Selected component has no checked change")
        evidence_path = catalog.root / "generators" / tid / "evidence" / f"review-{assignment_id}-v{version:04d}.json"
        if evidence_path.exists():
            raise FileExistsError("This return already has integration evidence")
        packet_path = review_root.parent / "var/review/full-packets" / returned["packet_id"] / "request.zip"
        desired: dict[str, bytes] = {}
        originals: dict[Path, bytes | None] = {}
        with zipfile.ZipFile(packet_path) as packet:
            for item in paths:
                relative = item.removeprefix("repo/")
                target = local_path(catalog.root, relative)
                if target.is_symlink():
                    raise ValueError(f"Authoritative symlink: {relative}")
                before = packet_member(packet, item) if item in packet_names(packet) else None
                current = target.read_bytes() if target.is_file() else None
                proposed = (candidate / item).read_bytes()
                if item == "repo/shared/data/canonical/puzzles.jsonl":
                    if before is None or current is None:
                        raise ValueError("Missing canonical ledger")
                    desired[relative] = _merge_rule(before, proposed, current,
                                                    contract["generator"]["rule_task_id"])
                else:
                    if current != before:
                        raise ValueError(f"Source drift or collision at {relative}; manual rebase required")
                    desired[relative] = proposed
                originals[target] = current
        stage = review_root.parent / "var/review/integration-staging" / assignment_id / f"{version:04d}"
        stage.mkdir(parents=True, exist_ok=True)
        for relative, raw in desired.items():
            staged = stage / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(raw)
        written: list[Path] = []
        try:
            for relative, raw in desired.items():
                target = local_path(catalog.root, relative)
                expected = originals[target]
                if (target.read_bytes() if target.is_file() else None) != expected:
                    raise ValueError(f"Source changed during integration: {relative}")
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(stage / relative, target)
                written.append(target)
            evidence = {"schema": "arcpuzzles-full-integration-v2", "assignment_id": assignment_id,
                        "version": version, "packet_id": returned["packet_id"],
                        "components": sorted(components),
                        "check_receipt": None if reviewer_reported else check["receipt_path"],
                        "verification_status": "reviewer_reported" if reviewer_reported else "independently_checked",
                        "reported_acceptance_receipt": check["receipt_path"] if reviewer_reported else None,
                        "integrated_files": {name: sha256(local_path(catalog.root, name)) for name in desired},
                        "rule_hash_at_integration": Catalog(catalog.root).describe(tid)["rule_hash"],
                        "source_hashes_at_assignment": contract["baseline_sha256"],
                        "disposition": "accepted"}
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
        except Exception:
            for target in written:
                raw = originals[target]
                if raw is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(raw)
            evidence_path.unlink(missing_ok=True)
            raise
        result = {"status": "integrated" if desired else "no_changes", "files": sorted(desired),
                  "components": sorted(components), "evidence_path": str(evidence_path)}
        if components:
            from .review_approval import approve_reviews
            result["approval"] = approve_reviews(catalog, review_root,
                                                 assignment_id=assignment_id, version=version)
    return result


def stage_full_combination(review_root: Path, sources: list[tuple[str, int]], out: Path) -> dict:
    review_root = review_root.resolve()
    out = out.resolve()
    if len(sources) < 2 or len(set(sources)) != len(sources):
        raise ValueError("Combination needs at least two distinct checked returns")
    checks, candidates, receipts = [], [], []
    for assignment_id, version in sources:
        receipt, check, candidate = _checked(review_root, assignment_id, version)
        checks.append(check)
        candidates.append(candidate)
        receipts.append(receipt)
    if len({r["packet_id"] for r in receipts}) != 1 or len({r["task_id"] for r in receipts}) != 1:
        raise ValueError("Combination sources must share packet and task")
    paths: dict[str, list[tuple[int, str]]] = {}
    for index, check in enumerate(checks):
        for path in check["paths"]:
            paths.setdefault(path, []).append((index, check["candidate_file_sha256"][path]))
    conflicts = {path: values for path, values in paths.items() if len({digest for _, digest in values}) > 1}
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema": "arcpuzzles-full-combination-v2", "status": "conflict" if conflicts else "staged_unchecked",
              "sources": [{"assignment_id": aid, "version": ver, "zip_sha256": receipt["zip_sha256"]}
                          for (aid, ver), receipt in zip(sources, receipts)],
              "task_id": receipts[0]["task_id"], "packet_id": receipts[0]["packet_id"],
              "conflicts": conflicts, "paths": sorted(paths),
              "warning": "A combination needs its own fresh checks before integration"}
    if not conflicts:
        shutil.copytree(candidates[0] / "repo", out / "repo")
        for path, entries in paths.items():
            source_index = entries[-1][0]
            target = out / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidates[source_index] / path, target)
    (out / "COMBINATION.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return {**report, "directory": str(out)}


def record_full_disposition(review_root: Path, assignment_id: str, version: int,
                            kind: str, status: str, reason: str) -> dict:
    if kind not in COMPONENTS | {"audit", "feedback", "decision"} or status not in {
            "accepted", "rejected", "needs_evidence", "deferred", "implemented"} or not reason.strip():
        raise ValueError("Disposition needs valid kind, status, and nonempty reason")
    review_root = review_root.resolve()
    _receipt(review_root, assignment_id, version)
    path = review_root / "assignments" / assignment_id / f"dispositions-{version:04d}.json"
    with _lock(review_root):
        document = json.loads(path.read_text()) if path.is_file() else {
            "schema": "arcpuzzles-full-dispositions-v2", "assignment_id": assignment_id,
            "version": version, "items": []}
        document["items"].append({"kind": kind, "status": status, "reason": reason})
        path.write_text(json.dumps(document, sort_keys=True, indent=2) + "\n")
    return {"path": str(path), "item": document["items"][-1]}
