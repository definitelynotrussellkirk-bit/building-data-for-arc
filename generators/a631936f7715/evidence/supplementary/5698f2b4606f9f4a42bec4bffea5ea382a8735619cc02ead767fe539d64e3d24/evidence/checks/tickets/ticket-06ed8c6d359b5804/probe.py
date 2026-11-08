from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

TASK_ID = "a631936f7715"
CURRENT_SHA = "965a662deb1bad237758745f2b18ad53eda6f8d0bf3c8d3d4febaa74b1e18d30"
AUDITED_SHA = "e2bc3fc23cc2ce1a45bf454bbbf2a94ada75a591ff868b2aac23a19e40680f41"
ASSETS_SHA = "38aa64b9766bd3e285933013c68f483aef3eebfaf19f2d33734e48249c832fd9"
INDEX_SHA = "70095d3603c6d44f0a4177199ca3189ec0a1c2acb20d00006813bd1e19729a45"
AUDIT_RECORD_SHA = "92fd31124ed50153d7f38bcffb5e32ce78e12a3fded402b8e31a463820e74689"
RETURN_ID = "review-f0f879d9b93ecdc8:v0001"
UNKNOWN_KEY = "__override_contract_unknown_axis__"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_replay_a631936f7715", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    started = time.perf_counter()
    repo = Path.cwd().resolve()
    out = repo.parent / "checks" / "tickets" / "ticket-06ed8c6d359b5804"
    out.mkdir(parents=True, exist_ok=True)

    generator_path = repo / "generators" / TASK_ID / "generator.py"
    index_path = repo / "generators" / TASK_ID / "evidence" / "review_index.json"
    review_dir = (
        repo
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "review-f0f879d9b93ecdc8-v0001"
    )
    assets_path = review_dir / "audit_assets.json"
    retained = review_dir / "retained"
    witness_path = retained / "checks" / "audit" / TASK_ID / "unknown-override.json"
    input_path = retained / "checks" / "audit" / TASK_ID / "input.json"
    retained_racket_path = retained / "checks" / "audit" / TASK_ID / "racket.json"

    assets = json.loads(assets_path.read_text())
    index = json.loads(index_path.read_text())
    record = next(row for row in index["audits"] if row.get("return_id") == RETURN_ID)
    file_receipts = []
    for row in assets["files"]:
        path = repo / row["path"]
        actual = sha256(path)
        file_receipts.append(
            {
                "path": row["path"],
                "expected_sha256": row["sha256"],
                "actual_sha256": actual,
                "matches": actual == row["sha256"],
            }
        )

    witness = json.loads(witness_path.read_text())
    retained_racket = json.loads(retained_racket_path.read_text())

    current = load_module(generator_path)
    current_unknown = {"accepted": False, "exception": None}
    try:
        current.generate(
            witness["seed"],
            witness["sample_index"],
            difficulty=witness["difficulty"],
            **witness["unknown_overrides"],
        )
        current_unknown["accepted"] = True
    except Exception as exc:  # exact current behavior is evidence, not a test expectation
        current_unknown["exception"] = f"{type(exc).__name__}: {exc}"

    replay_path = out / "current-racket.json"
    command = [
        sys.executable,
        "-m",
        "arcpuzzles",
        "apply",
        TASK_ID,
        "--input",
        str(input_path),
        "--out",
        str(replay_path),
    ]
    completed = subprocess.run(command, cwd=repo, text=True, capture_output=True)
    replay = json.loads(replay_path.read_text()) if replay_path.is_file() else None
    retained_output = retained_racket["results"][0]["output"]
    replay_output = replay["results"][0]["output"] if replay else None

    audited_source_present = any(
        receipt["actual_sha256"] == AUDITED_SHA for receipt in file_receipts
    ) or sha256(generator_path) == AUDITED_SHA

    checks = {
        "current_source_pin_matches": sha256(generator_path) == CURRENT_SHA,
        "audit_index_pin_matches": sha256(index_path) == INDEX_SHA,
        "assets_manifest_pin_matches": sha256(assets_path) == ASSETS_SHA,
        "audit_record_pin_matches": hashlib.sha256(canonical_json(record)).hexdigest()
        == AUDIT_RECORD_SHA,
        "all_retained_assets_match": all(row["matches"] for row in file_receipts),
        "witness_binds_audited_source": witness.get("generator_sha256") == AUDITED_SHA,
        "audited_source_present": audited_source_present,
        "current_source_rejects_unknown_key": not current_unknown["accepted"]
        and current_unknown["exception"] is not None,
        "racket_command_passed": completed.returncode == 0,
        "racket_output_reproduced": replay_output == retained_output,
        "rule_hash_reproduced": bool(replay)
        and replay.get("executed_rule_hash") == retained_racket.get("executed_rule_hash"),
    }
    source_claim_reproduced = (
        checks["audited_source_present"]
        and checks["witness_binds_audited_source"]
        and current_unknown["accepted"]
    )
    report = {
        "schema": "arc-review-audit-replay-v1",
        "ticket_id": "ticket-06ed8c6d359b5804",
        "task_id": TASK_ID,
        "return_id": RETURN_ID,
        "status": "completed" if source_claim_reproduced else "blocked",
        "claim_reproduced": source_claim_reproduced,
        "blocker": None
        if source_claim_reproduced
        else (
            "The retained bundle pins the old generator hash but does not contain "
            "those source bytes. The current generator has a different approved hash "
            "and rejects the unknown key, so re-executing it cannot reproduce the old "
            "acceptance defect. Retained asset integrity and the canonical Racket output "
            "were independently replayed."
        ),
        "checks": checks,
        "current_unknown_override": current_unknown,
        "racket": {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "output_path": str(replay_path.relative_to(repo.parent)),
        },
        "file_receipts": file_receipts,
        "elapsed_seconds": time.perf_counter() - started,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(
        checks[key]
        for key in (
            "current_source_pin_matches",
            "audit_index_pin_matches",
            "assets_manifest_pin_matches",
            "audit_record_pin_matches",
            "all_retained_assets_match",
            "witness_binds_audited_source",
            "current_source_rejects_unknown_key",
            "racket_command_passed",
            "racket_output_reproduced",
            "rule_hash_reproduced",
        )
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
