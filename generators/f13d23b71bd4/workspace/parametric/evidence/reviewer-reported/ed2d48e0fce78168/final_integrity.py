#!/usr/bin/env python3
"""Source-bound integrity check for review-ed2d48e0fce78168 return evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

TASK_ID = "f13d23b71bd4"
GENERATOR_SHA256 = "5b2f9dfdf528813ad9d342a086943138201231be812b77fcf135c510c57b2b32"
CANONICAL_SOURCE_SHA256 = "71a162d2019efc9e1dad31b9b6f99b2a6f80089126ad749ee444696b61efbf45"
PROTOTYPE_SHA256 = "f28ff7b4094a9e9df3addfc7e5b5be560269f5b445347f08eecf241af9a05eec"
TEST_SHA256 = "b6dc6e7a606ada802b7341362fa64b66990fb432e223aac9b4669be468e3d818"
README_SHA256 = "a602d7cdfc04ffc4f712afb782cc9448d1fbf7edc0a3adf8e3b8474a76c9ccc5"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    here = Path(__file__).resolve()
    work = here.parent.parent
    repo = work / "repo"
    evidence = work / "checks/parametric/f13d23b71bd4-minimum-fall-size-v1"
    report_path = evidence / "report.json"
    checks: list[dict] = []

    def check(name: str, condition: bool, detail=None) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    generator = repo / f"generators/{TASK_ID}/generator.py"
    prototype = repo / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    tests = repo / f"generators/{TASK_ID}/tests/test_parametric_minimum_fall_size.py"
    readme = repo / f"generators/{TASK_ID}/workspace/parametric/README.md"
    check("generator_source_unchanged", sha256(generator) == GENERATOR_SHA256, sha256(generator))
    check("prototype_source_pinned", sha256(prototype) == PROTOTYPE_SHA256, sha256(prototype))
    check("test_source_pinned", sha256(tests) == TEST_SHA256, sha256(tests))
    check("readme_source_pinned", sha256(readme) == README_SHA256, sha256(readme))

    canonical_sources = set()
    with (repo / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    canonical_sources.add(row.get("program_solution"))
    canonical_hashes = sorted(
        hashlib.sha256(source.encode()).hexdigest()
        for source in canonical_sources if isinstance(source, str)
    )
    check(
        "canonical_source_unchanged",
        canonical_hashes == [CANONICAL_SOURCE_SHA256],
        canonical_hashes,
    )

    report = json.loads(report_path.read_text())
    check("report_status_proposed", report.get("status") == "proposed_unapproved")
    check("report_not_approved", report.get("approved") is False)
    check("report_generator_binding", report.get("base_generator_sha256") == GENERATOR_SHA256)
    check("report_canonical_binding", report.get("canonical_source_sha256") == CANONICAL_SOURCE_SHA256)
    source_expect = {
        f"generators/{TASK_ID}/workspace/parametric/prototype.py": PROTOTYPE_SHA256,
        f"generators/{TASK_ID}/tests/test_parametric_minimum_fall_size.py": TEST_SHA256,
        f"generators/{TASK_ID}/workspace/parametric/README.md": README_SHA256,
    }
    reported_sources = {row["path"]: row["sha256"] for row in report.get("sources", [])}
    check("report_source_hashes", reported_sources == source_expect, reported_sources)

    file_hash_mismatches = []
    for row in report.get("files", []):
        path = evidence / row["path"]
        actual = sha256(path) if path.is_file() else None
        if actual != row["sha256"]:
            file_hash_mismatches.append({"path": row["path"], "expected": row["sha256"], "actual": actual})
    check("retained_file_hashes", not file_hash_mismatches, file_hash_mismatches)

    episode_rows = report.get("episodes", [])
    public_ids = [row["public_id"] for row in episode_rows]
    check("episode_metadata_sorted_by_public_id", public_ids == sorted(public_ids), public_ids)
    check("three_settings_exercised", {row["parameters"]["minimum_fall_size"] for row in episode_rows} == {3, 4, 5})

    private_episodes = []
    public_problems = []
    for row in episode_rows:
        public_path = evidence / row["public_path"]
        private_path = evidence / row["private_path"]
        public_bytes = public_path.read_bytes()
        public = json.loads(public_bytes)
        private = json.loads(private_path.read_text())
        private_episodes.append(private)
        visible_digest = hashlib.sha256(public_bytes).hexdigest()
        if visible_digest != row["public_id"] or public_path.name != f"challenge-{visible_digest}.json":
            public_problems.append({"path": row["public_path"], "digest": visible_digest, "id": row["public_id"]})
        if set(public) != {"train", "test"}:
            public_problems.append({"path": row["public_path"], "keys": sorted(public)})
        if any(set(pair) != {"input", "output"} for pair in public.get("train", [])):
            public_problems.append({"path": row["public_path"], "train_shape": "invalid"})
        if any(set(pair) != {"input"} for pair in public.get("test", [])):
            public_problems.append({"path": row["public_path"], "test_shape": "invalid"})
    check("public_projection_and_visible_hash_ids", not public_problems, public_problems)

    train_pairs = sum(len(ep["train"]) for ep in private_episodes)
    query_pairs = sum(len(ep["test"]) for ep in private_episodes)
    input_hashes = {
        pair["input_sha256"]
        for ep in private_episodes
        for pair in ep["train"] + ep["test"]
    }
    rival_problems = []
    for ep in private_episodes:
        selected = ep["parameters"]["minimum_fall_size"]
        for rival in ep["parameter_rivals"]:
            if rival["minimum_fall_size"] == selected:
                if rival["status"] != "matches_episode":
                    rival_problems.append({"seed": ep["seed"], "rival": rival})
            elif rival["status"] != "refuted_by_demonstrations" or not rival["demonstration_mismatch_indices"]:
                rival_problems.append({"seed": ep["seed"], "rival": rival})
    expected_counts = {
        "episodes": 3,
        "train_pairs": 9,
        "query_pairs": 12,
        "distinct_input_grids": 21,
        "settings_exercised": 3,
        "canonical_pairs_checked": 4,
        "parameter_rival_episode_checks": 9,
        "ambiguous_parameter_rivals": 0,
    }
    actual_counts = dict(report.get("counts", {}))
    check("report_counts_exact", actual_counts == expected_counts, actual_counts)
    check(
        "episode_contents_match_counts",
        (len(private_episodes), train_pairs, query_pairs, len(input_hashes)) == (3, 9, 12, 21),
        {"episodes": len(private_episodes), "train": train_pairs, "queries": query_pairs, "inputs": len(input_hashes)},
    )
    check("demonstrations_refute_all_declared_rivals", not rival_problems, rival_problems)

    adversarial = json.loads((work / "checks/parametric/f13d23b71bd4-adversarial-v1/result.json").read_text())
    check("adversarial_probe_source_binding", adversarial.get("prototype_sha256") == PROTOTYPE_SHA256)
    check(
        "adversarial_probe_passed",
        adversarial.get("status") == "bounded_no_finding"
        and len(adversarial.get("checks", [])) == 8
        and all(row.get("passed") for row in adversarial.get("checks", [])),
        adversarial.get("status"),
    )

    ticket_a = json.loads((work / "checks/tickets/ticket-331c36790188dfd0/result.json").read_text())
    ticket_b = json.loads((work / "checks/tickets/ticket-abf3e5c83d95b30e/probe.json").read_text())
    check("ticket_a_completed", ticket_a.get("status") == "completed" and ticket_a.get("finding") is None)
    ticket_b_checks = dict(ticket_b.get("checks", {}))
    historical_runtime_available = ticket_b_checks.pop(
        "exact_historical_racket_binary_available", None
    )
    check(
        "ticket_b_completed",
        ticket_b.get("status") == "completed"
        and historical_runtime_available is False
        and bool(ticket_b_checks)
        and all(ticket_b_checks.values()),
        {
            "exact_historical_racket_binary_available": historical_runtime_available,
            "substantive_checks": ticket_b_checks,
        },
    )

    failed = [row for row in checks if not row["passed"]]
    result = {
        "schema": "arcpuzzles-review-final-integrity-v1",
        "assignment_id": "review-ed2d48e0fce78168",
        "task_id": TASK_ID,
        "status": "passed" if not failed else "failed",
        "check_count": len(checks),
        "failed_count": len(failed),
        "checks": checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
