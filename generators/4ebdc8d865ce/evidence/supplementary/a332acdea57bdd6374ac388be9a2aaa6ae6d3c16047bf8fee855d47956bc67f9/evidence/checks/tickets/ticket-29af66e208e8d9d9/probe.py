from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TICKET_ID = "ticket-29af66e208e8d9d9"
TASK_ID = "4ebdc8d865ce"
PINNED_SHA256 = "943bbd19be3918848e6377245c7f264068812dc9331f0e19a97658d189927797"
PINNED_RULE_HASH = "6c1ad8a5edc2"
PROBE_SEED_HEX = "087509dbf747a43e9938a95246c6f0490bee3590ad81dfa377725054cb99d88b"
SEARCH_LIMIT = 64
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "tickets" / TICKET_ID
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

assert SOURCE_SHA256 == PINNED_SHA256
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == PINNED_SHA256
assert GEN.RULE_HASH == PINNED_RULE_HASH


def omit_south_rival(grid):
    """Plausible directional bug: checks N/W/E, but forgets S."""
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2:
                continue
            has_checked_neighbor = any(
                0 <= rr < height
                and 0 <= cc < width
                and grid[rr][cc] == 2
                for rr, cc in (
                    (row - 1, col),
                    (row, col - 1),
                    (row, col + 1),
                )
            )
            if not has_checked_neighbor:
                output[row][col] = 1
    return output


canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
canonical_checks = []
for pair in canonical:
    rival_output = omit_south_rival(pair["input"])
    matches = rival_output == pair["output"]
    canonical_checks.append(
        {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "rival_matches_label": matches,
        }
    )
assert canonical and all(row["rival_matches_label"] for row in canonical_checks)

seed = int(PROBE_SEED_HEX, 16)
witness = None
for sample_index in range(SEARCH_LIMIT):
    grid = GEN.generate(
        seed,
        sample_index,
        difficulty=None,
        scene_family="generalized",
    )
    errors = GEN.self_check(grid)
    assert errors == []
    intended = GEN.rule_mirror(grid)
    rival = omit_south_rival(grid)
    if intended == rival:
        continue
    differences = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if intended[row][col] != rival[row][col]:
                neighbors = {}
                for name, rr, cc in (
                    ("north", row - 1, col),
                    ("west", row, col - 1),
                    ("east", row, col + 1),
                    ("south", row + 1, col),
                ):
                    neighbors[name] = (
                        grid[rr][cc]
                        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0])
                        else None
                    )
                differences.append(
                    {
                        "row": row,
                        "column": col,
                        "input": grid[row][col],
                        "intended": intended[row][col],
                        "rival": rival[row][col],
                        "orthogonal_neighbors": neighbors,
                    }
                )
    witness = {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": None,
        "overrides": {"scene_family": "generalized"},
        "self_check": errors,
        "observed_overrides": GEN.observe_overrides(grid),
        "canonical_profile_signature": GEN.canonical_profile_signature(grid),
        "input": grid,
        "intended_output": intended,
        "rival_output": rival,
        "differences": differences,
    }
    break

assert witness is not None, f"no witness found in {SEARCH_LIMIT} lawful samples"
assert all(
    difference["orthogonal_neighbors"] == {
        "north": 0,
        "west": 0,
        "east": 0,
        "south": 2,
    }
    for difference in witness["differences"]
)

input_path = OUT / "input.json"
racket_path = OUT / "racket.json"
input_path.write_text(json.dumps({"input": witness["input"]}, indent=2) + "\n")
subprocess.run(
    [
        sys.executable,
        "-m",
        "arcpuzzles",
        "apply",
        TASK_ID,
        "--input",
        str(input_path),
        "--out",
        str(racket_path),
    ],
    cwd=ROOT,
    check=True,
    timeout=120,
)
racket = json.loads(racket_path.read_text())
racket_output = racket["results"][0]["output"]
assert racket["executed_rule_hash"] == PINNED_RULE_HASH
assert racket_output == witness["intended_output"]

report = {
    "schema": "arcpuzzles-supplementary-adversarial-witness-v1",
    "ticket_id": TICKET_ID,
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "rule_hash": PINNED_RULE_HASH,
    "probe_seed_hex": PROBE_SEED_HEX,
    "search_limit": SEARCH_LIMIT,
    "samples_examined": witness["sample_index"] + 1,
    "shortcut": (
        "recolor a 2 unless it has a north, west, or east 2-neighbor; "
        "south is accidentally omitted"
    ),
    "canonical_pairs_checked": canonical_checks,
    "canonical_shortcut_survives": True,
    "lawful_generated_witness_found": True,
    "witness": witness,
    "racket": {
        "path": str(racket_path.relative_to(ROOT.parent)),
        "executed_rule_hash": racket["executed_rule_hash"],
        "matches_intended_output": True,
    },
    "outcome": (
        "completed: the selected generator emits a lawful generalized scene "
        "that refutes this canonical-fitting directional shortcut"
    ),
}
(OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(
    json.dumps(
        {
            "canonical_pairs_checked": len(canonical_checks),
            "samples_examined": report["samples_examined"],
            "witness_sample_index": witness["sample_index"],
            "difference_count": len(witness["differences"]),
            "racket_matches": True,
        },
        indent=2,
        sort_keys=True,
    )
)
