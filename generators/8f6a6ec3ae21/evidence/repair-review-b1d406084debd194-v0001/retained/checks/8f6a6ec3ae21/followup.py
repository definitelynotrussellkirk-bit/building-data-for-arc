"""Bounded replay of retained one-sided audit and an UNSELECTED schedule proposal.

Run from the outer packet: WORK/.venv/bin/python review.py run python3
../checks/8f6a6ec3ae21/followup.py
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from reviewer_support import canonical_pairs, find_root, load_selected_generator
from arcpuzzles import Catalog

TASK = "8f6a6ec3ae21"
SOURCE = "a30551fabf7d39bc1056441e22e0a9153c2457be1f5d488d9307f5eee57e6475"
RULE = "ca6d5269f15c"


def rival(grid, side):
    rows = [r for r in range(len(grid))
            if (grid[r][0] == 1 if side == "left" else grid[r][0] != 0)]
    cols = [c for c in range(len(grid[0]))
            if (grid[0][c] == 2 if side == "top" else grid[0][c] != 0)]
    return [[8 if r in rows and c in cols else 0 for c in range(len(grid[0]))]
            for r in range(len(grid))]


def ambiguities(pairs):
    found = []
    for query in range(3):
        for side in ("left", "top"):
            if all(rival(p["input"], side) == p["output"]
                   for i, p in enumerate(pairs) if i != query):
                if rival(pairs[query]["input"], side) != pairs[query]["output"]:
                    found.append({"query_index": query, "rival": "filter_" + side + "_only"})
    return found


def main():
    root = find_root(__file__)
    assert root == ROOT
    gen, source, digest = load_selected_generator(TASK, root=root)
    assert digest == SOURCE and gen.RULE_HASH == RULE
    catalog = Catalog(root)
    selected = catalog.get(TASK)
    assert selected["generator_sha256"] == SOURCE and selected["rule_hash"] == RULE
    programs = sorted({v["program_solution"] for v in selected["variants"]
                       if v.get("program_solution")})
    assert len(programs) == 1
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    defaults = [gen.generate(10401, i, difficulty="medium") for i in range(3)]
    # Proposal only: every consecutive pair covers decoys on both borders.
    # Overrides preserve generator bytes, version, and selected approval.
    schedule = [(1, 1), (0, 1), (1, 0)]
    proposed = [gen.generate(10401, i, difficulty="medium",
                            n_row_decoys=schedule[i % 3][0],
                            n_col_decoys=schedule[i % 3][1]) for i in range(5)]
    inputs = [p["input"] for p in canonical] + defaults + proposed
    assert all(not gen.self_check(g) and not gen.strict_canonical_like(g) for g in inputs)
    applied = catalog.apply(TASK, inputs, reference="canonical", timeout=45,
                            check_generator_domain=True)
    (HERE / "racket.json").write_text(json.dumps(applied, indent=2) + "\n")
    assert applied["executed_rule_hash"] == RULE and applied["generator_sha256"] == SOURCE
    assert applied["rule_hash_matches_catalog"]
    assert all(p["valid_output"] and p["error"] is None for p in applied["results"])
    pairs = [{"input": p["input"], "output": p["output"]} for p in applied["results"]]
    assert all(p["output"] == gen.rule_mirror(p["input"]) for p in pairs)
    n = len(canonical)
    assert pairs[:n] == [{"input": p["input"], "output": p["output"]} for p in canonical]
    assert all(rival(p["input"], side) == p["output"]
               for p in pairs[:n] for side in ("left", "top"))
    default = pairs[n:n+3]
    found = ambiguities(default)
    assert found == [{"query_index": 1, "rival": "filter_left_only"}]
    assert gen.lesson_identifiable([default[0], default[2]], default[1]) == []
    differences = [[r, c] for r, row in enumerate(default[1]["output"])
                   for c, value in enumerate(row)
                   if value != rival(default[1]["input"], "left")[r][c]]
    assert differences == [[2, 1], [3, 1], [6, 1]]
    proposed_pairs = pairs[n+3:]
    windows = [{"start_index": i, "ambiguities": ambiguities(proposed_pairs[i:i+3])}
               for i in range(3)]
    assert all(not w["ambiguities"] for w in windows)
    result = {
        "schema": "8f6a6ec3ae21-bounded-schedule-followup-v1",
        "verification_status": "reviewer_reported_pending_owner_checked_integration",
        "generator_sha256": digest, "rule_hash": RULE,
        "canonical_program": programs[0],
        "canonical_program_sha256": hashlib.sha256(programs[0].encode()).hexdigest(),
        "executed_rule_text_sha256": applied["rule_text_sha256"],
        "fresh_racket_inputs": len(inputs), "canonical_pairs": n,
        "default_seed": 10401, "difficulty": "medium", "default_indices": [0, 1, 2],
        "default_ambiguities": found, "default_query_difference_coordinates": differences,
        "declared_lesson_hook_misses_existing_rival": True,
        "proposal_status": "unselected_explicit_overrides_only",
        "proposed_decoy_cycle_row_col": schedule,
        "proposed_window_checks": windows,
        "audit_resolution": "unresolved_unchanged",
        "limits": ["One seed and one band; no full battery or parametric qualification.",
                   "Nine proposal holdouts reject only the two named one-sided rivals.",
                   "Existing ordinary ordered production lessons had no demonstrated gap against these rivals.",
                   "No generator, canonical program, approval, or audit index was changed."]}
    (HERE / "followup.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "passed", "fresh_racket_inputs": len(inputs),
                      "existing_default_ambiguity": found, "proposal_holdouts_checked": 9}))


if __name__ == "__main__":
    main()
