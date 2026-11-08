#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs, load_selected_generator


def diagonal_only(grid):
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions[value].append((r, c))
    for color, points in positions.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        dr, dc = r2 - r1, c2 - c1
        if abs(dr) != abs(dc):
            continue
        sr = 1 if dr > 0 else -1
        sc = 1 if dc > 0 else -1
        for k in range(abs(dr) + 1):
            out[r1 + k * sr][c1 + k * sc] = color
    return out


def connect_any_aligned_pair(grid):
    """Incorrect rival: fill horizontal/vertical pairs as well as diagonals."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions[value].append((r, c))
    for color, points in positions.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        dr, dc = r2 - r1, c2 - c1
        if dr == 0 and dc != 0:
            sr, sc, steps = 0, (1 if dc > 0 else -1), abs(dc)
        elif dc == 0 and dr != 0:
            sr, sc, steps = (1 if dr > 0 else -1), 0, abs(dr)
        elif abs(dr) == abs(dc) and dr != 0:
            sr, sc, steps = (1 if dr > 0 else -1), (1 if dc > 0 else -1), abs(dr)
        else:
            continue
        for k in range(steps + 1):
            out[r1 + k * sr][c1 + k * sc] = color
    return out


def main():
    generation = json.loads((HERE / "generation.json").read_text())
    grid = json.loads((HERE / "input.json").read_text())["input"]
    receipt = json.loads((HERE / "racket.json").read_text())
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["generator_sha256"] == generation["generator_sha256"]
    assert receipt["results"][0]["error"] is None
    authority = receipt["results"][0]["output"]
    intended = diagonal_only(grid)
    rival = connect_any_aligned_pair(grid)
    assert intended == authority
    assert rival != authority

    generator, _, _ = load_selected_generator("366ce015cd2a", root=REPO)
    assert generator.self_check(grid) == []

    canon = canonical_pairs("366ce015cd2a", root=REPO, labeled_only=True)
    canonical_fit = sum(connect_any_aligned_pair(pair["input"]) == pair["output"] for pair in canon)
    generated_fit = 0
    generated_total = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(20):
            sample = generator.generate(500 + 100 * band_index + index, index, difficulty=band)
            generated_total += 1
            generated_fit += int(connect_any_aligned_pair(sample) == diagonal_only(sample))
    assert canonical_fit == len(canon)
    assert generated_fit == generated_total

    result = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": "366ce015cd2a",
        "classification": "accepted semantic-domain gap / shortcut",
        "generator_sha256": generation["generator_sha256"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "rival": "connect every same-color pair aligned horizontally, vertically, or diagonally",
        "canonical_fit": {"passed": canonical_fit, "total": len(canon)},
        "generated_fit": {"passed": generated_fit, "total": generated_total},
        "witness_self_check": generator.self_check(grid),
        "input": grid,
        "authority_output": authority,
        "rival_output": rival,
        "conclusion": (
            "The canonical examples and all 60 sampled default generated inputs contain only "
            "diagonal pairs, so the rival fits them. The exact witness is accepted by self_check "
            "and adds one horizontal pair: the authority leaves it as endpoints, while the rival "
            "fills the row. The axis_aligned_pair texture is declared degenerate and is never "
            "mixed with helpful diagonal pairs by the production sampler."
        ),
        "evidence_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("input.json", "generation.json", "racket.json")
        },
    }
    (HERE / "counterexample.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_fit": result["canonical_fit"],
        "generated_fit": result["generated_fit"],
        "witness_accepted": result["witness_self_check"] == [],
        "witness_disagrees": result["authority_output"] != result["rival_output"],
    }, indent=2))


if __name__ == "__main__":
    main()
