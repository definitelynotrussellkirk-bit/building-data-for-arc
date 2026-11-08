"""Replay one pinned Python-only audit; no Racket or peer edits.

The retained probe is executed only after its complete asset closure and audited
source are verified. Its three canonical cases, two control cases and twelve
ordinary draws must reproduce exactly. This does not test reference outputs.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback


HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK_ID = "5a0a99ffdb0a"
TICKET_ID = "ticket-ab0d200dcc8bcb90"
RETURN_ID = "review-c91c8b8b50062268:v0001"
SOURCE_SHA = "569741a2236e8da7ae9888a05a27d3a29c7b398710d858397fce143556bb387b"
INDEX_SHA = "bdc5be19d0b56793a134a70949261eac488a6e54d1e0cb848af931943890b040"
RECORD_SHA = "86b62d6f2ff2f87bf19e645e8fa3298f034bf8712e35efe374cec845825fc60e"
MANIFEST_SHA = "6c5ff4f6690bf17c2a74c2990865f485626e04569846d47a0cab60195e726209"
RULE_SHA = "e9baaaadfd93848762d2c35290411894ea8e32d3b7fe98596af4edaaf46bdc4d"
RULE_HASH = "e9baaaadfd93"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_sha(value):
    # Match the ticket producer, including its default ensure_ascii=True.
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def verified_file(path, expected, *, size=None):
    raw = path.read_bytes()
    actual = sha(raw)
    if actual != expected or (size is not None and len(raw) != size):
        raise ValueError(f"Pinned asset mismatch: {path}: {actual}, {len(raw)} bytes")
    return raw, {"path": str(path.relative_to(WORK)), "sha256": actual,
                 "bytes": len(raw), "verified": True}


def deadline(signum, frame):
    raise TimeoutError("Bounded replay exceeded its 110-second internal deadline")


def main():
    started = time.monotonic()
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(110)
    result = {
        "schema": "supplementary-audit-replay-v1", "ticket_id": TICKET_ID,
        "type": "audit_replay", "task_id": TASK_ID,
        "audit_return_id": RETURN_ID, "status": "blocked",
        "argv": [sys.executable, "-B", *sys.argv], "cwd": str(Path.cwd()),
        "environment": {"PYTHONPATH": os.environ.get("PYTHONPATH")},
        "probe_sha256": sha(Path(__file__).read_bytes()),
        "probe_seed": "c93a33b3192289e7122a41c6ded1924cbb2e42da6c6f5b5b76a88124bc218cbb",
        "authoring_elapsed_minutes": None, "racket_executed": False,
        "scope": "Exact retained Python-only witness: 3 canonical inputs, 2 override cases, 12 ordinary draws. No reference-output or lesson-identifiability claim.",
        "bindings": {},
    }
    try:
        home = REPO / "generators" / TASK_ID
        _, result["bindings"]["source"] = verified_file(home / "generator.py", SOURCE_SHA)
        raw, result["bindings"]["audit_index"] = verified_file(home / "evidence/review_index.json", INDEX_SHA)
        index = json.loads(raw)
        audits = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
        if len(audits) != 1 or json_sha(audits[0]) != RECORD_SHA:
            raise ValueError("Pinned audit record mismatch")
        audit = audits[0]
        if audit["source_sha256"] != SOURCE_SHA or index["current_source_sha256"] != SOURCE_SHA:
            raise ValueError("Audit source binding mismatch")
        result["bindings"]["audit_record_sha256"] = RECORD_SHA
        manifest_path = home / "counterexamples/review-c91c8b8b50062268-v0001/audit_assets.json"
        raw, result["bindings"]["assets_manifest"] = verified_file(manifest_path, MANIFEST_SHA)
        manifest = json.loads(raw)
        if (audit["assets_manifest"] != str(manifest_path.relative_to(REPO))
                or audit["assets_manifest_sha256"] != MANIFEST_SHA
                or manifest["audited_generator_sha256"] != SOURCE_SHA
                or manifest["return_id"] != RETURN_ID):
            raise ValueError("Audit asset identity mismatch")
        verified_assets = []
        assets = {}
        for entry in manifest["files"]:
            path = (REPO / entry["path"]).resolve()
            if not path.is_relative_to(home.resolve()):
                raise ValueError("Retained asset escapes the audited task")
            _, binding = verified_file(path, entry["sha256"], size=entry["bytes"])
            verified_assets.append(binding)
            assets[entry["original_member"]] = path
        result["bindings"]["assets"] = verified_assets
        prefix = f"checks/audit/{TASK_ID}/"
        retained = json.loads(assets[prefix + "probe.json"].read_text())
        if retained["generator_sha256"] != SOURCE_SHA or retained["canonical_rule_sha256"] != [RULE_SHA]:
            raise ValueError("Retained case source/rule identity mismatch")
        rows = []
        with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
            for line in handle:
                if line.strip() and (row := json.loads(line)).get("task_id") == TASK_ID:
                    rows.append(row)
        if not rows or any(sha(row["program_solution"].encode()) != RULE_SHA for row in rows):
            raise ValueError("Current canonical rule differs from retained authority")
        if any(sha(" ".join(row["program_solution"].split()).encode())[:12] != RULE_HASH for row in rows):
            raise ValueError("Pinned canonical rule hash mismatch")
        result["bindings"]["rule"] = {
            "rule_task_id": TASK_ID, "rule_hash": RULE_HASH, "source_sha256": RULE_SHA,
            "canonical_row_sha256": [json_sha(row) for row in rows], "verified": True,
        }
        result["bindings_verified"] = True
        result["status"] = "unknown"

        # Execute exactly the inspected, hash-pinned original probe, once.
        sys.path.insert(0, str(REPO / "shared/runtime"))
        path = assets[prefix + "probe.py"]
        spec = importlib.util.spec_from_file_location("pinned_5a0a99ffdb0a_audit_probe", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        old_argv = sys.argv
        try:
            sys.argv = [str(path), "--out", str(HERE / "replay.json")]
            module.main()
        finally:
            sys.argv = old_argv
        replay = json.loads((HERE / "replay.json").read_text())
        comparisons = {name: replay[name] == retained[name] for name in (
            "canonical_cases", "exact_control_cases", "ordinary_draws", "summary",
            "declared_n_distinct_colors", "canonical_rule_sha256", "generator_sha256",
        )}
        result["exact_retained_comparison"] = comparisons
        result["summary"] = replay["summary"]
        result["replay_sha256"] = sha((HERE / "replay.json").read_bytes())
        result["source_unchanged"] = sha((home / "generator.py").read_bytes()) == SOURCE_SHA
        if all(comparisons.values()) and result["source_unchanged"]:
            result["status"] = "finding"
            result["findings_reproduced"] = ["A2-5A-CANONICAL-SEP", "A2-5A-COLOR-CONTROL"]
            result["conclusion"] = "Both pinned contract defects reproduced exactly; retained ordinary-draw controls also matched. Existing audit remains unresolved."
        else:
            result["conclusion"] = "Retained evidence did not reproduce exactly; inspect comparison fields. No no-issue or closure claim."
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    finally:
        signal.alarm(0)
        result["elapsed_seconds"] = round(time.monotonic() - started, 6)
        (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ticket_id": TICKET_ID, "status": result["status"],
                      "elapsed_seconds": result["elapsed_seconds"],
                      "error": result.get("error"), "summary": result.get("summary")}, sort_keys=True))
    return 0 if result["status"] == "finding" else 2


if __name__ == "__main__":
    raise SystemExit(main())
