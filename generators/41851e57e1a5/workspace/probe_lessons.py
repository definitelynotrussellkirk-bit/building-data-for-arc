#!/usr/bin/env python3
"""Small, source-bound lesson probe for the bbox-overlap task.

Run directly or with PYTHONPATH=shared/runtime:src. Labels here use an
independent Python bbox oracle, checked against every stored canonical pair;
this probe does not execute Racket or replace the production reference checks.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

try:
    from reviewer_support import canonical_pairs, canonical_path, find_root
except ModuleNotFoundError:
    # Locate the helper in this script's own tree. Canonical data are resolved
    # by its public find_root(), never by an assumed parent depth or cwd.
    for ancestor in Path(__file__).resolve().parents:
        helpers = [ancestor / relative for relative in
                   ("reviewer_support.py", "shared/runtime/reviewer_support.py")]
        helper = next((path for path in helpers if path.is_file()), None)
        if helper is not None:
            sys.path.insert(0, str(helper.parent))
            break
    from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "41851e57e1a5"
BASELINE_SHA256 = "58378291ce5dc1b1d1aa54a8f155d7a479efa1ae5166d4c2cdf9fd1313fa0806"
BANDS = (None, "easy", "medium", "hard")

# Materialized from the exact baseline source above, generate(seed, i), i=0..3.
# The first three are demonstrations. These are compact retained inputs, not
# an executable dependency on the review packet's baseline directory.
BASELINE_INPUTS = {
    0: [
        ["000000000000", "000000000000", "000000000000", "000000000000", "000000000000", "000000110000", "000002110007", "000002200000", "000000200000", "000000000000"],
        ["000000000000", "000000000000", "000000000000", "000000000000", "000000010000", "000000011000", "000000221000", "000000220000", "009000000000", "000000000000", "000000000000"],
        ["00000000000", "00000000000", "00000000000", "00000000000", "00000000000", "00000000000", "00110000000", "00122000000", "00022000005"],
        ["0000000010", "0000000011", "0000000021", "0000000022", "0000000002", "0000000000", "0000000000", "0000000000", "0000000000", "0000000060", "0000000000"],
    ],
    8: [
        ["00000000000", "00000000000", "00000000000", "00000200000", "00000220000", "00001120000", "00001100700", "00000000000", "00000000000"],
        ["000000000000", "000000000000", "022200000000", "112000000000", "110000000000", "000000000000", "000000000000", "000000000000", "000000000700"],
        ["000000000000", "000000000008", "000000000000", "000000000000", "000000000000", "000000000000", "000000000000", "000000000000", "000000011100", "000000001220", "000000000200"],
        ["00000000000", "00000000000", "00000000000", "00000000000", "00000010000", "00000011000", "00000201006", "00000220000", "00000020000", "00000000000"],
    ],
    42: [
        ["0000000000", "0000000000", "0000000003", "0000000000", "0000000000", "0000000000", "0000000000", "0000000000", "0011100000", "2221000000", "0200000000"],
        ["0000000000", "0000000000", "0300000000", "0000110000", "0002100000", "0002200000", "0000200000", "0000000000", "0000000000"],
        ["00000000000", "00000000000", "00000000000", "00000000300", "00000000000", "00022200000", "00112000000", "00110000000", "00000000000"],
        ["000000000000", "000000000000", "022200000000", "002100000000", "000110000700", "000010000000", "000000000000", "000000000000", "000000000000", "000000000000"],
    ],
}


def load_generator(path):
    path = Path(path).resolve()
    name = "bbox_probe_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bounds(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value == color]
    if not cells:
        raise ValueError(f"missing shape color {color}")
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def intersection(grid):
    red, blue = bounds(grid, 2), bounds(grid, 1)
    return (max(red[0], blue[0]), max(red[1], blue[1]),
            min(red[2], blue[2]), min(red[3], blue[3]))


def key_color(grid):
    return next(value for row in grid for value in row if value not in (0, 1, 2))


def predict(grid, mode="intersection"):
    """Independent oracle and explicitly defined, deterministic rival rules."""
    red, blue = bounds(grid, 2), bounds(grid, 1)
    box = intersection(grid)
    if mode == "red_bbox":
        box = red
    elif mode == "blue_bbox":
        box = blue
    elif mode == "union_bbox":
        box = (min(red[0], blue[0]), min(red[1], blue[1]),
               max(red[2], blue[2]), max(red[3], blue[3]))
    r0, c0, r1, c1 = box
    color = key_color(grid)
    if mode == "upper_left_key":
        color = grid[0][0]
    elif mode.startswith("fixed_key_"):
        color = int(mode.rsplit("_", 1)[1])
    out = [[0 for _ in row] for row in grid]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if mode == "corner_only" and (r, c) != (r0, c0):
                continue
            if mode == "occupied_only" and grid[r][c] == 0:
                continue
            if mode == "perimeter_only" and r not in (r0, r1) and c not in (c0, c1):
                continue
            out[r][c] = color
    return out


RIVAL_NAMES = (
    "corner_only", "occupied_only", "perimeter_only", "red_bbox", "blue_bbox",
    "union_bbox", "upper_left_key", *(f"fixed_key_{color}" for color in range(3, 10)),
)
FIXED_RIVALS = {name: (lambda grid, mode=name: predict(grid, mode)) for name in RIVAL_NAMES}


def labeled(grid):
    return {"input": deepcopy(grid), "output": predict(grid)}


def baseline_lesson(seed):
    return [labeled([[int(value) for value in row] for row in grid])
            for grid in BASELINE_INPUTS[seed]]


def features(grid):
    r0, c0, r1, c1 = intersection(grid)
    height, width = max(0, r1 - r0 + 1), max(0, c1 - c0 + 1)
    blank = sum(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
    interior_blank = sum(grid[r][c] == 0 for r in range(r0 + 1, r1)
                         for c in range(c0 + 1, c1))
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "key_color": key_color(grid),
            "overlap_h": height, "overlap_w": width, "blank_fill": blank,
            "interior_blank_fill": interior_blank,
            "rich": height >= 3 and width >= 3 and interior_blank > 0,
            "red_size": sum(value == 2 for row in grid for value in row),
            "blue_size": sum(value == 1 for row in grid for value in row)}


def score_lesson(demos, query, rivals=FIXED_RIVALS, *, cache=None):
    """Classify each rival without counting agreement on a query as ambiguity."""
    cache = {} if cache is None else cache
    def prediction(name, fn, pair):
        key = (name, tuple(tuple(row) for row in pair["input"]))
        if key not in cache:
            cache[key] = fn(deepcopy(pair["input"]))
        return cache[key]
    result = {}
    for name, fn in rivals.items():
        if not all(prediction(name, fn, pair) == pair["output"] for pair in demos):
            result[name] = "refuted"
        elif prediction(name, fn, query) == query["output"]:
            result[name] = "survived_all"
        else:
            result[name] = "ambiguous"
    return result


def ambiguous_rivals(demos, query, rivals=FIXED_RIVALS):
    return {name for name, status in score_lesson(demos, query, rivals).items()
            if status == "ambiguous"}


def source_identity(generator_path, root):
    rules = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program = row["program_solution"]
            rules.append(hashlib.sha256(program.encode()).hexdigest())
    if len(set(rules)) != 1:
        raise ValueError("expected one unambiguous canonical rule")
    return {"generator_sha256": hashlib.sha256(Path(generator_path).read_bytes()).hexdigest(),
            "canonical_rule_sha256": rules[0],
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", required=True, type=Path)
    parser.add_argument("--seeds", default=20, type=int, help="consecutive seeds beginning at zero")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--baseline-witnesses", action="store_true",
                        help="also rescore retained baseline lessons at seeds 0, 8 and 42")
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    root = find_root(__file__)
    gen = load_generator(args.generator)
    declared = getattr(gen, "LESSON_COMPETITORS", None) or getattr(gen, "SEMANTIC_RIVALS", None)
    rivals = declared if declared else FIXED_RIVALS
    if not isinstance(rivals, dict) or any(not callable(fn) for fn in rivals.values()):
        raise TypeError("expected named callable rivals")
    hook = getattr(gen, "lesson_identifiable", None)
    report = {"schema": "bbox-overlap-lesson-probe-v1", "task_id": TASK_ID,
              **source_identity(args.generator, root),
              "label_basis": "independent Python bbox oracle; stored canonical labels cross-checked; Racket not executed",
              "rival_basis": "selected generator declarations" if declared else "independent fixed rivals",
              "seed_range": [0, args.seeds - 1], "bands": list(BANDS),
              "cyclic_starts": list(range(12)), "query_rotations": [0, 1, 2, 3],
              "canonical": [], "counts": Counter(), "features": Counter(),
              "per_rival": {name: Counter() for name in rivals},
              "first_ambiguous_examples": {}, "errors": []}
    canonical = canonical_pairs(TASK_ID, root=root)
    for pair in canonical:
        agrees = predict(pair["input"]) == pair["output"]
        row = {key: pair[key] for key in ("variant", "split", "pair_index")}
        row.update({"oracle_agrees": agrees, "self_check": gen.self_check(pair["input"])})
        if hasattr(gen, "strict_canonical_like"):
            row["strict_canonical_like"] = gen.strict_canonical_like(pair["input"])
        report["canonical"].append(row)
        if not agrees:
            raise AssertionError(f"independent oracle differs from canonical {row}")
    unique_inputs = set()
    for band in BANDS:
        for seed in range(args.seeds):
            pairs, cache = [], {}
            for index in range(15):
                try:
                    grid = gen.generate(seed, index, difficulty=band)
                    errors = gen.self_check(grid)
                    if errors:
                        raise ValueError(f"self_check rejected generated input: {errors}")
                    pairs.append(labeled(grid))
                    report["counts"]["materialized_pairs"] += 1
                    if hasattr(gen, "strict_canonical_like"):
                        strict = gen.strict_canonical_like(grid)
                        report["counts"]["strict_checked"] += 1
                        report["counts"]["strict_accepted"] += strict is True or strict == []
                    unique_inputs.add(tuple(tuple(row) for row in grid))
                    profile = features(grid)
                    for name in ("rich", "blank_fill", "interior_blank_fill"):
                        report["features"][name] += bool(profile[name])
                    shape = f"{profile['overlap_h']}x{profile['overlap_w']}"
                    report["features"][f"overlap_{shape}"] += 1
                except Exception as exc:
                    report["errors"].append({"seed": seed, "sample_index": index,
                                             "difficulty": band, "error": f"{type(exc).__name__}: {exc}"})
                    break
            if len(pairs) != 15:
                continue
            for start in range(12):
                window = pairs[start:start + 4]
                for query_index in range(4):
                    demos = [pair for i, pair in enumerate(window) if i != query_index]
                    query = window[query_index]
                    report["counts"]["rotated_lessons"] += 1
                    score = score_lesson(demos, query, rivals, cache=cache)
                    ambiguous = [name for name, status in score.items() if status == "ambiguous"]
                    report["counts"]["ambiguous_rotations"] += bool(ambiguous)
                    if query_index == 3:
                        report["counts"]["ordinary_lessons"] += 1
                        report["counts"]["ambiguous_ordinary_lessons"] += bool(ambiguous)
                    for name, status in score.items():
                        report["per_rival"][name][status] += 1
                        if query_index == 3:
                            report["per_rival"][name][f"ordinary_{status}"] += 1
                    for name in ambiguous:
                        report["first_ambiguous_examples"].setdefault(name, {
                            "seed": seed, "difficulty": band, "start": start,
                            "query_offset": query_index, "sample_indices": list(range(start, start + 4)),
                            "train": demos, "query": query, "rival_output": rivals[name](query["input"])})
                    if hook is not None:
                        reasons = hook(deepcopy(demos), deepcopy(query))
                        if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
                            raise TypeError("lesson_identifiable must return list[str]")
                        report["counts"]["hook_flagged_rotations"] += bool(reasons)
                        if bool(reasons) != bool(ambiguous):
                            report["errors"].append({"seed": seed, "difficulty": band, "start": start,
                                                     "query_offset": query_index,
                                                     "error": "hook and rival ambiguity disagree", "reasons": reasons,
                                                     "ambiguous_rivals": ambiguous})
    report["counts"]["unique_inputs"] = len(unique_inputs)
    if args.baseline_witnesses:
        report["baseline_witnesses"] = {"generator_sha256": BASELINE_SHA256, "lessons": []}
        for seed in BASELINE_INPUTS:
            pairs = baseline_lesson(seed)
            score = score_lesson(pairs[:3], pairs[3], rivals)
            report["baseline_witnesses"]["lessons"].append({
                "seed": seed, "train": pairs[:3], "query": pairs[3], "rival_status": score,
                "hook_reasons": hook(deepcopy(pairs[:3]), deepcopy(pairs[3])) if hook else None})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "identity": source_identity(args.generator, root),
                      "counts": report["counts"], "error_count": len(report["errors"])}))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
