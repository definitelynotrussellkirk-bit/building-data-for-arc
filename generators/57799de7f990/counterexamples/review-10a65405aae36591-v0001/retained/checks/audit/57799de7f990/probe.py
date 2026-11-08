"""Focused audit: axis-local marker recognition and advertised degenerates.

No private reference execution helpers are imported. Labels come from CLI apply.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, find_root

TASK = "57799de7f990"
SOURCE = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def axis_local(grid, require_third_arm=False):
    """Intentional rival: recognize horizontal and vertical arms independently."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        candidates = [c for c in range(1, w - 1)
                      if grid[r][c - 1] == grid[r][c + 1] == 2
                      and (not require_third_arm or grid[r - 1][c] == 2 or grid[r + 1][c] == 2)]
        for a, b in zip(candidates, candidates[1:]):
            for c in range(a + 1, b):
                if out[r][c] == 0:
                    out[r][c] = 1
    for c in range(1, w - 1):
        candidates = [r for r in range(1, h - 1)
                      if grid[r - 1][c] == grid[r + 1][c] == 2
                      and (not require_third_arm or grid[r][c - 1] == 2 or grid[r][c + 1] == 2)]
        for a, b in zip(candidates, candidates[1:]):
            for r in range(a + 1, b):
                if out[r][c] == 0:
                    out[r][c] = 1
    return out

if len(sys.argv) == 1 or sys.argv[1] == "prepare":
    cases = []
    for seed in range(4):
        for difficulty in ("easy", "medium", "hard"):
            grid = mod.generate(seed, 0, difficulty=difficulty)
            cases.append({"kind": "generated", "seed": seed, "sample_index": 0,
                          "difficulty": difficulty, "overrides": {}, "input": grid})
    for texture in mod.DEGENERATE_TEXTURES:
        grid = mod.generate(0, 0, texture=texture)
        cases.append({"kind": "generated_degenerate", "seed": 0, "sample_index": 0,
                      "difficulty": None, "overrides": {"texture": texture}, "input": grid})
    grid = [[0] * 17 for _ in range(13)]
    for r, c in ((3, 3), (4, 6), (3, 11)):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            grid[r + dr][c + dc] = 2
    cases.append({"kind": "handmade_domain_probe", "seed": None, "sample_index": None,
                  "overrides": None, "centers": [[3, 3], [4, 6], [3, 11]], "input": grid,
                  "documented_generator_domain": False,
                  "reason": "Three intact disjoint diamonds, irregular nonlattice placement."})
    for pair in canonical_pairs(TASK, root=find_root(SOURCE)):
        cases.append({"kind": "canonical", "variant": pair["variant"],
                      "split": pair["split"], "pair_index": pair["pair_index"],
                      "input": pair["input"]})
    for index, case in enumerate(cases):
        case["index"] = index
        case["validator_errors"] = mod.self_check(case["input"])
        case["rival_output"] = axis_local(case["input"])
    record = {"task_id": TASK,
              "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "declarations": {"CANONICAL_SHORTCUTS": getattr(mod, "CANONICAL_SHORTCUTS", None),
                               "LESSON_COMPETITORS": getattr(mod, "LESSON_COMPETITORS", None)},
              "rival": "axis_local", "cases": cases}
    (HERE / "input.json").write_text(json.dumps([c["input"] for c in cases]) + "\n")
    (HERE / "probe.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"cases": len(cases), "generator_sha256": record["generator_sha256"],
                      "validator_failures": [c["index"] for c in cases if c["validator_errors"]]}))
else:
    record = json.loads((HERE / "probe.json").read_text())
    authority = json.loads((HERE / "racket.json").read_text())
    canonical_labels = {(p["variant"], p["split"], p["pair_index"]): p["output"]
                        for p in canonical_pairs(TASK, root=find_root(SOURCE))}
    for case, result in zip(record["cases"], authority["results"], strict=True):
        case["racket_output"] = result["output"]
        case["racket_error"] = result["error"]
        case["rival_matches"] = case["rival_output"] == result["output"]
        case["different_cells"] = [[r, c] for r, row in enumerate(case["input"])
                                   for c in range(len(row))
                                   if case["rival_output"][r][c] != result["output"][r][c]]
        case["three_arm_rival_output"] = axis_local(case["input"], require_third_arm=True)
        case["three_arm_rival_matches"] = case["three_arm_rival_output"] == result["output"]
        case["three_arm_different_cells"] = [[r, c] for r, row in enumerate(case["input"])
                                             for c in range(len(row))
                                             if case["three_arm_rival_output"][r][c] != result["output"][r][c]]
        if case["kind"] == "canonical":
            case["racket_matches_canonical_label"] = result["output"] == canonical_labels[(
                case["variant"], case["split"], case["pair_index"])]
    record["rule_hash"] = authority["executed_rule_hash"]
    record["rule_text_sha256"] = authority["rule_text_sha256"]
    record["authority_generator_sha256"] = authority["generator_sha256"]
    record["summary"] = {"cases": len(record["cases"]),
                         "racket_errors": sum(c["racket_error"] is not None for c in record["cases"]),
                         "rival_matches": sum(c["rival_matches"] for c in record["cases"]),
                         "mismatch_indices": [c["index"] for c in record["cases"] if not c["rival_matches"]],
                         "three_arm_rival_matches": sum(c["three_arm_rival_matches"] for c in record["cases"]),
                         "three_arm_mismatch_indices": [c["index"] for c in record["cases"] if not c["three_arm_rival_matches"]],
                         "canonical_label_matches": sum(c.get("racket_matches_canonical_label", False) for c in record["cases"])}
    (HERE / "probe.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps(record["summary"]))
