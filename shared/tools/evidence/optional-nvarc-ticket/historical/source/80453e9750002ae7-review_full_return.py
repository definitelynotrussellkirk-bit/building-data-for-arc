"""Compact reviewer returns with a shared static validator."""
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

from .review_full_packet import canonical_json
from .review_feedback import feedback_items
from .review_return import MAX_MEMBERS, check_zip_budget, scan_zip
from . import review_evidence_bundle as bundles


_DIFF = re.compile(r"^diff --git a/(repo/[^\s]+) b/(repo/[^\s]+)$", re.M)
REQUIRED_DOCS = ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _allowed(path: str, contract: dict) -> bool:
    tid = contract["task_id"]
    home = f"repo/generators/{tid}/"
    if path in {home + "generator.py", home + "notes.md", home + "SUMMARY.md"}:
        return True
    if path.startswith((home + "workspace/", home + "tests/", home + "counterexamples/")):
        return True
    if path == "repo/shared/data/canonical/puzzles.jsonl":
        return True
    if path in contract["baseline_sha256"] and path.startswith("repo/shared/data/base/"):
        return True
    return False


def _canonical_only_task(before: bytes, after: bytes, task_id: str) -> None:
    old, new = before.splitlines(), after.splitlines()
    if len(old) != len(new):
        raise ValueError("Canonical row count changed")
    for left, right in zip(old, new):
        if left != right:
            a, b = json.loads(left), json.loads(right)
            if a.get("task_id") != task_id or b.get("task_id") != task_id:
                raise ValueError("Patch changed an unrelated canonical row")


def _patch_paths(patch: str, contract: dict) -> list[str]:
    if any(line.startswith(("GIT binary patch", "Binary files ", "rename from ", "rename to ",
                            "copy from ", "copy to ", "old mode ", "new mode ",
                            "deleted file mode ")) for line in patch.splitlines()):
        raise ValueError("Binary, rename, mode, or deletion patch is forbidden")
    if any(line.startswith("new file mode ") and line != "new file mode 100644"
           for line in patch.splitlines()):
        raise ValueError("Executable or nonregular new file forbidden")
    pairs = _DIFF.findall(patch)
    if not pairs:
        raise ValueError("No valid repo-rooted diff header")
    paths = []
    for old, new in pairs:
        if old != new or ".." in PurePosixPath(old).parts or "\\" in old or not _allowed(old, contract):
            raise ValueError(f"Patch path is outside selected task: {old}")
        paths.append(old)
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate patch path")
    current_path = None
    in_hunk = False
    for line in patch.splitlines():
        header = _DIFF.fullmatch(line)
        if header:
            current_path = header.group(1)
            in_hunk = False
        elif line.startswith("@@ "):
            in_hunk = True
        elif not in_hunk and line.startswith(("--- ", "+++ ")):
            value = line[4:].split("\t", 1)[0]
            prefix = "a/" if line.startswith("--- ") else "b/"
            if value != "/dev/null" and value != prefix + str(current_path):
                raise ValueError(f"Patch header escapes selected task: {value}")
    # Canonical rows are one JSON object per line. Only changed +/- rows count.
    if "repo/shared/data/canonical/puzzles.jsonl" in paths:
        in_canonical = False
        for line in patch.splitlines():
            if line.startswith("diff --git "):
                in_canonical = "repo/shared/data/canonical/puzzles.jsonl" in line
            elif in_canonical and line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                try:
                    row = json.loads(line[1:])
                except json.JSONDecodeError as exc:
                    raise ValueError("Canonical patch contains malformed row") from exc
                if row.get("task_id") != contract["generator"]["rule_task_id"]:
                    raise ValueError("Patch changed an unrelated canonical row")
    return paths


def _bundled_paths(payload: dict[str, bytes]) -> set[str]:
    if bundles.MANIFEST not in payload:
        return set()
    return {row["path"] for row in bundles.read_manifest(payload[bundles.MANIFEST])["files"]}


