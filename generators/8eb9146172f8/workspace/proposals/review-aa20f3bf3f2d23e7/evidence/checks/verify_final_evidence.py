#!/usr/bin/env python3
"""Static final verifier for this return's retained evidence and source pins."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
TASK = "8eb9146172f8"
EXPECTED_GENERATOR = "84301bd12c17dbb0897847b4ddd15d66ee1e7fa0c74d4cafaa9f9a3480472d95"
EXPECTED_CANONICAL_FILE = "9753b39efd3802300657ea312d1a48220ab06fdbabe80b0137af36724f81750f"
EXPECTED_SAMPLE = ["80271cb9b303", "59a7762bc6da", "548c1010ce89"]
EXPECTED_PRIORITY = ["548c1010ce89", "59a7762bc6da", "80271cb9b303"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    generator = WORK / f"repo/generators/{TASK}/generator.py"
    canonical = WORK / "repo/shared/data/canonical/puzzles.jsonl"
    prototype = WORK / f"repo/generators/{TASK}/workspace/parametric/prototype.py"
    evidence = WORK / "checks/parametric-step-size"
    report = load(evidence / "report.json")

    assert sha(generator) == EXPECTED_GENERATOR
    assert sha(canonical) == EXPECTED_CANONICAL_FILE
    assert report["source_hashes"]["generator.py"] == EXPECTED_GENERATOR
    assert report["source_hashes"]["prototype.py"] == sha(prototype)
    assert report["status"] == "proposed_unapproved"
    assert report["step_sizes"] == [1, 2]
    assert report["n_train"] == report["n_test"] == 4
    assert report["episode_count"] == 2
    assert report["public_ids"] == sorted(report["public_ids"])
    assert report["cross_setting_same_inputs"] is True
    assert report["cross_setting_outputs_differ"] is True
    assert report["all_identified_from_demonstrations"] is True
    assert report["all_queries_refute_rival"] is True

    public_rows = []
    for public_id in report["public_ids"]:
        path = evidence / f"public/challenge-{public_id}.json"
        raw = path.read_bytes()
        assert sha(path) == public_id
        lowered = raw.lower()
        for forbidden in (b'"step_size"', b'"seed"', b'"racket"', b'"parameters"', b'"output_sha256"'):
            assert forbidden not in lowered
        value = json.loads(raw)
        assert set(value) == {"train", "test"}
        assert len(value["train"]) == len(value["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in value["train"])
        assert all(set(pair) == {"input"} for pair in value["test"])
        public_rows.append(value)

    private_paths = sorted((evidence / "private").glob("episode-*.json"))
    assert len(private_paths) == 2
    episodes = [load(path) for path in private_paths]
    assert [episode["public_id"] for episode in episodes] == report["public_ids"]
    all_input_sets = []
    for episode, visible in zip(episodes, public_rows, strict=True):
        pairs = [*episode["train"], *episode["test"]]
        assert len(pairs) == 8
        assert len({pair["input_sha256"] for pair in pairs}) == 8
        assert episode["analysis"]["identified_from_demonstrations"] is True
        assert episode["analysis"]["query_answers_used_for_identification"] is False
        assert len(episode["analysis"]["demo_refutation_indices"]) == 4
        assert len(episode["analysis"]["queries"]) == 4
        assert all(row["rival_differs"] for row in episode["analysis"]["queries"])
        assert episode["verification"]["racket_python_parity_count"] == 16
        assert visible == {
            "train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
            "test": [{"input": p["input"]} for p in episode["test"]],
        }
        all_input_sets.append([pair["input_sha256"] for pair in pairs])
    assert all_input_sets[0] == all_input_sets[1]

    rule_paths = sorted((evidence / "private/rules").glob("rule-*.rkt"))
    assert len(rule_paths) == 2
    for path in rule_paths:
        assert sha(path) == path.stem.removeprefix("rule-")

    manifest = load(evidence / "manifest.json")
    listed = {row["path"]: row for row in manifest["files"]}
    actual = {
        path.relative_to(evidence).as_posix(): path
        for path in evidence.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    assert set(listed) == set(actual)
    for name, path in actual.items():
        assert listed[name]["sha256"] == sha(path)
        assert listed[name]["bytes"] == path.stat().st_size

    audit_dir = WORK / "checks/tickets/ticket-7f261484c1c9689c"
    replay = load(audit_dir / "replay_summary.json")
    audit_process = load(audit_dir / "process.json")
    assert replay["status"] == "completed"
    assert replay["semantic_replay_match"] is True
    assert all(replay["semantic_field_matches"].values())
    assert all(row["match"] for row in replay["pinned_inputs"].values())
    assert audit_process["exit_code"] == 0 and audit_process["timed_out"] is False

    allocation_dir = WORK / "checks/tickets/ticket-5f63d21523eda9b5"
    allocation = load(allocation_dir / "allocation_report.json")
    allocation_process = load(allocation_dir / "process.json")
    assert allocation["sampled_ids"] == EXPECTED_SAMPLE
    assert allocation["alternative"]["sample_priority_order"] == EXPECTED_PRIORITY
    assert allocation["pinned_ticket_source"]["match"] is True
    assert allocation["draw_policy"]["focus_probability"] == {"numerator": 1, "denominator": 10}
    assert allocation["normal_pool_snapshot"]["normal_pool_records"] == 162
    assert allocation["normal_pool_snapshot"]["catalog_mix_weight_counts"] == {"1.0": 162}
    assert allocation["alternative"]["production_change"] is False
    assert allocation_process["exit_code"] == 0 and allocation_process["timed_out"] is False
    assert not (WORK / "AUDIT.md").exists()

    result = {
        "schema": "arcpuzzles-review-final-evidence-verification-v1",
        "status": "passed",
        "task_id": TASK,
        "production_generator_sha256": sha(generator),
        "prototype_sha256": sha(prototype),
        "canonical_file_sha256": sha(canonical),
        "parametric": {
            "episodes": 2,
            "demonstrations_per_episode": 4,
            "queries_per_episode": 4,
            "racket_python_comparisons": sum(e["verification"]["racket_python_parity_count"] for e in episodes),
            "public_ids": report["public_ids"],
        },
        "tickets": {
            "ticket-7f261484c1c9689c": "semantic replay reproduced; audit retained unresolved",
            "ticket-5f63d21523eda9b5": "seeded allocation report and no-change shadow proposal retained",
        },
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
