"""Small source-bound semantic probe for task d48317a7c7c8.

Run from a review packet with its public Racket wrapper::

    python3 ../run_with_racket.py python3 -B \
        generators/d48317a7c7c8/workspace/probe_review.py \
        --out ../checks/semantic-probe/probe.json

The fixtures and run detector are independent of generator helpers. All labels
in the report come from public Catalog.apply, in batches of at most 64. Rival
functions are discovered from the selected generator, never copied here.
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
from typing import Any

sys.dont_write_bytecode = True

from reviewer_support import canonical_pairs, find_root, normalize_grid


TASK_ID = "d48317a7c7c8"
RULE_HASH = "b2af6531f18d"
RIVAL_NAMESPACES = ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")


def grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def generator_path(root: Path) -> Path:
    for relative in (
        f"generators/{TASK_ID}/generator.py",
        f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py",
    ):
        candidate = root / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No selected generator for {TASK_ID} under {root}")


def load_generator(root: Path):
    source = generator_path(root)
    spec = importlib.util.spec_from_file_location(f"review_probe_{TASK_ID}_generator", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def exact_yellow_bars(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Detect exact 4-connected targets by runs and external-neighbor exclusion.

    This uses no flood-fill helper from the implementation under review. A
    collinear yellow triple is an entire size-three component exactly when no
    yellow cardinal neighbor lies outside it. Diagonal contact is permitted.
    """
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    found = []
    for row in range(height):
        for col in range(width):
            for dr, dc, orientation in ((0, 1, "horizontal"), (1, 0, "vertical")):
                cells = {(row + step * dr, col + step * dc) for step in range(3)}
                if not all(
                    0 <= r < height and 0 <= c < width and grid[r][c] == 4
                    for r, c in cells
                ):
                    continue
                outside = {
                    (r + nr, c + nc)
                    for r, c in cells
                    for nr, nc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                } - cells
                if any(
                    0 <= r < height and 0 <= c < width and grid[r][c] == 4
                    for r, c in outside
                ):
                    continue
                caps = [(row - dr, col - dc), (row + 3 * dr, col + 3 * dc)]
                found.append({
                    "orientation": orientation,
                    "cells": sorted(cells),
                    "caps": caps,
                    "available_caps": [
                        (r, c) for r, c in caps
                        if 0 <= r < height and 0 <= c < width and grid[r][c] == 0
                    ],
                })
    return found


def independent_reference(grid: list[list[int]]) -> list[list[int]]:
    """Independent prediction checked against Racket; never used as a label."""
    output = normalize_grid(grid)
    for bar in exact_yellow_bars(grid):
        for row, col in bar["available_caps"]:
            output[row][col] = 8
    return output


def _case(name, objects, cyan_cells=(), *, height=8, width=8):
    grid = [[0] * width for _ in range(height)]
    for color, cells in objects:
        for row, col in cells:
            if grid[row][col] != 0:
                raise ValueError(f"Overlapping fixture objects in {name}")
            grid[row][col] = color
    output = deepcopy(grid)
    for row, col in cyan_cells:
        if output[row][col] != 0:
            raise ValueError(f"Fixture {name} tries to overwrite an occupied cap")
        output[row][col] = 8
    return {"name": name, "input": grid, "expected_output": output}


def semantic_cases() -> list[dict[str, Any]]:
    """Literal edge cases; expected changed coordinates are authored explicitly."""
    bar = [(3, col) for col in range(2, 5)]
    shared = [(4, [(2, col) for col in range(1, 4)]),
              (4, [(row, 4) for row in range(3, 6)])]
    return [
        _case("nonyellow_three_bar_unchanged", [(6, bar)]),
        _case("yellow_four_bar_unchanged", [(4, [(3, col) for col in range(2, 6)])]),
        _case("yellow_bent_three_unchanged", [(4, [(3, 2), (3, 3), (4, 3)])]),
        _case("triple_inside_bent_four_unchanged", [(4, bar + [(4, 3)])]),
        _case("diagonal_yellow_contact_is_separate", [(4, bar), (4, [(2, 1)])],
              [(3, 1), (3, 5)]),
        _case("occupied_magenta_cap_preserved", [(4, bar), (6, [(3, 1)])], [(3, 5)]),
        _case("occupied_cyan_cap_preserved", [(4, bar), (8, [(3, 1)])], [(3, 5)]),
        _case("both_occupied_caps_preserved", [(4, bar), (6, [(3, 1)]), (7, [(3, 5)])]),
        _case("left_boundary_clips_one_cap", [(4, [(3, col) for col in range(3)])],
              [(3, 3)]),
        _case("top_boundary_clips_one_cap", [(4, [(row, 3) for row in range(3)])],
              [(3, 3)]),
        _case("both_caps_outside_is_noop", [(4, [(3, col) for col in range(3)])], width=3),
        _case("shared_empty_cap_is_painted_once", shared, [(2, 0), (2, 4), (6, 4)]),
        _case("shared_occupied_cap_is_preserved", shared + [(6, [(2, 4)])],
              [(2, 0), (6, 4)]),
        _case("compact_rich_counterexample", [
            (4, [(1, col) for col in range(3)]),
            (4, [(0, 3)]),
            (4, [(row, 6) for row in range(3, 6)]),
            (6, [(2, 6)]),
            (4, [(3, col) for col in range(1, 5)]),
            (4, [(5, 1), (5, 2), (5, 3), (6, 1)]),
            (6, [(7, col) for col in range(4, 7)]),
        ], [(1, 3), (6, 6)]),
    ]