def _intake_summary(payload: dict[str, bytes], contract: dict, results: dict) -> dict:
    bundled = _bundled_paths(payload)
    commands = results.get("verification_commands", [])
    if not isinstance(commands, list):
        raise ValueError("Invalid verification commands")
    for index, command in enumerate(commands):
        label = f"verification_commands[{index}]"
        if not isinstance(command, dict):
            raise ValueError(f"Invalid verification command: {label} must be an object")
        cwd, argv = command.get("cwd"), command.get("argv")
        directory = PurePosixPath(cwd) if isinstance(cwd, str) else None
        evidence = command.get("evidence_paths", [])
        if directory is None or directory.is_absolute() or ".." in directory.parts or not cwd:
            raise ValueError(f"Invalid verification command: {label}.cwd must be a packet-relative directory")
        if not isinstance(argv, list) or not argv:
            raise ValueError(f"Invalid verification command: {label}.argv must be a nonempty list")
        for arg_index, value in enumerate(argv):
            if not isinstance(value, str) or not value or "\0" in value:
                raise ValueError(f"Invalid verification command: {label}.argv[{arg_index}] must be a nonempty string without NUL")
        if not isinstance(evidence, list):
            raise ValueError(f"Invalid verification command: {label}.evidence_paths must be a list")
        for path_index, path in enumerate(evidence):
            if not isinstance(path, str) or (path not in payload and path not in bundled):
                raise ValueError(f"Invalid verification command: {label}.evidence_paths[{path_index}] "
                                 f"is not packaged: {path!r}; keep command evidence under checks/ or solve/")
    paths = sorted({path for name, raw in payload.items() if name.startswith("patches/")
                    for path in _patch_paths(raw.decode("utf-8"), contract)})
    home = f"repo/generators/{contract['task_id']}/"
    components = sorted({"generator" if path == home + "generator.py" else
                         "racket" if path.startswith("repo/shared/data/") else "tests_notes"
                         for path in paths})
    feedback = feedback_items(payload["FEEDBACK_TO_CODEX.md"].decode("utf-8"))
    if len({item["id"] for item in feedback}) != len(feedback):
        raise ValueError("Repeated feedback item ID")
    audits = []
    if "AUDIT_ASSIGNMENT.json" in payload:
        audit = json.loads(payload["AUDIT_ASSIGNMENT.json"])
        if audit.get('schema') == 'arcpuzzles-full-audit-v4':
            from .review_tickets import ticket_safety_targets
            audits = ticket_safety_targets(audit, results.get('supplementary_tickets', []))
        else:
            audits = audit.get("targets", [{"task_id": audit.get("task_id"),
                                             "generator_sha256": audit.get("generator_sha256")}])
    solve = None
    if "solve/summary.json" in payload:
        source = json.loads(payload["solve/summary.json"])
        keys = ("status", "generator_hash", "instance_hash", "attempt_count", "source_kind",
                "earlier_rule_exposure", "reference_consulted_during_solve", "feedback_policy")
        solve = {key: source.get(key) for key in keys}
        solve["attempt_reports"] = sorted(name for name in payload
                                          if name.startswith("solve/attempts/") and name.endswith("/report.json"))
        reports = {name: json.loads(payload[name]) for name in solve["attempt_reports"]}
        # Preserve derivation of legacy INTAKE.json byte-for-byte in meaning;
        # only newer reports declare intent. Missing declarations stay unknown.
        if any("attempt_intent" in report for report in reports.values()):
            solve["attempt_intents"] = {name: report.get("attempt_intent", "unknown")
                                        for name, report in reports.items()}
    blind = None
    if "solve-blind/summary.json" in payload:
        source = json.loads(payload["solve-blind/summary.json"])
        blind = {key: source.get(key) for key in ("status", "solve_kind", "task_id", "generator_hash",
                 "instance_hash", "attempt_count", "source_kind", "earlier_rule_exposure",
                 "reference_consulted_during_solve", "feedback_policy")}
        blind["attempt_reports"] = sorted(name for name in payload
                                          if name.startswith("solve-blind/attempts/") and name.endswith("/report.json"))
        blind["attempt_intents"] = {name: json.loads(payload[name]).get("attempt_intent", "unknown")
                                    for name in blind["attempt_reports"]}
    summary = {"schema": "arcpuzzles-review-intake-v1", "assignment_id": contract["assignment_id"],
            "packet_id": contract["packet_id"], "task_id": contract["task_id"],
            "baseline_generator_sha256": contract["generator"]["generator_sha256"],
            "completion_state": results["completion_state"], "stopping_reason": results["stopping_reason"],
            "changed_paths": paths, "components": components, "verification_commands": commands,
            "feedback_items": feedback, "audit_targets": audits, "reviewer_solve": solve,
            "evidence_sha256": {name: _sha(raw) for name, raw in sorted(payload.items())
                                if name not in {"INTAKE.json", "RESULTS.json"}},
            "verification_status": "reviewer_reported_requires_maintainer_replay",
            "training_admitted": False}
    if 'AUDIT_ASSIGNMENT.json' in payload:
        ticket_contract = json.loads(payload['AUDIT_ASSIGNMENT.json'])
        if ticket_contract.get('schema') == 'arcpuzzles-full-audit-v4':
            from .review_tickets import ticket_report_rows
            summary['supplementary_tickets'] = ticket_report_rows(ticket_contract, results.get('supplementary_tickets', []))
            if 'work_scope' in results:
                summary['work_scope'] = results['work_scope']
            if 'delta_omissions' in results:
                summary['delta_omissions'] = results['delta_omissions']
    if "curriculum" in results:
        summary["curriculum"] = results["curriculum"]
    if blind is not None:
        # Absent for legacy returns, so their stored INTAKE.json still recomputes exactly.
        summary["reviewer_blind_solve"] = blind
    if bundled:
        manifest = bundles.read_manifest(payload[bundles.MANIFEST])
        summary["evidence_bundle"] = {"archive": bundles.ARCHIVE, "archive_sha256": manifest["archive_sha256"],
                                      "count": manifest["count"], "expanded_bytes": manifest["expanded_bytes"]}
    return summary


