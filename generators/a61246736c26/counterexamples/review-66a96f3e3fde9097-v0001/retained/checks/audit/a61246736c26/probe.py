"""Focused, findings-only probes. Run through review.py; no private rule runner."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

TASK = "a61246736c26"
HERE = Path(__file__).resolve().parent
WORK = next(p for p in HERE.parents if (p / "repo" / "generators" / TASK).is_dir())
ROOT = WORK / "repo"
SOURCE = ROOT / "generators" / TASK / "generator.py"


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def module():
    sys.path.insert(0, str(ROOT / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def identity():
    canonical = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    row = next(json.loads(s) for s in canonical.read_text().splitlines()
               if json.loads(s).get("task_id") == TASK)
    program = row["program_solution"]
    return {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "rule_raw_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "source_path": "WORK/repo/generators/a61246736c26/generator.py",
        "rule_path": "WORK/repo/shared/data/canonical/puzzles.jsonl",
    }


def scene(grid):
    """Independent structural read for well-formed generated lattices."""
    n = (len(grid) - 4) // 3
    cols = [c for c in range(len(grid[0])) if all(row[c] == 8 for row in grid)]
    starts = [1] + [c + 1 for c in cols[:-1]]
    row_starts = [1 + r * (n + 1) for r in range(3)]
    tiles = [[
        [row[c:c+n] for row in grid[r:r+n]]
        for c in starts
    ] for r in row_starts]
    solid_rows, fills, patterns = [], [], []
    for c in range(len(starts)):
        candidates = []
        pattern = None
        for r in range(3):
            tile = tiles[r][c]
            interior = {tile[y][x] for y in range(1, n-1) for x in range(1, n-1)}
            if len(interior) == 1 and interior <= {3, 4, 6, 7}:
                candidates.append((r, next(iter(interior))))
            if interior == {2, 8} and pattern is None:
                pattern = tile
        assert len(candidates) == 1 and pattern is not None
        r, fill = candidates[0]
        solid_rows.append(r)
        fills.append(fill)
        patterns.append(pattern)
    return {
        "tile_size": n,
        "column_count": len(starts),
        "row_colors": [grid[r][0] for r in row_starts],
        "solid_rows": solid_rows,
        "fills": fills,
        "patterns": patterns,
        "tiles": tiles,
        "row_starts": row_starts,
        "col_starts": starts,
    }


def recolor(grid, *, shortcut=False):
    info = scene(grid)
    same_row = len(set(info["solid_rows"])) == 1
    tiles = []
    for c, pattern in enumerate(info["patterns"]):
        frame = 0 if shortcut and same_row else info["row_colors"][info["solid_rows"][c]]
        fill = info["fills"][c]
        tiles.append([[frame if x == 1 else fill if x == 2 else x for x in row] for row in pattern])
    output = []
    for r in range(info["tile_size"]):
        row = []
        for c, tile in enumerate(tiles):
            if c:
                row.append(8)
            row.extend(tile[r])
        output.append(row)
    return output


def all_top(grid):
    result = copy.deepcopy(grid)
    info = scene(grid)
    n = info["tile_size"]
    for c, solid_row in enumerate(info["solid_rows"]):
        if solid_row == 0:
            continue
        for dest, src in ((0, solid_row), (solid_row, 0)):
            y, x = info["row_starts"][dest], info["col_starts"][c]
            tile = info["tiles"][src][c]
            for r in range(n):
                result[y+r][x:x+n] = tile[r][:]
    return result


def validation(mod, grid):
    try:
        errors = mod.self_check(grid)
        return {"accepted": errors == [], "errors": errors}
    except Exception as exc:
        return {"accepted": False, "exception_type": type(exc).__name__, "exception": str(exc)}


def prepare():
    mod = module()
    pin = identity()
    assert pin["generator_sha256"] == "33e5c3a10739251440d40b658e523234ff2ef3fe823b9fbe76f74a1717a41767"
    assert pin["rule_hash"] == "08238424436c"
    cases = []
    for i, profile in enumerate(mod.SCENE_PROFILES):
        difficulty = ("easy", "medium", "hard")[i % 3]
        seed, index = i, i * 17
        grid = mod.generate(seed, index, difficulty=difficulty, scene_profile=profile)
        cases.append({
            "name": "generated_" + profile,
            "seed": seed,
            "sample_index": index,
            "difficulty": difficulty,
            "overrides": {"scene_profile": profile},
            "generated_without_mutation": True,
            "input": grid,
            "validator": validation(mod, grid),
            "rival_output": recolor(grid, shortcut=True),
            "independent_output": recolor(grid),
        })
    base = mod.generate(3, 0, difficulty="easy", scene_profile="permuted_frames")
    assert scene(base)["tile_size"] == 4 and scene(base)["row_colors"] == [9, 0, 5]
    accepted = all_top(base)
    assert validation(mod, accepted) == {"accepted": True, "errors": []}
    cases.append({
        "name": "accepted_all_top_frame_9",
        "seed": 3,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"scene_profile": "permuted_frames"},
        "generated_without_mutation": False,
        "mutation": "In columns 1 and 2, swap the solid tile with the top pattern copy; zero-based indices.",
        "input": accepted,
        "validator": validation(mod, accepted),
        "observed_overrides": mod.observe_overrides(accepted),
        "rival_output": recolor(accepted, shortcut=True),
        "independent_output": recolor(accepted),
    })
    standard = copy.deepcopy(accepted)
    for r, color in zip(scene(standard)["row_starts"], (5, 9, 0)):
        for y in range(r, r + 4):
            standard[y][0] = color
    cases.append({
        "name": "rejected_all_top_standard_frames",
        "seed": 3,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"scene_profile": "permuted_frames"},
        "generated_without_mutation": False,
        "mutation": "From accepted_all_top_frame_9, change only row-swatch strips from [9,0,5] to [5,9,0].",
        "input": standard,
        "validator": validation(mod, standard),
        "rival_output": recolor(standard, shortcut=True),
        "independent_output": recolor(standard),
    })
    malformed = copy.deepcopy(base)
    malformed[5][0] = 9
    write("malformed.json", {"input": malformed})
    write("input.json", {"inputs": [c["input"] for c in cases]})
    counts, same_rows, accepted_count = Counter(), Counter(), 0
    for seed in range(1024):
        difficulty = ("easy", "medium", "hard")[seed % 3]
        grid = mod.generate(seed, seed * 29, difficulty=difficulty)
        assert mod.self_check(grid) == []
        accepted_count += 1
        counts[mod.observe_overrides(grid)["scene_profile"]] += 1
        info = scene(grid)
        if len(set(info["solid_rows"])) == 1:
            same_rows[str(info["row_colors"][info["solid_rows"][0]])] += 1
        assert recolor(grid) == recolor(grid, shortcut=True)
    write("prepared.json", {
        **pin,
        "cases": cases,
        "census": {
            "kind": "Python-only generation, validation and independently implemented rival comparison; not Racket labels",
            "seed_range_inclusive": [0, 1023],
            "sample_index": "seed * 29",
            "difficulty": "('easy', 'medium', 'hard')[seed % 3]",
            "overrides": {},
            "count": 1024,
            "validator_accepted": accepted_count,
            "profile_counts": dict(counts),
            "same_row_output_frame_counts": dict(same_rows),
            "rival_agreement_count": 1024,
        },
        "malformed": {
            "seed": 3,
            "sample_index": 0,
            "difficulty": "easy",
            "overrides": {"scene_profile": "permuted_frames"},
            "mutation": {"row": 5, "column": 0, "from": 8, "to": 9},
            "base_input": base,
            "input": malformed,
            "base_validator": validation(mod, base),
            "mutated_validator": validation(mod, malformed),
            "documented_domain": False,
        },
    })
    print(json.dumps({"cases": len(cases), "identity": pin, "profile_counts": dict(counts),
                      "same_row_frame_counts": dict(same_rows), "malformed_validator": validation(mod, malformed)}))


def assess():
    prepared = json.loads((HERE / "prepared.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    malformed = json.loads((HERE / "malformed-racket.json").read_text())
    assert identity()["generator_sha256"] == prepared["generator_sha256"] == actual["generator_sha256"]
    assert actual["executed_rule_hash"] == prepared["rule_hash"]
    assert len(prepared["cases"]) == len(actual["results"]) == 16
    comparisons = []
    for case, result in zip(prepared["cases"], actual["results"]):
        assert result["valid_output"] and result["error"] is None
        assert result["input"] == case["input"]
        assert result["output"] == case["independent_output"]
        differences = [
            [r, c] for r, row in enumerate(result["output"])
            for c, color in enumerate(row) if color != case["rival_output"][r][c]
        ]
        if case["generated_without_mutation"]:
            assert not differences
        else:
            assert len(differences) == 36
        comparisons.append({
            "name": case["name"],
            "racket_result_index": result["index"],
            "generated_without_mutation": case["generated_without_mutation"],
            "validator": case["validator"],
            "racket_valid_output": result["valid_output"],
            "independent_recolor_matches_racket": True,
            "shortcut_matches_racket": not differences,
            "shortcut_difference_cells": len(differences),
        })
    witness = prepared["cases"][14]
    output = actual["results"][14]
    assert not malformed["results"][0]["valid_output"]
    assert malformed["results"][0]["output"] is None
    assert prepared["malformed"]["mutated_validator"]["exception_type"] == "IndexError"
    evidence = {
        **identity(),
        "phase": "unchanged selected audit source",
        "racket_rule_text_sha256": actual["rule_text_sha256"],
        "selected_source_modified": False,
        "reference_modified": False,
        "rival": "Apply the canonical recoloring, except force every output tile frame to 0 when all solid tiles occupy one row.",
        "rival_status": "intentional teaching negative; not a model solve",
        "comparisons": comparisons,
        "counts": {
            "generated_profile_examples_racket_labeled": 14,
            "generated_profile_examples_rival_matches_racket": 14,
            "generated_profile_examples_validator_accepted": 14,
            "counterfactuals_racket_labeled": 2,
            "counterfactuals_refuting_rival": 2,
            "counterfactuals_validator_accepted": 1,
            "malformed_reference_failures": 1,
        },
        "accepted_counterexample": {
            **{k:v for k,v in witness.items() if k != "independent_output"},
            "input_shape": [len(witness["input"]), len(witness["input"][0])],
            "racket_output": output["output"],
            "output_shape": [len(output["output"]), len(output["output"][0])],
            "input_sha256": output["input_sha256"],
            "output_sha256": output["output_sha256"],
            "rival_differs_in_cells": 36,
            "solid_rows": [0, 0, 0],
            "row_colors": [9, 0, 5],
            "documented_structural_invariants_satisfied": True,
            "emittable_by_current_generator": False,
        },
        "census": prepared["census"],
        "validator_crash": {
            **prepared["malformed"],
            "racket_error": malformed["results"][0]["error"],
            "racket_output": None,
            "racket_receipt": "WORK/checks/audit/a61246736c26/malformed-racket.json",
        },
        "limitations": [
            "No full battery or task-test suite was run for this audit target.",
            "The 1,024-draw census uses an independent Python recolorer, not 1,024 Racket labels.",
            "The accepted counterexample is a controlled mutation; it is not an observed incorrect generated label.",
            "The broken-separator input is outside the documented lattice domain; its defect is an unhandled validator exception.",
        ],
    }
    write("evidence.json", evidence)
    print(json.dumps({"counts": evidence["counts"], "census": evidence["census"],
                      "witness_first_output_row": output["output"][0],
                      "witness_first_rival_row": witness["rival_output"][0]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "assess"))
    args = parser.parse_args()
    {"prepare": prepare, "assess": assess}[args.action]()
