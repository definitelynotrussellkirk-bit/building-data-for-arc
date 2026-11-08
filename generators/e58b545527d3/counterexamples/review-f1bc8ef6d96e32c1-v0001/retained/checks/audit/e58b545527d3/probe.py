"""Bounded source-bound audit; pure diagnostic rules, public generation later verifies labels."""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "e58b545527d3"


def zero_regions(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            region = []
            colors = set()
            edge = False
            while todo:
                rr, cc = todo.popleft()
                region.append((rr, cc))
                edge |= rr in (0, h - 1) or cc in (0, w - 1)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        color = grid[nr][nc]
                        if color == 0 and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            todo.append((nr, nc))
                        elif color not in (0, 8):
                            colors.add(color)
            yield region, edge, colors


def diagnostic_room_fill(grid):
    out = deepcopy(grid)
    for region, edge, colors in zero_regions(grid):
        if not edge and len(colors) == 1:
            color = next(iter(colors))
            for r, c in region:
                out[r][c] = color
    return out


def nearest_global_seed(grid):
    """Use closed zero regions, but pick each cell's globally closest seed; row-major ties."""
    out = deepcopy(grid)
    seeds = [(r, c, v) for r, row in enumerate(grid)
             for c, v in enumerate(row) if v not in (0, 8)]
    if not seeds:
        return out
    for region, edge, _ in zero_regions(grid):
        if not edge:
            for r, c in region:
                chosen = min(seeds, key=lambda s: (abs(r-s[0]) + abs(c-s[1]), s[0], s[1]))
                out[r][c] = chosen[2]
    return out


def domain_status(grid):
    """Independent diagnostic, not an absent generator-owned self_check."""
    issues = []
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        issues.append("invalid dimensions")
    if any(len(row) != w or any(type(v) is not int or v not in range(10) for v in row)
           for row in grid):
        issues.append("invalid grid")
    enclosed = [item for item in zero_regions(grid) if not item[1]]
    if not enclosed or any(len(colors) != 1 for _, _, colors in enclosed):
        issues.append("each enclosed zero region must have one adjacent seed color")
    if any(colors for _, edge, colors in zero_regions(grid) if edge):
        issues.append("a seed touches the exterior")
    return {"independent_issues": issues, "enclosed_regions": len(enclosed),
            "generator_self_check": "absent", "generator_strict_canonical_like": "absent"}


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-seeds", type=int, default=256)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    source = repo / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = next(json.loads(line) for line in (repo / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                  if json.loads(line).get("task_id") == TASK)
    canonical = record["train"] + record["test"]
    report = {"task_id": TASK, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "generator_version": module.VERSION,
              "rule_sha256": hashlib.sha256(record["program_solution"].encode()).hexdigest(),
              "normalized_rule_sha256": hashlib.sha256(" ".join(record["program_solution"].split()).encode()).hexdigest(),
              "rival": "nearest_global_seed", "canonical_rival_matches": [],
              "canonical_diagnostic_matches": [], "bounded_search": [],
              "source_self_check": callable(getattr(module, "self_check", None))}
    for i, pair in enumerate(canonical):
        report["canonical_rival_matches"].append(nearest_global_seed(pair["input"]) == pair["output"])
        report["canonical_diagnostic_matches"].append(diagnostic_room_fill(pair["input"]) == pair["output"])
    witness = None
    for band in ("medium", "hard"):
        for seed in range(args.max_seeds):
            grids = [module.generate(seed, index, difficulty=band) for index in range(4)]
            agreement = [nearest_global_seed(grid) == diagnostic_room_fill(grid) for grid in grids]
            report["bounded_search"].append({"difficulty": band, "seed": seed, "rival_agreement": agreement})
            if all(agreement[:3]) and not agreement[3]:
                witness = {"difficulty": band, "seed": seed, "sample_indices": [0, 1, 2, 3],
                           "inputs": grids, "rival_outputs": [nearest_global_seed(g) for g in grids],
                           "diagnostic_outputs": [diagnostic_room_fill(g) for g in grids],
                           "domain_status": [domain_status(g) for g in grids]}
                break
        if witness:
            break
    report["search_attempts"] = len(report["bounded_search"])
    report["witness_found"] = witness is not None
    report["unique_searched_inputs"] = None  # No census claimed from this first-witness search.
    report["override_probes"] = []
    for override in ({"palette_size": 2}, {"palette_size": 3}, {"n_distinct_colors": 2}, {"grid_h": 14}):
        try:
            grid = module.generate(0, 0, difficulty="easy", **override)
            report["override_probes"].append({"difficulty": "easy", "seed": 0, "sample_index": 0,
                                               "overrides": override, "shape": [len(grid), len(grid[0])],
                                               "observed_palette": sorted({v for row in grid for v in row}),
                                               "grid_sha256": digest(grid)})
        except Exception as exc:
            report["override_probes"].append({"difficulty": "easy", "seed": 0, "sample_index": 0,
                                               "overrides": override, "error": type(exc).__name__, "message": str(exc)})
    (out / "probe-report.json").write_text(json.dumps(report, indent=2) + "\n")
    if witness:
        (out / "diagnostic-lesson.json").write_text(json.dumps(witness, indent=2) + "\n")
        (out / "input.json").write_text(json.dumps({"inputs": [p["input"] for p in canonical] + witness["inputs"]}, indent=2) + "\n")
        (out / "query-input.json").write_text(json.dumps(witness["inputs"][3], indent=2) + "\n")
        (out / "rival-query-output.json").write_text(json.dumps(witness["rival_outputs"][3], indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256", "canonical_rival_matches", "canonical_diagnostic_matches", "search_attempts", "witness_found", "override_probes")}, indent=2))
    if witness:
        print(json.dumps({key: witness[key] for key in ("difficulty", "seed", "sample_indices", "domain_status")}, indent=2))
    return 0 if witness else 1


if __name__ == "__main__":
    raise SystemExit(main())
