#!/usr/bin/env python3
"""Reproduce one production lesson with an unrefuted rightmost-panel rival."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "5d1263287a4f"
HERE = Path(__file__).resolve().parent


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def rightmost(grid):
    third = len(grid[0]) // 3
    return [list(row[2 * third:]) for row in grid]


def prepare():
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK, root=root)
    authority = json.loads((HERE / "selected_authority.json").read_text())
    assert digest == authority["generator_sha256"]
    assert digest == "e88a731c55edf29fc56e15aaf9c56d0f379c262f63d569caeab9af498822339d"
    program = authority["variants"][0]["program_solution"]
    rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    assert rule_hash == gen.RULE_HASH == authority["rule_hash"] == "92f6a0f9f7b3"
    (HERE / "generator_snapshot.py").write_bytes(source.read_bytes())
    (HERE / "rule_snapshot.rkt").write_text(program)

    episodes = [json.loads(line) for line in (HERE / "production.jsonl").read_text().splitlines()]
    assert len(episodes) == 3
    episode = episodes[2]
    assert episode["seed"] == 20261008 and episode["episode_index"] == 2
    assert episode["sample_indices"] == [0, 1, 2, 3]
    assert episode["executed_rule_hash"] == rule_hash
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    rows = []
    for index, pair in enumerate(pairs):
        regenerated = gen.generate(20261008, index, difficulty="medium")
        assert regenerated == pair["input"], index
        errors = gen.self_check(pair["input"])
        assert errors == [], (index, errors)
        rows.append({
            "role": "demo" if index < 3 else "query",
            "sample_index": index,
            "profiles": gen.observe_overrides(pair["input"]),
            "self_check": errors,
            "regenerated_equals_production": True,
            "input": pair["input"],
            "production_output": pair["output"],
            "rival_output": rightmost(pair["input"]),
            "rival_fits_production_output": rightmost(pair["input"]) == pair["output"],
        })
    fit = [rightmost(deepcopy(pair["input"])) == pair["output"]
           for pair in canonical_pairs(TASK, root=root)]
    assert fit == [True] * 4
    assert [row["rival_fits_production_output"] for row in rows] == [True, True, True, False]
    report = {
        "schema": "arcpuzzles-bounded-shortcut-audit-v1", "task_id": TASK,
        "finding": "rightmost_panel_rival_survives_all_demos_and_fails_query",
        "generator_sha256": digest, "rule_hash": rule_hash,
        "canonical_rule_source_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "known_prior_finding": "review-d3192d76dc7ddbba:v0001; same source, needs_triage",
        "canonical_rival_fit": fit,
        "catalog_seed": 20261006, "production_episodes_materialized": 3,
        "episode_index": episode["episode_index"], "generator_seed": episode["seed"],
        "difficulty": "medium", "overrides": {},
        "sampling": episode["sampling"], "lesson_check": episode["lesson_check"],
        "pairs": rows,
        "classification": "production_lesson_teaching_shortcut; not a reference-output mismatch",
        "status": "awaiting_fresh_public_racket_apply",
    }
    write_json("input.json", {"inputs": [row["input"] for row in rows]})
    write_json("finding.json", report)
    print(json.dumps({
        "status": report["status"], "generator_sha256": digest,
        "rule_hash": rule_hash, "generator_seed": episode["seed"],
        "sample_indices": episode["sample_indices"],
        "layouts": [row["profiles"]["panel_layout"] for row in rows],
        "canonical_rival_fit": fit,
    }, indent=2))


def verify():
    report = json.loads((HERE / "finding.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    assert racket["generator_sha256"] == report["generator_sha256"]
    assert racket["executed_rule_hash"] == report["rule_hash"]
    # Public apply's rule_text_sha256 hashes the bridge-ready callable after
    # rule_wrap.wrap_rule, whereas Catalog.show exposes the original rule!
    # source. Keep these distinct identities; executed_rule_hash above binds
    # the normalized selected authority shared by both public commands.
    source_text = (HERE / "rule_snapshot.rkt").read_text()
    assert hashlib.sha256(source_text.encode()).hexdigest() == report["canonical_rule_source_sha256"]
    assert hashlib.sha256(" ".join(source_text.split()).encode()).hexdigest()[:12] == racket["executed_rule_hash"]
    report["racket_callable_text_sha256"] = racket["rule_text_sha256"]
    assert racket["rule_hash_matches_catalog"]
    assert len(racket["results"]) == 4
    for pair, result in zip(report["pairs"], racket["results"]):
        assert result["input"] == pair["input"]
        assert result["error"] is None and result["valid_output"]
        assert result["output"] == pair["production_output"]
        pair["racket_equals_production_output"] = True
        pair["rival_fits_racket_output"] = pair["rival_output"] == result["output"]
    assert [p["rival_fits_racket_output"] for p in report["pairs"]] == [True, True, True, False]
    report["status"] = "reproduced"
    report["fresh_public_racket_apply"] = {
        "receipt": "checks/audit/5d1263287a4f/racket.json",
        "pairs_checked": 4, "output_errors": 0,
        "outputs_match_production": True,
        "executed_rule_hash": racket["executed_rule_hash"],
    }
    write_json("finding.json", report)
    print(json.dumps({
        "status": report["status"], "generator_sha256": report["generator_sha256"],
        "rule_hash": report["rule_hash"], "racket_pairs_checked": 4,
        "rival_fits": [pair["rival_fits_racket_output"] for pair in report["pairs"]],
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "verify"))
    args = parser.parse_args()
    prepare() if args.phase == "prepare" else verify()
