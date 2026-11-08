"""Bounded independent shortcut probe; run via WORK/run_with_racket.py.

Uses selected task canonical pairs and public Catalog.apply. Retained grids are
authoring evidence. Counts concern the explicit finite draw set, not production
episode materialization or universal identifiability.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, normalize_grid

TASK = "1ee7274bdbb0"
# These independent hypotheses are additional probes, not a copied list of
# generator declarations. Actual declarations are discovered at run time below.
INDEPENDENT_RIVALS = ("center_marker_only", "exactly_one_marker", "alternate_from_first",
                      "single_marker_center_only", "marker_pivot", "motif_bbox_cw",
                      "connected_only", "disconnected_only")


def declared_rules(generator):
    found, errors = {}, []
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        rules = getattr(generator, namespace, {})
        if not isinstance(rules, dict):
            errors.append(f"{namespace}: expected named-callable dictionary")
            continue
        for name, fn in rules.items():
            if isinstance(name, str) and callable(fn):
                found[f"{namespace}:{name}"] = fn
            else:
                errors.append(f"{namespace}:{name}: invalid declaration")
    return found, errors


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def inspect(grid):
    height, width = len(grid), len(grid[0])
    rd = [r for r in range(height) if all(v == 9 for v in grid[r])]
    cd = [c for c in range(width) if all(row[c] == 9 for row in grid)]
    rows, cols = [-1, *rd, height], [-1, *cd, width]
    tiles = []
    for row, (ra, rb) in enumerate(zip(rows, rows[1:])):
        for col, (ca, cb) in enumerate(zip(cols, cols[1:])):
            motif = {(r-ra-1, c-ca-1) for r in range(ra+1, rb) for c in range(ca+1, cb) if grid[r][c] == 2}
            markers = {(r-ra-1, c-ca-1) for r in range(ra+1, rb) for c in range(ca+1, cb) if grid[r][c] == 3}
            reached = {min(motif)} if motif else set()
            frontier = list(reached)
            for r, c in frontier:
                for point in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                    if point in motif and point not in reached:
                        reached.add(point)
                        frontier.append(point)
            tiles.append(dict(row=row, col=col, r0=ra+1, c0=ca+1, size=rb-ra-1,
                              motif=motif, markers=markers, connected=reached == motif))
    return tiles


def predict(grid, rule="intended"):
    tiles = inspect(grid)
    output = [[9 if v == 9 else 0 for v in row] for row in grid]
    for index, tile in enumerate(tiles):
        cells, markers, size = tile["motif"], tile["markers"], tile["size"]
        turn = bool(markers)
        if rule == "center_marker_only":
            centers = {(size-1)//2, size//2}
            turn = any(r in centers and c in centers for r, c in markers)
        elif rule == "single_marker_center_only":
            centers = {(size-1)//2, size//2}
            turn = len(markers) > 1 or any(r in centers and c in centers for r, c in markers)
        elif rule == "exactly_one_marker":
            turn = len(markers) == 1
        elif rule == "alternate_from_first":
            turn = bool(tiles[0]["markers"]) != bool(index % 2)
        elif rule in ("connected_only", "disconnected_only"):
            turn = tile["connected"] == (rule == "connected_only")
        if turn:
            if rule == "marker_pivot":
                pr, pc = min(markers)
                cells = {(pr+c-pc, pc-r+pr) for r, c in cells}
            elif rule == "motif_bbox_cw":
                r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
                r1 = max(r for r, _ in cells)
                cells = {(r0+c-c0, c0+r1-r) for r, c in cells}
            else:
                cells = {(c, size-1-r) for r, c in cells}
        for r, c in cells:
            if 0 <= r < size and 0 <= c < size:
                output[tile["r0"]+r][tile["c0"]+c] = 8
    return output


def features(grid):
    return [{key: (sorted(value) if isinstance(value, set) else value)
             for key, value in tile.items()} for tile in inspect(grid)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20261007)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source = Path(__file__).resolve().parent.parent / "generator.py"
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    (args.out / "generator_snapshot.py").write_bytes(source_bytes)
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    declarations, declaration_errors = declared_rules(gen)
    canonical = canonical_pairs(TASK, root=root)
    cases = [dict(kind="canonical", **pair) for pair in canonical]
    handmade = [row[:] for row in canonical[0]["input"]]
    handmade[1][5], handmade[1][9] = 3, 0
    cases.append(dict(kind="handmade_first_two_marked", input=handmade))
    errors = [{"kind": "declaration_error", "error": e} for e in declaration_errors]
    for band in ("easy", "medium", "hard"):
        for index in range(args.per_band):
            try:
                grid = gen.generate(args.seed, index, difficulty=band)
                cases.append(dict(kind="generated", difficulty=band, seed=args.seed,
                                  sample_index=index, input=grid, self_check=gen.self_check(grid)))
            except Exception as exc:
                errors.append(dict(difficulty=band, seed=args.seed, sample_index=index,
                                   error=f"{type(exc).__name__}: {exc}"))
    receipts, applied = [], []
    for start in range(0, len(cases), 64):
        receipt = Catalog(root).apply(TASK, [c["input"] for c in cases[start:start+64]], timeout=180)
        receipts.append(receipt)
        applied.extend(receipt["results"])
        if receipt["generator_sha256"] != source_hash:
            errors.append(dict(kind="source_mismatch", expected=source_hash,
                               observed=receipt["generator_sha256"]))
    if source.read_bytes() != source_bytes:
        errors.append(dict(kind="source_changed_during_probe"))
    summary = {band: {"draws": 0, "refuted": Counter(), "count_flag_conflicts": 0,
                      "declared_rival_statuses": {name: Counter() for name in declarations},
                      "connectivity_flag_conflicts": 0, "first_two_same_flag": 0,
                      "first_disconnected": 0, "second_connected": 0}
               for band in ("easy", "medium", "hard")}
    witnesses = {}
    for case, result in zip(cases, applied, strict=True):
        official = result["output"]
        if official is None:
            raise RuntimeError(f"Reference execution failed: {result}")
        case["stored_label_matches_racket"] = case.get("output", official) == official
        case["output"] = official
        case["independent_rule_matches_racket"] = predict(case["input"]) == official
        case["input_sha256"], case["output_sha256"] = sha(case["input"]), sha(official)
        case["features"] = features(case["input"])
        case["rivals"] = {rival: predict(case["input"], rival) == official for rival in INDEPENDENT_RIVALS}
        case["declared_rivals"] = {}
        for name, fn in declarations.items():
            try:
                prediction = normalize_grid(fn(deepcopy(case["input"])))
                case["declared_rivals"][name] = "fits" if prediction == official else "refuted"
            except Exception as exc:
                case["declared_rivals"][name] = "error"
                errors.append(dict(kind="rival_execution", rival=name,
                                   input_sha256=case["input_sha256"], error=f"{type(exc).__name__}: {exc}"))
        if case["kind"] != "generated":
            continue
        band, tiles = case["difficulty"], inspect(case["input"])
        counters = summary[band]
        counters["draws"] += 1
        for name, status in case["declared_rivals"].items():
            counters["declared_rival_statuses"][name][status] += 1
        for rival, fits in case["rivals"].items():
            if not fits:
                counters["refuted"][rival] += 1
                witnesses.setdefault(rival, dict(case=case, rival_prediction=predict(case["input"], rival)))
        for key, group in (("count_flag_conflicts", lambda t: len(t["motif"])),
                           ("connectivity_flag_conflicts", lambda t: t["connected"])):
            groups = {}
            for tile in tiles:
                groups.setdefault(group(tile), set()).add(bool(tile["markers"]))
            counters[key] += any(len(values) == 2 for values in groups.values())
        counters["first_two_same_flag"] += bool(tiles[0]["markers"]) == bool(tiles[1]["markers"])
        counters["first_disconnected"] += not tiles[0]["connected"]
        counters["second_connected"] += tiles[1]["connected"]
    report = dict(schema="task-local-rival-probe-v1", task_id=TASK, generator_sha256=source_hash,
                  seed=args.seed, per_band=args.per_band, errors=errors,
                  canonical_fit={r: all(c["rivals"][r] for c in cases if c["kind"] == "canonical") for r in INDEPENDENT_RIVALS},
                  declared_canonical_fit={name: Counter(c["declared_rivals"][name] for c in cases if c["kind"] == "canonical")
                                          for name in declarations},
                  per_band_summary=summary, cases=cases, first_generated_witness=witnesses,
                  limits="Finite draws and named rivals only; no production lesson claim. Marker-pivot rival clips outside-tile coordinates; multiple markers use first row-major marker.")
    for filename, value in (("probe.json", report), ("racket_receipts.json", receipts)):
        (args.out / filename).write_text(json.dumps(value, indent=2)+"\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256", "canonical_fit", "per_band_summary", "errors")}, indent=2))


if __name__ == "__main__":
    main()