def discover_rivals(generator):
    """Retain namespaces while deduplicating identical named callable objects."""
    by_name = {}
    declarations = {}
    for namespace in RIVAL_NAMESPACES:
        declared = getattr(generator, namespace, {})
        if not isinstance(declared, dict):
            raise TypeError(f"{namespace} must be a dictionary")
        declarations[namespace] = {}
        for name, solve in sorted(declared.items()):
            if not isinstance(name, str) or not callable(solve):
                raise TypeError(f"Invalid {namespace} entry {name!r}")
            by_name.setdefault(name, {}).setdefault(id(solve), []).append((namespace, solve))
    rivals, membership = {}, {}
    for name, functions in sorted(by_name.items()):
        for entries in functions.values():
            key = name if len(functions) == 1 else f"{entries[0][0]}:{name}"
            rivals[key] = entries[0][1]
            membership[key] = [namespace for namespace, _ in entries]
            for namespace, _ in entries:
                declarations[namespace][name] = key
    return rivals, declarations, membership


def output_difference(expected, actual):
    """Exact row/column changes, including cells beyond either grid's shape."""
    changes = []
    for row in range(max(len(expected), len(actual))):
        left = expected[row] if row < len(expected) else []
        right = actual[row] if row < len(actual) else []
        for col in range(max(len(left), len(right))):
            before = left[col] if col < len(left) else None
            after = right[col] if col < len(right) else None
            if before != after:
                changes.append([row, col, before, after])
    return changes


