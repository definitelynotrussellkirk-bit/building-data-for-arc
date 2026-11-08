#!/usr/bin/env python3
"""Embed the negative witness next to a true frame within normal grid bounds."""
from pathlib import Path
import json
from arcpuzzles import Catalog
from probe import area_rival, hole_rival

out = Path(__file__).resolve().parent
grid = [[0] * 11 for _ in range(9)]
frame = [[3,3,3],[3,0,3],[3,3,3]]
distractor = [[0,2,2,2],[2,0,0,2],[2,2,2,2]]
for r in range(3):
    grid[r][:3] = frame[r]
    grid[r][4:8] = distractor[r]
result = Catalog().apply("54875f792be0", [grid], timeout=60)
reference = result["results"][0]["output"]
expected = [[0] * 11 for _ in range(9)]
for r in range(3):
    expected[r][:3] = frame[r]
assert reference == expected
assert area_rival(grid) != reference and hole_rival(grid) != reference
result["witness_name"] = "mixed_complete_frame_and_missing_corner"
result["area_rival_output"] = area_rival(grid)
result["hole_rival_output"] = hole_rival(grid)
result["semantic_invariants"] = "0 background; one true frame; one non-frame; distinct colors; disconnected objects; 9x11 valid easy dimensions"
(out / "mixed_reference_witness.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"witness_name": result["witness_name"], "reference_matches_expected": True,
                  "both_rivals_refuted": True, "generator_sha256": result["generator_sha256"],
                  "executed_rule_hash": result["executed_rule_hash"]}))
