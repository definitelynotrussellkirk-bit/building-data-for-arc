#!/usr/bin/env python3
"""Compact findings-only audit. Run prepare, public apply, then compare.

Uses public selected-generator/canonical helpers; never reads solve artifacts.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "9cea0e6444f1"
HERE = Path(__file__).resolve().parent


def cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def render(points):
    r0, c0 = min(r for r, c in points), min(c for r, c in points)
    h, w = max(r for r, c in points) - r0 + 1, max(c for r, c in points) - c0 + 1
    out = [[0] * w for _ in range(h)]
    for r, c in points:
        out[r - r0][c - c0] = 3
    return out


def first_pixel_union(grid):
    """Rival: align the first row-major cell of each color, then crop union."""
    merged = set()
    for color in (1, 2):
        points = cells(grid, color)
        r0, c0 = min(points)
        merged.update((r - r0, c - c0) for r, c in points)
    return render(merged)


def place(one, two):
    grid = [[0] * 9 for _ in range(9)]
    for color, points, (r0, c0) in ((1, one, (1, 1)), (2, two, (5, 5))):
        for r, c in points:
            grid[r0 + r][c0 + c] = color
    return grid


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    root = find_root(__file__)
    gen, source, sha = load_selected_generator(TASK, root=root)
    canonical = canonical_pairs(TASK, root=root)
    puzzle = Catalog(root=root).get(TASK)
    program = puzzle["variants"][0]["program_solution"]
    report = {
        "task_id": TASK,
        "generator_path": str(source),
        "generator_sha256": sha,
        "declared_rule_hash": gen.RULE_HASH,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "canonical_program_source": "Catalog(root=find_root(__file__)).get(TASK)['variants'][0]['program_solution']",
        "canonical_program": program,
        "rows": [],
    }
    grids = []
    for seed in (0, 17, 90210):
        for difficulty in ("easy", "medium", "hard"):
            for index in range(6):
                grid = gen.generate(seed, index, difficulty=difficulty)
                grids.append(grid)
                report["rows"].append({
                    "kind": "generated", "seed": seed, "sample_index": index,
                    "difficulty": difficulty, "overrides": {},
                    "observed_overrides": gen.observe_overrides(grid),
                    "self_check": gen.self_check(grid),
                    "strict_canonical_like": gen.strict_canonical_like(grid),
                })
    for pair in canonical:
        grids.append(pair["input"])
        report["rows"].append({
            "kind": "canonical", "split": pair["split"], "pair_index": pair["pair_index"],
            "recorded_output": pair["output"],
            "self_check": gen.self_check(pair["input"]),
            "strict_canonical_like": gen.strict_canonical_like(pair["input"]),
        })
    mixed = place({(0, 0), (0, 1), (1, 0), (2, 0)}, {(0, 1), (1, 0), (1, 1), (1, 2)})
    identical = place({(0, 0), (1, 0), (1, 1)}, {(0, 0), (1, 0), (1, 1)})
    for label, grid in (("mixed_origin_query", mixed), ("retained_validator_hole_recreation", identical)):
        grids.append(grid)
        try:
            observed = gen.observe_overrides(grid)
        except Exception as exc:
            observed = {"error_type": type(exc).__name__, "message": str(exc)}
        report["rows"].append({
            "kind": label, "seed": None, "sample_index": None, "overrides": None,
            "construction": "hand-authored; see place() and literal masks in probe.py",
            "observed_overrides": observed,
            "self_check": gen.self_check(grid),
            "strict_canonical_like": gen.strict_canonical_like(grid),
            "semantic_witnesses": {name: bool(fn(grid)) for name, fn in gen.SEMANTIC_WITNESSES.items()},
        })
    report["canonical_shortcut_validation"] = {
        name: {
            "checked": len(canonical),
            "mismatches": [
                {"split": p["split"], "pair_index": p["pair_index"], "rival_output": fn(p["input"]), "canonical_output": p["output"]}
                for p in canonical if fn(p["input"]) != p["output"]
            ],
        } for name, fn in gen.CANONICAL_SHORTCUTS.items()
    }
    save("input.json", {"inputs": grids})
    save("mixed_origin_input.json", mixed)
    save("rival.json", {"outputs": [first_pixel_union(grid) for grid in grids]})
    save("prepared.json", report)
    print(json.dumps({"phase": "prepare", "generator_sha256": sha, "canonical_program_sha256": report["canonical_program_sha256"], "rows": len(grids)}))


def compare():
    prepared = json.loads((HERE / "prepared.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    rival = json.loads((HERE / "rival.json").read_text())["outputs"]
    print(json.dumps({"racket_top_keys": list(actual) if isinstance(actual, dict) else None}))
    assert actual["generator_sha256"] == prepared["generator_sha256"]
    assert actual["executed_rule_hash"] == prepared["declared_rule_hash"]
    assert all(row["error"] is None and row["valid_output"] for row in actual["results"])
    outputs = [row["output"] for row in actual["results"]]
    prepared["racket_provenance"] = {k: actual[k] for k in (
        "reference", "rule_file", "executed_rule_hash", "catalog_rule_hash",
        "rule_hash_matches_catalog", "rule_text_sha256", "generator_sha256", "command", "cwd"
    )}
    assert len(outputs) == len(prepared["rows"]) == 61
    for i, row in enumerate(prepared["rows"]):
        row["input_index"] = i
        row["first_pixel_rival_agrees_with_racket"] = rival[i] == outputs[i]
        if row["kind"] == "canonical":
            row["recorded_output_matches_racket"] = row["recorded_output"] == outputs[i]
        if row["kind"] in ("mixed_origin_query", "retained_validator_hole_recreation"):
            row["racket_output"] = outputs[i]
            row["first_pixel_rival_output"] = rival[i]
    summary = {}
    for kind in ("generated", "canonical", "mixed_origin_query", "retained_validator_hole_recreation"):
        rows = [row for row in prepared["rows"] if row["kind"] == kind]
        summary[kind] = {
            "checked": len(rows),
            "first_pixel_rival_agreements": sum(row["first_pixel_rival_agrees_with_racket"] for row in rows),
            "self_check_accepted": sum(row["self_check"] == [] for row in rows),
            "strict_canonical_like_accepted": sum(row["strict_canonical_like"] == [] for row in rows),
        }
    prepared["summary"] = summary
    save("report.json", prepared)
    save("mixed_origin_racket.json", outputs[59])
    save("mixed_origin_rival.json", rival[59])
    print(json.dumps(summary, indent=2))
    assert summary["generated"]["first_pixel_rival_agreements"] == 54
    assert summary["canonical"]["first_pixel_rival_agreements"] == 5
    assert summary["mixed_origin_query"]["first_pixel_rival_agreements"] == 0
    assert all(row.get("recorded_output_matches_racket", True) for row in prepared["rows"])


if __name__ == "__main__":
    {"prepare": prepare, "compare": compare}[sys.argv[1]]()
