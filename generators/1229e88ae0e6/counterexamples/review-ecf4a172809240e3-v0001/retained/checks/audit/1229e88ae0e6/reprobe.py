"""Bounded, source-bound findings-only centering audit; Racket supplies labels.

Run through packet review.py run, or use run_audit.py for recorded commands.
The census oracle is an independent diagnostic Python implementation only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "1229e88ae0e6"
OUT = Path(__file__).resolve().parent
ROOT = find_root(Path(__file__).resolve().parents[3] / "repo")
BANDS = ("easy", "medium", "hard")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


def facts(grid):
    cells = [(r, c, v) for r, row in enumerate(grid)
             for c, v in enumerate(row) if v]
    r0 = min(r for r, _, _ in cells)
    r1 = max(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    c1 = max(c for _, c, _ in cells)
    return len(grid), len(grid[0]), r0, c0, r1-r0+1, c1-c0+1, cells


def paste(grid, top, left):
    h, w, r0, c0, _, _, cells = facts(grid)
    out = [[0]*w for _ in range(h)]
    for r, c, value in cells:
        rr, cc = top+r-r0, left+c-c0
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = value
    return out


def specification(grid):
    h, w, _, _, bh, bw, _ = facts(grid)
    return paste(grid, (h-bh)//2, (w-bw)//2)


def line_sort(grid, axis, reverse):
    out = specification(grid)
    h, w = len(out), len(out[0])
    for line in range(h if axis == "row" else w):
        positions = ([(line, c) for c in range(w)] if axis == "row"
                     else [(r, line) for r in range(h)])
        occupied = [(r, c) for r, c in positions if out[r][c]]
        values = sorted((out[r][c] for r, c in occupied), reverse=reverse)
        for (r, c), value in zip(occupied, values):
            out[r][c] = value
    return out


def centroid(grid, rounding):
    h, w, r0, c0, _, _, cells = facts(grid)
    dr = rounding(Fraction(h-1, 2) - Fraction(sum(r for r, _, _ in cells), len(cells)))
    dc = rounding(Fraction(w-1, 2) - Fraction(sum(c for _, c, _ in cells), len(cells)))
    return paste(grid, r0+dr, c0+dc)


def assumed_bbox(grid, bh, bw):
    h, w, *_ = facts(grid)
    return paste(grid, (h-bh)//2, (w-bw)//2)


def rounded_bbox(grid):
    h, w, _, _, bh, bw, _ = facts(grid)
    return paste(grid, round(Fraction(h-bh, 2)), round(Fraction(w-bw, 2)))


def per_color(grid):
    h, w, _, _, _, _, cells = facts(grid)
    out = [[0]*w for _ in range(h)]
    for color in sorted({v for _, _, v in cells}):
        body = [(r, c) for r, c, v in cells if v == color]
        r0, c0 = min(r for r, _ in body), min(c for _, c in body)
        bh = max(r for r, _ in body)-r0+1
        bw = max(c for _, c in body)-c0+1
        for r, c in body:
            out[(h-bh)//2+r-r0][(w-bw)//2+c-c0] = color
    return out


def candidates(module):
    rivals = {
        "sort_colors_within_rows_ascending": lambda g: line_sort(g, "row", False),
        "sort_colors_within_rows_descending": lambda g: line_sort(g, "row", True),
        "sort_colors_within_columns_ascending": lambda g: line_sort(g, "column", False),
        "sort_colors_within_columns_descending": lambda g: line_sort(g, "column", True),
        "centroid_nearest_integer_ties_even": lambda g: centroid(g, round),
        "centroid_floor_integer": lambda g: centroid(g, math.floor),
        "centroid_ceil_integer": lambda g: centroid(g, math.ceil),
        "bbox_center_nearest_integer_ties_even": rounded_bbox,
        "assume_2_by_2_bbox": lambda g: assumed_bbox(g, 2, 2),
        "assume_3_by_3_bbox": lambda g: assumed_bbox(g, 3, 3),
        "center_each_color_separately": per_color,
    }
    rivals.update({"declared:"+name: fn for name, fn in module.SEMANTIC_RIVALS.items()})
    return rivals


def binding(module, source, source_sha):
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    rows = []
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append((line, row))
    assert len(rows) == 1, "Audit requires one canonical rule authority"
    raw, row = rows[0]
    return {
        "task_id": TASK,
        "generator_source": str(source.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "generator_version": module.VERSION,
        "generator_declared_rule_hash": module.RULE_HASH,
        "canonical_row_sha256_without_newline": hashlib.sha256(raw.encode()).hexdigest(),
        "canonical_rule_text_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "canonical_ledger_sha256": digest(ledger),
        "canonical_rule_text": row["program_solution"],
        "reprobe_sha256": digest(__file__),
    }


def scan():
    module, source, source_sha = load_selected_generator(TASK, root=ROOT)
    rivals = candidates(module)
    stats = {name: {"demo_survivals": 0, "harmful_query_disagreements": 0,
                   "per_band_harmful": {band: 0 for band in BANDS},
                   "first_harmful": None} for name in rivals}
    failures = []
    summary = {}
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    for pair in canonical:
        if (specification(pair["input"]) != pair["output"] or
                module.self_check(pair["input"]) or
                module.strict_canonical_like(pair["input"])):
            failures.append({"check": "canonical_pair", "pair": pair})
    first_witnesses = {}
    representative = []
    for band in BANDS:
        zones, canvases, bboxes, counts = Counter(), Counter(), Counter(), Counter()
        for seed in range(20):
            grids = [module.generate(seed, index, difficulty=band) for index in range(5)]
            outputs = [specification(grid) for grid in grids]
            pairs = [{"input": g, "output": y} for g, y in zip(grids, outputs)]
            for index, grid in enumerate(grids):
                errors = module.self_check(grid, difficulty=band)
                strict = module.strict_canonical_like(grid)
                if errors or strict or module.rule_mirror(grid) != outputs[index]:
                    failures.append({"check": "draw", "band": band, "seed": seed,
                                     "index": index, "self_check": errors, "strict": strict})
                h, w, _, _, bh, bw, cells = facts(grid)
                zones[module.observe_overrides(grid)["source_zone"]] += 1
                canvases[f"{h}x{w}"] += 1
                bboxes[f"{bh}x{bw}"] += 1
                counts[str(len(cells))] += 1
            lesson_errors = module.lesson_identifiable(pairs[:4], pairs[4])
            if lesson_errors:
                failures.append({"check": "lesson_gate", "band": band, "seed": seed,
                                 "errors": lesson_errors})
            for name, rival in rivals.items():
                agreements = [rival(g) == y for g, y in zip(grids, outputs)]
                if all(agreements[:4]):
                    stats[name]["demo_survivals"] += 1
                    if not agreements[4]:
                        stats[name]["harmful_query_disagreements"] += 1
                        stats[name]["per_band_harmful"][band] += 1
                        if stats[name]["first_harmful"] is None:
                            witness = {"band": band, "seed": seed,
                                       "sample_indices": list(range(5)),
                                       "rival": name, "agreement_signature": agreements,
                                       "lesson_identifiable_errors": lesson_errors}
                            stats[name]["first_harmful"] = witness
                            first_witnesses[name] = {**witness, "pairs": pairs,
                                "rival_outputs": [rival(grid) for grid in grids]}
            if not representative:
                representative = grids[:4]
        summary[band] = {"draws": 100, "episodes": 20, "source_zones": dict(zones),
                         "canvases": dict(canvases), "bbox_shapes": dict(bboxes),
                         "cell_counts": dict(counts)}
    preference = ["sort_colors_within_rows_ascending",
                  "sort_colors_within_columns_ascending",
                  "sort_colors_within_rows_descending",
                  "sort_colors_within_columns_descending",
                  "centroid_nearest_integer_ties_even"]
    preferred = next((name for name in preference if name in first_witnesses), None)
    if preferred is None and first_witnesses:
        preferred = next(iter(first_witnesses))
    chosen = first_witnesses.get(preferred)
    if chosen:
        inputs = [pair["input"] for pair in chosen["pairs"]]
        inputs += [pair["input"] for pair in canonical[:3]]
        input_roles = [f"witness:sample_index={i}" for i in range(5)]
        input_roles += [f"canonical:{p['split']}:{p['pair_index']}" for p in canonical[:3]]
    else:
        inputs = [pair["input"] for pair in canonical] + representative
        input_roles = [f"canonical:{p['split']}:{p['pair_index']}" for p in canonical]
        input_roles += [f"generated:easy:seed=0:index={i}" for i in range(len(representative))]
    result = {"schema": "centering-bounded-adversarial-audit-v1",
              "binding": binding(module, source, source_sha),
              "diagnostic_oracle": "independent_python_coordinate_specification_not_Racket",
              "generation_recipe": {"bands": list(BANDS), "seeds": list(range(20)),
                                    "sample_indices": list(range(5)), "overrides": {}},
              "total_draws": 300, "total_episodes": 60,
              "canonical_pairs_checked": len(canonical), "per_band": summary,
              "rivals": stats, "diagnostic_failures": failures,
              "chosen_witness": chosen, "racket_input_roles": input_roles,
              "source_unchanged_after_probe": digest(source) == source_sha}
    write("census.json", result)
    write("input.json", {"inputs": inputs})
    print(json.dumps({"draws": 300, "episodes": 60, "diagnostic_failures": failures,
                      "harmful_rivals": {name: row for name, row in stats.items()
                                         if row["harmful_query_disagreements"]},
                      "chosen_witness": preferred}, indent=2))
    return int(bool(failures) or not result["source_unchanged_after_probe"])


def verify():
    module, source, source_sha = load_selected_generator(TASK, root=ROOT)
    scan_result = json.loads((OUT / "census.json").read_text())
    racket = json.loads((OUT / "racket.json").read_text())
    expected_inputs = json.loads((OUT / "input.json").read_text())["inputs"]
    errors = []
    if source_sha != scan_result["binding"]["generator_sha256"]:
        errors.append("source changed since census")
    canonical_now = binding(module, source, source_sha)
    normalized_rule_hash = hashlib.sha256(" ".join(
        canonical_now["canonical_rule_text"].split()).encode()).hexdigest()[:12]
    if (racket["generator_sha256"] != source_sha or
            not racket["rule_hash_matches_catalog"] or
            racket["executed_rule_hash"] != module.RULE_HASH or
            racket["executed_rule_hash"] != normalized_rule_hash or
            canonical_now["canonical_rule_text_sha256"] !=
            scan_result["binding"]["canonical_rule_text_sha256"]):
        errors.append("Racket authority/source hash binding mismatch")
    for index, row in enumerate(racket["results"]):
        if (row["input"] != expected_inputs[index] or row.get("error") or
                row["output"] != specification(row["input"])):
            errors.append(f"Racket result {index} failed input/parity check")
    chosen = scan_result["chosen_witness"]
    confirmation = None
    if chosen:
        pairs = [{"input": row["input"], "output": row["output"]}
                 for row in racket["results"][:5]]
        rival = candidates(module)[chosen["rival"]]
        agreement = [rival(pair["input"]) == pair["output"] for pair in pairs]
        lesson_errors = module.lesson_identifiable(pairs[:4], pairs[4])
        confirmation = {"band": chosen["band"], "seed": chosen["seed"],
                        "sample_indices": chosen["sample_indices"], "rival": chosen["rival"],
                        "Racket_agreement_signature": agreement,
                        "Racket_labeled_lesson_identifiable_errors": lesson_errors,
                        "query_correct_output": pairs[4]["output"],
                        "query_rival_output": rival(pairs[4]["input"])}
        if agreement != [True, True, True, True, False] or lesson_errors:
            errors.append("Chosen teaching shortcut was not confirmed on Racket labels")
    result = {"schema": "centering-audit-Racket-confirmation-v1",
              "source_sha256": source_sha, "rule_hash": racket["executed_rule_hash"],
              "executed_callable_sha256": racket["rule_text_sha256"],
              "canonical_rule_text_sha256": canonical_now["canonical_rule_text_sha256"],
              "hash_contract": "apply.rule_text_sha256 hashes the executable callable; "
                               "canonical program_solution has its own exact-text SHA-256. "
                               "src/arcpuzzles/worker.py:174-176 records both contracts.",
              "racket_inputs_checked": len(racket["results"]),
              "confirmation": confirmation, "errors": errors,
              "evidence_hashes": {name: digest(OUT / name)
                                  for name in ("census.json", "input.json", "racket.json", "reprobe.py")}}
    write("confirmation.json", result)
    print(json.dumps(result, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("scan", "verify"))
    args = parser.parse_args()
    raise SystemExit(scan() if args.mode == "scan" else verify())
