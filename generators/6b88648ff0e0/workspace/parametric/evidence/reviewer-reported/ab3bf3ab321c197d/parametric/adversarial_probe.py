#!/usr/bin/env python3
"""Bounded adversarial probes for the task-local strip episode prototype."""
import copy
import hashlib
import json
import signal
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
PARAMETRIC = REPO / "generators/6b88648ff0e0/workspace/parametric"
sys.path[:0] = [str(PARAMETRIC), str(REPO / "shared/runtime")]
import episodes as e
import strip_stack as s
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes

signal.alarm(120)
started = time.monotonic()
checks, findings = [], []

def check(name, condition, detail=None):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(name)

def rejects(name, fn):
    try:
        fn()
    except ValueError as exc:
        check(name, True, str(exc))
    else:
        check(name, False, "accepted")

with RacketBridge(timeout=20) as bridge:
    base = e.build_episode("strip", "top_to_bottom", 41, bridge=bridge, n_demo=1, n_query=1)
    check("baseline_verified", e.verify_episode(base, bridge))
    visible = copy.deepcopy(base["challenge"])
    initial = e.certify(visible, "strip", bridge)
    visible["test"][0]["output"] = [[True]]
    visible["hidden_seed"] = "private"
    check("query_label_and_private_metadata_do_not_change_certificate", initial == e.certify(visible, "strip", bridge))
    bad = copy.deepcopy(base)
    bad["challenge"] = visible
    rejects("private_bool_label_rejected", lambda: e.verify_episode(bad, bridge))
    demo, query = s.sample_input(17, 3), s.sample_input(19, 0)
    ambiguous = {"train": [{"input": demo, "output": s.python_expected(demo)}],
                 "test": [{"input": query, "output": s.python_expected(query)}]}
    rejects("query_answer_cannot_rescue_ambiguous_demos", lambda: e.certify(ambiguous, "strip", bridge))
    for field, value in (("demo", True), ("query", 2)):
        bad = copy.deepcopy(base)
        bad["requested_counts"][field] = value
        rejects("stored_count_rejected_" + field, lambda: e.verify_episode(bad, bridge))
    for kwargs in ({"n_demo": 0}, {"n_query": 9}, {"max_attempts": True}, {"max_attempts": 4097}):
        with patch.object(s, "sample_input", side_effect=AssertionError("sampled before validating counts")):
            rejects("invalid_count_before_sampling_" + repr(kwargs), lambda: e.build_episode("strip", s.DEFAULT, 41, bridge=bridge, **kwargs))
    first, second = s.sample_input(41, 0), s.sample_input(41, 1)
    with patch.object(s, "sample_input", side_effect=[first, first, second]) as sampler:
        retry = e.build_episode("strip", s.DEFAULT, 41, bridge=bridge, n_demo=1, n_query=1, max_attempts=3)
        check("retry_succeeds_on_last_allowed_attempt", retry["attempts"] == 3 and sampler.call_count == 3)
    with patch.object(s, "sample_input", return_value=first) as sampler:
        rejects("duplicate_budget_exhausts", lambda: e.build_episode("strip", s.DEFAULT, 41, bridge=bridge, n_demo=1, n_query=1, max_attempts=3))
        check("duplicate_budget_does_not_overrun", sampler.call_count == 3)
    maximum = e.build_episode("strip", s.DEFAULT, 41, bridge=bridge, n_demo=8, n_query=8, max_attempts=16)
    check("maximum_counts_fit_exact_budget", maximum["attempts"] == 16 and e.verify_episode(maximum, bridge))
    with tempfile.TemporaryDirectory(prefix="adversarial-", dir=Path(__file__).parent) as temp:
        batch = Path(temp) / "batch"
        e.write_batch([base], batch, bridge)
        check("baseline_batch_verified", e.verify_batch(batch, bridge)["verified_episodes"] == 1)
        public_file = next((batch / "public").iterdir())
        raw = public_file.read_bytes()
        check("export_is_exact_hash_named_projection", raw == public_challenge_bytes(base["challenge"]) and public_file.stem == hashlib.sha256(raw).hexdigest())
        public_file.write_bytes(raw + b" ")
        rejects("semantic_json_with_changed_bytes_rejected", lambda: e.verify_batch(batch, bridge))
        public_file.write_bytes(raw)
        extra = batch / "public/extra.json"
        extra.write_text("{}")
        rejects("extra_public_file_rejected", lambda: e.verify_batch(batch, bridge))
        extra.unlink()
        report_path = batch / "private/verification.json"
        report = json.loads(report_path.read_text())
        report.update(status="approved", training_admitted=True, episode_count=999, label_count=999, public_ids=[])
        report_path.write_text(json.dumps(report))
        accepted = e.verify_batch(batch, bridge)
        findings.append({"id": "verification_report_unchecked", "severity": "medium", "accepted_result": accepted,
                         "evidence": "verify_batch accepts status=approved, training_admitted=true, false counts and empty public_ids in private/verification.json"})
        report_path.unlink()
        check("missing_verification_report_is_also_accepted", e.verify_batch(batch, bridge)["verified_episodes"] == 1)
    bad = copy.deepcopy(base)
    bad.update(seed=True, input_seed="not-an-integer", attempts=-1)
    if e.verify_episode(bad, bridge):
        findings.append({"id": "generation_metadata_unchecked", "severity": "low", "evidence": "verify_episode accepts seed=true, input_seed=not-an-integer and attempts=-1"})
    bad = copy.deepcopy(base)
    bad["certificate"]["query_count"] = True
    if e.verify_episode(bad, bridge):
        findings.append({"id": "certificate_query_count_bool_accepted", "severity": "low", "evidence": "one-query certificate query_count=true equals freshly computed integer 1 under Python dict equality"})

result = {"schema": "parametric-adversarial-probe-v1", "command": "python3 review.py run python3 ../checks/parametric/adversarial_probe.py", "exit_code": 1 if findings else 0,
          "elapsed_seconds": round(time.monotonic() - started, 3), "checks": checks, "findings": findings}
output = Path(__file__).with_name("adversarial_probe_results.json")
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
signal.alarm(0)
raise SystemExit(result["exit_code"])
