"""Owner policy: an accepted repair is a safety review of those exact bytes.

No generator, test, or returned program is executed here. Approval retains its
review basis and does not admit any model trajectory to training.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import zipfile

from .catalog import Catalog, local_path, sha256
from .review import _lock, _now, _write
from .review_full_inbox import _receipts
from .review_targets import MULTI_SCHEMA, assignment_targets, validate_target_outcomes


POLICY = "owner-accepted-repair-is-safety-review-20261003"


def generator_metadata(path: Path) -> dict:
    """Read literal descriptive fields without importing reviewer code."""
    fields = {}
    for statement in ast.parse(path.read_bytes()).body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        for target in targets:
            if not isinstance(target, ast.Name) or target.id not in {"VERSION", "SUMMARY"}:
                continue
            # A later computed assignment invalidates an earlier literal claim.
            field = {"VERSION": "version", "SUMMARY": "summary"}[target.id]
            fields.pop(field, None)
            try:
                value = ast.literal_eval(statement.value)
            except (ValueError, TypeError):
                continue
            if isinstance(value, str) and value.strip():
                fields[field] = value
    return fields


def _rule_binding(catalog: Catalog, evidence: dict, contract: dict) -> str | None:
    if evidence.get("rule_hash_at_integration"):
        return evidence["rule_hash_at_integration"]
    canonical = "shared/data/canonical/puzzles.jsonl"
    if canonical not in evidence.get("integrated_files", {}):
        return contract["generator"].get("rule_hash")
    # A repaired canonical row can differ from its assignment. Use the retained
    # candidate's target row, not the hash of an unrelated full current ledger.
    report = evidence.get("reported_acceptance_receipt") or evidence.get("check_receipt")
    if not report:
        return None
    checked = json.loads(Path(report).read_text())
    candidate = Path(checked["candidate_path"]) / "repo" / canonical
    rows = [json.loads(line) for line in candidate.read_text().splitlines() if line.strip()]
    tid = contract["generator"]["rule_task_id"]
    rules = [r.get("program_solution") for r in rows if r.get("task_id") == tid]
    hashes = {hashlib.sha256(" ".join(r.split()).encode()).hexdigest()[:12]
              for r in rules if isinstance(r, str) and r.strip()}
    return next(iter(hashes)) if len(hashes) == 1 else None


def approve_reviews(catalog: Catalog, review_root: Path, *, assignment_id: str | None = None,
                    version: int | None = None, all_integrated: bool = False) -> dict:
    """Backfill or finalize accepted repairs, refusing source/rule drift."""
    if not all_integrated and (assignment_id is None or type(version) is not int or version < 1):
        raise ValueError("Choose --all-integrated or an assignment and positive version")
    if all_integrated and (assignment_id is not None or version is not None):
        raise ValueError("Do not combine an assignment with --all-integrated")
    review_root = review_root.resolve()
    with _lock(review_root):
        fresh = Catalog(catalog.root)
        path = local_path(fresh.root, "catalog/puzzles.jsonl")
        original = path.read_bytes()
        canonical_path = local_path(fresh.root, "shared/data/canonical/puzzles.jsonl")
        canonical_sha = sha256(canonical_path)
        before_approved = fresh.stats()["approved"]
        receipts = _receipts(review_root)
        if not all_integrated:
            receipts = [r for r in receipts if r["assignment_id"] == assignment_id and r["version"] == version]
            if not receipts:
                raise ValueError("No retained return for this assignment/version")
        projected = []
        for receipt in receipts:
            contract_path = review_root/'assignments'/receipt['assignment_id']/'ASSIGNMENT.json'
            contract = json.loads(contract_path.read_text())
            if contract.get('schema') != MULTI_SCHEMA:
                projected.append(receipt)
                continue
            archive = Path(receipt['archive_path'])
            if sha256(archive) != receipt['zip_sha256']:
                raise ValueError('Retained return hash changed')
            with zipfile.ZipFile(archive) as z:
                if z.read('ASSIGNMENT.json') != contract_path.read_bytes():
                    raise ValueError('Retained assignment differs from return')
                outcomes = {r['task_id']: r for r in validate_target_outcomes(contract,
                    json.loads(z.read('RESULTS.json')))}
            for target_row in assignment_targets(contract):
                tid = target_row['task_id']
                disposition = receipt.get('repair_dispositions', {}).get(tid, {})
                projected.append(dict(receipt, task_id=tid,
                    disposition_status=disposition.get('disposition_status', 'unreviewed'),
                    _target_contract=dict(contract, task_id=tid, generator=target_row['generator']),
                    _target_outcome=outcomes[tid]))
        approved, skipped, records, changes, metadata_refreshed = [], [], [], {}, []
        for receipt in projected:
            key = {"assignment_id": receipt["assignment_id"], "version": receipt["version"],
                   "task_id": receipt["task_id"]}
            def skip(reason):
                skipped.append(key | {"reason": reason})
            from .review_base_preflight import completed_base_review
            completed_base = completed_base_review(receipt.get('_target_contract', {}), receipt.get('_target_outcome', {}))
            if not completed_base and receipt.get('_target_outcome', {}).get('outcome', 'repaired') != 'repaired':
                skip('target_not_repaired')
                continue
            if receipt.get("disposition_status") != "accepted":
                skip("repair_not_accepted")
                continue
            tid = receipt["task_id"]
            evidence_path = local_path(fresh.root,
                f"generators/{tid}/evidence/review-{receipt['assignment_id']}-v{receipt['version']:04d}.json")
            if not evidence_path.is_file():
                skip("missing_integration_evidence")
                continue
            evidence = json.loads(evidence_path.read_text())
            selected = set(evidence.get("components", []))
            proposed = set(receipt.get("intake_summary", {}).get("components", []))
            if '_target_outcome' in receipt:
                proposed = set(receipt['_target_outcome']['changed_components'])
                integrated = evidence.get('integrated_files', {})
                actual_source = (('generator' in selected and f'generators/{tid}/generator.py' in integrated)
                    or ('racket' in selected and any(name.startswith(('shared/data/canonical/', 'shared/data/base/')) for name in integrated)))
                reviewed_unchanged = (completed_base and selected == {'tests_notes'} and proposed == {'tests_notes'})
                if (evidence.get('task_id') != tid or (not reviewed_unchanged and
                        (evidence.get('repair_outcome') != 'repaired'
                         or not actual_source or not proposed & {'generator', 'racket'}))):
                    skip('target_has_no_accepted_source_repair')
                    continue
                if proposed - selected:
                    skip('partial_target_component_selection')
                    continue
            if not selected & {"generator", "racket"}:
                # A complete review may find the generator already correct and
                # return only regressions/notes. A partial selection from a
                # proposed source repair must not approve the unrepaired source.
                if selected != {"tests_notes"} or proposed != {"tests_notes"}:
                    skip("notes_only_selection_or_no_review")
                    continue
            contract_path = local_path(review_root, f"assignments/{receipt['assignment_id']}/ASSIGNMENT.json")
            contract = receipt.get('_target_contract') or json.loads(contract_path.read_text())
            row = fresh.describe(tid)
            generator = row["generator"]
            expected = evidence.get("integrated_files", {}).get(generator,
                       contract["generator"].get("generator_sha256"))
            if expected != row["generator_sha256"]:
                skip("superseded_generator_source")
                continue
            rule = _rule_binding(fresh, evidence, contract)
            if not rule or rule != row["rule_hash"] or "ambiguous_canonical_rule" in row["approval_reasons"]:
                skip("missing_or_changed_rule_binding")
                continue
            if tid in changes:
                skip("same_live_source_already_selected")
                continue
            metadata = generator_metadata(local_path(fresh.root, generator))
            if row.get("approval_policy") == POLICY and row["approved"]:
                if any(fresh._records[tid].get(k) != v for k, v in metadata.items()):
                    changes[tid] = dict(fresh._records[tid]) | metadata
                    metadata_refreshed.append(key | {"generator_sha256": expected,
                                                     "generator_metadata": metadata})
                skip("already_approved")
                continue
            archive = Path(receipt["archive_path"])
            if sha256(archive) != receipt["zip_sha256"]:
                raise ValueError(f"Retained return hash changed: {archive}")
            with zipfile.ZipFile(archive) as z:
                if z.read("ASSIGNMENT.json") != contract_path.read_bytes():
                    raise ValueError("Retained assignment differs from return")
                results = json.loads(z.read("RESULTS.json"))
                brief = z.read("REVIEW.md").decode("utf-8", errors="replace")[:2400]
            verification = evidence.get("verification_status") or (
                "independently_checked" if evidence.get("check_receipt") else "reviewer_reported")
            record = {"schema": "arcpuzzles-approval-v1", **key, "policy": POLICY,
                      "generator_sha256": expected, "rule_hash": rule,
                      "return_sha256": receipt["zip_sha256"],
                      "integration_evidence": str(evidence_path.relative_to(fresh.root)),
                      "integration_evidence_sha256": sha256(evidence_path),
                      "verification_status": verification,
                      "generator_metadata": metadata,
                      "reported_completion": results.get("completion_state", "unknown"),
                      "reported_remaining_failures": results.get("remaining_failures", []),
                      "review_brief": brief, "reviewed_at": _now(),
                      "previous_catalog_record": fresh._records[tid],
                      "scope": "Accepted generator repair; finite reviewer evidence, no new maintainer execution",
                      "trajectory_training_admitted": False}
            if '_target_outcome' in receipt:
                record['repair_outcome'] = receipt['_target_outcome']['outcome']
                record['target_report'] = receipt['_target_outcome']
                record['reported_remaining_failures'] = receipt['_target_outcome']['remaining_failures']
            identity = hashlib.sha256(json.dumps([tid, expected, rule, receipt["zip_sha256"]]).encode()).hexdigest()
            record_path = local_path(fresh.root, f"REVIEW/approvals/{identity}.json")
            change = dict(fresh._records[tid])
            change.update(metadata)
            change.update(train_safety="reviewed_safe", reviewed_generator_sha256=expected,
                          reviewed_rule_hash=rule, review_status="accepted_repair",
                          approval_policy=POLICY, approval_verification_status=verification,
                          approval_receipt=str(record_path.relative_to(fresh.root)))
            changes[tid] = change
            records.append((record_path, record))
            approved.append(key | {"generator_sha256": expected, "rule_hash": rule,
                                   "verification_status": verification})
        # Recheck all byte bindings immediately before the atomic catalog write.
        if path.read_bytes() != original or sha256(canonical_path) != canonical_sha:
            raise ValueError("Catalog or authority changed during approval; retry")
        for item in approved + metadata_refreshed:
            generator = local_path(fresh.root, changes[item["task_id"]]["generator"])
            if sha256(generator) != item["generator_sha256"]:
                raise ValueError("Generator changed during approval; retry")
        for target, record in records:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                _write(target, record)
        if changes:
            lines = original.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if line.strip():
                    tid = json.loads(line)["id"]
                    if tid in changes:
                        lines[i] = (json.dumps(changes[tid], sort_keys=True) + "\n").encode()
            temporary = path.with_suffix(".approval.tmp")
            temporary.write_bytes(b"".join(lines))
            temporary.replace(path)
        updated = Catalog(fresh.root)
        catalog._records = updated._records
        for item in approved:
            live = updated.describe(item["task_id"])
            item.update(effective_approved=live["approved"], approval_reasons=live["approval_reasons"])
        after_approved = updated.stats()["approved"]
        return {"schema": "arcpuzzles-approval-batch-v1", "policy": POLICY,
                "safety_reviews_recorded": len(approved), "newly_effective_approvals": after_approved - before_approved,
                "approved": approved, "skipped": skipped, "catalog_approved": after_approved,
                "metadata_refreshed": metadata_refreshed,
                "no_generator_execution": True, "trajectory_training_admitted": False}
