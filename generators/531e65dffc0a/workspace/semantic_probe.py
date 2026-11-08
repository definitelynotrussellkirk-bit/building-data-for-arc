"""Independent task-local semantics, witnesses, and source-bound rival census.

Run from repo with PYTHONPATH=shared/runtime. Official labels use only the
packet's run_with_racket.py + public apply CLI, in batches of at most 64.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "531e65dffc0a"
ROOT = find_root(__file__)
PACKET = ROOT.parent


def normalize(cells):
    mr, mc = min(r for r, c in cells), min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def rotate_cells(cells, code):
    cells = normalize(cells)
    h, w = max(r for r, c in cells) + 1, max(c for r, c in cells) + 1
    return sorted({2: lambda r, c: (r, c), 3: lambda r, c: (c, h-1-r),
                   4: lambda r, c: (h-1-r, w-1-c),
                   5: lambda r, c: (w-1-c, r)}[code](r, c) for r, c in cells)


def objects(grid):
    """Monochrome four-connected components in raster discovery order."""
    h, w, seen, result = len(grid), len(grid[0]), set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells, todo = [], [(r, c)]
            seen.add((r, c))
            for a, b in todo:
                cells.append((a, b))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    p = a + dr, b + dc
                    if (0 <= p[0] < h and 0 <= p[1] < w
                            and p not in seen and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        todo.append(p)
            result.append((color, sorted(cells)))
    return result


def decompose(grid):
    candidates = [(color, cells) for color, cells in objects(grid)
                  if color not in (2, 3, 4, 5)]
    if not candidates:
        raise ValueError("no prototype")
    color, cells = max(candidates, key=lambda item: len(item[1]))
    anchors = [(r, c, value) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value in (2, 3, 4, 5)]
    return color, cells, normalize(cells), anchors


def transform(grid, rival="reference"):
    """Independent rule and plausible rival predictions; returns a grid."""
    mapping = None
    if rival.startswith("code_"):
        parts = rival.split("_")
        if len(parts) != 4 or parts[2] != "as":
            raise ValueError(f"invalid mapping rival {rival}")
        mapping = int(parts[1]), int(parts[3])
        if any(code not in (2, 3, 4, 5) for code in mapping) or mapping[0] == mapping[1]:
            raise ValueError(f"invalid mapping rival {rival}")
    if rival not in {"reference", "yellow_identity", "absolute_source_offsets", "shift_stamp_to_fit",
                     "suppress_clipped_stamps", "wrap_edges", "xor_overlap", "erase_source_after_stamping"} and mapping is None:
        raise ValueError(f"no independent implementation for rival {rival}")
    h, w = len(grid), len(grid[0])
    color, source, shape, anchors = decompose(grid)
    out = [[0] * w for _ in range(h)]
    for ar, ac, code in anchors:
        if mapping and code == mapping[0]:
            code = mapping[1]
        rotated = rotate_cells(shape, 2 if rival == "yellow_identity" and code == 4 else code)
        if rival == "absolute_source_offsets":
            sr, sc = min(r for r, c in source), min(c for r, c in source)
            rotated = [(r + sr, c + sc) for r, c in rotated]
        sh, sw = max(r for r, c in rotated) + 1, max(c for r, c in rotated) + 1
        if rival == "shift_stamp_to_fit":
            ar, ac = min(ar, h-sh), min(ac, w-sw)
        placed = [(ar+r, ac+c) for r, c in rotated]
        if rival == "suppress_clipped_stamps" and any(not (0 <= r < h and 0 <= c < w) for r, c in placed):
            continue
        for r, c in placed:
            if rival == "wrap_edges":
                r, c = r % h, c % w
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = (0 if out[r][c] else color) if rival == "xor_overlap" else color
    if rival == "erase_source_after_stamping":
        for r, c in source:
            out[r][c] = 0
    return out


def features(grid):
    h, w = len(grid), len(grid[0])
    color, source, shape, anchors = decompose(grid)
    multiplicity, clipped, empty_corner, yellow_changes = Counter(), 0, 0, 0
    supports = []
    for ar, ac, code in anchors:
        rotated = rotate_cells(shape, code)
        positions = {(ar+r, ac+c) for r, c in rotated}
        visible = {(r, c) for r, c in positions if 0 <= r < h and 0 <= c < w}
        supports.append(visible)
        multiplicity.update(visible)
        clipped += len(visible) != len(shape)
        empty_corner += (0, 0) not in rotated
        yellow_changes += code == 4 and rotate_cells(shape, 4) != shape
    return {"height": h, "width": w, "prototype_color": color,
            "prototype_size": len(shape), "prototype_shape": shape,
            "prototype_origin": [min(r for r, c in source), min(c for r, c in source)],
            "anchor_count": len(anchors), "anchor_codes": [code for r, c, code in anchors],
            "distinct_codes": len({code for r, c, code in anchors}),
            "rotation_orbit": len({tuple(rotate_cells(shape, code)) for code in (2, 3, 4, 5)}),
            "clipped_stamps": clipped, "empty_corner_stamps": empty_corner,
            "informative_yellow_anchors": yellow_changes,
            "overlap_cells": sum(n > 1 for n in multiplicity.values()),
            "source_overlap_cells": len(set(source) & multiplicity.keys()),
            "visible_stamp_cells": len(multiplicity),
            "full_stamp_count": len(anchors) - clipped}


def load_generator(path):
    spec = importlib.util.spec_from_file_location("semantic_target_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def declarations(module):
    """Use generator-owned declarations; no duplicated census rival registry."""
    result = {}
    for category in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        for name, fn in getattr(module, category, {}).items():
            if not callable(fn):
                raise TypeError(f"{category}[{name}] must be callable(grid)")
            result[f"{category}/{name}"] = {"category": category, "predict": fn}
    return result


def canonical_fit_report(module):
    pairs = canonical_pairs(TASK, root=ROOT)
    rivals = declarations(module)
    return {name: {"category": entry["category"], "matched": sum(entry["predict"](p["input"]) == p["output"] for p in pairs),
                   "total": len(pairs),
                   "fits_all_canonical": all(entry["predict"](p["input"]) == p["output"] for p in pairs)} for name, entry in rivals.items()}


def family_summary(rows, windows, rotations, rival_names):
    """Separate six canonical shortcuts, mapping alternatives, and their union."""
    groups = {
        "canonical_shortcuts": [name for name in rival_names if name.startswith("CANONICAL_SHORTCUTS/")],
        "code_mapping": [name for name in rival_names if name.startswith("LESSON_COMPETITORS/code_")],
        "full_lesson_competitors": [name for name in rival_names if name.startswith("LESSON_COMPETITORS/")],
    }
    result = {}
    for family, names in groups.items():
        members = set(names)
        result[family] = {
            "rival_count": len(names),
            "refutation_counts": {name: sum(row.get("rival_refutations", row.get("refutations"))[name] for row in rows) for name in names},
            "all_family_rivals_refuted_cases": sum(bool(names) and all(row.get("rival_refutations", row.get("refutations"))[name] for name in names) for row in rows),
            **{kind: {"window_count": len(items),
                      "windows_with_surviving_rivals": sum(bool(members.intersection(row["surviving_rivals"])) for row in items),
                      "windows_with_query_ambiguity": sum(bool(members.intersection(row["query_ambiguous_rivals"])) for row in items)}
               for kind, items in (("linear", windows), ("cyclic", rotations))}}
    return result


def witnesses():
    def make(h, w, shape, source, anchors):
        g = [[0] * w for _ in range(h)]
        for r, c in shape:
            g[source[0]+r][source[1]+c] = 6
        for r, c, code in anchors:
            g[r][c] = code
        return g
    ell = [(0, 0), (1, 0), (1, 1)]
    return {
        "asymmetric_yellow": make(5, 5, ell, (0, 0), [(3, 3, 4)]),
        "clipped_identity": make(5, 5, ell, (0, 0), [(4, 4, 2)]),
        "overlap_union": make(6, 6, ell, (0, 0), [(2, 2, 2), (3, 3, 2)]),
        "source_footprint_overlap": make(7, 7, [(0, c) for c in range(4)], (3, 3), [(0, 3, 3)]),
        "relocated_prototype": make(6, 6, ell, (1, 0), [(3, 3, 2)]),
        "empty_rotated_corner": make(5, 5, ell, (0, 0), [(3, 3, 5)]),
    }


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=ROOT / f"generators/{TASK}/generator.py")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=["witnesses", "census"], default="witnesses")
    parser.add_argument("--seeds", default="0,1,17")
    parser.add_argument("--indices", type=int, default=64)
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    args = parser.parse_args()
    if not (PACKET / "run_with_racket.py").is_file():
        parser.error("Official-label CLI needs the review packet's run_with_racket.py; this module's transform/features APIs work in portable runtimes.")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source_before = sha(args.generator)
    module = load_generator(args.generator)
    seeds = [int(s) for s in args.seeds.split(",")]
    cases = [{"name": name, "input": grid} for name, grid in witnesses().items()] if args.mode == "witnesses" else [
        {"seed": seed, "sample_index": index, "difficulty": args.difficulty,
         "input": module.generate(seed, index, difficulty=args.difficulty)}
        for seed in seeds for index in range(args.indices)]
    rivals = declarations(module)
    commands, applied = [], []
    for start in range(0, len(cases), 64):
        folder = out / f"batch-{start // 64:03d}"
        folder.mkdir()
        input_file, label_file = folder / "input.json", folder / "racket.json"
        input_file.write_text(json.dumps({"inputs": [c["input"] for c in cases[start:start+64]]}) + "\n")
        cmd = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
               "--input", str(input_file), "--out", str(label_file)]
        commands.append({"cwd": str(PACKET), "argv": cmd})
        run = subprocess.run(cmd, cwd=PACKET, capture_output=True, text=True)
        (folder / "apply.log").write_text(run.stdout + run.stderr)
        if run.returncode:
            raise RuntimeError(f"apply failed: {folder / 'apply.log'}")
        payload = json.loads(label_file.read_text())
        applied.extend(payload["results"])
    rows = []
    for case, label in zip(cases, applied, strict=True):
        if not label["valid_output"]:
            raise RuntimeError(label["error"])
        rows.append({**case, "features": features(case["input"]),
                     "independent_reference_matches": transform(case["input"]) == label["output"],
                     "generator_reference_matches": module._prediction(case["input"]) == label["output"] if hasattr(module, "_prediction") else None,
                     "validator_errors": {name: getattr(module, name)(case["input"]) for name in ("self_check", "strict_canonical_like") if hasattr(module, name)},
                     "independent_rival_parity": {name: entry["predict"](case["input"]) == transform(case["input"], name.split("/", 1)[1]) for name, entry in rivals.items()},
                     "rival_refutations": {name: entry["predict"](case["input"]) != label["output"] for name, entry in rivals.items()}})
    (out / "cases.json").write_text(json.dumps(rows, indent=2) + "\n")
    counts = {key: sum(bool(row["features"][key]) for row in rows) for key in
              ["clipped_stamps", "empty_corner_stamps", "informative_yellow_anchors", "overlap_cells", "source_overlap_cells"]}
    windows, rotations = [], []
    if args.mode == "census":
        for seed in seeds:
            group = [row for row in rows if row["seed"] == seed]
            for start in range(max(0, len(group)-3)):
                demonstrations, query = group[start:start+3], group[start+3]
                survivors = [name for name in rivals if not any(row["rival_refutations"][name] for row in demonstrations)]
                windows.append({"seed": seed, "demo_indices": [row["sample_index"] for row in demonstrations],
                                "query_index": query["sample_index"], "surviving_rivals": survivors,
                                "query_ambiguous_rivals": [name for name in survivors if query["rival_refutations"][name]]})
                four = group[start:start+4]
                for query_offset in range(4):
                    demos = four[query_offset+1:] + four[:query_offset]
                    query = four[query_offset]
                    survivors = [name for name in rivals if not any(row["rival_refutations"][name] for row in demos)]
                    rotations.append({"seed": seed, "window_start": group[start]["sample_index"],
                                      "query_offset": query_offset, "demo_indices": [row["sample_index"] for row in demos],
                                      "query_index": query["sample_index"], "surviving_rivals": survivors,
                                      "query_ambiguous_rivals": [name for name in survivors if query["rival_refutations"][name]]})
        (out / "windows.json").write_text(json.dumps(windows, indent=2) + "\n")
        (out / "rotations.json").write_text(json.dumps(rotations, indent=2) + "\n")
    report = {"task_id": TASK, "mode": args.mode, "generator_path": str(args.generator.resolve()),
              "generator_sha256_before": source_before, "generator_sha256_after": sha(args.generator),
              "probe_sha256": sha(__file__), "canonical_file_sha256": sha(canonical_path(ROOT)),
              "commands": commands, "seeds": seeds if args.mode == "census" else [], "indices": args.indices if args.mode == "census" else None,
              "case_count": len(rows), "unique_inputs": len({json.dumps(c["input"]) for c in cases}),
              "independent_mismatches": sum(not row["independent_reference_matches"] for row in rows),
              "generator_reference_mismatches": sum(row["generator_reference_matches"] is False for row in rows),
              "validator_failed_cases": sum(any(row["validator_errors"].values()) for row in rows),
              "independent_rival_parity_mismatches": {name: sum(not row["independent_rival_parity"][name] for row in rows) for name in rivals},
              "feature_case_counts": counts, "canonical_rival_fit": canonical_fit_report(module),
              "refutation_counts": {name: sum(row["rival_refutations"][name] for row in rows) for name in rivals},
              "all_declared_rivals_refuted_case_count": sum(bool(rivals) and all(row["rival_refutations"].values()) for row in rows),
              "window_count": len(windows),
              "windows_with_surviving_rivals": sum(bool(row["surviving_rivals"]) for row in windows),
              "windows_with_query_ambiguity": sum(bool(row["query_ambiguous_rivals"]) for row in windows),
              "cyclic_query_rotation_count": len(rotations),
              "cyclic_rotations_with_surviving_rivals": sum(bool(row["surviving_rivals"]) for row in rotations),
              "cyclic_rotations_with_query_ambiguity": sum(bool(row["query_ambiguous_rivals"]) for row in rotations),
              "query_ambiguity_counts": {name: sum(name in row["query_ambiguous_rivals"] for row in windows) for name in rivals}}
    report["rival_families"] = family_summary(rows, windows, rotations, rivals)
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
