#!/usr/bin/env python3
"""Authoring-only current-source replay of an exact-frame teaching shortcut."""
from collections import deque
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "54875f792be0"


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid):
    seen, result = set(), []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if not grid[r][c] or (r, c) in seen:
                continue
            color, cells, todo = grid[r][c], [], deque([(r, c)])
            seen.add((r, c))
            while todo:
                row, col = todo.popleft()
                cells.append((row, col))
                for nr, nc in ((row-1, col), (row+1, col), (row, col-1), (row, col+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((color, cells))
    return result


def rival(grid):
    """Keep >=8-cell components unless they fill their entire bounding box."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        height = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        width = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if len(cells) >= 8 and len(cells) < height * width:
            for r, c in cells:
                out[r][c] = color
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output exists; choose a new report path")
    root = args.library
    if root is None:
        root = next(parent / "repo" for parent in Path(__file__).resolve().parents
                    if (parent / "repo/shared/runtime/reviewer_support.py").is_file())
    root = root.resolve()
    sys.path[:0] = [str(root / "src"), str(root / "shared/runtime")]
    from reviewer_support import canonical_pairs, find_root
    from arcpuzzles import Catalog
    root = find_root(root)
    source = root / "generators" / TASK / "generator.py"
    source_hash = file_sha(source)
    spec = importlib.util.spec_from_file_location("frame_generator_audit", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    canonical = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
                  "input_sha256": sha(p["input"]), "output_sha256": sha(p["output"]),
                  "rival_matches_label": rival(p["input"]) == p["output"]} for p in pairs]
    grid = [[0] * 11 for _ in range(9)]
    loop = [[0, 2, 2, 2, 0], [2, 2, 0, 2, 2], [2, 0, 0, 0, 2], [2, 2, 2, 2, 2]]
    for r, row in enumerate(loop, 4):
        grid[r][1:6] = row
    for r in range(1, 4):
        for c in range(7, 10):
            if r in (1, 3) or c in (7, 9):
                grid[r][c] = 3
    expected = [[0 if cell == 2 else cell for cell in row] for row in grid]
    cases = [{"kind": "handmade_equal_perimeter_nonrectangular_loop", "seed": None,
              "sample_index": None, "difficulty": "easy", "overrides": {},
              "input": grid, "expected_reference_output": expected,
              "domain": "9x11; distinct nonzero colors; separated intact 3x3 frame and non-frame 4x5 loop. The loop has 14 cells, matching its bounding-box perimeter, but contains interior cells and lacks both top corners; it is outside emitted constructor support."}]
    for band in ("easy", "medium", "hard"):
        for index in (0, 1):
            cases.append({"kind": "direct_production_generate", "seed": 54875,
                          "sample_index": index, "difficulty": band, "overrides": {},
                          "input": gen.generate(54875, index, difficulty=band)})
    applied = Catalog(root).apply(TASK, [case["input"] for case in cases], timeout=args.timeout)
    for case, result in zip(cases, applied["results"], strict=True):
        case["input_sha256"] = sha(case["input"])
        case["self_check"] = gen.self_check(deepcopy(case["input"]), difficulty=case["difficulty"])
        case["actual_reference_output"] = result["output"]
        case["reference_valid_output"] = result["valid_output"]
        case["rival_output"] = rival(case["input"])
        case["rival_matches_reference"] = case["rival_output"] == result["output"]
    finding = (all(p["rival_matches_label"] for p in canonical)
               and not cases[0]["self_check"] and cases[0]["actual_reference_output"] == expected
               and not cases[0]["rival_matches_reference"]
               and all(c["reference_valid_output"] and not c["self_check"] and c["rival_matches_reference"] for c in cases[1:])
               and file_sha(source) == source_hash)
    review_index = source.parent / "evidence/review_index.json"
    report = {"schema": "exact-frame-shortcut-audit-v1", "task_id": TASK,
              "status": "reproduced_current_source_support_gap" if finding else "expectation_failed",
              "generator_sha256": source_hash, "probe_sha256": file_sha(Path(__file__)),
              "canonical_pairs_sha256": sha(pairs), "canonical_fit": canonical,
              "review_index_sha256": file_sha(review_index),
              "prior_finding": "Independently confirms the unresolved >=8-cell/non-solid shortcut retained in review-5b3c0730e794b9be:v0001; fresh equal-perimeter nonrectangular closed-loop witness and fresh direct production samples.",
              "cases": cases, "actual_apply_receipt": {k: v for k, v in applied.items() if k != "results"},
              "limits": "Four canonical labels, six direct generate() draws and one handmade mixed witness. No full battery or training experiment. Finite measured agreement is not universal proof. No wrong generated Racket output was observed; finding is missing contrast support."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "canonical_pairs": len(pairs),
                      "production_inputs": len(cases)-1, "source_sha256": source_hash,
                      "executed_rule_hash": applied["executed_rule_hash"], "report": str(args.out)}))
    return 0 if finding else 1


if __name__ == "__main__":
    raise SystemExit(main())
