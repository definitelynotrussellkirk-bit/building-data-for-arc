"""Read-only, source-bound semantic investigation using public Racket labels.

Replay from packet root:
  python3 run_with_racket.py python3 generators/e521d16d403e/workspace/semantic_probe.py \
    --phase after --out ../checks/semantic-after
Use --generator PATH to investigate an explicitly saved source snapshot. Output
directories must be new or empty so earlier source-bound evidence is preserved.
The structural Python model below is audit logic, never a source of labels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

TASK = "e521d16d403e"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"


def digest(value):
    data = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()


def objects(grid, *, connectivity=4, same_color=True, group_color=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == 8:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            if group_color:
                cells = [(rr, cc) for rr in range(h) for cc in range(w)
                         if grid[rr][cc] == color]
                seen.update(cells)
            else:
                for rr, cc in cells:
                    for dr, dc in steps:
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                                and grid[nr][nc] and (not same_color or grid[nr][nc] == color)):
                            seen.add((nr, nc))
                            cells.append((nr, nc))
            r0, r1 = min(x[0] for x in cells), max(x[0] for x in cells)
            c0, c1 = min(x[1] for x in cells), max(x[1] for x in cells)
            crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
            found.append({"color": color, "size": len(cells), "bbox": [r0, c0, r1, c1],
                          "cells": cells, "height": r1 - r0 + 1, "width": c1 - c0 + 1,
                          "area": (r1 - r0 + 1) * (c1 - c0 + 1), "crop": crop,
                          "lr": all(row == row[::-1] for row in crop), "ud": crop == crop[::-1]})
    return found


def predict(grid, name="reference_structure"):
    obs = objects(grid, connectivity=8 if name == "eight_connected" else 4,
                  same_color=name != "nonzero_connected", group_color=name == "group_by_color")
    if not obs:
        return None
    if name == "largest_object":
        candidates = obs
    else:
        candidates = [o for o in obs if
                      (o["lr"] and (name == "width_one_allowed" or o["width"] > 1))
                      or (name == "either_axis" and o["ud"] and o["height"] > 1)]
    if not candidates:
        return obs[0]["crop"]
    if name == "first_lr":
        chosen = candidates[0]
    elif name == "last_lr":
        chosen = candidates[-1]
    elif name == "smallest_lr":
        chosen = min(candidates, key=lambda o: o["size"])
    else:
        chosen = max(candidates, key=lambda o: o["area"] if name == "largest_bbox_lr" else o["size"])
    return chosen["crop"]


RIVALS = ["largest_object", "first_lr", "last_lr", "smallest_lr", "largest_bbox_lr",
          "width_one_allowed", "either_axis", "group_by_color", "eight_connected", "nonzero_connected"]


def describe(grid):
    obs = objects(grid)
    candidate = [o for o in obs if o["width"] > 1 and o["lr"]]
    answer = predict(grid)
    return {"shape": [len(grid), len(grid[0])], "colors": sorted({v for row in grid for v in row}),
            "objects": [{k: v for k, v in o.items() if k != "cells"} for o in obs],
            "candidate_count": len(candidate), "structural_prediction": answer,
            "rival_matches_structural_prediction": {n: predict(grid, n) == answer for n in RIVALS}}


def scene(*placements, h=10, w=10):
    grid = [[0] * w for _ in range(h)]
    for block, r, c, color in placements:
        for dr, row in enumerate(block):
            for dc, value in enumerate(row):
                if value:
                    assert grid[r + dr][c + dc] == 0
                    grid[r + dr][c + dc] = color
    return grid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=SOURCE,
                        help="generator source; defaults to this library/runtime's selected task")
    parser.add_argument("--out", required=True, type=Path,
                        help="new or empty evidence directory; nonempty directories are refused")
    parser.add_argument("--phase", choices=("before", "after"), default="after",
                        help="source role recorded in metadata and artifact names (default: after)")
    parser.add_argument("--seeds", type=int, default=100,
                        help="default-draw seeds per band (default: 100)")
    args = parser.parse_args()
    source = args.generator.resolve()
    out = args.out.resolve()
    if not source.is_file():
        parser.error(f"generator source does not exist: {source}")
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error(f"refusing nonempty or non-directory output path: {out}")
    out.mkdir(parents=True, exist_ok=True)

    def write_artifact(suffix, payload):
        path = out / f"{args.phase}-{suffix}.json"
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2) + "\n")

    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    spec = importlib.util.spec_from_file_location("semantic_probe_subject", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    pairs = canonical_pairs(TASK, root=ROOT)
    unique = {}
    for pair in pairs:
        unique.setdefault(digest(pair["input"]), pair)
    canonical = [{**p, "input_sha256": digest(p["input"]), "analysis": describe(p["input"])}
                 for p in unique.values()]
    canonical_fit = {n: all(predict(p["input"], n) == p["output"] for p in canonical) for n in RIVALS}
    generated = []
    for band in ("easy", "medium", "hard"):
        for seed in range(args.seeds):
            g = gen.generate(seed, 0, difficulty=band)
            generated.append({"seed": seed, "sample_index": 0, "difficulty": band,
                              "input": g, "input_sha256": digest(g), "analysis": describe(g),
                              "self_check": gen.self_check(g, difficulty=band)})
    selected = [{"name": f"canonical-{i}", "input": p["input"], "expected": p["output"]}
                for i, p in enumerate(canonical)]
    selected += [{"name": f"default-{x['difficulty']}-{x['seed']}", "input": x["input"],
                  "structural_prediction": x["analysis"]["structural_prediction"]}
                 for x in generated if x["seed"] < 10]
    witnesses = {
        "larger_asym_and_first_smallest_lr": scene(([[1, 1]], 0, 0, 3),
            ([[1, 1, 1, 1], [1, 0, 0, 0], [1, 1, 1, 1]], 3, 0, 2),
            ([[1, 1], [1, 1]], 7, 7, 4)),
        "cell_count_not_bbox_area": scene(([[1, 0, 0, 0, 1], [1, 1, 1, 1, 1]], 0, 0, 3),
            ([[1, 1, 1, 1], [1, 1, 1, 1]], 6, 5, 4)),
        "width_one_ineligible": scene(([[1], [1], [1], [1], [1]], 0, 0, 2),
            ([[1, 1], [1, 1]], 5, 5, 4)),
        "group_by_color_is_not_components": scene(([[1, 1], [1, 1]], 1, 1, 4),
            ([[1, 1], [1, 0]], 5, 5, 4), ([[1, 1]], 8, 0, 2)),
        "four_not_eight_connectivity": scene(([[1, 1], [1, 1]], 0, 0, 4),
            ([[1, 1], [1, 1]], 2, 2, 4), ([[1, 1]], 8, 0, 2)),
        "same_color_not_all_nonzero_components": scene(([[1, 1], [1, 1]], 0, 0, 4),
            ([[1], [1]], 1, 2, 2), ([[1, 1]], 8, 0, 3)),
        "raw_bbox_pixels_not_object_mask": scene(([[1, 1, 1, 1, 1], [1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]], 0, 0, 4),
            ([[1]], 1, 1, 2), ([[1, 1], [1, 1]], 7, 7, 3)),
        "no_candidate_fallback_first": scene(([[1], [1], [1]], 0, 0, 2),
            ([[1, 1], [1, 0]], 5, 5, 3)),
    }
    selected += [{"name": name, "input": g, "structural_prediction": predict(g)}
                 for name, g in witnesses.items()]
    # The generated records are pinned before a concurrent repair can alter code.
    identity = {"task_id": TASK, "phase": args.phase, "generator_path": str(source),
                "generator_sha256": source_hash, "generator_version": gen.VERSION,
                "command": sys.argv}
    preliminary = {**identity,
                   "canonical_record_count": len(pairs), "canonical_unique_count": len(canonical),
                   "canonical": canonical, "canonical_rival_fit": canonical_fit, "generated": generated}
    write_artifact("structural-evidence", preliminary)
    if source.read_bytes() != source_bytes:
        raise RuntimeError("Source changed while collecting evidence. Partial evidence retained; rerun in a new directory.")
    from arcpuzzles import Catalog
    catalog = Catalog()
    applied = catalog.apply(TASK, [x["input"] for x in selected], timeout=180)
    for case, result in zip(selected, applied["results"], strict=True):
        case["racket_result"] = result
        case["analysis"] = describe(case["input"])
        case["structural_model_matches_racket"] = predict(case["input"]) == result["output"]
        case["rival_matches_racket"] = {n: predict(case["input"], n) == result["output"] for n in RIVALS}
    write_artifact("racket-cases", {**identity,
                   "authority": {k: v for k, v in applied.items() if k != "results"},
                   "cases": selected})
    summary = {**identity, "rule_hash": applied["executed_rule_hash"],
               "canonical_records": len(pairs), "canonical_unique_grids": len(canonical),
               "canonical_profiles": sorted({tuple(x["analysis"]["shape"] + [len(x["analysis"]["colors"])])
                                              for x in canonical}),
               "canonical_rival_fit": canonical_fit,
               "racket_cases": len(selected),
               "structural_model_racket_mismatches": [x["name"] for x in selected if not x["structural_model_matches_racket"]],
               "generated_per_band": {b: {"count": sum(x["difficulty"] == b for x in generated),
                    "selfcheck_rejected": sum(bool(x["self_check"]) for x in generated if x["difficulty"] == b),
                    "largest_shortcut_matches": sum(x["analysis"]["rival_matches_structural_prediction"]["largest_object"]
                                                    for x in generated if x["difficulty"] == b),
                    "candidate_count_histogram": dict(Counter(x["analysis"]["candidate_count"] for x in generated if x["difficulty"] == b)),
                    "output_width_histogram": dict(Counter(len(x["analysis"]["structural_prediction"][0]) for x in generated if x["difficulty"] == b))}
                    for b in ("easy", "medium", "hard")},
               "witness_refutations": {x["name"]: [n for n, equal in x["rival_matches_racket"].items() if not equal]
                                        for x in selected if x["name"] in witnesses}}
    write_artifact("summary", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
