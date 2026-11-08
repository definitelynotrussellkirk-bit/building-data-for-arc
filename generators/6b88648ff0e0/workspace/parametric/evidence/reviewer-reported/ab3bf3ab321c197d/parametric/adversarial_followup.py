#!/usr/bin/env python3
"""One narrow follow-up: three original gaps reject; healthy artifacts verify."""
import copy
import hashlib
import json
import signal
import sys
import tempfile
import time
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
PARAMETRIC = REPO / "generators/6b88648ff0e0/workspace/parametric"
sys.path[:0] = [str(PARAMETRIC), str(REPO / "shared/runtime")]
import episodes as e
from arc_repl.racket_bridge import RacketBridge

signal.alarm(120)
started = time.monotonic()
checks = []
before_path = Path(__file__).with_name("adversarial_probe_results.json")
before_sha = hashlib.sha256(before_path.read_bytes()).hexdigest()

def record(name, passed, detail=None):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

def rejects(name, fn):
    try:
        result = fn()
    except ValueError as exc:
        record(name, True, str(exc))
    except Exception as exc:
        record(name, False, type(exc).__name__ + ": " + str(exc))
    else:
        record(name, False, {"unexpectedly_accepted": result})

with RacketBridge(timeout=20) as bridge:
    base = e.build_episode("strip", "top_to_bottom", 41, bridge=bridge, n_demo=1, n_query=1)
    record("healthy_episode_verifies", e.verify_episode(base, bridge))
    for field, value in (("seed", True), ("input_seed", "not-an-integer"), ("attempts", -1)):
        bad = copy.deepcopy(base)
        bad[field] = value
        rejects("invalid_generation_metadata_rejected_" + field, lambda: e.verify_episode(bad, bridge))
    bad = copy.deepcopy(base)
    bad["certificate"]["query_count"] = True
    rejects("boolean_certificate_query_count_rejected", lambda: e.verify_episode(bad, bridge))
    with tempfile.TemporaryDirectory(prefix="adversarial-followup-", dir=Path(__file__).parent) as temp:
        batch = Path(temp) / "batch"
        e.write_batch([base], batch, bridge)
        record("healthy_batch_verifies", e.verify_batch(batch, bridge)["verified_episodes"] == 1)
        report_path = batch / "private/verification.json"
        report = json.loads(report_path.read_text())
        report.update(status="approved", training_admitted=True, episode_count=999, label_count=999, public_ids=[])
        report_path.write_text(json.dumps(report))
        rejects("tampered_verification_report_rejected", lambda: e.verify_batch(batch, bridge))
        report_path.unlink()
        rejects("missing_verification_report_rejected", lambda: e.verify_batch(batch, bridge))

record("original_before_evidence_unchanged", hashlib.sha256(before_path.read_bytes()).hexdigest() == before_sha)
exit_code = 0 if all(c["passed"] for c in checks) else 1
result = {"schema": "parametric-adversarial-followup-v1", "command": "python3 review.py run python3 ../checks/parametric/adversarial_followup.py", "exit_code": exit_code,
          "elapsed_seconds": round(time.monotonic() - started, 3), "engine_sha256": hashlib.sha256(Path(e.__file__).read_bytes()).hexdigest(),
          "before_evidence_sha256": before_sha, "checks": checks}
Path(__file__).with_name("adversarial_followup_results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
signal.alarm(0)
raise SystemExit(exit_code)
