#!/usr/bin/env python3
"""Verify the selected-task delta and all source-bound review evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
TASK_ID = "fcac68386147"
TASK = REPO / "generators" / TASK_ID
BASE_TASK = WORK / ".review" / "baseline" / "repo" / "generators" / TASK_ID
EVIDENCE = HERE / "repeat-offset-evidence-v1"
OUT = HERE / "final-integrity.json"

EXPECTED = {
    "generator.py": "e3cb70cda6c756fd3124cc0211641e83381f144ccc3245db06653f775236c005",
    "tests/test_generator_fcac68386147.py": "8db8ce1b146c7021c62258d4755d60ab95c9b2f0f7bc6db9ac6a6a7022056ee1",
    "tests/test_parametric_repeat_offsets.py": "315327109e177cc0b20ae54846f83ad49a68bc45c7a299540fc1ceb281801a89",
    "workspace/parametric/prototype.py": "9091b65104ae88b4226d1e92063b6e8bcd6f49c6ee1c36a61eb442949a2cc431",
    "workspace/parametric/README.md": "497003e4b036e92900079c006f895d830cab223a85ed110f25ad7b95131235af",
}
EXPECTED_CANONICAL_SOURCE = "e78dc62cf0344fbef6542ba31bb4f9f50b42ab2458d9378af989e89482329eab"
EXPECTED_RULE_HASH = "350a34d04ac2"
EXPECTED_LEDGER = "bf156091ce279591defd86beeadae028b58330a542516f07924da6c4bf066bb7"

checks: list[dict[str, Any]] = []
errors: list[str] = []


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name: str, ok: bool, detail: Any) -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})
    if not ok:
        errors.append(f"{name}: {detail}")


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


# Required control records and documents.
for rel in (
    "ASSIGNMENT.json",
    "AUDIT_ASSIGNMENT.json",
    "TICKETS.md",
    "REVIEW.md",
    "FEEDBACK_TO_CODEX.md",
    "RESULTS.json",
):
    path = WORK / rel
    record(f"required:{rel}", path.is_file() and not path.is_symlink(), str(path.relative_to(WORK)))
record("no-audit-md-without-finding", not (WORK / "AUDIT.md").exists(), "AUDIT.md absent")

# Selected source identities and immutable production source.
source_hashes: dict[str, str] = {}
for rel, expected in EXPECTED.items():
    path = TASK / rel
    actual = sha(path) if path.is_file() else "missing"
    source_hashes[rel] = actual
    record(f"source-sha:{rel}", actual == expected, {"expected": expected, "actual": actual})
record(
    "production-generator-equals-frozen-baseline",
    (TASK / "generator.py").read_bytes() == (BASE_TASK / "generator.py").read_bytes(),
    EXPECTED["generator.py"],
)
ledger = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
record("canonical-ledger-sha", sha(ledger) == EXPECTED_LEDGER, {"expected": EXPECTED_LEDGER, "actual": sha(ledger)})

# RESULTS evidence references must exist and ticket count/scope must be exact.
results = load(WORK / "RESULTS.json")
record("results-complete", results.get("completion_state") == "complete", results.get("completion_state"))
commands = results.get("verification_commands", [])
missing_evidence: list[str] = []
for row in commands:
    for rel in row.get("evidence_paths", []):
        if not (WORK / rel).is_file():
            missing_evidence.append(rel)
record("results-evidence-paths-exist", not missing_evidence, missing_evidence or f"{sum(len(r.get('evidence_paths', [])) for r in commands)} paths")
reported_tickets = results.get("supplementary_tickets", [])
record("exactly-two-supplementary-tickets", len(reported_tickets) == 2, [r.get("ticket_id") for r in reported_tickets])

# Ticket assignment/result identities and outcomes.
audit = load(WORK / "AUDIT_ASSIGNMENT.json")
ticket_contracts = {r["ticket_id"]: r for r in audit.get("tickets", [])}
record("audit-has-two-ticket-contracts", len(ticket_contracts) == 2, sorted(ticket_contracts))
for reported in reported_tickets:
    ticket_id = reported.get("ticket_id")
    contract = ticket_contracts.get(ticket_id)
    path = WORK / "checks" / "tickets" / str(ticket_id) / "result.json"
    data = load(path) if path.is_file() else {}
    identity_ok = bool(contract) and all(
        [
            data.get("ticket_id") == ticket_id,
            data.get("task_id") == contract.get("task_id"),
            data.get("source_sha256") == contract.get("generator_sha256"),
            data.get("rule_hash") == contract.get("rule_hash"),
            data.get("status") == "pass",
            data.get("finding") is None,
            reported.get("status") == "completed",
        ]
    )
    record(
        f"ticket:{ticket_id}",
        identity_ok,
        {
            "type": data.get("schema"),
            "status": data.get("status"),
            "task_id": data.get("task_id"),
            "source_sha256": data.get("source_sha256"),
            "finding": data.get("finding"),
        },
    )

# Final test gate.
final_tests = load(HERE / "verification-final-task-tests" / "result.json")
record(
    "fresh-final-task-tests",
    final_tests.get("passed") is True and final_tests.get("status") == "completed" and final_tests.get("task_id") == TASK_ID,
    {"passed": final_tests.get("passed"), "status": final_tests.get("status"), "task_id": final_tests.get("task_id")},
)

# Prototype evidence report and exact Racket receipts.
report = load(EVIDENCE / "report.json")
summary = report.get("summary", {})
record(
    "prototype-report-pass",
    report.get("status") == "pass"
    and report.get("prototype_version") == "repeat-offset-prototype-v1"
    and report.get("source_sha256", {}).get(f"generators/{TASK_ID}/generator.py") == EXPECTED["generator.py"]
    and report.get("source_sha256", {}).get(f"generators/{TASK_ID}/workspace/parametric/prototype.py") == EXPECTED["workspace/parametric/prototype.py"],
    {"status": report.get("status"), "prototype_version": report.get("prototype_version")},
)
record(
    "prototype-four-settings-four-query-contract",
    len(report.get("rules", [])) == 4
    and len(report.get("episodes", [])) == 4
    and report.get("counts", {}).get("queries") == 4
    and report.get("counts", {}).get("demos") == 3
    and summary.get("all_declared_rivals_refuted") is True
    and summary.get("all_queries_distinguish_every_rival") is True,
    {"rules": len(report.get("rules", [])), "episodes": len(report.get("episodes", [])), "counts": report.get("counts")},
)

receipt_outputs = 0
receipt_rows: list[dict[str, Any]] = []
for rule in report.get("rules", []):
    rule_path = EVIDENCE / rule["private_rule_path"]
    receipt_path = EVIDENCE / rule["private_receipt_path"]
    receipt_doc = load(receipt_path)
    receipt = receipt_doc.get("receipt", {})
    outputs = receipt.get("test_outputs", [])
    receipt_outputs += len(outputs)
    stored_rule = rule_path.read_text(encoding="utf-8") if rule_path.is_file() else ""
    exact_program = stored_rule[:-1] if stored_rule.endswith("\n") else stored_rule
    ok = (
        rule_path.is_file()
        and hashlib.sha256(exact_program.encode("utf-8")).hexdigest() == rule.get("program_sha256")
        and receipt_doc.get("program_sha256") == rule.get("program_sha256")
        and receipt.get("status") == "pass"
        and receipt.get("backend") == "racket"
        and receipt.get("process", {}).get("returncode") == 0
        and receipt.get("input_purity") is True
        and len(outputs) == 28
    )
    receipt_rows.append(
        {
            "setting": rule.get("setting"),
            "ok": ok,
            "backend": receipt.get("backend"),
            "status": receipt.get("status"),
            "outputs": len(outputs),
        }
    )
record("exact-racket-receipts", all(r["ok"] for r in receipt_rows) and receipt_outputs == 112, {"total_outputs": receipt_outputs, "rules": receipt_rows})
canonical_rules = [row for row in report.get("rules", []) if row.get("canonical_default")]
record(
    "canonical-default-exact-source",
    len(canonical_rules) == 1 and canonical_rules[0].get("program_sha256") == EXPECTED_CANONICAL_SOURCE,
    canonical_rules,
)

# Public export integrity and no hidden fields.
public_rows: list[dict[str, Any]] = []
for episode in report.get("episodes", []):
    public_path = EVIDENCE / episode["public_path"]
    private_path = EVIDENCE / episode["private_path"]
    raw = public_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    public = json.loads(raw)
    private = load(private_path)
    demos = private["pairs"][: private["demo_count"]]
    queries = private["pairs"][private["demo_count"] :]
    reconstructed = {
        "train": [{"input": p["input"], "output": p["output"]} for p in demos],
        "test": [{"input": p["input"]} for p in queries],
    }
    ok = (
        digest == episode.get("public_sha256")
        and public_path.stem == digest
        and set(public) == {"train", "test"}
        and public == reconstructed
        and private.get("public_sha256") == digest
        and private.get("program_sha256") in {r.get("program_sha256") for r in report.get("rules", [])}
    )
    public_rows.append({"path": episode["public_path"], "ok": ok, "sha256": digest})
record("public-private-export-integrity", all(r["ok"] for r in public_rows) and len(public_rows) == 4, public_rows)

# Bounded adversarial probe.
adversarial = load(HERE / "adversarial-probe.json")
public_surface = adversarial.get("surfaces", {}).get("public_private_export", {})
sampler_surface = adversarial.get("surfaces", {}).get("sampler_count_boundaries", {})
record(
    "bounded-adversarial-probe",
    adversarial.get("status") == "pass"
    and public_surface.get("hidden_field_leaks") == 0
    and public_surface.get("private_to_public_exact_reconstructions") == 4
    and sampler_surface.get("duplicate_or_rule_stream_coupling_findings") == 0
    and sampler_surface.get("inputs_checked") == 4096,
    adversarial.get("surfaces"),
)

# Task-local manifest is itself independently reproducible.
manifest_path = TASK / "workspace" / "parametric" / "evidence" / "manifest.json"
manifest = load(manifest_path)
manifest_failures: list[dict[str, Any]] = []
for row in manifest.get("files", []):
    path = WORK / row["path"]
    actual_sha = sha(path) if path.is_file() else "missing"
    actual_bytes = path.stat().st_size if path.is_file() else None
    if actual_sha != row.get("sha256") or actual_bytes != row.get("bytes"):
        manifest_failures.append(
            {"path": row.get("path"), "expected_sha": row.get("sha256"), "actual_sha": actual_sha, "expected_bytes": row.get("bytes"), "actual_bytes": actual_bytes}
        )
for rel, expected in manifest.get("source_sha256", {}).items():
    path = REPO / rel
    actual = sha(path) if path.is_file() else "missing"
    if actual != expected:
        manifest_failures.append({"path": f"repo/{rel}", "expected_sha": expected, "actual_sha": actual})
record(
    "task-local-evidence-manifest",
    not manifest_failures
    and manifest.get("canonical_rule_hash") == EXPECTED_RULE_HASH
    and manifest.get("canonical_source_sha256") == EXPECTED_CANONICAL_SOURCE
    and manifest.get("production_parametric_api") is False
    and manifest.get("variant_approved") is False,
    manifest_failures or {"files": len(manifest.get("files", [])), "rule_hash": manifest.get("canonical_rule_hash")},
)

payload = {
    "schema": "fcac68386147-final-integrity-v1",
    "status": "pass" if not errors else "fail",
    "task_id": TASK_ID,
    "source_sha256": source_hashes,
    "checks_run": len(checks),
    "checks_passed": sum(1 for row in checks if row["ok"]),
    "errors": errors,
    "checks": checks,
}
OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({k: payload[k] for k in ("schema", "status", "task_id", "checks_run", "checks_passed", "errors")}, indent=2))
sys.exit(0 if not errors else 1)
