"""Bounded source-pinned reproduction of the existing color-only teaching defect.

From the packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/4bc78768be8b/probe.py
The query is canonical train pair 0, repurposed as a transfer query; this is
deliberately not claimed to be a production generated episode or blind solve.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "4bc78768be8b"
PIN = "5fee237462cf0d46b5b94588f7718480d1cc244145499faf27dc603d1e846688"
RULE_HASH = "b5f96aa039c4"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
assert SOURCE_SHA256 == PIN, (SOURCE_SHA256, PIN)  # Before any generation.


def rival(grid):
    return [[4 if cell == 2 else cell for cell in row] for row in grid]


def main():
    schedule = [
        {"seed": 44000, "sample_index": 5, "difficulty": "easy"},
        {"seed": 45000, "sample_index": 5, "difficulty": "medium"},
        {"seed": 46000, "sample_index": 5, "difficulty": "hard"},
    ]
    demos = [GEN.generate(**spec) for spec in schedule]
    checks = [GEN.self_check(grid) for grid in demos]
    assert checks == [[], [], []], checks
    query = next(p for p in canonical_pairs(TASK_ID, root=ROOT)
                 if p["variant"] == 0 and p["split"] == "train" and p["pair_index"] == 0)
    grids = demos + [query["input"]]
    applied = Catalog(ROOT).apply(TASK_ID, grids, allow_unapproved=True, timeout=45)
    assert applied["generator_sha256"] == PIN
    assert applied["executed_rule_hash"] == RULE_HASH
    assert applied["rule_hash_matches_catalog"] is True
    outputs = [r["output"] for r in applied["results"]]
    assert outputs[-1] == query["output"], "Fresh Racket query label differs from canonical"
    matches = [rival(grid) == output for grid, output in zip(grids, outputs)]
    assert matches == [True, True, True, False], matches
    wrong = rival(grids[-1])
    differences = [
        {"row": r, "col": c, "authority": outputs[-1][r][c], "rival": wrong[r][c]}
        for r in range(len(wrong)) for c in range(len(wrong[0]))
        if wrong[r][c] != outputs[-1][r][c]
    ]
    assert len(differences) == 5, differences
    evidence = {
        "schema": "arcpuzzles-bounded-peer-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": SOURCE_SHA256,
        "generator_version": GEN.VERSION,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rule_hash": applied["executed_rule_hash"],
        "rule_text_sha256": applied["rule_text_sha256"],
        "catalog_approved": applied["catalog_approved"],
        "rival": "Recolor every color-2 cell yellow (4), regardless of component size.",
        "schedule": schedule,
        "generated_self_check": checks,
        "demo_matches": matches[:-1],
        "query_match": matches[-1],
        "query_identity": {"variant": 0, "split": "train", "pair_index": 0},
        "query_domain": "Canonical authoring input used as transfer query; outside ordinary generator support.",
        "query_differences": differences,
        "challenge": {"train": [{"input": g, "output": o} for g, o in zip(demos, outputs)],
                      "test": [{"input": grids[-1]}]},
        "query_authority_output": outputs[-1],
        "query_rival_output": wrong,
        "scope": "Fresh Racket reproduction of existing unresolved audit; no source fix or approval.",
        "limits": ["One rival, three generated demos, one canonical transfer query.",
                   "No ordinary generated query disagreement established; the same shortcut also solves ordinary generated queries.",
                   "No battery, parameter admission, ignored-axis retest, or degenerate retest.",
                   "Reviewer-reported proposal until independently integrated/checked by owner."],
    }
    (HERE / "evidence.json").write_text(json.dumps(evidence, separators=(",", ":"), sort_keys=True) + "\n")
    (HERE / "racket.json").write_text(json.dumps(applied, separators=(",", ":"), sort_keys=True) + "\n")
    print(json.dumps({"task_id": TASK_ID, "source_sha256": SOURCE_SHA256,
                      "rule_hash": RULE_HASH, "demo_matches": "3/3", "query_match": False,
                      "query_differing_cells": len(differences),
                      "catalog_approved": applied["catalog_approved"]}, sort_keys=True))


if __name__ == "__main__":
    main()
