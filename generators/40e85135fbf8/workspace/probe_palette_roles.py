#!/usr/bin/env python3
"""Source-bound palette-role and ordered-lesson diagnostic for 40e85135fbf8.

From the packet root:
  python3 run_with_racket.py python3 \
    generators/40e85135fbf8/workspace/probe_palette_roles.py \
    --seed-start 0 --seed-count 32 --sample-start 0 --sample-count 36 \
    --out ../checks/palette-roles-after.json

The wrapper supplies portable imports. This probe itself executes no Racket:
canonical labels come from canonical_pairs; generated labels use the explicitly
identified generator.rule_mirror. Selected witnesses retain inputs for separate
authority execution. Only serialized, ordered lessons are scored; there is no
query-rotation claim. Every declared rival is discovered dynamically, with a
separately named, independent diagnostic for the original ordinal-rank defect.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "40e85135fbf8"
ROOT = find_root(__file__)
BASELINE_DIAGNOSTIC = "DIAGNOSTICS.baseline_ordinal_header_rank"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"))
                          .encode("utf-8")).hexdigest()


def load_generator():
    source = next(path for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ) if path.is_file())
    spec = importlib.util.spec_from_file_location("palette_roles_probe_generator", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def baseline_ordinal_header_rank(grid):
    """Wrong baseline extension, independent of generator rival declarations."""
    rows = [line[0] for line in grid[1:]]
    cols = grid[0][1:]
    row_rank = {color: rank for rank, color in enumerate(sorted(set(rows)))}
    col_rank = {color: rank for rank, color in enumerate(sorted(set(cols)))}
    return [[row if row_rank[row] == col_rank[col] else 0 for col in cols]
            for row in rows]


def header_roles(grid):
    row_colors = {line[0] for line in grid[1:]}
    col_colors = set(grid[0][1:])
    palette = sorted(row_colors | col_colors)
    private = row_colors ^ col_colors
    if not private:
        scene, absent_color, absent_rank = "canonical", None, None
    else:
        if len(private) != 1:
            raise ValueError(f"Expected one absent color; saw {sorted(private)}")
        absent_color = next(iter(private))
        scene = "row_gap" if absent_color in row_colors else "col_gap"
        absent_rank = palette.index(absent_color)
    return {"scene": scene, "palette": palette, "row_colors": sorted(row_colors),
            "col_colors": sorted(col_colors), "absent_color": absent_color,
            "absent_rank": absent_rank}


def declared_rivals(gen):
    result = {}
    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        declarations = getattr(gen, namespace)
        if not isinstance(declarations, dict):
            raise TypeError(f"{namespace} is not a mapping")
        for name, predictor in declarations.items():
            if not callable(predictor):
                raise TypeError(f"{namespace}.{name} is not callable")
            result[f"{namespace}.{name}"] = predictor
    result[BASELINE_DIAGNOSTIC] = baseline_ordinal_header_rank
    return result


def score_rivals(rivals, grid, expected):
    statuses, predictions, errors = {}, {}, {}
    for name, predictor in rivals.items():
        try:
            prediction = predictor(deepcopy(grid))
            statuses[name] = "fit" if prediction == expected else "refuted"
            predictions[name] = prediction
        except Exception as exc:
            statuses[name] = "error"
            errors[name] = f"{type(exc).__name__}: {exc}"
    return statuses, predictions, errors


def rule_bindings(gen):
    path = canonical_path(ROOT)
    bindings = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            program = row["program_solution"]
            normalized = " ".join(program.split())
            full_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            bindings.append({"variant": len(bindings),
                             "program_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(),
                             "normalized_program_sha256": full_hash,
                             "rule_hash": full_hash[:12]})
    return {"canonical_path": str(path.relative_to(ROOT)),
            "generator_rule_pin": gen.RULE_HASH,
            "canonical_rules": bindings,
            "pin_matches_all_canonical_rules": bool(bindings) and all(
                item["rule_hash"] == gen.RULE_HASH for item in bindings)}


def run_probe(*, seed_start, seed_count, sample_start, sample_count, bands):
    gen, source = load_generator()
    lesson_size = gen.EXAMPLES_NEEDED
    if sample_count < lesson_size:
        raise ValueError(f"sample-count must be at least EXAMPLES_NEEDED={lesson_size}")
    seeds = list(range(seed_start, seed_start + seed_count))
    indices = list(range(sample_start, sample_start + sample_count))
    starts = indices[:sample_count - lesson_size + 1]
    rivals = declared_rivals(gen)
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    canonical_scores = {name: Counter() for name in rivals}
    canonical_errors = []
    for pair in canonical:
        statuses, _, errors = score_rivals(rivals, pair["input"], pair["output"])
        for name, status in statuses.items():
            canonical_scores[name][status] += 1
        if errors:
            canonical_errors.append({"variant": pair["variant"], "split": pair["split"],
                                     "pair_index": pair["pair_index"], "errors": errors})

    report = {
        "schema": "40e85135fbf8-palette-role-probe-v1", "task_id": TASK_ID,
        "source": {"generator_path": str(source.relative_to(ROOT)),
                   "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                   "generator_version": gen.VERSION,
                   "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   **rule_bindings(gen)},
        "labels": {"canonical": "canonical_pairs: retained canonical labels",
                   "generated": "generator.rule_mirror: Python mirror, not Racket labels",
                   "racket_executed": False},
        "population": {"difficulty_bands": list(bands),
                       "seed_range": {"start": seed_start, "stop_exclusive": seed_start + seed_count},
                       "seeds": seeds, "sample_indices": indices,
                       "ordered_lesson_size": lesson_size, "lesson_start_indices": starts,
                       "observed_start_residues_mod_9": sorted({index % 9 for index in starts}),
                       "sampling": "direct generate calls, no rejection/materialization",
                       "query": "next sampled input when available; final window has no query",
                       "query_rotations": "not tested; ordered curriculum only"},
        "canonical": {"pair_count": len(canonical), "rival_scores": {
            name: {"fit_count": counts["fit"], "refuted_count": counts["refuted"],
                   "error_count": counts["error"], "fits_all": counts["fit"] == len(canonical)}
            for name, counts in canonical_scores.items()}, "errors": canonical_errors},
        "bands": {}, "selected_witnesses": {},
    }
    all_hashes = set()
    totals = Counter()
    for band in bands:
        scene_counts, palette_counts, absent_counts = Counter(), Counter(), {
            "row_gap": Counter(), "col_gap": Counter()}
        color_counts, fingerprints = Counter(), set()
        by_scene = {scene: set() for scene in ("canonical", "row_gap", "col_gap")}
        rival_grid_scores = {name: Counter() for name in rivals}
        rival_lesson_scores = {name: Counter() for name in rivals}
        records, lessons, errors = [], [], []
        failed_nonmax_windows, hook_warnings = [], []
        for seed in seeds:
            sampled = []
            for index in indices:
                grid = gen.generate(seed, index, difficulty=band)
                expected = gen.rule_mirror(grid)
                roles = header_roles(grid)
                observed = gen.observe_overrides(grid)
                statuses, predictions, rival_errors = score_rivals(rivals, grid, expected)
                identity = {"difficulty": band, "seed": seed, "sample_index": index,
                            "input_sha256": digest(grid)}
                record = {**identity, **roles, "observed_axes": observed,
                          "rival_statuses": statuses}
                records.append(record)
                sampled.append({"record": record, "input": grid, "output": expected})
                fingerprints.add(identity["input_sha256"])
                all_hashes.add(identity["input_sha256"])
                by_scene[roles["scene"]].add(identity["input_sha256"])
                scene_counts[roles["scene"]] += 1
                palette_counts[observed["palette_kind"]] += 1
                color_counts.update(roles["palette"])
                rank = roles["absent_rank"]
                if rank is not None:
                    absent_counts[roles["scene"]][str(rank)] += 1
                    key = f"{roles['scene']}:absent_rank_{rank}"
                    report["selected_witnesses"].setdefault(key, {
                        **identity, **roles, "input": grid, "python_mirror_output": expected,
                        "baseline_ordinal_prediction": predictions.get(BASELINE_DIAGNOSTIC)})
                for name, status in statuses.items():
                    rival_grid_scores[name][status] += 1
                if rival_errors:
                    errors.append({**identity, "rival_errors": rival_errors})

            for offset, start in enumerate(starts):
                demos = sampled[offset:offset + lesson_size]
                query = sampled[offset + lesson_size] if offset + lesson_size < len(sampled) else None
                identity = {"difficulty": band, "seed": seed, "start_index": start,
                            "demo_indices": [pair["record"]["sample_index"] for pair in demos],
                            "query_index": query["record"]["sample_index"] if query else None}
                nonmax_axes = sorted({pair["record"]["scene"] for pair in demos
                                      if pair["record"]["absent_rank"] is not None and
                                      pair["record"]["absent_rank"] < len(pair["record"]["palette"]) - 1})
                if nonmax_axes != ["col_gap", "row_gap"]:
                    failed_nonmax_windows.append({**identity, "nonmax_gap_axes": nonmax_axes})
                hook_reasons = gen.lesson_identifiable(
                    [{"input": pair["input"], "output": pair["output"]} for pair in demos],
                    {"input": query["input"], "output": query["output"]} if query else None)
                if hook_reasons:
                    hook_warnings.append({**identity, "reasons": hook_reasons})
                statuses = {}
                for name in rivals:
                    demo_scores = [pair["record"]["rival_statuses"][name] for pair in demos]
                    if "error" in demo_scores:
                        status = "error"
                    elif "refuted" in demo_scores:
                        status = "refuted_on_demos"
                    elif query is None:
                        status = "survived_demos_no_query"
                    else:
                        status = {"fit": "survived_all", "refuted": "ambiguous_query",
                                  "error": "error"}[query["record"]["rival_statuses"][name]]
                    statuses[name] = status
                    rival_lesson_scores[name][status] += 1
                lessons.append({**identity, "nonmax_gap_axes": nonmax_axes,
                                "rival_statuses": statuses})

        stats = {"input_count": len(records), "distinct_input_count": len(fingerprints),
                 "distinct_input_counts_by_scene": {name: len(values) for name, values in by_scene.items()},
                 "scene_counts": dict(scene_counts), "palette_kind_counts": dict(palette_counts),
                 "header_color_presence_counts": dict(sorted(color_counts.items())),
                 "absence_rank_counts_by_scene": {name: dict(sorted(counts.items()))
                                                   for name, counts in absent_counts.items()},
                 "rival_grid_scores": {name: dict(counts) for name, counts in rival_grid_scores.items()},
                 "rival_ordered_lesson_scores": {name: dict(counts) for name, counts in rival_lesson_scores.items()},
                 "ordered_lesson_count": len(lessons), "failed_nonmax_windows": failed_nonmax_windows,
                 "hook_warnings": hook_warnings, "rival_errors": errors,
                 "input_records": records, "ordered_lessons": lessons}
        report["bands"][band] = stats
        totals.update({"input_count": len(records), "ordered_lesson_count": len(lessons),
                       "failed_nonmax_windows": len(failed_nonmax_windows),
                       "hook_warnings": len(hook_warnings), "rival_errors": len(errors),
                       "ambiguous_rival_queries": sum(counts["ambiguous_query"]
                                                      for counts in rival_lesson_scores.values()),
                       "baseline_diagnostic_surviving_lessons": sum(
                           count for status, count in rival_lesson_scores[BASELINE_DIAGNOSTIC].items()
                           if status in ("survived_all", "survived_demos_no_query", "ambiguous_query"))})
    report["totals"] = {**dict(totals), "distinct_input_count": len(all_hashes)}
    report["status"] = "findings" if (
        totals["failed_nonmax_windows"] or totals["hook_warnings"] or totals["rival_errors"]
        or totals["ambiguous_rival_queries"] or canonical_errors
        or not report["source"]["pin_matches_all_canonical_rules"]
    ) else "no_findings_in_sample"
    return report


def positive_int(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=positive_int, default=32)
    parser.add_argument("--sample-start", type=int, default=0)
    parser.add_argument("--sample-count", type=positive_int, default=36)
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"),
                        default=("easy", "medium", "hard"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}; use a new evidence path")
    report = run_probe(seed_start=args.seed_start, seed_count=args.seed_count,
                       sample_start=args.sample_start, sample_count=args.sample_count,
                       bands=tuple(dict.fromkeys(args.bands)))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "generator_sha256": report["source"]["generator_sha256"],
                      "totals": report["totals"]}, sort_keys=True))
    return 1 if report["status"] == "findings" else 0


if __name__ == "__main__":
    raise SystemExit(main())
