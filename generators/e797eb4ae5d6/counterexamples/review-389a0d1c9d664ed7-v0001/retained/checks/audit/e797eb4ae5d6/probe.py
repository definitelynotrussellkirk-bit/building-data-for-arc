#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
OUT = Path(__file__).resolve().parent / "shortcut"
GEN_PATH = REPO / "generators/e797eb4ae5d6/generator.py"
SOL_PATH = REPO / "shared/data/base/solutions/training/e5c44e8f__e797eb4ae5d6.json"
EXPECTED_GEN_SHA = "e1f56c2fc4a180c99e1eb0f563e41256e9bba2b0e6c6bc611facc86dbf9ddd19"

sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_e797_generator", GEN_PATH)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)

RELS = tuple(GEN._RELS)
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def seed_cell(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    assert len(cells) == 1
    return cells[0]


def mask_cells(grid):
    sr, sc = seed_cell(grid)
    h, w = len(grid), len(grid[0])
    return {
        (sr + dr, sc + dc)
        for dr, dc in RELS
        if 0 <= sr + dr < h and 0 <= sc + dc < w and grid[sr + dr][sc + dc] != 2
    }


def connected_cells(grid):
    seed = seed_cell(grid)
    mask = mask_cells(grid)
    reached = {seed}
    q = deque([seed])
    while q:
        r, c = q.popleft()
        for dr, dc in CARDINAL:
            p = (r + dr, c + dc)
            if p in mask and p not in reached:
                reached.add(p)
                q.append(p)
    return reached


def paint(grid, cells):
    out = [row[:] for row in grid]
    for r, c in cells:
        if out[r][c] == 0:
            out[r][c] = 3
    return out


def intended(grid):
    has_blockers = any(v == 2 for row in grid for v in row)
    return paint(grid, connected_cells(grid) if has_blockers else mask_cells(grid))


def anchor_gated_rival(grid):
    # Canonical/default-fitting shortcut: a blocker triggers connected mode only
    # when it touches the stencil or the seed is the fixed scheduled anchor (4,5).
    seed = seed_cell(grid)
    mask = mask_cells(grid)
    sr, sc = seed
    h, w = len(grid), len(grid[0])
    stencil_positions = {
        (sr + dr, sc + dc)
        for dr, dc in RELS
        if 0 <= sr + dr < h and 0 <= sc + dc < w
    }
    blocker_touches = any(grid[r][c] == 2 for r, c in stencil_positions)
    has_blockers = any(v == 2 for row in grid for v in row)
    connected_mode = has_blockers and (seed == (4, 5) or blocker_touches)
    return paint(grid, connected_cells(grid) if connected_mode else mask)


def size_gated_rival(grid):
    # A second ordinary-support shortcut: the disconnected tail is painted only
    # on exactly 11x11 blocker-free inputs. Blocker-bearing behavior is retained.
    has_blockers = any(v == 2 for row in grid for v in row)
    use_full = not has_blockers and len(grid) == 11 and len(grid[0]) == 11
    return paint(grid, mask_cells(grid) if use_full else connected_cells(grid))


def canonical_pairs():
    record = json.loads(SOL_PATH.read_text())
    visible = json.loads(record["visible_context"]["samples_text"])
    pairs = [(x["input"], x["output"]) for x in visible["train"]]
    for item, output in zip(visible["test"], record["verification"]["expected_test_outputs"]):
        pairs.append((item["input"], output))
    return pairs


def source_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_override_cases():
    dimension = None
    anchor = None
    for i in range(10000):
        if dimension is None:
            g = GEN.generate("audit-size", i, grid_h=20, grid_w=20, blockers=0)
            if intended(g) != size_gated_rival(g):
                dimension = (i, g)
        if anchor is None:
            g = GEN.generate("audit-anchor", i, grid_h=12, grid_w=11, blockers=1)
            if intended(g) != anchor_gated_rival(g):
                anchor = (i, g)
        if dimension and anchor:
            return dimension, anchor
    raise AssertionError("failed to find both exact-override counterexamples")


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    assert source_sha(GEN_PATH) == EXPECTED_GEN_SHA

    pairs = canonical_pairs()
    canonical = {
        "pairs": len(pairs),
        "authority_mirror_matches": sum(int(intended(g) == out) for g, out in pairs),
        "anchor_gated_rival_fits": sum(int(anchor_gated_rival(g) == out) for g, out in pairs),
        "size_gated_rival_fits": sum(int(size_gated_rival(g) == out) for g, out in pairs),
        "dimensions": [[len(g), len(g[0])] for g, _ in pairs],
    }

    generated = {}
    for band in (None, "easy", "medium", "hard"):
        name = "default" if band is None else band
        counts = Counter()
        unique = set()
        for i in range(250):
            g = GEN.generate(f"audit-e797:{name}", i, difficulty=band)
            errors = GEN.self_check(g)
            assert errors == [], errors
            truth = intended(g)
            counts["draws"] += 1
            counts["anchor_gated_matches"] += anchor_gated_rival(g) == truth
            counts["size_gated_matches"] += size_gated_rival(g) == truth
            counts["no_blockers"] += not any(v == 2 for row in g for v in row)
            counts["no_blockers_non_11x11"] += (
                not any(v == 2 for row in g for v in row)
                and (len(g), len(g[0])) != (11, 11)
            )
            unique.add(json.dumps(g, separators=(",", ":")))
        counts["unique_inputs"] = len(unique)
        generated[name] = dict(counts)

    (dimension_i, dimension), (anchor_i, anchor) = find_override_cases()
    assert GEN.self_check(dimension) == []
    assert GEN.self_check(anchor) == []
    inputs = [anchor, dimension]
    (OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (OUT / "anchor-input.json").write_text(json.dumps(anchor, indent=2) + "\n")
    (OUT / "dimension-input.json").write_text(json.dumps(dimension, indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps({
        "anchor_gated_output": anchor_gated_rival(anchor),
        "size_gated_output": size_gated_rival(dimension),
    }, indent=2) + "\n")
    prep = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": "e797eb4ae5d6",
        "generator_sha256": EXPECTED_GEN_SHA,
        "declared_rule_hash": GEN.RULE_HASH,
        "canonical": canonical,
        "generated_probe": generated,
        "calls": {
            "anchor": {"seed": "audit-anchor", "sample_index": anchor_i, "difficulty": None,
                       "overrides": {"grid_h": 12, "grid_w": 11, "blockers": 1}},
            "dimension": {"seed": "audit-size", "sample_index": dimension_i, "difficulty": None,
                          "overrides": {"grid_h": 20, "grid_w": 20, "blockers": 0}},
        },
        "validator": {"anchor": GEN.self_check(anchor), "dimension": GEN.self_check(dimension)},
        "inputs": inputs,
        "rivals": {
            "anchor_gated": "with blockers, use connected mode only when a blocker touches the stencil or seed==(4,5)",
            "size_gated": "paint disconnected tail on blocker-free inputs only when dimensions are exactly 11x11",
        },
    }
    (OUT / "prepared.json").write_text(json.dumps(prep, indent=2) + "\n")
    print(json.dumps({"canonical": canonical, "generated_probe": generated, "calls": prep["calls"]}, indent=2))


def verify():
    prep = json.loads((OUT / "prepared.json").read_text())
    receipt = json.loads((OUT / "racket.json").read_text())
    rival = json.loads((OUT / "rival.json").read_text())
    assert receipt["executed_rule_hash"] == GEN.RULE_HASH
    assert receipt["generator_sha256"] == EXPECTED_GEN_SHA
    assert len(receipt["results"]) == 2
    actual_anchor = receipt["results"][0]["output"]
    actual_dimension = receipt["results"][1]["output"]
    anchor = prep["inputs"][0]
    dimension = prep["inputs"][1]
    assert actual_anchor == intended(anchor)
    assert actual_dimension == intended(dimension)
    assert actual_anchor != rival["anchor_gated_output"]
    assert actual_dimension != rival["size_gated_output"]

    def diffs(a, b):
        return [[r, c] for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]

    summary = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": "e797eb4ae5d6",
        "generator_sha256": EXPECTED_GEN_SHA,
        "rule_hash": receipt["executed_rule_hash"],
        "canonical": prep["canonical"],
        "generated_probe": prep["generated_probe"],
        "counterexamples": [
            {
                "id": "anchor_gated_global_switch",
                "call": prep["calls"]["anchor"],
                "validator_result": prep["validator"]["anchor"],
                "documented_domain": True,
                "input": anchor,
                "authority_output": actual_anchor,
                "rival_output": rival["anchor_gated_output"],
                "differing_cells": diffs(actual_anchor, rival["anchor_gated_output"]),
            },
            {
                "id": "size_gated_disconnected_tail",
                "call": prep["calls"]["dimension"],
                "validator_result": prep["validator"]["dimension"],
                "documented_domain": True,
                "input": dimension,
                "authority_output": actual_dimension,
                "rival_output": rival["size_gated_output"],
                "differing_cells": diffs(actual_dimension, rival["size_gated_output"]),
            },
        ],
        "racket_evidence": "checks/audit/e797eb4ae5d6/shortcut/racket.json",
        "command": receipt["command"],
        "cwd": receipt["cwd"],
        "assessment": "two reproduced curriculum shortcuts; selected Racket rule remains internally consistent",
    }
    (OUT / "counterexample.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({
        "rule_hash": summary["rule_hash"],
        "canonical": summary["canonical"],
        "generated_totals": {
            k: {kk: vv for kk, vv in v.items() if kk != "unique_inputs"}
            for k, v in summary["generated_probe"].items()
        },
        "counterexample_differences": [len(x["differing_cells"]) for x in summary["counterexamples"]],
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "verify"}:
        raise SystemExit("usage: probe.py prepare|verify")
    globals()[sys.argv[1]]()