def validate_full_return(archive: zipfile.ZipFile, packet_manifest: dict) -> dict:
    infos = scan_zip(archive)
    names = {info.filename for info in infos}
    ticket_mode = bool(packet_manifest.get('supplementary_ticket_policy'))
    docs = set(REQUIRED_DOCS) - ({'QUESTION_ANSWER.md', 'DECISIONS.md'} if ticket_mode else set())
    required = {"ASSIGNMENT.json", "RESULTS.json", *docs}
    if ticket_mode:
        required.add('AUDIT_ASSIGNMENT.json')
    if not required <= names:
        raise ValueError(f"Missing required return files: {sorted(required - names)}")
    contract = json.loads(archive.read("ASSIGNMENT.json"))
    packet_id = _sha(canonical_json(packet_manifest))
    tid = contract.get("task_id")
    if (contract.get("schema") != "arcpuzzles-full-assignment-v2" or contract.get("packet_id") != packet_id
            or tid not in packet_manifest["main_ids"] or not re.fullmatch(r"review-[0-9a-f]{16}", contract.get("assignment_id", ""))):
        raise ValueError("Invalid full-packet assignment contract")
    row = packet_manifest["generators"][tid]
    if contract.get("generator") != row:
        raise ValueError("Generator contract does not match packet")
    for path, digest in contract.get("baseline_sha256", {}).items():
        if packet_manifest["files"].get(path) != digest:
            raise ValueError(f"Baseline hash differs from packet: {path}")
    question = contract.get("question")
    if question not in packet_manifest["questions"]:
        raise ValueError("Question differs from packet")
    audit = None
    audit_targets = []
    if "AUDIT_ASSIGNMENT.json" in names:
        audit = json.loads(archive.read("AUDIT_ASSIGNMENT.json"))
        if audit.get("packet_id") != packet_id:
            raise ValueError("Invalid audit contract")
        if audit.get("schema") == "arcpuzzles-full-audit-v2":
            targets = [{"task_id": audit.get("task_id"), "generator_sha256": audit.get("generator_sha256")}]
        elif audit.get("schema") == "arcpuzzles-full-audit-v3":
            targets = audit.get("targets")
            if not isinstance(targets, list) or len(targets) != 2:
                raise ValueError("Invalid two-target audit contract")
        elif audit.get('schema') == 'arcpuzzles-full-audit-v4' and ticket_mode:
            from .review_tickets import supplementary_contract
            from .review_full_draw import blind_id_for_seed
            blind = (blind_id_for_seed(packet_manifest, contract['task_id'], bytes.fromhex(contract['seed']))
                     if packet_manifest.get('reviewer_solve', {}).get('blind', {}).get('required') else None)
            expected = supplementary_contract(packet_manifest, packet_id, contract, bytes.fromhex(audit['seed']), blind)
            if audit != expected:
                raise ValueError('Supplementary ticket draw cannot be reproduced')
            targets = []  # Actual safety findings come only from structured ticket outcomes below.
        else:
            raise ValueError("Invalid audit contract")
        if ticket_mode and audit.get('schema') != 'arcpuzzles-full-audit-v4':
            raise ValueError('This packet requires its supplementary ticket contract')
        for target in targets:
            if not isinstance(target, dict):
                raise ValueError("Invalid audit contract")
            target_id = target.get("task_id")
            if (target_id not in packet_manifest["all_ids"]
                    or target.get("generator_sha256") != packet_manifest["generators"][target_id]["generator_sha256"]):
                raise ValueError("Invalid audit contract")
            audit_targets.append(target_id)
        if len(set(audit_targets)) != len(audit_targets):
            raise ValueError("Repeated audit target")
    results = json.loads(archive.read("RESULTS.json"))
    if (results.get("schema") != "arcpuzzles-full-results-v2"
            or results.get("assignment_id") != contract["assignment_id"]
            or results.get("completion_state") not in {"complete", "blocked", "in_progress"}):
        raise ValueError("Invalid result identity or completion state")
    ticket_reports = None
    if ticket_mode:
        from .review_tickets import validate_ticket_reports, ticket_safety_targets, copied_transport_path
        expanded_names = names | (_bundled_paths({bundles.MANIFEST: archive.read(bundles.MANIFEST)})
                                  if bundles.MANIFEST in names else set())
        if any(copied_transport_path(name) for name in expanded_names):
            raise ValueError('Return contains copied packet, checkout or runtime; send only the delta')
        ticket_reports = validate_ticket_reports(audit, results.get('supplementary_tickets'), expanded_names)
        audit_targets = [t['task_id'] for t in ticket_safety_targets(audit, ticket_reports)]
    artifacts = results.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("Missing artifact declaration")
    expected_names = names - {"ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json", "BLIND_ASSIGNMENT.json", "RESULTS.json"}
    declared = set()
    for item in artifacts:
        path = item.get("path") if isinstance(item, dict) else None
        if path not in expected_names or not item.get("kind") or path in declared:
            raise ValueError(f"Invalid or repeated artifact declaration: {path}")
        declared.add(path)
        if _sha(archive.read(path)) != item.get("sha256"):
            raise ValueError(f"Artifact hash differs: {path}")
    if declared != expected_names:
        raise ValueError(f"Undeclared return files: {sorted(expected_names - declared)}")
    if bundles.MANIFEST in names or bundles.ARCHIVE in names:
        if not {bundles.MANIFEST, bundles.ARCHIVE} <= names:
            raise ValueError("Evidence bundle needs both its archive and manifest")
        bundle_manifest = bundles.read_manifest(archive.read(bundles.MANIFEST))
        bundles.check_budget(bundle_manifest, [(info.filename, info.file_size) for info in infos
                                               if info.filename != bundles.ARCHIVE])
        bundles.verify(archive.read(bundles.ARCHIVE), bundle_manifest)
        if {row["path"] for row in bundle_manifest["files"]} & names:
            raise ValueError("A bundled evidence path is also an ordinary return member")
        # The bundle counts at its expanded size, so the existing limit still bounds extraction.
        check_zip_budget([(info.filename, bundle_manifest["expanded_bytes"] if info.filename == bundles.ARCHIVE
                           else info.file_size) for info in infos])
    if ticket_mode and any(r['type'] == 'nvarc_visual' for r in ticket_reports):
        # Verify optional dataset proof bytes as well as declarations. Only the
        # selected one-file evidence is retained when checks are bundled.
        selected = {p for r in ticket_reports if r['type'] == 'nvarc_visual' for p in r['evidence_paths']}
        bundled_proofs = (bundles.verify(archive.read(bundles.ARCHIVE), bundle_manifest,
            retain=selected & {r['path'] for r in bundle_manifest['files']}) or {}
            if selected and bundles.MANIFEST in names else {})
        validate_ticket_reports(audit, ticket_reports, expanded_names,
            read_member=lambda name: bundled_proofs[name] if name in bundled_proofs else archive.read(name))
    if "INTAKE.json" in names:
        expected = _intake_summary({name: archive.read(name) for name in names
                                    if name not in {"INTAKE.json", "RESULTS.json"}}, contract, results)
        recorded = json.loads(archive.read("INTAKE.json"))
        if recorded != expected:
            # Older builders skipped parenthetical feedback headings. Accept
            # only their exact derivation; all other fields remain source-bound.
            legacy = dict(expected)
            legacy["feedback_items"] = feedback_items(
                archive.read("FEEDBACK_TO_CODEX.md").decode("utf-8"), qualified_headings=False)
            if recorded != legacy:
                raise ValueError("Invalid intake summary: differs from retained source")
    if ticket_mode:
        if ('AUDIT.md' in names) != bool(audit_targets):
            raise ValueError('AUDIT.md is only required for actual supplementary safety findings')
    elif ("AUDIT.md" in names) != (audit is not None):
        raise ValueError("Audit finding and contract must appear together")
    if audit and (audit["schema"] == "arcpuzzles-full-audit-v3" or (ticket_mode and audit_targets)):
        audit_text = archive.read("AUDIT.md").decode("utf-8")
        sections = audit_sections(audit_text)
        headings = re.findall(r"^## ([A-Za-z0-9][A-Za-z0-9_-]*)\s*$", audit_text, re.M)
        if (len(headings) != len(audit_targets) or set(headings) != set(audit_targets)
                or any(not sections[tid].partition("\n")[2].strip() for tid in audit_targets)):
            raise ValueError("Missing or extra audit target section")
    patches = []
    for name in sorted(n for n in names if n.startswith("patches/")):
        patch = archive.read(name).decode("utf-8")
        patches.extend(_patch_paths(patch, contract))
    for info in infos:
        archive.read(info)  # verify CRC/decompression before returning
    from .review_solve import validate_solve_payload
    reviewer_solve = validate_solve_payload(archive.read, names, contract,
        complete=results["completion_state"] == "complete" and bool(packet_manifest.get("reviewer_solve", {}).get("required")))
    blind_required = bool(packet_manifest.get("reviewer_solve", {}).get("blind", {}).get("required"))
    has_blind_files = any(name == "BLIND_ASSIGNMENT.json" or name.startswith("solve-blind/") for name in names)
    blind_solve = None
    if blind_required:
        from .review_full_draw import blind_contract
        if "BLIND_ASSIGNMENT.json" not in names:
            raise ValueError("Packet requires a blind solve assignment")
        blind = json.loads(archive.read("BLIND_ASSIGNMENT.json"))
        if blind != blind_contract(packet_manifest, packet_id, contract):
            raise ValueError("Blind solve assignment differs from the draw for this assignment seed")
        blind_solve = validate_solve_payload(archive.read, names, blind, kind="blind",
            complete=results["completion_state"] == "complete")
    elif has_blind_files:
        raise ValueError("Blind solve files in a return whose packet has no blind solve")
    expected_feedback = packet_manifest.get("reviewer_solve", {}).get("feedback_policy")
    for solve in (reviewer_solve, blind_solve):
        if solve and expected_feedback and solve.get("feedback_policy") != expected_feedback:
            raise ValueError("Reviewer solve feedback policy differs from its source packet")
    checked = {"packet_id": packet_id, "assignment_id": contract["assignment_id"], "task_id": tid,
               "audit_target": audit_targets[0] if audit_targets else None,
               "audit_targets": audit_targets,
               "completion_state": results["completion_state"], "artifacts": artifacts,
               "patch_paths": sorted(set(patches)), "reviewer_solve": reviewer_solve,
               "intake_summary": json.loads(archive.read("INTAKE.json")) if "INTAKE.json" in names else None}
    if ticket_mode:
        from .review_tickets import ticket_report_rows
        checked['supplementary_tickets'] = ticket_report_rows(audit, ticket_reports)
    if blind_solve is not None:
        checked["reviewer_blind_solve"] = blind_solve
    return checked


