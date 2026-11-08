#!/usr/bin/env python3
"""Finite authoring probe; run through WORK/run_with_racket.py.

This checks raw consecutive draws, not runner acceptance/rejection behavior.
Use the public lesson census separately for materialized lesson evidence.
Only failing cases and first rival counterexamples retain complete grids.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path

TASK_ID = "d65b2dd82d74"
BANDS = ("easy", "medium", "hard")
NAMESPACES = ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def parse_bars(grid):
    """Independent row-major same-color 4CC extraction and bar eligibility."""
    h, w = len(grid), len(grid[0])
    seen, bars = set(), []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            queue, cells = deque([(r, c)]), []
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows, cols = zip(*cells)
            r1, r2 = min(rows), max(rows)
            if min(cols) == max(cols) and len(cells) == r2 - r1 + 1 and len(cells) >= 2:
                bars.append((color, r1, r2, min(cols)))
    return bars


def independent_oracle(grid):
    """Mirror the published authority; never call generator-private helpers."""
    groups = defaultdict(list)
    for color, r1, r2, c in parse_bars(grid):
        groups[(color, r1, r2)].append(c)
    out = deepcopy(grid)
    for (color, r1, r2), cols in groups.items():
        cols.sort()
        for i in range(0, len(cols) - 1, 2):
            for r in range(r1, r2 + 1):
                for c in range(cols[i], cols[i + 1] + 1):
                    out[r][c] = color
    return out


def features(grid):
    groups, spans = defaultdict(list), defaultdict(set)
    for color, r1, r2, c in parse_bars(grid):
        groups[(color, r1, r2)].append(c)
        spans[color].add((r1, r2))
    counts = [len(cols) for cols in groups.values()]
    return {
        "colors": sorted({v for row in grid for v in row if v}),
        "n_pairs": sum(n // 2 for n in counts),
        "n_bars": sum(counts),
        "key_multiplicities": sorted(counts),
        "even_ge4": any(n >= 4 and n % 2 == 0 for n in counts),
        "odd_ge3": any(n >= 3 and n % 2 == 1 for n in counts),
        "mismatched_spans": any(len(s) > 1 for s in spans.values()),
        "shape": [len(grid), len(grid[0])],
    }


def hook_reasons(value):
    if value is True:
        return []
    if value is False:
        return ["hook returned False"]
    if isinstance(value, (list, tuple)) and all(isinstance(x, str) for x in value):
        return list(value)
    raise TypeError(f"invalid hook result: {value!r}")


def window_checks(records, predictions, names):
    """Every six-draw window, every single-query holdout, all named rivals."""
    result = {"enabled": True, "window_size": 6, "windows": 0, "holdouts": 0,
              "rival_holdouts": 0, "ambiguities": 0, "scoring_errors": 0,
              "per_rival": {name: {"refuted": 0, "survived_all": 0,
                                    "ambiguous": 0, "errors": 0} for name in names},
              "first_ambiguity": {}}
    for band in BANDS:
        band_indices = [i for i, row in enumerate(records) if row["meta"].get("band") == band]
        for start in range(max(0, len(band_indices) - 5)):
            ids = band_indices[start:start + 6]
            result["windows"] += 1
            for q in range(6):
                result["holdouts"] += 1
                demo_ids = [i for j, i in enumerate(ids) if j != q]
                qi = ids[q]
                for name in names:
                    result["rival_holdouts"] += 1
                    pred = predictions[name]
                    counts = result["per_rival"][name]
                    if any(pred[i] is None for i in ids):
                        counts["errors"] += 1
                        result["scoring_errors"] += 1
                    elif any(pred[i] != records[i]["output"] for i in demo_ids):
                        counts["refuted"] += 1
                    elif pred[qi] == records[qi]["output"]:
                        counts["survived_all"] += 1
                    else:
                        counts["ambiguous"] += 1
                        result["ambiguities"] += 1
                        if name not in result["first_ambiguity"]:
                            result["first_ambiguity"][name] = {
                                "band": band, "start": start, "query_position": q,
                                "demo_positions": [j for j in range(6) if j != q],
                                "lesson": [records[i] for i in ids],
                                "rival_query_output": pred[qi],
                            }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New compact JSON report path")
    parser.add_argument("--per-band", type=int, default=60, help="Consecutive raw draws per band (default: 60)")
    parser.add_argument("--seed", type=int, default=17, help="Actual generation seed (default: 17)")
    parser.add_argument("--skip-windows", action="store_true", help="Omit exhaustive local six-draw windows")
    args = parser.parse_args(argv)
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    if args.out.exists():
        parser.error("--out must be a new path")

    from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import MAX_APPLY_INPUTS

    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    records = []
    for pair in canonical_pairs(TASK_ID, root=root):
        records.append({"meta": {"population": "canonical", "variant": pair["variant"],
                                  "split": pair["split"], "pair_index": pair["pair_index"]},
                        "input": pair["input"], "canonical_label": pair["output"]})
    n_canonical = len(records)
    for band in BANDS:
        for index in range(args.per_band):
            grid = normalize_grid(gen.generate(args.seed, index, difficulty=band))
            records.append({"meta": {"population": "generated", "seed": args.seed,
                                      "sample_index": index, "band": band}, "input": grid})

    report = {
        "schema": "d65b2dd82d74-local-curriculum-probe-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash, "generator_file": str(source.relative_to(root)),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "settings": {"seed": args.seed, "per_band": args.per_band, "bands": list(BANDS),
                     "overrides": {}, "apply_batch_limit": MAX_APPLY_INPUTS},
        "authority_batches": [], "sample_metadata": [], "band_counts": {},
        "failures": [], "rivals": {},
        "limits": ["Finite raw draws and local windows; not runner accepted-pair coverage.",
                   "Declared rival checks do not prove universal identifiability.",
                   "Canonical and generated labels executed by the selected Racket authority."],
    }
    catalog = Catalog(root)
    rule_identity = None
    for start in range(0, len(records), MAX_APPLY_INPUTS):
        batch = records[start:start + MAX_APPLY_INPUTS]
        applied = catalog.apply(TASK_ID, [r["input"] for r in batch], allow_unapproved=True)
        identity = (applied["executed_rule_hash"], applied["rule_text_sha256"], applied["generator_sha256"])
        if applied["generator_sha256"] != source_hash or not applied["rule_hash_matches_catalog"]:
            raise RuntimeError("Source/rule identity changed or canonical hash does not match catalog")
        if rule_identity is not None and identity != rule_identity:
            raise RuntimeError("Source/rule identity changed between Racket batches")
        rule_identity = identity
        report["authority_batches"].append({"first_record": start, "count": len(batch),
            "executed_rule_hash": identity[0], "rule_text_sha256": identity[1],
            "generator_sha256": identity[2], "rule_file": applied["rule_file"]})
        for row, labelled in zip(batch, applied["results"], strict=True):
            row["output"] = normalize_grid(labelled["output"])
            row["input_sha256"] = grid_hash(row["input"])
            row["output_sha256"] = grid_hash(row["output"])
            if independent_oracle(row["input"]) != row["output"]:
                report["failures"].append({"kind": "independent_oracle_mismatch", "case": row,
                                           "oracle_output": independent_oracle(row["input"])})
            if "canonical_label" in row and row["canonical_label"] != row["output"]:
                report["failures"].append({"kind": "canonical_label_mismatch", "case": row})
    report["executed_rule_hash"], report["rule_text_sha256"], _ = rule_identity

    for band in ("canonical", *BANDS):
        selected = [r for r in records if (r["meta"].get("band") == band or
                    band == "canonical" and r["meta"]["population"] == "canonical")]
        counts = {"pairs": len(selected), "unique_inputs": len({r["input_sha256"] for r in selected}),
                  "colors": Counter(), "n_distinct_colors": Counter(), "n_pairs": Counter(),
                  "shapes": Counter(), "even_ge4": 0, "odd_ge3": 0, "mismatched_spans": 0,
                  "self_check_failures": 0, "strict_acceptances": 0, "strict_rejections": 0}
        for row in selected:
            facts = features(row["input"])
            counts["colors"].update(map(str, facts["colors"]))
            counts["n_distinct_colors"][str(len(facts["colors"]))] += 1
            counts["n_pairs"][str(facts["n_pairs"])] += 1
            counts["shapes"]["x".join(map(str, facts["shape"]))] += 1
            for name in ("even_ge4", "odd_ge3", "mismatched_spans"):
                counts[name] += int(facts[name])
            meta = {**row["meta"], "input_sha256": row["input_sha256"],
                    "output_sha256": row["output_sha256"], "features": facts}
            if callable(getattr(gen, "self_check", None)):
                reasons = hook_reasons(gen.self_check(deepcopy(row["input"]),
                    difficulty=row["meta"].get("band")))
                if reasons:
                    counts["self_check_failures"] += 1
                    report["failures"].append({"kind": "self_check", "reasons": reasons, "case": row})
            if callable(getattr(gen, "strict_canonical_like", None)):
                reasons = hook_reasons(gen.strict_canonical_like(deepcopy(row["input"])))
                meta["strict_reasons"] = reasons
                counts["strict_rejections" if reasons else "strict_acceptances"] += 1
                if band == "canonical" and reasons:
                    report["failures"].append({"kind": "canonical_strict_rejection", "reasons": reasons, "case": row})
            if callable(getattr(gen, "observe_overrides", None)):
                meta["observe_overrides"] = gen.observe_overrides(deepcopy(row["input"]))
            report["sample_metadata"].append(meta)
        report["band_counts"][band] = counts

    predictions = {}
    for namespace in NAMESPACES:
        rivals = getattr(gen, namespace, {})
        if not isinstance(rivals, dict):
            raise TypeError(f"{namespace} must be a dictionary")
        for name, rival in rivals.items():
            if not isinstance(name, str) or not callable(rival):
                raise TypeError(f"invalid {namespace} entry: {name!r}")
            key = f"{namespace}:{name}"
            pred = predictions[key] = []
            stats = {"canonical": {"pairs": n_canonical, "matches": 0, "refutations": 0, "errors": 0},
                     "generated": {band: {"pairs": args.per_band, "matches": 0,
                                            "refutations": 0, "errors": 0} for band in BANDS},
                     "first_counterexample": None, "first_error": None}
            for row in records:
                bucket = (stats["canonical"] if row["meta"]["population"] == "canonical"
                          else stats["generated"][row["meta"]["band"]])
                try:
                    guess = normalize_grid(rival(deepcopy(row["input"])))
                except Exception as exc:
                    pred.append(None)
                    bucket["errors"] += 1
                    if stats["first_error"] is None:
                        stats["first_error"] = {"case": row, "error": f"{type(exc).__name__}: {exc}"}
                    continue
                pred.append(guess)
                agrees = guess == row["output"]
                bucket["matches" if agrees else "refutations"] += 1
                if not agrees and stats["first_counterexample"] is None:
                    stats["first_counterexample"] = {**row, "rival_output": guess,
                        "generator_sha256": source_hash, "executed_rule_hash": rule_identity[0]}
            stats["canonical_fit"] = stats["canonical"]["matches"] == n_canonical
            report["rivals"][key] = stats
    report["windows"] = ({"enabled": False} if args.skip_windows else
                          window_checks(records, predictions, list(predictions)))
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Generator source changed during probe")
    errors = sum(s["canonical"]["errors"] + sum(b["errors"] for b in s["generated"].values())
                 for s in report["rivals"].values())
    report["summary"] = {"canonical_pairs": n_canonical, "generated_pairs": 3 * args.per_band,
        "total_pairs": len(records), "unique_inputs": len({r["input_sha256"] for r in records}),
        "oracle_compared_pairs": len(records), "failures": len(report["failures"]),
        "rival_errors": errors, "window_ambiguities": report["windows"].get("ambiguities", 0)}
    report["status"] = "fail" if report["failures"] or errors or report["summary"]["window_ambiguities"] else "pass"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "status": report["status"], **report["summary"]}, sort_keys=True))
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
