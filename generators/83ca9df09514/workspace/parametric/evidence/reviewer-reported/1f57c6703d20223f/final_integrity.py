#!/usr/bin/env python3
"""Verify the retained review delta without mutating source or evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[1]
REPO = PACKET / "repo"
CHECKS = PACKET / "checks"
TASK_ID = "83ca9df09514"
EXPECTED_GENERATOR_SHA = "70db137b815d1463c9b759c9258749291aef361633d91fbf64e7c72c8d6f2233"
EXPECTED_CANONICAL_SHA = "cae56e2f8161ccd2fd21aa8b0d4e0b51318d3e114e626ea9097fab7c2602af87"
EXPECTED_ALTERNATE_SHA = "5af8f8f0bd1f06067a61a13b03bee9ea3d817efb71248e0340125d4ddf1f6c47"


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return sha_bytes(raw)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


assignment = load(PACKET / "ASSIGNMENT.json")
results = load(PACKET / "RESULTS.json")
base = CHECKS / "parametric" / "duplicate-precedence-v1"
manifest = load(base / "manifest.json")
prototype = REPO / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
generator = REPO / "generators" / TASK_ID / "generator.py"

check(assignment["task_id"] == TASK_ID, "assignment task drift")
check(assignment["generator"]["generator_sha256"] == EXPECTED_GENERATOR_SHA, "assignment generator drift")
check(sha_bytes(generator.read_bytes()) == EXPECTED_GENERATOR_SHA, "selected production generator changed")
check(manifest["selected_generator"]["sha256"] == EXPECTED_GENERATOR_SHA, "manifest generator mismatch")
check(sha_bytes(prototype.read_bytes()) == manifest["prototype"]["sha256"], "prototype hash mismatch")
check(manifest["canonical_source_sha256"] == EXPECTED_CANONICAL_SHA, "canonical hash mismatch")
check(manifest["canonical_default_unchanged"] is True, "canonical default not preserved")

program_hashes = {}
for setting, expected in {
    "rightmost_wins": EXPECTED_CANONICAL_SHA,
    "leftmost_wins": EXPECTED_ALTERNATE_SHA,
}.items():
    row = manifest["programs"][setting]
    digest = sha_bytes((base / row["file"]).read_bytes())
    check(digest == row["sha256"] == expected, f"{setting} program hash mismatch")
    program_hashes[setting] = digest

canonical_checks = load(base / "private" / "canonical-default-check.json")
check(len(canonical_checks) == 10, "expected ten source-qualified canonical checks")
check(all(row.get("matched") is True for row in canonical_checks), "canonical replay mismatch")

public_rows: list[dict[str, Any]] = []
private_rows: list[dict[str, Any]] = []
for episode in manifest["episodes"]:
    public_path = base / episode["public_file"]
    private_path = base / episode["private_file"]
    public_id = episode["public_id"]
    check(public_path.name == f"challenge-{public_id}.json", "public filename/id mismatch")
    check(sha_bytes(public_path.read_bytes()) == public_id, "public bytes do not hash to public ID")
    public = load(public_path)
    private = load(private_path)
    check(set(public) == {"train", "test"}, "public evidence leaked extra top-level fields")
    check(len(public["train"]) == manifest["demo_count"], "public demo count mismatch")
    check(len(public["test"]) == manifest["query_count"], "public query count mismatch")
    check(all(set(item) == {"input", "output"} for item in public["train"]), "malformed public demo")
    check(all(set(item) == {"input"} for item in public["test"]), "query output/private metadata leaked")
    check(private["public_id"] == public_id, "private/public ID mismatch")
    setting = private["parameter"]["duplicate_precedence"]
    check(setting == episode["parameter"]["duplicate_precedence"], "episode setting mismatch")
    check(private["program_sha256"] == program_hashes[setting], "private program hash mismatch")
    check(private["surviving_settings_from_demonstrations"] == [setting], "demos do not identify setting")
    rival = next(value for value in program_hashes if value != setting)
    check(private["rival_checks"][rival]["matches_all_demonstrations"] is False, "rival survived demos")
    check(private["rival_checks"][rival]["query_disagreements"] == list(range(manifest["query_count"])),
          "a retained query does not separate settings")
    public_rows.append(public)
    private_rows.append(private)

check(len(public_rows) == 2, "expected exactly two paired retained episodes")
for split in ("train", "test"):
    left_inputs = [item["input"] for item in public_rows[0][split]]
    right_inputs = [item["input"] for item in public_rows[1][split]]
    check(left_inputs == right_inputs, f"paired {split} inputs differ")
check(all(a["output"] != b["output"] for a, b in zip(public_rows[0]["train"], public_rows[1]["train"], strict=True)),
      "a retained demonstration does not distinguish settings")

adversarial = load(CHECKS / "parametric" / "duplicate-precedence-adversarial.json")
check(adversarial["status"] == "passed", "adversarial report is not passed")
boundary = adversarial["surfaces"]["sampler_and_lesson_boundaries"]
check(boundary["paired_inputs"] is True, "adversarial paired inputs failed")
check(boundary["input_count"] == boundary["distinct_input_count"] == 16, "adversarial uniqueness failed")
check(boundary["all_inputs_separate_settings_in_racket"] is True, "Racket separation failed")

# Supplementary ticket 1: retained source-bound witness and independently stored grids.
t1 = CHECKS / "tickets" / "ticket-a0f8f09b9f0a9a2e"
t1_report = load(t1 / "report.json")
t1_input = load(t1 / "input.json")
t1_selected = load(t1 / "selected-output.json")
t1_rival = load(t1 / "one-to-one-rival-output.json")
check(t1_report["exactly_matches_retained_witness"] is True, "ticket 1 retained-witness match failed")
check(t1_report["selected_differs_from_rival"] is True, "ticket 1 rival does not differ")
check(stable_sha(t1_input) == t1_report["input_sha256"], "ticket 1 input hash mismatch")
check(stable_sha(t1_selected) == t1_report["selected_output_sha256"], "ticket 1 selected hash mismatch")
check(stable_sha(t1_rival) == t1_report["rival_output_sha256"], "ticket 1 rival hash mismatch")

# Supplementary ticket 2: source checks, bounded episode, and no policy mutation.
t2 = CHECKS / "tickets" / "ticket-4c319e9b0935a11f"
t2_report = load(t2 / "report.json")
t2_probe = load(t2 / "probe.json")
t2_selection = load(t2 / "selection.json")
check(t2_report["status"] == "completed", "ticket 2 not completed")
check(t2_report["mixture_or_approval_changed"] is False, "ticket 2 changed policy state")
check(t2_report["targeted_probes"] == 1, "ticket 2 probe count drift")
check(t2_selection["selected_ids"] == t2_report["sampled_task_ids"], "ticket 2 seeded selection mismatch")
check(t2_probe["execution"]["racket_matches_python_mirror"] is True, "ticket 2 Racket/Python mismatch")
check(t2_probe["episode"]["all_inputs_distinct"] is True, "ticket 2 duplicate inputs")
check(t2_probe["episode"]["demo_count"] == 3 and t2_probe["episode"]["query_count"] == 4,
      "ticket 2 episode count mismatch")
check(all(not row["survives_all_demos"] for row in t2_probe["lesson_rivals"].values()),
      "ticket 2 bounded rival survived demos")

# Structured return declarations must all resolve to packaged packet-relative files.
check(results["completion_state"] == "complete", "RESULTS is not complete")
check(len(results["supplementary_tickets"]) == 2, "RESULTS ticket count mismatch")
for group in (results["verification_commands"], results["supplementary_tickets"]):
    for row in group:
        for rel in row.get("evidence_paths", []):
            check((PACKET / rel).is_file(), f"declared evidence missing: {rel}")
check(not (PACKET / "AUDIT.md").exists(), "AUDIT.md must be absent without a new finding")

report = {
    "schema": "arcpuzzles-final-integrity-v1",
    "status": "passed",
    "task_id": TASK_ID,
    "selected_generator_sha256": EXPECTED_GENERATOR_SHA,
    "prototype_sha256": manifest["prototype"]["sha256"],
    "canonical_replays": len(canonical_checks),
    "retained_episodes": len(public_rows),
    "public_privacy_checks": len(public_rows),
    "adversarial_distinct_inputs": boundary["distinct_input_count"],
    "supplementary_tickets_checked": 2,
    "declared_evidence_paths_checked": sum(
        len(row.get("evidence_paths", []))
        for group in (results["verification_commands"], results["supplementary_tickets"])
        for row in group
    ),
}
print(json.dumps(report, indent=2, sort_keys=True))