def audit_sections(text: str) -> dict[str, str]:
    """Split the v3 AUDIT.md by exact task headings for per-task intake."""
    matches = list(re.finditer(r"^## ([A-Za-z0-9][A-Za-z0-9_-]*)\s*$", text, re.M))
    if not matches:
        return {}
    return {match.group(1): text[match.start():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
            for i, match in enumerate(matches)}


def _text(raw: bytes, path: str) -> str:
    if b"\0" in raw:
        raise ValueError(f"Binary source is not patchable: {path}")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Non-UTF-8 source is not patchable: {path}") from exc


def _diff(path: str, before: bytes | None, after: bytes) -> str:
    # Git records are LF-delimited; splitlines also splits literal CR/Unicode
    # separators inside a source line and produces invalid hunk counts.
    def lines(raw: bytes) -> list[str]:
        text = _text(raw, path)
        parts = text.split("\n")
        return [part + "\n" for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])
    old = lines(before or b"")
    new = lines(after)
    header = f"diff --git a/{path} b/{path}\n"
    if before is None:
        header += "new file mode 100644\n"
    fromfile = "/dev/null" if before is None else f"a/{path}"
    body = "".join(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
                   for line in difflib.unified_diff(old, new, fromfile=fromfile, tofile=f"b/{path}"))
    return header + body