def run_probe(root: Path, *, per_band=12, seed=20261008, sample_index=0):
    from arcpuzzles import Catalog

    source = generator_path(root)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    generator = load_generator(root)
    catalog = Catalog(root)
    description = catalog.describe(TASK_ID)
    if description["generator_sha256"] != source_hash:
        raise RuntimeError("Selected generator differs from the public catalog identity")
    rivals, declarations, membership = discover_rivals(generator)
    witnesses = getattr(generator, "SEMANTIC_WITNESSES", {})
    claims = getattr(generator, "WITNESS_RIVALS", {})
    cases = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        cases.append({
            "name": f"canonical_v{pair['variant']}_{pair['split']}_{pair['pair_index']}",
            "kind": "canonical", "input": pair["input"], "expected_output": pair["output"],
        })
    cases.extend({**case, "kind": "handmade"} for case in semantic_cases())
    for band_index, band in enumerate(("easy", "medium", "hard")):
        band_seed = seed + 1009 * band_index
        for offset in range(per_band):
            index = sample_index + offset
            grid = generator.generate(band_seed, index, difficulty=band)
            cases.append({
                "name": f"generated_{band}_{index}", "kind": "generated",
                "difficulty": band, "seed": band_seed, "sample_index": index,
                "input": normalize_grid(grid),
            })

    receipts, outputs = [], []
    for start in range(0, len(cases), 64):
        receipt = catalog.apply(TASK_ID, [case["input"] for case in cases[start:start + 64]],
                                reference="canonical", timeout=300)
        if (receipt["generator_sha256"] != source_hash
                or not receipt["rule_hash_matches_catalog"]
                or receipt["catalog_rule_hash"] != RULE_HASH):
            raise RuntimeError("Public reference receipt does not match the selected authority")
        metadata = {key: value for key, value in receipt.items() if key != "results"}
        metadata.update(case_start=start, case_count=len(receipt["results"]))
        receipts.append(metadata)
        outputs.extend(receipt["results"])
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Generator source changed during the probe; rerun on final bytes")

    failures, records = [], []
    if getattr(generator, "RULE_HASH", None) != RULE_HASH:
        failures.append({"error": "Generator does not pin the selected canonical rule hash"})
    counts = {kind: {name: 0 for name in rivals}
              for kind in ("canonical", "handmade", "easy", "medium", "hard")}
    rival_errors = {kind: {name: 0 for name in rivals} for kind in counts}
    totals = Counter()
    band_counts = {band: {"draws": 0, "changed": 0, "self_check_rejections": 0,
                         "witness_hits": Counter(), "target_counts": Counter()}
                   for band in ("easy", "medium", "hard")}
    for case, applied in zip(cases, outputs, strict=True):
        grid, output = case["input"], applied["output"]
        kind = case["difficulty"] if case["kind"] == "generated" else case["kind"]
        totals[kind] += 1
        record = {key: value for key, value in case.items() if key != "expected_output"}
        record.update(output=output, input_sha256=applied["input_sha256"],
                      output_sha256=applied["output_sha256"], reference_error=applied["error"])
        if applied["error"] is not None:
            failures.append({"case": case["name"], "error": applied["error"]})
            records.append(record)
            continue
        if "expected_output" in case and output != case["expected_output"]:
            record["expected_output"] = case["expected_output"]
            failures.append({"case": case["name"], "error": "literal expected output disagrees with Racket"})
        mirror = independent_reference(grid)
        if mirror != output:
            record["independent_reference_difference"] = output_difference(output, mirror)
            failures.append({"case": case["name"], "error": "independent run detector disagrees with Racket"})
        try:
            production_mirror = normalize_grid(generator.rule_mirror(deepcopy(grid)))
            if production_mirror != output:
                record["generator_mirror_difference"] = output_difference(output, production_mirror)
                failures.append({"case": case["name"], "error": "generator mirror disagrees with Racket"})
        except Exception as exc:
            failures.append({"case": case["name"], "error": f"generator mirror: {type(exc).__name__}: {exc}"})
        changes = output_difference(grid, output)
        record["changed_cells"] = changes
        different, errors = {}, {}
        for name, solve in rivals.items():
            try:
                predicted = normalize_grid(solve(deepcopy(grid)))
                if predicted != output:
                    counts[kind][name] += 1
                    different[name] = {"output_sha256": grid_hash(predicted),
                                       "changes_from_reference": output_difference(output, predicted)}
            except Exception as exc:
                rival_errors[kind][name] += 1
                errors[name] = f"{type(exc).__name__}: {exc}"
                failures.append({"case": case["name"], "rival": name, "error": errors[name]})
        record["rival_differences"] = different
        if errors:
            record["rival_errors"] = errors
        hits = []
        for name, predicate in sorted(witnesses.items()):
            try:
                fired = predicate(deepcopy(grid))
                if type(fired) is not bool:
                    raise TypeError("witness must return bool")
                if not fired:
                    continue
                hits.append(name)
                named = claims.get(name, [])
                named = [named] if isinstance(named, str) else named
                if named and not any(declarations["SEMANTIC_RIVALS"][rival] in different for rival in named):
                    failures.append({"case": case["name"], "witness": name,
                                     "error": "witness fired without its claimed rival disagreement"})
            except Exception as exc:
                failures.append({"case": case["name"], "witness": name,
                                 "error": f"{type(exc).__name__}: {exc}"})
        record["witness_hits"] = hits
        if case["kind"] == "generated":
            band = band_counts[case["difficulty"]]
            findings = generator.self_check(deepcopy(grid))
            record["self_check"] = findings
            band["draws"] += 1
            band["changed"] += bool(changes)
            band["self_check_rejections"] += bool(findings)
            band["witness_hits"].update(hits)
            band["target_counts"].update([len(exact_yellow_bars(grid))])
            if findings:
                failures.append({"case": case["name"], "error": f"self_check rejected generated input: {findings}"})
        records.append(record)
    for band in band_counts.values():
        band["witness_hits"] = dict(sorted(band["witness_hits"].items()))
        band["target_counts"] = dict(sorted(band["target_counts"].items()))
    if not rivals:
        failures.append({"error": "Selected generator declares no executable rivals"})
    fitting = [name for name in rivals
               if counts["canonical"][name] == 0 and rival_errors["canonical"][name] == 0]
    missing = [name for name in fitting
               if not any(counts[band][name] for band in ("easy", "medium", "hard"))]
    if missing and per_band:
        failures.append({"error": "Canonical-fitting rivals had no generated counterexample", "rivals": missing})
    return {
        "schema": "d48317a7c7c8-semantic-probe-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash, "declared_rule_hash": getattr(generator, "RULE_HASH", None),
        "settings": {"seed": seed, "sample_index": sample_index, "per_band": per_band,
                     "bands": ["easy", "medium", "hard"], "max_apply_batch": 64},
        "rival_namespaces": declarations, "rival_membership": membership,
        "witness_rivals": claims, "apply_receipts": receipts,
        "summary": {"case_counts": dict(totals), "canonical_fitting_rivals": fitting,
                    "rival_disagreements": counts, "rival_errors": rival_errors,
                    "generated_bands": band_counts,
                    "failures": failures, "passed": not failures},
        "cases": records,
        "limitations": "Finite component and rival checks; no universal identifiability or approval claim.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--sample-index", type=int, default=0)
    args = parser.parse_args(argv)
    if args.per_band < 0:
        parser.error("--per-band must be nonnegative")
    if args.out.exists():
        parser.error("--out must be a new path")
    report = run_probe(find_root(__file__), per_band=args.per_band, seed=args.seed,
                       sample_index=args.sample_index)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
    print(json.dumps({"output": str(args.out), **report["summary"]}, sort_keys=True))
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
