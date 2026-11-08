"""Source-bound authoring audit; reference execution uses the public apply CLI.

Run via review.py run so reviewer_support resolves the selected local source.
This file does not import a private generator alias or reference runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "1620d15035b5"
HERE = Path(__file__).resolve().parent
BANDS = ("easy", "medium", "hard")
REFERENCE_INDICES = (0, 15, 31)


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def objects(grid):
    seen = set()
    found = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 1, 3) or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = rr + dr, cc + dc
                    if (0 <= p[0] < h and 0 <= p[1] < w and p not in seen
                            and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        pending.append(p)
            found.append({"color": color, "cells": sorted(cells), "area": len(cells),
                          "width": max(p[1] for p in cells) - min(p[1] for p in cells) + 1})
    return found


def select(grid, area, width):
    out = [[0] * len(grid[0]) for _ in grid]
    matches = [obj for obj in objects(grid)
               if obj["area"] == area and obj["width"] == width
               and all(r > 0 and c > 0 for r, c in obj["cells"])]
    if matches:
        for r, c in matches[0]["cells"]:
            out[r][c] = 8
    return out


def measures(grid):
    top = [c for c, v in enumerate(grid[0]) if v == 1]
    left = [r for r, row in enumerate(grid) if row[0] == 3]
    return {"area_legend_columns": top, "width_legend_rows": left,
            "count_area": len(top), "count_width": len(left),
            "endpoint_area": max(top, default=0), "endpoint_width": max(left, default=0)}


def count_rule(grid):
    m = measures(grid)
    return select(grid, m["count_area"], m["count_width"])


def endpoint_rival(grid):
    m = measures(grid)
    return select(grid, m["endpoint_area"], m["endpoint_width"])


def documented_domain(grid):
    m = measures(grid)
    obs = objects(grid)
    matches = [o for o in obs if (o["area"], o["width"]) == (m["count_area"], m["count_width"])]
    checks = {
        "dimensions_at_most_30": len(grid) <= 30 and len(grid[0]) <= 30,
        "legal_colors": all(type(v) is int and 0 <= v <= 9 for row in grid for v in row),
        "area_legend_range": 1 <= m["count_area"] <= 8,
        "width_legend_range": 1 <= m["count_width"] <= 5,
        "two_to_four_candidate_objects": 2 <= len(obs) <= 4,
        "candidates_in_interior": all(r > 0 and c > 0 for o in obs for r, c in o["cells"]),
        "exactly_one_joint_match": len(matches) == 1,
        "all_color_1_in_top_row": all(r == 0 for r, row in enumerate(grid) for v in row if v == 1),
        "all_color_3_in_left_column": all(c == 0 for row in grid for c, v in enumerate(row) if v == 3),
    }
    return {"passes": all(checks.values()), "checks": checks, "objects": obs, **m}


def authored_witness():
    grid = [[0] * 12 for _ in range(10)]
    for c in (1, 2, 3, 5):
        grid[0][c] = 1
    for r in (1, 3):
        grid[r][0] = 3
    for r, c in ((4, 3), (4, 4), (5, 3), (5, 4)):
        grid[r][c] = 4
    for r, c in ((6, 7), (6, 8), (6, 9), (7, 8), (8, 8)):
        grid[r][c] = 6
    return grid


def prepare():
    root = find_root(__file__)
    gen, path, digest = load_selected_generator(TASK, root=root)
    witness = authored_witness()
    inputs = [witness]
    cases = [{"case_id": "authored_sparse_legends", "provenance": "authored", "generated": False,
              "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
              "self_check": gen.self_check(witness), "domain": documented_domain(witness),
              "ordinary_generation_support": False,
              "support_reason": "Ordinary generation fixes legend marks to indices 1..K and 1..W."}]
    observations = []
    for band in BANDS:
        for index in range(32):
            grid = gen.generate(0, index, difficulty=band)
            m = measures(grid)
            row = {"seed": 0, "sample_index": index, "difficulty": band, "overrides": {},
                   "input_sha256": grid_hash(grid), "shape": [len(grid), len(grid[0])],
                   "self_check": gen.self_check(grid, difficulty=band),
                   "legend_endpoints_equal_counts": (m["count_area"], m["count_width"]) ==
                                                    (m["endpoint_area"], m["endpoint_width"]),
                   "rival_matches_python_count_rule": endpoint_rival(grid) == count_rule(grid),
                   "documented_domain_passes": documented_domain(grid)["passes"], **m}
            observations.append(row)
            if index in REFERENCE_INDICES:
                inputs.append(grid)
                cases.append({"case_id": f"generated_{band}_s0_i{index}", "provenance": "generated",
                              "generated": True, **row})
    canon = []
    for pair in canonical_pairs(TASK, root=root, labeled_only=True):
        grid = pair["input"]
        canon.append({k: pair[k] for k in ("variant", "split", "pair_index")} |
                     {"input_sha256": grid_hash(grid), "measures": measures(grid),
                      "endpoint_rival_matches_canonical_output": endpoint_rival(grid) == pair["output"],
                      "python_count_rule_matches_canonical_output": count_rule(grid) == pair["output"]})
    result = {"task_id": TASK, "generator_version": gen.VERSION, "generator_sha256": digest,
              "generator_path": str(path.relative_to(root)),
              "sample_scope": {"seed": 0, "sample_indices": [0, 31], "difficulties": BANDS,
                               "overrides": {}, "unique_inputs": len({x["input_sha256"] for x in observations}),
                               "count": len(observations), "reference_indices_per_band": REFERENCE_INDICES},
              "observations": observations, "public_apply_cases": cases,
              "canonical_pairs": canon,
              "declared_canonical_shortcuts": repr(getattr(gen, "CANONICAL_SHORTCUTS", None)),
              "declared_lesson_competitors": repr(getattr(gen, "LESSON_COMPETITORS", None)),
              "tests_directory_present": (root / "generators" / TASK / "tests").exists(),
              "review_index_present": (root / "generators" / TASK / "evidence/review_index.json").exists()}
    write("probe.json", result)
    write("input.json", inputs)
    write("rival_outputs.json", [endpoint_rival(g) for g in inputs])
    assert not cases[0]["self_check"] and cases[0]["domain"]["passes"]
    assert count_rule(witness) != endpoint_rival(witness)
    print(json.dumps({"generator_sha256": digest, "draws": len(observations),
                      "unique_inputs": result["sample_scope"]["unique_inputs"],
                      "self_check_passes": sum(not x["self_check"] for x in observations),
                      "endpoint_count_equivalence": sum(x["legend_endpoints_equal_counts"] for x in observations),
                      "documented_domain_passes": sum(x["documented_domain_passes"] for x in observations),
                      "apply_inputs": len(inputs), "canonical": canon}, indent=2))


def finalize():
    probe = json.loads((HERE / "probe.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    rival = json.loads((HERE / "rival_outputs.json").read_text())
    assert probe["generator_sha256"] == racket["generator_sha256"]
    comparisons = []
    for case, row, predicted in zip(probe["public_apply_cases"], racket["results"], rival, strict=True):
        comparisons.append({"case_id": case["case_id"], "reference_error": row["error"],
                            "rival_matches_racket": predicted == row["output"],
                            "python_count_rule_matches_racket": count_rule(row["input"]) == row["output"],
                            "racket_generator_domain": row.get("generator_domain")})
    result = {"finding_id": "A1620-1", "task_id": TASK,
              "classification": "reproduced distribution shortcut with authored in-domain counterexample",
              "generator_sha256": racket["generator_sha256"],
              "executed_rule_hash": racket["executed_rule_hash"],
              "rule_text_sha256": racket["rule_text_sha256"],
              "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
              "counterexample_provenance": probe["public_apply_cases"][0],
              "input": racket["results"][0]["input"],
              "actual_racket_output": racket["results"][0]["output"],
              "rival_output": rival[0],
              "rival_description": "Read area as the greatest column index marked 1 in row 0 and width as the greatest row index marked 3 in column 0; select the first candidate matching those two numbers; emit zeros if none.",
              "reference_command": {"cwd": "packet_root", "effective_cwd": "repo", "argv": [
                  "WORK/.venv/bin/python", "review.py", "run", "../.venv/bin/python", "-m", "arcpuzzles",
                  "apply", TASK, "--input", "../checks/audit/1620d15035b5/input.json", "--out",
                  "../checks/audit/1620d15035b5/racket.json", "--check-generator-domain"], "exit_code": 0},
              "comparisons": comparisons}
    write("counterexample.json", result)
    assert all(x["reference_error"] is None for x in comparisons)
    assert all(x["python_count_rule_matches_racket"] for x in comparisons)
    assert not comparisons[0]["rival_matches_racket"]
    assert all(x["rival_matches_racket"] for x in comparisons[1:])
    print(json.dumps({"task_id": TASK, "generator_sha256": racket["generator_sha256"],
                      "executed_rule_hash": racket["executed_rule_hash"],
                      "rule_text_sha256": racket["rule_text_sha256"],
                      "reference_cases": len(comparisons), "comparisons": comparisons}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "finalize"))
    args = parser.parse_args()
    {"prepare": prepare, "finalize": finalize}[args.mode]()