def build_full_return(packet_root: Path, out: Path | None = None, *, bundle_evidence: bool = False) -> dict:
    packet_root = packet_root.resolve()
    manifest = json.loads((packet_root / "PACKET-MANIFEST.json").read_text())
    contract_bytes = (packet_root / "ASSIGNMENT.json").read_bytes()
    contract = json.loads(contract_bytes)
    if contract.get("packet_id") != _sha(canonical_json(manifest)):
        raise ValueError("Assignment packet ID mismatch")
    tid = contract["task_id"]
    for path, digest in contract["baseline_sha256"].items():
        frozen = packet_root / ".review/baseline" / path
        if not frozen.is_file() or frozen.is_symlink() or _sha(frozen.read_bytes()) != digest:
            raise ValueError(f"Frozen baseline changed: {path}")
    changes = []
    home = f"repo/generators/{tid}/"
    candidates = set(contract["baseline_sha256"])
    candidates.update(path.relative_to(packet_root).as_posix() for path in
                      (packet_root / home).rglob("*")
                      if (path.is_file() or path.is_symlink())
                      and not any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
                                  for part in path.relative_to(packet_root).parts)
                      and path.suffix not in {".pyc", ".pyo"})
    for path in sorted(candidates):
        if path not in manifest["files"] and not path.startswith(home):
            raise ValueError(f"Unexpected new source path: {path}")
        target = packet_root / path
        if target.is_symlink() or (target.exists() and (not target.is_file() or target.stat().st_mode & 0o111)):
            raise ValueError(f"Unsafe changed source: {path}")
        baseline = packet_root / ".review/baseline" / path
        before = baseline.read_bytes() if baseline.is_file() else None
        after = target.read_bytes() if target.is_file() else None
        if after == before:
            continue
        if not _allowed(path, contract) or after is None:
            raise ValueError(f"Changed source outside allowed task scope: {path}")
        if path == "repo/shared/data/canonical/puzzles.jsonl":
            _canonical_only_task(before, after, contract["generator"]["rule_task_id"])
        changes.append(_diff(path, before, after))
    # Detect edits to the rest of the packaged repository, including helpers.
    for path, digest in manifest["files"].items():
        if path.startswith("repo/") and path not in candidates:
            target = packet_root / path
            if not target.is_file() or target.is_symlink() or _sha(target.read_bytes()) != digest:
                raise ValueError(f"Changed or missing shared packet source: {path}")
    for target in (packet_root / "repo").rglob("*"):
        if not (target.is_file() or target.is_symlink()):
            continue
        path = target.relative_to(packet_root).as_posix()
        if any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
               for part in target.relative_to(packet_root).parts) or target.suffix in {".pyc", ".pyo"}:
            continue
        if path not in manifest["files"] and path not in candidates:
            raise ValueError(f"Undeclared new source outside selected generator: {path}")
    payload = {"ASSIGNMENT.json": contract_bytes}
    ticket_mode = bool(manifest.get('supplementary_ticket_policy'))
    audit_path = packet_root / "AUDIT_ASSIGNMENT.json"
    if ticket_mode and not audit_path.is_file():
        raise ValueError('Draw and report the two supplementary tickets with assignment.py tickets')
    if audit_path.is_file():
        payload["AUDIT_ASSIGNMENT.json"] = audit_path.read_bytes()
        if not ticket_mode and not (packet_root / "AUDIT.md").is_file():
            raise ValueError("Drawn audit needs AUDIT.md findings")
    blind_path = packet_root / "BLIND_ASSIGNMENT.json"
    if blind_path.is_file():
        payload["BLIND_ASSIGNMENT.json"] = blind_path.read_bytes()
    for name in REQUIRED_DOCS:
        path = packet_root / name
        if ticket_mode and name in {'QUESTION_ANSWER.md', 'DECISIONS.md'} and not path.is_file():
            continue
        if ticket_mode and name == 'FEEDBACK_TO_CODEX.md' and not path.is_file():
            payload[name] = b''
            continue
        if not path.is_file():
            raise ValueError(f"Missing review document: {name}")
        payload[name] = path.read_bytes()
    if audit_path.is_file() and (packet_root / 'AUDIT.md').is_file():
        payload["AUDIT.md"] = (packet_root / "AUDIT.md").read_bytes()
    checks = packet_root / "checks"
    if checks.is_symlink():
        raise ValueError(f"Symlink check evidence: {checks}")
    delta_omissions = 0
    if checks.exists():
        for path in checks.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink check evidence: {path}")
            if path.is_file():
                name = path.relative_to(packet_root).as_posix()
                if ticket_mode:
                    from .review_tickets import copied_transport_path
                    if copied_transport_path(name):
                        delta_omissions += 1
                        continue
                payload[name] = path.read_bytes()
    if changes:
        payload["patches/source.patch"] = "".join(changes).encode("utf-8")
    solve_root = packet_root / "solve"
    if solve_root.is_symlink():
        raise ValueError(f"Symlink solve evidence: {solve_root}")
    if solve_root.exists():
        for path in solve_root.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink solve evidence: {path}")
            if path.is_file() and not any(p.startswith(".") or p == "__pycache__" for p in path.relative_to(solve_root).parts):
                payload[path.relative_to(packet_root).as_posix()] = path.read_bytes()
        frozen_generator = packet_root / ".review/solve-private/generator.py"
        if frozen_generator.is_file():
            payload["solve/source/generator.py"] = frozen_generator.read_bytes()
    blind_root = packet_root / "solve-blind"
    if blind_root.is_symlink():
        raise ValueError(f"Symlink solve evidence: {blind_root}")
    if blind_root.exists():
        for path in blind_root.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink solve evidence: {path}")
            if path.is_file() and not any(p.startswith(".") or p == "__pycache__" for p in path.relative_to(blind_root).parts):
                payload[path.relative_to(packet_root).as_posix()] = path.read_bytes()
        frozen_blind = packet_root / ".review/solve-private-blind/generator.py"
        if frozen_blind.is_file():
            payload["solve-blind/source/generator.py"] = frozen_blind.read_bytes()
    projected = len(payload) + 2  # INTAKE.json and RESULTS.json
    checks_files = {name: raw for name, raw in payload.items() if name.startswith("checks/")}
    if checks_files and (bundle_evidence or projected > MAX_MEMBERS):
        for name in checks_files:
            del payload[name]
        payload.update(bundles.pack(checks_files))
        print(f"Packed {len(checks_files)} checks/ files into {bundles.ARCHIVE}; "
              f"return members {projected} -> {len(payload) + 2} (limit {MAX_MEMBERS}).", file=sys.stderr)
    results_path = packet_root / "RESULTS.json"
    supplied = json.loads(results_path.read_text()) if results_path.is_file() else {}
    results = {"schema": "arcpuzzles-full-results-v2", "assignment_id": contract["assignment_id"],
               "generator_id": tid, "completion_state": supplied.get("completion_state", "in_progress"),
               "stopping_reason": supplied.get("stopping_reason", "not recorded"),
               "modified_components": supplied.get("modified_components", []),
               "remaining_failures": supplied.get("remaining_failures", []),
               "verification_commands": supplied.get("verification_commands", []),
               "artifacts": [{"path": name, "kind": ("patch" if name.startswith("patches/") else
                             "check" if name.startswith("checks/") or name.startswith("EVIDENCE-BUNDLE.") else
                             "document"), "sha256": _sha(raw)}
                             for name, raw in sorted(payload.items())
                             if name not in {"ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json", "BLIND_ASSIGNMENT.json"}]}
    if ticket_mode:
        results['supplementary_tickets'] = supplied.get('supplementary_tickets')
        results['delta_omissions'] = {'copied_transport_or_runtime_files': delta_omissions}
        if 'work_scope' in supplied:
            results['work_scope'] = supplied['work_scope']
    if "curriculum" in supplied:
        from .review_curriculum import bind_curriculum
        evidence = {name: _sha(raw) for name, raw in payload.items()}
        if bundles.MANIFEST in payload:
            evidence.update({row["path"]: row["sha256"] for row in
                             bundles.read_manifest(payload[bundles.MANIFEST])["files"]})
        results["curriculum"] = bind_curriculum(supplied["curriculum"], task_id=tid,
            generator=(packet_root / f"repo/generators/{tid}/generator.py").read_bytes(),
            canonical=(packet_root / "repo/shared/data/canonical/puzzles.jsonl").read_bytes(),
            rule_task_id=contract["generator"]["rule_task_id"], evidence=evidence)
    if ticket_mode:
        from .review_tickets import validate_ticket_reports
        audit_contract = json.loads(payload['AUDIT_ASSIGNMENT.json'])
        evidence_names = set(payload) | _bundled_paths(payload)
        supplied_reports = validate_ticket_reports(audit_contract, results.get('supplementary_tickets'), evidence_names)
        selected = {p for r in supplied_reports if r['type'] == 'nvarc_visual' for p in r['evidence_paths']}
        bundled_proofs = (bundles.verify(payload[bundles.ARCHIVE], bundles.read_manifest(payload[bundles.MANIFEST]),
            retain=selected & _bundled_paths(payload)) or {} if selected and bundles.MANIFEST in payload else {})
        validate_ticket_reports(audit_contract, supplied_reports, evidence_names,
                                read_member=lambda name: bundled_proofs[name] if name in bundled_proofs else payload[name])
    payload["INTAKE.json"] = canonical_json(_intake_summary(payload, contract, results))
    results["artifacts"].append({"path": "INTAKE.json", "kind": "document", "sha256": _sha(payload["INTAKE.json"])})
    payload["RESULTS.json"] = canonical_json(results)
    out = (out or packet_root / f"review_response_{contract['assignment_id']}.zip").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(out)
    expanded = (bundles.read_manifest(payload[bundles.MANIFEST])["expanded_bytes"]
                if bundles.MANIFEST in payload else None)
    check_zip_budget((name, expanded if name == bundles.ARCHIVE else len(raw)) for name, raw in payload.items())
    with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    try:
        with zipfile.ZipFile(out) as archive:
            checked = validate_full_return(archive, manifest)
    except Exception:
        out.unlink()
        raise
    return {"zip": str(out), "zip_sha256": _sha(out.read_bytes()), **checked}
