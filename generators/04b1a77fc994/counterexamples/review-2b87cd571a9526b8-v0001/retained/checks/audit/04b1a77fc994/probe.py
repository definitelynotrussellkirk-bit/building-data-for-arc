#!/usr/bin/env python3
"""Score a border-count rival on one public generated episode; no private runner."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
SOURCE = REPO / "generators/04b1a77fc994/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            count = sum((any(rr == 0 for rr, _ in cells), any(rr == h - 1 for rr, _ in cells), any(cc == 0 for _, cc in cells), any(cc == w - 1 for _, cc in cells)))
            yield {"input_color": color, "cells": sorted(cells), "border_count": count}


def rival(grid):
    """Natural unsaturated rival: each object's color equals border count + 1."""
    out = [[0] * len(grid[0]) for _ in grid]
    for obj in components(grid):
        for r, c in obj["cells"]:
            out[r][c] = obj["border_count"] + 1
    return out


def main():
    episode = json.loads((HERE / "episode.jsonl").read_text())
    canonical = json.loads((HERE / "canonical.json").read_text())
    spec = importlib.util.spec_from_file_location("audit_target_04b1a77fc994", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert sha == episode["provenance"]["generator_sha256"] == canonical["generator_sha256"]
    assert module.RULE_HASH == episode["executed_rule_hash"] == canonical["rule_hash"]
    assert episode["sample_indices"] == [1, 2, 3, 4, 5]
    assert len(episode["train"]) == 4 and len(episode["test"]) == 1
    pairs = []
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            sample_index = index + 1 if split == "train" else 5
            grid = pair["input"]
            errors = module.self_check(grid, difficulty="medium", meta={})
            prediction = rival(grid)
            facts = module.profile_facts(grid)
            assert errors == []
            assert module.generate(0, sample_index, difficulty="medium") == grid
            pairs.append({
                "split": split, "pair_index": index, "sample_index": sample_index,
                "input": grid, "authoritative_generated_output": pair["output"],
                "python_rival_output": prediction, "rival_matches_output": prediction == pair["output"],
                "self_check_errors": errors, "validator_accepts": True,
                "documented_domain_status": "in declared linked-profile domain; ordinary generated draw, no overrides",
                "observed_profile": facts["scene_profile"], "touch_counts": facts["touch_counts"],
            })
    canonical_scores = []
    for vi, variant in enumerate(canonical["variants"]):
        for split in ("train", "test"):
            for pi, pair in enumerate(variant[split]):
                canonical_scores.append({"variant": vi, "split": split, "pair_index": pi, "rival_matches_output": rival(pair["input"]) == pair["output"]})
    assert all(pair["rival_matches_output"] for pair in pairs[:4])
    assert not pairs[4]["rival_matches_output"]
    assert all(pair["rival_matches_output"] for pair in canonical_scores)
    query = pairs[4]
    changed = [[r, c, query["authoritative_generated_output"][r][c], query["python_rival_output"][r][c]] for r, row in enumerate(query["input"]) for c, _ in enumerate(row) if query["authoritative_generated_output"][r][c] != query["python_rival_output"][r][c]]
    evidence = {
        "task_id": module.TASK_ID, "source_sha256": sha, "rule_hash": module.RULE_HASH,
        "seed": 0, "difficulty": "medium", "overrides": {},
        "sample_indices": [1, 2, 3, 4, 5], "demonstrations": 4, "queries": 1,
        "policy": "ordered four demonstrations at indices 1-4, one following query at index 5; public supported --sample-index 1",
        "rival_description": "For every monochromatic 4-connected nonzero object, recolor it to the number of touched grid borders plus 1, without saturation at 4.",
        "rival_intent": "intentional teaching-negative audit probe; not an attempted blind solve",
        "pairs": pairs, "canonical_rival_scores": canonical_scores,
        "demo_fits": 4, "demo_count": 4, "query_matches": 0, "query_count": 1,
        "query_mismatch_cells": changed,
        "current_audit_index_exists": (SOURCE.parent / "evidence/review_index.json").exists(),
        "catalog_audit_unresolved": canonical.get("audit_unresolved"),
        "novelty": "new concrete wrong-query teaching-shortcut finding; current audit index absent and catalog reports no unresolved audit. Associated notes discuss high-touch branch coverage and finite-profile limits, but not this unsaturated rival.",
    }
    write("input.json", query["input"])
    write("rival-output.json", query["python_rival_output"])
    write("counterexample.json", evidence)
    print(json.dumps({"source_sha256": sha, "rule_hash": module.RULE_HASH, "profiles": [p["observed_profile"] for p in pairs], "touch_counts": [p["touch_counts"] for p in pairs], "demo_fit": "4/4", "query_fit": "0/1", "canonical_fit": f"{len(canonical_scores)}/{len(canonical_scores)}", "query_mismatch_cell_count": len(changed), "validator_accepted_inputs": len(pairs)}, sort_keys=True))


if __name__ == "__main__":
    main()
