#!/usr/bin/env python3
"""Reproducible component-outline coverage and declared-rival evidence.

From the extracted packet root (authoring lane, never a blind solve):
  WORK/.venv/bin/python review.py run ../.venv/bin/python \
    generators/623cca1dd5a8/workspace/probe_outline_semantics.py \
    --seed-count 8 --sample-count 24 --racket --require-coverage \
    --out ../checks/semantic-probe/after-probe.json

The broad census uses an explicitly identified, independent Python mirror.
With --racket, a bounded set of retained canonical, hand-made and generated
inputs is separately labelled through public Catalog.apply. Those results and
source identities are retained in full. No lesson-identifiability or exhaustive
random-support claim follows from this individual-input probe.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "623cca1dd5a8"
ROOT = find_root(__file__)
RIVAL_NAMESPACES = ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")
REQUIRED_COVERAGE = ("repeated_color", "thin_bbox", "broad_bbox", "removes_interior", "adds_border")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def components(grid):
    """Independent four-neighbor equal-color flood fill, unrelated to generator code."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while unseen:
        origin = min(unseen)
        color = grid[origin[0]][origin[1]]
        unseen.remove(origin)
        todo, cells = [origin], set()
        while todo:
            r, c = todo.pop()
            cells.add((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    todo.append(point)
        result.append((color, cells))
    return result


def bounds(cells):
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def python_outline_mirror(grid, *, color_union=False, preserve_input=False, filled=False):
    """Diagnostic prediction only; Catalog.apply supplies the Racket authority."""
    groups = components(grid)
    if color_union:
        colors = {}
        for color, cells in groups:
            colors.setdefault(color, set()).update(cells)
        groups = list(colors.items())
    out = deepcopy(grid) if preserve_input else [[0] * len(grid[0]) for _ in grid]
    for color, cells in groups:
        r0, c0, r1, c1 = bounds(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if filled or r in (r0, r1) or c in (c0, c1):
                    out[r][c] = color
    return out


def declared_rivals(module):
    """Read the actual declaration dictionaries, preserving namespace identity."""
    rivals, inventory = {}, {}
    for namespace in RIVAL_NAMESPACES:
        declarations = getattr(module, namespace, {})
        if not isinstance(declarations, dict):
            raise TypeError(f"{namespace} must be a dictionary")
        inventory[namespace] = list(declarations)
        for name, predictor in declarations.items():
            if not isinstance(name, str) or not callable(predictor):
                raise TypeError(f"Invalid declaration {namespace}.{name}")
            rivals[f"{namespace}.{name}"] = predictor
    rivals["DIAGNOSTIC.color_union_outline"] = lambda grid: python_outline_mirror(grid, color_union=True)
    rivals["DIAGNOSTIC.add_border_only"] = lambda grid: python_outline_mirror(grid, preserve_input=True)
    rivals["DIAGNOSTIC.filled_component_bbox"] = lambda grid: python_outline_mirror(grid, filled=True)
    rivals["DIAGNOSTIC.identity"] = deepcopy
    return rivals, inventory


def score_rivals(rivals, grid, expected):
    scores = {}
    for name, predictor in rivals.items():
        try:
            prediction = predictor(deepcopy(grid))
            scores[name] = {"status": "fit" if prediction == expected else "refuted",
                            "prediction_sha256": digest(prediction)}
            if prediction != expected:
                scores[name]["prediction"] = prediction
        except Exception as exc:
            scores[name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return scores


def check_input(module, grid):
    try:
        reasons = module.self_check(deepcopy(grid))
        return {"status": "passed" if reasons == [] else "failed", "reasons": reasons}
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def input_features(grid):
    groups = components(grid)
    boxes = [bounds(cells) for _, cells in groups]
    sizes = [(r1 - r0 + 1, c1 - c0 + 1) for r0, c0, r1, c1 in boxes]
    expected = python_outline_mirror(grid)
    palette = sorted({value for row in grid for value in row})
    counts = Counter(color for color, _ in groups)
    overlaps = []
    for i, (r0, c0, r1, c1) in enumerate(boxes):
        for j in range(i):
            a0, b0, a1, b1 = boxes[j]
            if max(r0, a0) <= min(r1, a1) and max(c0, b0) <= min(c1, b1):
                overlaps.append([j, i])
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "n_components": len(groups),
        "n_distinct_colors_including_background": len(palette), "palette": palette,
        "bbox_sizes": sizes, "bbox_overlap_pairs": overlaps,
        "repeated_color": any(count > 1 for count in counts.values()),
        "thin_bbox": any(min(h, w) <= 2 for h, w in sizes),
        "broad_bbox": any(min(h, w) >= 3 for h, w in sizes),
        "removes_interior": any(value and not expected[r][c]
                                for r, row in enumerate(grid) for c, value in enumerate(row)),
        "adds_border": any(not value and expected[r][c]
                           for r, row in enumerate(grid) for c, value in enumerate(row)),
        "edge_touch": any(r0 == 0 or c0 == 0 or r1 == len(grid) - 1 or c1 == len(grid[0]) - 1
                          for r0, c0, r1, c1 in boxes),
        "identity": expected == grid,
    }


def hand_made_inputs():
    repeated = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 4, 0, 0, 0, 0, 4, 4, 4, 0],
        [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
        [0, 4, 4, 4, 0, 0, 0, 0, 4, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    interior = [[0, 0, 0, 0, 0], [0, 6, 0, 0, 0], [0, 6, 6, 0, 0],
                [0, 6, 6, 6, 0], [0, 0, 0, 0, 0]]
    return [
        {"name": "retained_repeated_color_counterexample", "input": repeated},
        {"name": "occupied_interior_and_missing_border", "input": interior},
        {"name": "repeated_color_transposed", "input": [list(row) for row in zip(*repeated)]},
        {"name": "repeated_color_recolored", "input": [[9 if value == 4 else value for value in row] for row in repeated]},
        {"name": "singleton", "input": [[4]]},
        {"name": "solid_rectangle", "input": [[3, 3, 3], [3, 3, 3], [3, 3, 3]]},
        {"name": "different_color_edge_contact", "input": [[2, 5]]},
        {"name": "same_color_diagonal_contact", "input": [[4, 0], [0, 4]]},
    ]


def run_probe(args):
    module, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    rivals, inventory = declared_rivals(module)
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    report = {
        "schema": "623cca1dd5a8-outline-semantic-probe-v1", "task_id": TASK_ID,
        "source": {"generator_path": str(source.relative_to(ROOT)), "generator_sha256": source_sha,
                   "generator_version": module.VERSION,
                   "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "canonical_path": str(canonical_path(ROOT).relative_to(ROOT)),
                   "canonical_labeled_pairs_sha256": digest(canonical)},
        "labels": {"canonical": "Retained canonical_pairs labels, no fresh Racket execution",
                   "generated_census": "Independent Python python_outline_mirror diagnostic predictions",
                   "racket_selection": "Fresh public Catalog.apply labels only when racket.executed is true"},
        "declaration_inventory": inventory,
        "limits": "Finite individual-input census. No lesson, rotation, universal coverage or approval claim.",
        "population": {"seed_start": args.seed_start, "seed_count": args.seed_count,
                       "sample_start": args.sample_start, "sample_count": args.sample_count,
                       "difficulty_bands": args.bands},
        "canonical": [], "hand_made": [], "generated": {}, "issues": [],
    }
    authority_inputs = []
    for pair in canonical:
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        entry = {**identity, "input": pair["input"], "retained_output": pair["output"],
                 "self_check": check_input(module, pair["input"]), "features": input_features(pair["input"]),
                 "python_mirror_matches_retained_label": python_outline_mirror(pair["input"]) == pair["output"],
                 "rival_scores_against_retained_label": score_rivals(rivals, pair["input"], pair["output"])}
        report["canonical"].append(entry)
        authority_inputs.append({"kind": "canonical", "identity": identity, "input": pair["input"],
                                 "retained_output": pair["output"]})
        if entry["self_check"]["status"] != "passed":
            report["issues"].append({"kind": "canonical_rejected", **identity, "self_check": entry["self_check"]})
        if not entry["python_mirror_matches_retained_label"]:
            report["issues"].append({"kind": "python_mirror_disagrees_with_canonical", **identity})
        for name, score in entry["rival_scores_against_retained_label"].items():
            if score["status"] == "error":
                report["issues"].append({"kind": "canonical_rival_error", **identity,
                                         "rival": name, "error": score["error"]})
    for witness in hand_made_inputs():
        entry = {**witness, "self_check": check_input(module, witness["input"]),
                 "features": input_features(witness["input"])}
        report["hand_made"].append(entry)
        authority_inputs.append({"kind": "hand_made", **witness})
        if entry["self_check"]["status"] != "passed":
            report["issues"].append({"kind": "lawful_hand_made_rejected", "name": witness["name"],
                                     "self_check": entry["self_check"]})
    selected_generated, selected_hashes = [], set()
    for band in args.bands:
        counts, objects, palettes, boxes, dimensions = Counter(), Counter(), Counter(), Counter(), Counter()
        rival_counts = {name: Counter() for name in rivals}
        witnesses, rival_witnesses, errors = {}, {}, []
        for seed in range(args.seed_start, args.seed_start + args.seed_count):
            for sample_index in range(args.sample_start, args.sample_start + args.sample_count):
                recipe = {"seed": seed, "sample_index": sample_index, "difficulty": band, "overrides": {}}
                try:
                    grid = module.generate(seed, sample_index, difficulty=band)
                    features = input_features(grid)
                    check = check_input(module, grid)
                    expected = python_outline_mirror(grid)
                    scores = score_rivals(rivals, grid, expected)
                except Exception as exc:
                    errors.append({"recipe": recipe, "error": f"{type(exc).__name__}: {exc}"})
                    continue
                counts["generated"] += 1
                counts["self_check_" + check["status"]] += 1
                objects[str(features["n_components"])] += 1
                palettes[str(features["n_distinct_colors_including_background"])] += 1
                dimensions[f"{features['grid_h']}x{features['grid_w']}"] += 1
                boxes.update(f"{h}x{w}" for h, w in features["bbox_sizes"])
                entry = {"recipe": recipe, "input": grid, "input_sha256": digest(grid),
                         "python_mirror_output": expected, "features": features, "self_check": check}
                newly_witnessed = False
                for feature in (*REQUIRED_COVERAGE, "edge_touch", "identity"):
                    if features[feature]:
                        counts[feature] += 1
                        if feature not in witnesses:
                            witnesses[feature] = entry
                            newly_witnessed = True
                for name, result in scores.items():
                    rival_counts[name][result["status"]] += 1
                    if result["status"] == "refuted" and name not in rival_witnesses:
                        rival_witnesses[name] = {**entry, "rival_prediction": result["prediction"]}
                        newly_witnessed = True
                    if result["status"] == "error":
                        errors.append({"recipe": recipe, "rival": name, "error": result["error"]})
                if check["status"] != "passed" or features["bbox_overlap_pairs"]:
                    errors.append(entry)
                if newly_witnessed and digest(grid) not in selected_hashes:
                    selected_generated.append({"kind": "generated", **entry})
                    selected_hashes.add(digest(grid))
        report["generated"][band] = {"counts": dict(counts), "n_components": dict(objects),
                                     "n_distinct_colors_including_background": dict(palettes),
                                     "bbox_sizes": dict(boxes), "grid_dimensions": dict(dimensions),
                                     "rival_counts_against_python_mirror": {name: dict(value) for name, value in rival_counts.items()},
                                     "coverage_witnesses": witnesses, "rival_witnesses_against_python_mirror": rival_witnesses,
                                     "errors": errors}
        if errors:
            report["issues"].append({"kind": "generated_errors", "difficulty": band, "count": len(errors)})
        for feature in REQUIRED_COVERAGE:
            if counts[feature] == 0:
                report["issues"].append({"kind": "missing_generated_coverage", "difficulty": band, "feature": feature})
    report["racket"] = {"executed": False, "status": "not_requested"}
    if args.racket:
        from arcpuzzles.catalog import Catalog

        remaining = 64 - len(authority_inputs)
        if remaining < 0:
            raise ValueError("Canonical and hand-made population exceeds the public 64-input apply limit")
        chosen = selected_generated[:min(args.racket_generated_limit, remaining)]
        authority_inputs.extend(chosen)
        try:
            raw = Catalog(ROOT).apply(TASK_ID, [item["input"] for item in authority_inputs], timeout=180)
        except Exception as exc:
            report["racket"] = {"executed": None, "status": "error",
                                 "error": f"{type(exc).__name__}: {exc}",
                                 "process_receipt": getattr(exc, "run", None),
                                 "requested_inputs": authority_inputs}
            report["issues"].append({"kind": "racket_execution_error", "error": report["racket"]["error"]})
            report["status"] = "issues_found"
            return report
        scored = []
        for context, result in zip(authority_inputs, raw["results"], strict=True):
            output = result["output"]
            entry = {"context": context, "authority_result": result,
                     "python_mirror_matches_racket": output == python_outline_mirror(context["input"]),
                     "rival_scores_against_racket": score_rivals(rivals, context["input"], output) if output is not None else {}}
            scored.append(entry)
            if output is None or not entry["python_mirror_matches_racket"]:
                report["issues"].append({"kind": "racket_mirror_mismatch_or_error", "context": context,
                                         "authority_result": result})
            if context["kind"] == "canonical" and output != context["retained_output"]:
                report["issues"].append({"kind": "racket_canonical_disagreement", "identity": context["identity"]})
            for name, score in entry["rival_scores_against_racket"].items():
                if score["status"] == "error":
                    report["issues"].append({"kind": "racket_rival_error", "rival": name,
                                             "context": context, "error": score["error"]})
        source_matches = raw["generator_sha256"] == source_sha
        if not source_matches or not raw["rule_hash_matches_catalog"]:
            report["issues"].append({"kind": "racket_source_binding_mismatch"})
        report["racket"] = {"executed": True, "generator_matches_census": source_matches,
                             "selected_generated_available": len(selected_generated),
                             "selected_generated_checked": len(chosen),
                             "selection_policy": "First distinct examples that witness an uncovered feature or refute a named rival in each band, bounded by --racket-generated-limit and the public 64-input apply limit",
                             "raw_apply": raw, "scored": scored}
    report["status"] = "issues_found" if report["issues"] else "passed_finite_probe"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--sample-start", type=int, default=0)
    parser.add_argument("--sample-count", type=int, default=24)
    parser.add_argument("--band", action="append", choices=("easy", "medium", "hard"), dest="bands")
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--racket-generated-limit", type=int, default=24)
    parser.add_argument("--require-coverage", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seed_count <= 0 or args.sample_count <= 0 or not 1 <= args.racket_generated_limit <= 53:
        parser.error("Counts must be positive; --racket-generated-limit must be 1..53")
    args.bands = args.bands or ["easy", "medium", "hard"]
    if args.out.exists():
        parser.error("--out must be a new path; preserve failed iterations")
    report = run_probe(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "generator_sha256": report["source"]["generator_sha256"],
                      "canonical_pairs": len(report["canonical"]), "issues": report["issues"],
                      "generated_counts": {band: row["counts"] for band, row in report["generated"].items()},
                      "racket_executed": report["racket"]["executed"]}, indent=2))
    return 1 if args.require_coverage and report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
