"""Retain and statically validate independent offline full-packet returns."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from .review import _lock
from .review_full_packet import canonical_json, packet_member
from .review_full_return import validate_full_return
from .review_full_draw import audit_ids_for_seed, blind_id_for_seed, main_selection_for_seed, repair_selection_for_seed
from .review_targets import MULTI_SCHEMA, assignment_targets, target_ids, validate_target_outcomes


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _next_return_version(review_root: Path, receipts_dir: Path, identifier: str,
                         checked: dict) -> int:
    """Avoid reusing an identity still referenced after transport compaction."""
    versions = [0]
    identity = re.compile(re.escape(identifier) + r":v([0-9]+)(?::.*)?")

    def retain_version(value: object) -> None:
        # Independent approvals have no reviewer return identity to reserve.
        if not isinstance(value, str):
            return
        match = identity.fullmatch(value)
        if match:
            versions.append(int(match[1]))

    for path in receipts_dir.glob("return-*.json"):
        match = re.fullmatch(r"return-([0-9]+)-.*\.json", path.name)
        if match:
            versions.append(int(match[1]))
    targets = set(checked.get("audit_targets", []))
    targets.update(checked.get("task_ids", []))
    targets.update(tid for tid in (checked.get("task_id"), checked.get("audit_target")) if tid)
    for tid in targets:
        home = review_root.parent / "generators" / tid
        index = home / "evidence/review_index.json"
        if index.is_file():
            state = json.loads(index.read_text())
            for row in [*state.get("audits", []), *state.get("decisions", [])]:
                retain_version(row.get("return_id", ""))
        for path in (home / "counterexamples").glob(identifier + "-v*"):
            match = re.fullmatch(re.escape(identifier) + r"-v([0-9]+)", path.name)
            if match:
                versions.append(int(match[1]))
    requests = review_root / "suggestions.json"
    if requests.is_file():
        for row in json.loads(requests.read_text()).get("items", []):
            retain_version(row.get("return_id", ""))
            retain_version(row.get("request_id", ""))
    return max(versions) + 1


def _reproduce(contract: dict, manifest: dict, packet: zipfile.ZipFile) -> None:
    packet_id = _sha(canonical_json(manifest))
    try:
        seed = bytes.fromhex(contract["seed"])
        if len(seed) != 32:
            raise ValueError("seed length")
        tid, focus = main_selection_for_seed(manifest, seed)
        expected_id = "review-" + _sha(bytes.fromhex(packet_id) + seed)[:16]
        questions = sorted(manifest["questions"], key=lambda item: item["id"])
        question = questions[int.from_bytes(hashlib.sha256(seed + b":question").digest(), "big") % len(questions)]
        if (contract["task_id"] != tid or contract["assignment_id"] != expected_id
                or contract["question"] != question or contract.get('authoring_focus') != focus):
            raise ValueError("Assignment draw cannot be reproduced")
        if manifest.get('repair_target_policy'):
            if contract.get('schema') != MULTI_SCHEMA:
                raise ValueError('Three-target packet requires v3 assignment')
            targets = assignment_targets(contract)
            if targets != repair_selection_for_seed(manifest, seed):
                raise ValueError('Repair target draw cannot be reproduced')
        else:
            if contract.get('schema') == MULTI_SCHEMA:
                raise ValueError('Legacy packet cannot authorize three repair targets')
            targets = [{'task_id': tid, 'generator': manifest['generators'][tid]}]
        homes = tuple(f"repo/generators/{target['task_id']}/" for target in targets)
        paths = {name for name in manifest["files"] if name.startswith(homes)}
        paths.add("repo/shared/data/canonical/puzzles.jsonl")
        mapping = json.loads(packet_member(packet, "repo/catalog/runtime_files.json"))
        authorities = json.loads(packet_member(packet, "repo/catalog/authority_files.json"))
        bound = {value for target in targets for value in
                 (target['task_id'], target['generator']['rule_task_id'])}
        for item in mapping:
            if item["target"].startswith("data/base/solutions/") and authorities.get(item["target"]) in bound:
                paths.add("repo/" + item["path"])
        baseline = {path: manifest["files"][path] for path in paths}
        if contract["baseline_sha256"] != baseline:
            raise ValueError("Selected baseline differs from packet")
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid offline assignment draw: {exc}") from exc


def _blind_id(manifest: dict, contract: dict) -> str | None:
    if not manifest.get("reviewer_solve", {}).get("blind", {}).get("required"):
        return None
    return blind_id_for_seed(manifest, contract["task_id"], bytes.fromhex(contract["seed"]))


def _reproduce_audit(audit: dict, manifest: dict, packet_id: str, contract: dict | None = None) -> None:
    try:
        seed = bytes.fromhex(audit["seed"])
        if len(seed) != 32:
            raise ValueError("seed length")
        if audit['schema'] == 'arcpuzzles-full-audit-v4':
            from .review_tickets import supplementary_contract
            if contract is None:
                raise ValueError('Supplementary tickets require their main contract')
            expected = supplementary_contract(manifest, packet_id, contract, seed, _blind_id(manifest, contract))
            if audit != expected:
                raise ValueError('Supplementary ticket draw cannot be reproduced')
            return
        if audit["schema"] == "arcpuzzles-full-audit-v2":
            expected = [manifest["all_ids"][int.from_bytes(seed, "big") % len(manifest["all_ids"])]]
            actual = [audit["task_id"]]
        elif audit["schema"] == "arcpuzzles-full-audit-v3":
            blind = _blind_id(manifest, contract) if contract is not None else None
            expected = audit_ids_for_seed([tid for tid in manifest["all_ids"] if tid != blind], seed)
            actual = [row["task_id"] for row in audit["targets"]]
        else:
            raise ValueError("Unknown audit schema")
        if actual != expected or audit["packet_id"] != packet_id:
            raise ValueError("Audit draw cannot be reproduced")
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid offline audit draw: {exc}") from exc


def _validate(raw_path: Path, review_root: Path) -> tuple[dict, bytes, list[zipfile.ZipInfo]]:
    with zipfile.ZipFile(raw_path) as archive:
        from .review_return import scan_zip
        infos = scan_zip(archive)
        contract_bytes = archive.read("ASSIGNMENT.json")
        contract = json.loads(contract_bytes)
        packet_id = contract.get("packet_id", "")
        if not re.fullmatch(r"[0-9a-f]{64}", packet_id):
            raise ValueError("Invalid packet ID")
        packet_path = review_root.parent / "var/review/full-packets" / packet_id / "request.zip"
        if not packet_path.is_file():
            raise FileNotFoundError(f"Packet not registered locally: {packet_id}")
        with zipfile.ZipFile(packet_path) as packet:
            manifest_bytes = packet_member(packet, "PACKET-MANIFEST.json")
            manifest = json.loads(manifest_bytes)
            if manifest_bytes != canonical_json(manifest) or _sha(manifest_bytes) != packet_id:
                raise ValueError("Registered packet manifest hash mismatch")
            checked = validate_full_return(archive, manifest)
            _reproduce(contract, manifest, packet)
            if contract.get('schema') == MULTI_SCHEMA:
                checked['task_ids'] = target_ids(contract)
                checked['repair_targets'] = assignment_targets(contract)
                checked['repair_outcomes'] = validate_target_outcomes(contract,
                    json.loads(archive.read('RESULTS.json')))
            if "AUDIT_ASSIGNMENT.json" in archive.namelist():
                _reproduce_audit(json.loads(archive.read("AUDIT_ASSIGNMENT.json")), manifest, packet_id, contract)
        return checked, contract_bytes, infos


def _collect_one(review_root: Path, source: Path) -> dict:
    raw = source.read_bytes()
    digest = _sha(raw)
    storage = review_root.parent / "var/review/returns"
    inbox = storage / "_inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    preserved = inbox / f"{digest}.zip"
    with _lock(review_root):
        if not preserved.exists():
            preserved.write_bytes(raw)
        if _sha(preserved.read_bytes()) != digest:
            raise RuntimeError("Content-addressed inbox collision")
        index = storage / "receipts-by-sha" / f"{digest}.json"
        cached = json.loads(index.read_text()) if index.is_file() else None
        if cached and cached.get('validation_status') == 'accepted':
            return cached
        status, reason, checked, contract_bytes, infos = "accepted", "", {}, b"", []
        try:
            checked, contract_bytes, infos = _validate(preserved, review_root)
        except zipfile.BadZipFile as exc:
            status, reason = "malformed_zip", str(exc)
        except FileNotFoundError as exc:
            status, reason = "missing_packet", str(exc)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, RuntimeError) as exc:
            status, reason = "rejected", str(exc)
        # An explicit collection retries rejected/missing-packet returns after
        # source or validator repair. Repeated identical failures reuse their
        # receipt; successful validation replaces only the lookup cache.
        if cached and cached.get('validation_status') == status and cached.get('reason') == reason:
            return cached
        identifier = checked.get("assignment_id", "unmapped")
        if status == "accepted":
            contract_path = review_root / "assignments" / identifier / "ASSIGNMENT.json"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            if contract_path.exists() and contract_path.read_bytes() != contract_bytes:
                status, reason = "rejected", "Assignment ID collides with different contract"
            elif not contract_path.exists():
                contract_path.write_bytes(contract_bytes)
        receipts_dir = review_root / (f"assignments/{identifier}/returns" if status == "accepted" else "returns/unmapped")
        receipts_dir.mkdir(parents=True, exist_ok=True)
        version = _next_return_version(review_root, receipts_dir, identifier, checked)
        destination = storage / identifier / f"{version:04d}-{digest[:12]}"
        destination.mkdir(parents=True, exist_ok=False)
        retained = destination / "original.zip"
        shutil.copy2(preserved, retained)
        if status == "accepted":
            extracted = destination / "extracted"
            extracted.mkdir()
            with zipfile.ZipFile(retained) as archive:
                for info in infos:
                    target = extracted / info.filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(info))
        receipt_path = receipts_dir / f"return-{version:04d}-{digest[:16]}.json"
        receipt = {"schema": "arcpuzzles-full-return-receipt-v2", "packet_id": checked.get("packet_id"),
                   "assignment_id": identifier, "task_id": checked.get("task_id"),
                   "audit_target": checked.get("audit_target"),
                   "audit_targets": checked.get("audit_targets", []), "version": version,
                   "zip_sha256": digest, "validation_status": status,
                   "completion_status": checked.get("completion_state", "unknown"),
                   "reviewer_solve": checked.get("reviewer_solve"),
                   "intake_summary": checked.get("intake_summary"),
                   "check_status": "not_run", "disposition_status": "unreviewed",
                   "reason": reason, "archive_path": str(retained), "receipt_path": str(receipt_path)}
        if status == 'accepted':
            contract = json.loads(contract_bytes)
            if contract.get('schema') == MULTI_SCHEMA:
                receipt['repair_targets'] = assignment_targets(contract)
                receipt['task_ids'] = target_ids(contract)
                receipt['repair_outcomes'] = checked.get('repair_outcomes',
                    (checked.get('intake_summary') or {}).get('repair_targets', []))
        if 'supplementary_tickets' in checked:
            receipt['supplementary_tickets'] = checked['supplementary_tickets']
        if checked.get("reviewer_blind_solve") is not None:
            receipt["reviewer_blind_solve"] = checked["reviewer_blind_solve"]
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        index.parent.mkdir(parents=True, exist_ok=True)
        if status == "accepted":
            from .review_maintenance import notify_accepted
            receipt["maintenance"] = notify_accepted(review_root, receipt)
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            from .review_packet_selection import queue_receipt_focus
            queue_receipt_focus(review_root, receipt)
            from .review_storage_study import retain_observations
            packet_path = review_root.parent / 'var/review/full-packets' / checked['packet_id'] / 'request.zip'
            # Optional observations never change source acceptance or admission.
            try:
                with zipfile.ZipFile(retained) as archive, packet_path.open('rb') as packet_handle:
                    observation = retain_observations(
                        review_root, archive, return_sha=digest,
                        packet_sha=hashlib.file_digest(packet_handle, 'sha256').hexdigest())
            except (OSError, ValueError, KeyError, TypeError) as exc:
                observation = dict(status='unavailable', reason=str(exc), admission_changed=False)
            if observation is not None:
                receipt['storage_study'] = observation
                receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        index.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        return receipt


def collect_full_returns(review_root: Path, directory: Path) -> dict:
    review_root = review_root.resolve()
    directory = directory.resolve()
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    receipts, ignored = [], []
    for source in sorted(directory.iterdir()):
        if not source.is_file() or not re.fullmatch(r"review_response_.*\.zip", source.name):
            ignored.append(source.name)
            continue
        try:
            receipts.append(_collect_one(review_root, source))
        except Exception as exc:  # preserve batch progress, but surface the file failure
            receipts.append({"validation_status": "collector_error", "reason": str(exc),
                             "source": str(source), "zip_sha256": _sha(source.read_bytes())})
    counts = {}
    for item in receipts:
        key = item["validation_status"]
        counts[key] = counts.get(key, 0) + 1
    from .review_full_inbox import build_full_inbox
    inbox = build_full_inbox(review_root, review_root.parent / "var/review/full-inbox")
    return {"counts": counts, "receipts": receipts, "ignored": ignored,
            "inbox": inbox["html"], "inbox_json": inbox["json"], "inbox_hint": inbox["html"]}
