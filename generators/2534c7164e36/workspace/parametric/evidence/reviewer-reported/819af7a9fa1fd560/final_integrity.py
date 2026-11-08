#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent.parent
OUT = WORK / "checks" / "final" / "integrity-report.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(relative: str):
    return json.loads((WORK / relative).read_text(encoding="utf-8"))


def main() -> int:
    expected = {
        "production_generator": "eab765a3418f667520bfac6419a2730a4666dcb1e3fb54508c5cc117ef051ac5",
        "canonical_rule": "3d9402d2c7a5a95e4e76a0cac9b607451694f4f32a7a501664be99032ab453e1",
        "prototype": "38adaac798fc610b42dec02a7fece050685aea3baa22cba0cdce45a6d684054a",
        "tests": "9990b876b5d817c95c571e1d7afc5320fa08a534b891438e637d061d2ccd7271",
    }
    actual = {
        "production_generator": sha(WORK / "repo/generators/2534c7164e36/generator.py"),
        "prototype": sha(WORK / "repo/generators/2534c7164e36/workspace/parametric/prototype.py"),
        "tests": sha(WORK / "repo/generators/2534c7164e36/tests/test_parametric_priority_order.py"),
    }
    programs = []
    for line in (WORK / "repo/shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == "2534c7164e36":
                programs.append(row["program_solution"])
    assert programs and len(set(programs)) == 1
    actual["canonical_rule"] = hashlib.sha256(programs[0].encode("utf-8")).hexdigest()
    assert actual == expected

    evidence = load("checks/parametric/2534-priority-order-public-batch-v2/report.json")
    assert evidence["status"] == "no_ambiguity_found"
    assert evidence["counts"] == {
        "canonical_labels_checked": 12,
        "canonical_labels_passed": 12,
        "counterfactual_labels": 12,
        "demonstrations": 4,
        "episode_labels": 12,
        "episodes": 2,
        "queries": 8,
        "query_ambiguities": 0,
        "settings_seen": ["q1_q2_q3", "q1_q3_q2"],
    }
    order = evidence["public_write_order"]
    episode_paths = [row["public_path"] for row in evidence["episodes"]]
    assert order == sorted(order)
    assert len(order) == len(set(order)) == 2
    assert set(order) == set(episode_paths)
    assert order != episode_paths  # seed 0 is the retained order-regression witness.
    for relative in order:
        path = WORK / "checks/parametric/2534-priority-order-public-batch-v2" / relative
        payload = path.read_bytes()
        assert path.stem.removeprefix("challenge-") == hashlib.sha256(payload).hexdigest()
        challenge = json.loads(payload)
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        serialized = json.dumps(challenge)
        assert not any(key in serialized for key in ("priority_order", "racket", "parameters", "seed", "query_output"))

    allocation = load("checks/tickets/ticket-312dd384a478aa32/probe_result.json")
    assert allocation["status"] == "completed"
    assert allocation["source_sha256"] == "e70ca9f847fc4919d7cba9fa328eec429f34aea56d6a9fe99facc6a0d5e9c11f"
    assert allocation["rule_hash"] == "ed3afc80127d"
    assert allocation["racket_labels_checked"] == 7
    assert allocation["python_racket_parity"] is True
    assert allocation["all_inputs_distinct"] is True
    assert allocation["query_answers_used_for_rival_elimination"] is False
    assert allocation["fixed_origin_rival_demo_fits"] == [True, True, True]
    assert allocation["fixed_origin_rival_query_fits"] == [False, False, False, False]
    assert allocation["query_differing_cell_counts"] == [8, 8, 6, 6]
    selection = load("checks/tickets/ticket-312dd384a478aa32/comparison_selection.json")
    assert selection["sampled_ids"] == ["71d5c4ac6ea3", "75837d4fa905", "90082143f2ec"]

    audit = load("checks/tickets/ticket-06ed8c6d359b5804/report.json")
    assert audit["status"] == "blocked"
    assert audit["claim_reproduced"] is False
    assert audit["checks"]["audited_source_present"] is False
    for key in (
        "all_retained_assets_match",
        "assets_manifest_pin_matches",
        "audit_index_pin_matches",
        "audit_record_pin_matches",
        "current_source_pin_matches",
        "current_source_rejects_unknown_key",
        "racket_command_passed",
        "racket_output_reproduced",
        "rule_hash_reproduced",
        "witness_binds_audited_source",
    ):
        assert audit["checks"][key] is True
    assert all(row["matches"] for row in audit["file_receipts"])

    pycache = [str(path.relative_to(WORK)) for path in (WORK / "checks").rglob("*.pyc")]
    assert not pycache, pycache

    result = {
        "schema": "arc-review-final-integrity-v1",
        "status": "pass",
        "source_hashes": actual,
        "main_evidence": {
            "status": evidence["status"],
            "counts": evidence["counts"],
            "public_write_order": order,
            "episode_public_order": episode_paths,
        },
        "allocation_ticket": {
            "status": allocation["status"],
            "sampled_ids": selection["sampled_ids"],
            "query_differing_cell_counts": allocation["query_differing_cell_counts"],
        },
        "audit_ticket": {
            "status": audit["status"],
            "audited_source_present": audit["checks"]["audited_source_present"],
            "racket_output_reproduced": audit["checks"]["racket_output_reproduced"],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
