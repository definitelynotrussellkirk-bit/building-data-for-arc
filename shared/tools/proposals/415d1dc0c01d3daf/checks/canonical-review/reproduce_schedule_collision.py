#!/usr/bin/env python3
"""Reproduce a duplicate-rejection exception to the all-query-rotation claim.

Run from WORK/repo:
  PYTHONDONTWRITEBYTECODE=1 python3 ../run_with_racket.py python3 ../checks/canonical-review/reproduce_schedule_collision.py

Exit 0 means the reported counterexample was independently reproduced through
the public Racket-backed generation API. This never changes the selected source.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2] / "repo"
SOURCE = ROOT / "generators/d89cff1052a2/generator.py"
EXPECTED_SOURCE = "14011768b609cdf2cacb79228b2e0d5fe0326d9dddc1fc9335510e6d4e660cce"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles import Catalog


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert sha256(SOURCE) == EXPECTED_SOURCE, "Reproduction is bound to the reviewed source"
    spec = importlib.util.spec_from_file_location("reviewed_d89cff1052a2", SOURCE)
    gen = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(gen)
    arguments = dict(count=1,seed=43514,difficulty="easy",n_test=1,sample_index=0)
    raw = [gen.generate(43514,i,difficulty="easy") for i in range(5)]
    assert raw[1] == raw[3]
    assert all(gen.self_check(grid) == [] for grid in raw)

    # Omitting n_train exercises the automatic EXAMPLES_NEEDED=3 policy.
    episode = Catalog(ROOT).generate("d89cff1052a2",**arguments)[0]
    pairs = episode["train"] + episode["test"]
    assert episode["sample_indices"] == [0,1,2,4], episode["sample_indices"]
    assert [len(pair["input"]) for pair in pairs] == [3,5,3,3]
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    for pair in pairs:
        assert pair["output"] == list(reversed(pair["input"])) + pair["input"]
    assert episode["executed_rule_hash"] == "370a7fcc45fc"
    assert any(r["sample_index"] == 3 and r["reason"] == "duplicate pair"
               for r in episode["rejections"])

    heldout_position = 1
    query = pairs[heldout_position]
    demos = [pair for i,pair in enumerate(pairs) if i != heldout_position]
    rival = gen.CANONICAL_SHORTCUTS["fixed_three_row_mirror"]
    assert all(rival(pair["input"]) == pair["output"] for pair in demos)
    assert rival(query["input"]) != query["output"]
    report = {
        "schema":"arcpuzzles-focused-counterexample-v1",
        "finding_id":"canonical-schedule-dedup",
        "task_id":"d89cff1052a2",
        "finding":"Duplicate rejection invalidates the claim that every four-pair lesson supports every query rotation.",
        "scope":"The default fixed-last-query lesson still passes the declared rivals and every Racket label is correct; the failure is the stronger rotation guarantee and two-of-each accepted-pair claim.",
        "source_sha256":EXPECTED_SOURCE,
        "rule_hash":episode["executed_rule_hash"],
        "support_hashes":{
            str(path.relative_to(ROOT)):sha256(path) for path in (
                ROOT / "src/arcpuzzles/worker.py",
                ROOT / "src/arcpuzzles/runtime.py",
                ROOT / "shared/runtime/puzzle_generators/base.py",
            )
        },
        "invocation":{
            "cwd":str(ROOT),
            "command":"PYTHONDONTWRITEBYTECODE=1 python3 ../run_with_racket.py python3 ../checks/canonical-review/reproduce_schedule_collision.py",
            "api":"Catalog(ROOT).generate",
            "task_id":"d89cff1052a2", "arguments":arguments,
            "overrides":{},"n_train":"omitted; automatically resolved to 3",
        },
        "raw_sample_heights":[len(grid) for grid in raw],
        "duplicate_raw_indices":[1,3],
        "accepted_sample_indices":episode["sample_indices"],
        "accepted_heights":[len(pair["input"]) for pair in pairs],
        "rejections":episode["rejections"],
        "original_lesson_check":episode["lesson_check"],
        "counterexample":{
            "heldout_pair_position":heldout_position,
            "demo_sample_indices":[0,2,4], "query_sample_index":1,
            "rival":"fixed_three_row_mirror",
            "rival_matches_every_demo":True,
            "rival_disagrees_with_query":True,
            "authority_query_height":len(query["output"]),
            "rival_query_height":len(rival(query["input"])),
            "train":[{"sample_index":index, **pair,
                      "rival_output":rival(pair["input"])}
                     for index,pair in zip((0,2,4),demos)],
            "query":{"sample_index":1, **query,
                     "rival_output":rival(query["input"])},
        },
        "exit_code":0,
    }
    destination = Path(__file__).with_name("minimal-reproduction.json")
    destination.write_text(json.dumps(report,indent=2)+"\n")
    summary = {key:report[key] for key in (
        "finding_id","source_sha256","rule_hash","accepted_sample_indices",
        "accepted_heights","rejections","exit_code")}
    summary["counterexample"] = {key:value for key,value in report["counterexample"].items()
                                 if key not in ("train","query")}
    print(json.dumps(summary,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
