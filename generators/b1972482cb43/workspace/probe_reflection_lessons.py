#!/usr/bin/env python3
"""Task-specific reflection witness and single-holdout schedule probe.

This complements the public lesson census. It checks a stronger sufficient
condition: every current declared rival has two refuting, distinct inputs in
each five-pair window, including the smallest dimension and palette overrides.
All five inputs must be distinct, so public duplicate rejection cannot skip a
scheduled witness. The default nine draws cover all five starting residues.
Generated comparisons use an independent point-reflection model, calibrated
against every labeled canonical pair and three exact Racket apply fixtures.
They are diagnostic comparisons, not newly authoritative training labels.

Run from the packet root (payload paths are relative to WORK/repo):
  python3 review.py run python3 generators/b1972482cb43/workspace/probe_reflection_lessons.py --write-oracle-inputs ../checks/lesson-design/oracle-inputs.json
  python3 review.py run python3 -m arcpuzzles apply b1972482cb43 --input ../checks/lesson-design/oracle-inputs.json --check-generator-domain --out ../checks/lesson-design/oracle-labels.json
  python3 review.py run python3 generators/b1972482cb43/workspace/probe_reflection_lessons.py --oracle-labels ../checks/lesson-design/oracle-labels.json --out ../checks/lesson-design/probe.json

Use new output paths after source edits. No generator or declaration is edited.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys


TASK = "b1972482cb43"


def _load_helpers():
    for ancestor in Path(__file__).resolve().parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            helper = ancestor / relative
            if helper.is_file():
                sys.path.insert(0, str(helper.parent))
                from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid
                return helper, canonical_pairs, find_root, load_selected_generator, normalize_grid
    raise FileNotFoundError("No local reviewer_support.py above this probe")


HELPER, canonical_pairs, find_root, load_selected_generator, normalize_grid = _load_helpers()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def point_model(grid):
    """Independent diagnostic model; Racket remains the labeling authority."""
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 1:
        raise ValueError("Model needs exactly one anchor")
    ar, ac = anchors[0]
    out = [[0] * w for _ in range(h)]
    out[ar][ac] = 9
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value not in (0, 9):
                out[r][c] = value
                rr, cc = 2 * ar - r, 2 * ac - c
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = value
    return out


def geometry(grid):
    """Check the old connected monochrome 2..5-cell domain independently."""
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    if not 4 <= h <= 12 or not 5 <= w <= 14:
        raise ValueError("Grid dimensions are outside the declared 4..12 by 5..14 domain")
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)}
    if len(anchors) != 1 or not 2 <= len(cells) <= 5:
        raise ValueError("Expected one 9-anchor and a 2..5-cell source")
    if len({grid[r][c] for r, c in cells}) != 1:
        raise ValueError("Source is not monochrome")
    reached, pending = set(), [next(iter(cells))]
    while pending:
        r, c = pending.pop()
        if (r, c) in reached:
            continue
        reached.add((r, c))
        pending.extend(p for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                       if p in cells and p not in reached)
    if reached != cells:
        raise ValueError("Source is not 4-connected")
    ar, ac = anchors[0]
    reflected = {(2 * ar - r, 2 * ac - c) for r, c in cells}
    visible = {(r, c) for r, c in reflected if 0 <= r < h and 0 <= c < w}
    if not visible or reflected & cells:
        raise ValueError("Reflection is invisible or overlaps the original")
    interior = {(r, c) for r, c in cells
                if {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)} <= cells}
    return {"height": h, "width": w, "anchor": [ar, ac], "source_cells": len(cells),
            "reflected_cells_visible": len(visible), "partial_clipping": len(visible) < len(cells),
            "copied_interior_visible": any((2 * ar - r, 2 * ac - c) in visible for r, c in interior)}


def exact_fixtures():
    specs = [
        ("small_plus_clipped", 4, 5, (1, 2), [(2, 1), (1, 1), (3, 1), (2, 0), (2, 2)], 2),
        ("small_asymmetric_clipped", 4, 5, (1, 1), [(0, 2), (0, 3), (1, 3)], 4),
        ("diagonal_full_plus", 5, 5, (2, 2), [(1, 1), (0, 1), (2, 1), (1, 0), (1, 2)], 6),
    ]
    result = []
    for name, h, w, anchor, cells, color in specs:
        grid = [[0] * w for _ in range(h)]
        grid[anchor[0]][anchor[1]] = 9
        for r, c in cells:
            grid[r][c] = color
        result.append({"name": name, "input": grid, "geometry": geometry(grid)})
    return result


def rival_bindings(module):
    """Read live declarations, including aliases, without a copied name list."""
    result, errors = {}, []
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declaration = getattr(module, namespace, None)
        if not isinstance(declaration, dict) or not declaration:
            errors.append(f"{namespace}: missing or empty declaration; coverage is not established")
            continue
        for name, fn in declaration.items():
            if not isinstance(name, str) or not callable(fn):
                errors.append(f"{namespace}: invalid named callable")
            else:
                result[f"{namespace}:{name}"] = fn
    return result, errors


def predict(fn, grid):
    copied = deepcopy(grid)
    output = normalize_grid(fn(copied))
    if copied != grid:
        raise ValueError("Rival mutated its input")
    return output


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def run(args):
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(TASK, root=root)
    bindings, failures = rival_bindings(module)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    report = {"schema": "b1972482cb43-reflection-probe-v1", "task_id": TASK,
              "generator_path": str(source.relative_to(root)), "generator_sha256": source_hash,
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "reviewer_support_sha256": hashlib.sha256(HELPER.read_bytes()).hexdigest(),
              "labeled_canonical_pairs_sha256": digest(canonical),
              "canonical_pairs": len(canonical), "declarations": sorted(bindings),
              "failures": failures, "canonical_fit": {}, "fixtures": [], "streams": [], "windows": [],
              "rotation_count": 0,
              "scope": "Bounded independent-model witness checks; Racket fixture calibration, not a public lesson census or all-seed proof."}
    if not canonical:
        failures.append("No labeled canonical population")
    for pair in canonical:
        if point_model(pair["input"]) != pair["output"]:
            failures.append(f"Independent model disagrees with canonical {pair['variant']}/{pair['split']}/{pair['pair_index']}")
    for binding, fn in bindings.items():
        mismatches = []
        for pair in canonical:
            try:
                equal = predict(fn, pair["input"]) == pair["output"]
            except Exception as exc:
                equal = False
                failures.append(f"{binding}: canonical prediction raised {type(exc).__name__}: {exc}")
            if not equal:
                mismatches.append({k: pair[k] for k in ("variant", "split", "pair_index")})
        report["canonical_fit"][binding] = {"checked": len(canonical), "mismatches": mismatches}
        if binding.startswith("CANONICAL_SHORTCUTS:") and mismatches:
            failures.append(f"{binding}: declaration does not fit all labeled canonical pairs")
    if args.declarations_only:
        report["mode"] = "declarations_only"
        report["verdict"] = "FAIL" if failures else "DECLARATIONS_ONLY"
        return report
    if not args.oracle_labels:
        failures.append("--oracle-labels from canonical arcpuzzles apply is required")
        report["verdict"] = "FAIL"
        return report
    labels_path = Path(args.oracle_labels)
    receipt = json.loads(labels_path.read_text())
    report["racket_fixture_receipt"] = {"path": str(labels_path), "sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest(),
                                        "executed_rule_hash": receipt.get("executed_rule_hash"),
                                        "rule_text_sha256": receipt.get("rule_text_sha256")}
    if (receipt.get("task_id") != TASK or receipt.get("reference") != "canonical"
            or not receipt.get("rule_hash_matches_catalog") or receipt.get("generator_sha256") != source_hash):
        failures.append("Racket fixture receipt is not bound to this current generator and canonical authority")
    fixtures = exact_fixtures()
    if len(receipt.get("results", [])) != len(fixtures):
        failures.append("Racket fixture result count mismatch")
    for fixture, actual in zip(fixtures, receipt.get("results", [])):
        if actual.get("input") != fixture["input"] or actual.get("output") != point_model(fixture["input"]):
            failures.append(f"{fixture['name']}: Racket fixture/model mismatch")
        row = {**fixture, "output": actual.get("output"), "refutes": []}
        for binding, fn in bindings.items():
            if predict(fn, fixture["input"]) != actual.get("output"):
                row["refutes"].append(binding)
        report["fixtures"].append(row)
    demos = getattr(module, "EXAMPLES_NEEDED", None)
    if type(demos) is not int or not 1 <= demos <= 32:
        failures.append("Missing or invalid EXAMPLES_NEEDED")
        report["verdict"] = "FAIL"
        return report
    width = demos + 1
    report["examples_needed"] = demos
    if args.samples < width:
        raise ValueError(f"--samples must be at least {width}")
    period = getattr(module, "LESSON_SCHEDULE_PERIOD", None)
    report["declared_schedule_period"] = period
    if type(period) is not int or period < 1:
        failures.append("Missing or invalid LESSON_SCHEDULE_PERIOD")
    else:
        residues = sorted({index % period for index in range(args.start, args.start + args.samples - width + 1)})
        report["starting_residues_checked_per_stream"] = residues
        if residues != list(range(period)):
            failures.append("The requested probe population does not cover every declared starting residue")
    hook = getattr(module, "lesson_identifiable", None)
    if not callable(hook):
        failures.append("Missing lesson_identifiable hook")
    configs = [(seed, difficulty, {}) for seed in args.seeds for difficulty in (None, "easy", "medium", "hard")]
    configs.extend((args.seeds[0], "medium", {"grid_h": h, "grid_w": w}) for h, w in ((4, 5), (4, 6), (5, 5)))
    configs.extend((args.seeds[0], "medium", {"grid_h": 4, "grid_w": 5, "palette_kind": kind})
                   for kind in ("warm", "cool", "varied"))
    global_hashes = set()
    for stream_index, (seed, difficulty, overrides) in enumerate(configs):
        draws, summaries = [], []
        for sample_index in range(args.start, args.start + args.samples):
            grid = module.generate(seed=seed, sample_index=sample_index, difficulty=difficulty, **overrides)
            if isinstance(grid, dict):
                grid = grid["input"]
            grid = normalize_grid(grid)
            output = point_model(grid)
            info = geometry(grid)
            if overrides.get("grid_h", info["height"]) != info["height"] or overrides.get("grid_w", info["width"]) != info["width"]:
                failures.append(f"stream {stream_index}, sample {sample_index}: explicit dimensions were not honored")
            fingerprint = digest(grid)
            global_hashes.add(fingerprint)
            checker = getattr(module, "self_check", None)
            if callable(checker) and checker(deepcopy(grid), difficulty=difficulty):
                failures.append(f"stream {stream_index}, sample {sample_index}: self_check rejected generated input")
            refutes = []
            for binding, fn in bindings.items():
                prediction = predict(fn, grid)
                if predict(fn, grid) != prediction:
                    failures.append(f"{binding}: nondeterministic prediction at stream {stream_index}, sample {sample_index}")
                if prediction != output:
                    refutes.append(binding)
            summaries.append({"sample_index": sample_index, "input_sha256": fingerprint, "geometry": info, "refutes": refutes})
            draws.append({"input": grid, "output": output})
        report["streams"].append({"stream": stream_index, "seed": seed, "difficulty": difficulty,
                                  "overrides": overrides, "draws": summaries})
        for offset in range(args.samples - width + 1):
            selected, pairs = summaries[offset:offset + width], draws[offset:offset + width]
            counts = {name: len({row["input_sha256"] for row in selected if name in row["refutes"]}) for name in bindings}
            demo_counts = {name: len({row["input_sha256"] for row in selected[:demos] if name in row["refutes"]}) for name in bindings}
            duplicates = width - len({row["input_sha256"] for row in selected})
            duplicate_demos = demos - len({row["input_sha256"] for row in selected[:demos]})
            feature_counts = {name: sum(row["geometry"][name] for row in selected)
                              for name in ("partial_clipping", "copied_interior_visible")}
            row = {"stream": stream_index, "sample_indices": [item["sample_index"] for item in selected],
                   "distinct_refutations": counts, "demonstration_refutations": demo_counts,
                   "feature_counts": feature_counts, "duplicate_inputs": duplicates,
                   "duplicate_demonstrations": duplicate_demos,
                   "hook_failures": []}
            reasons = [f"{name} has only {count} distinct refuting inputs" for name, count in counts.items() if count < 2]
            reasons.extend(f"{name} has only {count} witnesses" for name, count in feature_counts.items() if count < 2)
            if duplicates:
                reasons.append("duplicate input could be skipped by public lesson materialization")
            for heldout in range(width):
                report["rotation_count"] += 1
                if callable(hook):
                    findings = hook(deepcopy([pair for i, pair in enumerate(pairs) if i != heldout]), deepcopy(pairs[heldout]))
                    if not isinstance(findings, list) or findings:
                        row["hook_failures"].append({"heldout_sample_index": selected[heldout]["sample_index"], "reasons": findings})
            if row["hook_failures"]:
                reasons.append("lesson hook rejected a holdout rotation")
            if reasons:
                row["failure_reasons"] = reasons
                row["pairs"] = pairs
                failures.append(f"stream {stream_index}, window {row['sample_indices']}: {'; '.join(reasons)}")
            report["windows"].append(row)
    report["generated_draws"] = len(configs) * args.samples
    report["unique_generated_inputs"] = len(global_hashes)
    report["verdict"] = "FAIL" if failures else "PASS"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-oracle-inputs", type=Path)
    parser.add_argument("--oracle-labels", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--declarations-only", action="store_true")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--samples", type=int, default=9)
    args = parser.parse_args()
    if args.write_oracle_inputs:
        write_new(args.write_oracle_inputs, {"inputs": [item["input"] for item in exact_fixtures()]})
        print(json.dumps({"oracle_inputs": str(args.write_oracle_inputs), "count": len(exact_fixtures())}))
        return 0
    if not args.out:
        parser.error("--out or --write-oracle-inputs is required")
    if args.start < 0 or any(not 0 <= seed <= 0xFFFFFFFF for seed in args.seeds):
        parser.error("Use nonnegative sample indices and uint32 seeds")
    report = run(args)
    write_new(args.out, report)
    print(json.dumps({"verdict": report["verdict"], "generator_sha256": report["generator_sha256"],
                      "declarations": len(report["declarations"]), "generated_draws": report.get("generated_draws", 0),
                      "windows": len(report["windows"]), "rotations": report["rotation_count"],
                      "failures": report["failures"], "report": str(args.out)}, indent=2))
    return int(report["verdict"] == "FAIL")


if __name__ == "__main__":
    raise SystemExit(main())
