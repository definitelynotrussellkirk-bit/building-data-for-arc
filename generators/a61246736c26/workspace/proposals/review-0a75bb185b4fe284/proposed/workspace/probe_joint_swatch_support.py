"""Finite task-local support census and retained Racket-witness assessment.

Run through WORK/run_with_racket.py, with payload paths relative to WORK/repo:
  python generators/a61246736c26/workspace/probe_joint_swatch_support.py census \
      --seeds 12 --out ../checks/regression/after/support.json
  python generators/a61246736c26/workspace/probe_joint_swatch_support.py assess \
      --witnesses ../checks/regression/before/witnesses.json \
      --racket ../checks/regression/before/racket.json \
      --malformed-racket ../checks/regression/before/malformed-racket.json \
      --out ../checks/regression/after/witness-assessment.json

The census executes no Racket. It compares generated cases against an independent
Python recolorer of the documented valid lattice and discovers all current rival
dictionaries dynamically. Canonical rival checks use retained labeled canonical
pairs. `assess` consumes separate public `arcpuzzles apply` receipts, verifies their
actual inputs and rule identity, and labels their generator source separately
from the currently selected generator. This is finite evidence, not a proof of
lesson identifiability. Inputs deliberately mutated for diagnostics are never
reported as natural solve failures. New output files are required.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid

TASK_ID = "a61246736c26"
BANDS = ("easy", "medium", "hard")
RIVAL_NAMESPACES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def scene(grid):
    """Parse only the documented valid equal lattice, independent of generator helpers."""
    if not grid or not grid[0] or len({len(r) for r in grid}) != 1:
        raise ValueError("nonempty rectangular grid required")
    height, width = len(grid), len(grid[0])
    if (height - 4) % 3:
        raise ValueError("height does not fit three equal bands")
    size = (height - 4) // 3
    if not 4 <= size <= 8 or (width - 1) % (size + 1):
        raise ValueError("tile dimensions outside the documented lattice")
    columns = (width - 1) // (size + 1)
    if columns not in (3, 4):
        raise ValueError("expected three or four tile columns")
    separator_rows = [i * (size + 1) for i in range(4)]
    separator_cols = [(i + 1) * (size + 1) for i in range(columns)]
    if any(grid[r][c] != 8 for r in range(height) for c in range(width)
           if r in separator_rows or c in separator_cols):
        raise ValueError("separator lattice is incomplete")
    row_colors = [grid[1 + r * (size + 1)][0] for r in range(3)]
    if set(row_colors) != {0, 5, 9}:
        raise ValueError("row palette must be a permutation of 0,5,9")
    solids, fills, patterns = [], [], []
    for column in range(columns):
        column_solids, column_patterns = [], []
        for band in range(3):
            start_row, start_col = 1 + band * (size + 1), 1 + column * (size + 1)
            tile = [row[start_col:start_col + size] for row in grid[start_row:start_row + size]]
            if any(tile[r][c] != 1 for r in range(size) for c in range(size)
                   if r in (0, size - 1) or c in (0, size - 1)):
                raise ValueError("tile border must be color1")
            interior = {tile[r][c] for r in range(1, size - 1) for c in range(1, size - 1)}
            if len(interior) == 1 and interior <= {3, 4, 6, 7}:
                column_solids.append((band, next(iter(interior))))
            elif interior == {2, 8}:
                column_patterns.append(tile)
            else:
                raise ValueError("tile is neither a supported solid nor a pattern")
        if len(column_solids) != 1 or len(column_patterns) != 2 or column_patterns[0] != column_patterns[1]:
            raise ValueError("one solid and two identical patterns are required")
        solids.append(column_solids[0][0])
        fills.append(column_solids[0][1])
        patterns.append(column_patterns[0])
    return {"size": size, "solid_rows": solids, "row_colors": row_colors,
            "fill_colors": fills, "patterns": patterns}


def python_label(grid, *, force_same_row_zero=False):
    """Independent Python prediction; this function never invokes Racket."""
    info = scene(grid)
    tiles = []
    force_zero = force_same_row_zero and len(set(info["solid_rows"])) == 1
    for row, fill, pattern in zip(info["solid_rows"], info["fill_colors"], info["patterns"]):
        frame = 0 if force_zero else info["row_colors"][row]
        tiles.append([[frame if v == 1 else fill if v == 2 else v for v in line] for line in pattern])
    output = []
    for r in range(info["size"]):
        row = []
        for col, tile in enumerate(tiles):
            if col:
                row.append(8)
            row.extend(tile[r])
        output.append(row)
    return output


def declarations(mod):
    entries = []
    for namespace in RIVAL_NAMESPACES:
        declared = getattr(mod, namespace, {})
        if not isinstance(declared, dict):
            raise ValueError(f"{namespace} must be a dictionary")
        for name, function in sorted(declared.items()):
            if not isinstance(name, str) or not callable(function):
                raise ValueError(f"invalid {namespace} declaration: {name!r}")
            try:
                function_sha256 = hashlib.sha256(inspect.getsource(function).encode()).hexdigest()
            except (OSError, TypeError):
                function_sha256 = None
            entries.append((f"{namespace}:{name}", function,
                            {"namespace": namespace, "name": name,
                             "callable_name": getattr(function, "__qualname__", None),
                             "callable_source_sha256": function_sha256}))
    return entries


def rival_prediction(function, grid):
    candidate = copy.deepcopy(grid)
    before = digest(candidate)
    first = normalize_grid(function(candidate))
    if digest(candidate) != before:
        raise ValueError("rival mutated its input")
    second = normalize_grid(function(copy.deepcopy(grid)))
    if first != second:
        raise ValueError("rival prediction is nondeterministic")
    return first


def validation(mod, grid):
    try:
        errors = mod.self_check(copy.deepcopy(grid))
        return {"status": "valid" if errors == [] else "rejected", "errors": errors}
    except Exception as exc:
        return {"status": "exception", "type": type(exc).__name__, "error": str(exc)}


def census(mod, root, seeds):
    inventory = declarations(mod)
    report = {"reference_kind": "independent_python_recolorer", "racket_executions": 0,
              "settings": {"bands": list(BANDS), "seeds": list(range(seeds)),
                           "sample_index": "seed * 29", "scene_profiles": list(mod.SCENE_PROFILES)},
              "declared_rivals": [item[2] for item in inventory],
              "canonical": {"reference_kind": "retained_labeled_canonical_pairs", "checked": 0,
                            "python_mismatches": [], "rivals": {}},
              "bands": {}, "first_same_row_witnesses": {}, "failures": []}
    for key, _function, _meta in inventory:
        report["canonical"]["rivals"][key] = {"agrees": 0, "disagrees": 0, "errors": []}
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        report["canonical"]["checked"] += 1
        identity = {k: pair[k] for k in ("variant", "split", "pair_index")}
        if python_label(pair["input"]) != pair["output"]:
            report["canonical"]["python_mismatches"].append(identity)
        for key, function, _meta in inventory:
            stats = report["canonical"]["rivals"][key]
            try:
                prediction = rival_prediction(function, pair["input"])
                stats["agrees" if prediction == pair["output"] else "disagrees"] += 1
            except Exception as exc:
                stats["errors"].append({"pair": identity, "error": f"{type(exc).__name__}: {exc}"})
    for band in BANDS:
        stats = {"generated": 0, "valid": 0, "distinct_input_count": 0,
                 "same_row_cases": 0, "same_row_frames": {},
                 "force_same_row_zero_agrees": 0, "force_same_row_zero_disagrees": 0,
                 "python_selected_mirror_agrees": 0, "profiles": {},
                 "declared_rivals": {key: {"agrees": 0, "disagrees": 0, "errors": 0}
                                     for key, _f, _m in inventory}}
        hashes = set()
        report["bands"][band] = stats
        report["first_same_row_witnesses"][band] = {}
        for profile in mod.SCENE_PROFILES:
            stats["profiles"][profile] = {"generated": 0, "same_row": 0, "frames": {}}
            for seed in range(seeds):
                identity = {"band": band, "seed": seed, "sample_index": seed * 29,
                            "requested_scene_profile": profile}
                stats["generated"] += 1
                stats["profiles"][profile]["generated"] += 1
                try:
                    grid = mod.generate(seed, seed * 29, difficulty=band, scene_profile=profile)
                    domain = validation(mod, grid)
                    if domain != {"status": "valid", "errors": []}:
                        raise ValueError(f"generated input rejected: {domain}")
                    observed = mod.observe_overrides(grid)
                    if observed != {"scene_profile": profile}:
                        raise ValueError(f"override observation differs: {observed}")
                    info = scene(grid)
                    output = python_label(grid)
                    if mod.rule_mirror(grid) != output:
                        raise ValueError("selected mirror differs from independent Python recolorer")
                    stats["python_selected_mirror_agrees"] += 1
                    stats["valid"] += 1
                    hashes.add(digest(grid))
                    rival = python_label(grid, force_same_row_zero=True)
                    stats["force_same_row_zero_agrees" if rival == output else "force_same_row_zero_disagrees"] += 1
                    if len(set(info["solid_rows"])) == 1:
                        frame = str(info["row_colors"][info["solid_rows"][0]])
                        stats["same_row_cases"] += 1
                        stats["same_row_frames"][frame] = stats["same_row_frames"].get(frame, 0) + 1
                        ps = stats["profiles"][profile]
                        ps["same_row"] += 1
                        ps["frames"][frame] = ps["frames"].get(frame, 0) + 1
                        report["first_same_row_witnesses"][band].setdefault(frame,
                            {**identity, "observed_overrides": observed, "input": grid,
                             "input_sha256": digest(grid), "solid_rows": info["solid_rows"],
                             "row_colors": info["row_colors"], "python_output": output})
                    for key, function, _meta in inventory:
                        rs = stats["declared_rivals"][key]
                        try:
                            prediction = rival_prediction(function, grid)
                            rs["agrees" if prediction == output else "disagrees"] += 1
                        except Exception as exc:
                            rs["errors"] += 1
                            report["failures"].append({**identity, "rival": key,
                                                      "error": f"{type(exc).__name__}: {exc}"})
                except Exception as exc:
                    report["failures"].append({**identity, "error": f"{type(exc).__name__}: {exc}"})
        stats["distinct_input_count"] = len(hashes)
    report["missing_zero_bands"] = [b for b in BANDS if "0" not in report["bands"][b]["same_row_frames"]]
    report["missing_nonzero_bands"] = [b for b in BANDS if not {"5", "9"} & set(report["bands"][b]["same_row_frames"])]
    report["limits"] = "Finite explicit-profile seed census. Generated outputs use an independent Python recolorer, not Racket. Rival agreement here is not lesson identifiability."
    failed = report["failures"] or report["canonical"]["python_mismatches"] or report["missing_zero_bands"] or report["missing_nonzero_bands"]
    return report, int(bool(failed))


def assess(mod, witness_path, racket_path, malformed_racket_path):
    witness = json.loads(witness_path.read_text())
    racket = json.loads(racket_path.read_text())
    grids = [witness["base_input"], witness["same_row_input"]]
    comparisons = []
    for grid, result in zip(grids, racket["results"], strict=True):
        if result["input"] != grid or not result["valid_output"] or result["error"]:
            raise ValueError("Racket receipt does not contain the expected valid input/output")
        independent = python_label(grid)
        comparisons.append({"input_sha256": digest(grid),
                            "racket_input_sha256": result["input_sha256"],
                            "racket_equals_independent_python": result["output"] == independent,
                            "selected_mirror_equals_racket": mod.rule_mirror(grid) == result["output"],
                            "selected_validator": validation(mod, grid)})
    actual = racket["results"][1]["output"]
    rival = python_label(grids[1], force_same_row_zero=True)
    malformed = witness["malformed_input"]
    report = {"reference_kind": "public_arcpuzzles_apply_Racket_receipt",
              "input_origin_source_sha256": witness["source_sha256"],
              "racket_generator_sha256": racket["generator_sha256"],
              "racket_executed_rule_hash": racket["executed_rule_hash"],
              "racket_rule_text_sha256": racket["rule_text_sha256"],
              "rule_identity_matches_selected_declaration": racket["executed_rule_hash"] == mod.RULE_HASH,
              "witnesses_file_sha256": hashlib.sha256(witness_path.read_bytes()).hexdigest(),
              "racket_file_sha256": hashlib.sha256(racket_path.read_bytes()).hexdigest(),
              "comparisons": comparisons, "same_row_racket_output": actual,
              "same_row_force_zero_rival_output": rival,
              "racket_rival_changed_cells": sum(a != b for ar, br in zip(actual, rival, strict=True)
                                                for a, b in zip(ar, br, strict=True)),
              "malformed_selected_validator": validation(mod, malformed)}
    if malformed_racket_path:
        bad = json.loads(malformed_racket_path.read_text())
        if len(bad["results"]) != 1 or bad["results"][0]["input"] != malformed:
            raise ValueError("malformed Racket receipt has a different input")
        report["malformed_racket"] = {k: bad["results"][0].get(k) for k in ("valid_output", "error", "input_sha256")}
        report["malformed_racket_file_sha256"] = hashlib.sha256(malformed_racket_path.read_bytes()).hexdigest()
    report["limits"] = "Racket labels cover these two retained valid inputs only. Malformed Racket failure is expected outside the rule domain; validator must reject with an error list."
    ok = (report["rule_identity_matches_selected_declaration"] and
          all(c["racket_equals_independent_python"] and c["selected_mirror_equals_racket"] and
              c["selected_validator"]["status"] == "valid" for c in comparisons) and
          report["racket_rival_changed_cells"] == 36 and
          report["malformed_selected_validator"]["status"] == "rejected")
    return report, 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Explicit selected library/runtime; default is this probe's own tree")
    sub = parser.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("census")
    c.add_argument("--seeds", type=int, default=12)
    c.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("assess")
    a.add_argument("--witnesses", type=Path, required=True)
    a.add_argument("--racket", type=Path, required=True)
    a.add_argument("--malformed-racket", type=Path)
    a.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    root = args.root.resolve() if args.root else find_root(__file__)
    mod, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if args.mode == "census":
        if not 1 <= args.seeds <= 10000:
            parser.error("--seeds must be between1 and10000")
        report, code = census(mod, root, args.seeds)
    else:
        report, code = assess(mod, args.witnesses, args.racket, args.malformed_racket)
    report.update(schema="a61246736c26-joint-swatch-probe-v1", mode=args.mode,
                  task_id=TASK_ID, selected_generator_sha256=source_sha256,
                  selected_generator_source=str(source), selected_generator_version=mod.VERSION,
                  selected_rule_hash=mod.RULE_HASH, source_root=str(root), command=sys.argv,
                  probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    report["selected_source_changed_during_run"] = hashlib.sha256(source.read_bytes()).hexdigest() != source_sha256
    if report["selected_source_changed_during_run"]:
        code = 2
    report["exit_code"] = code
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {"out": str(args.out), "mode": args.mode, "exit_code": code,
               "source_sha256": source_sha256, "racket_executions": report.get("racket_executions", "consumed saved receipts")}
    if args.mode == "census":
        summary["bands"] = {b: {k: report["bands"][b][k] for k in
                              ("generated", "valid", "same_row_cases", "same_row_frames", "force_same_row_zero_disagrees")}
                            for b in BANDS}
    else:
        summary["racket_rival_changed_cells"] = report["racket_rival_changed_cells"]
        summary["malformed_selected_validator"] = report["malformed_selected_validator"]
    print(json.dumps(summary, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
