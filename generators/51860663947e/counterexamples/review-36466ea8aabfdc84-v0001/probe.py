from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path

import argparse
import sys

RUNTIME = next((p / "shared" / "runtime" for p in Path(__file__).resolve().parents
                if (p / "shared" / "runtime" / "reviewer_support.py").is_file()), None)
if RUNTIME is None:
    raise FileNotFoundError("Run from a relocated ARCpuzzles library containing shared/runtime")
sys.path.insert(0, str(RUNTIME))
from reviewer_support import find_root
ROOT = find_root(__file__)
TASK = "51860663947e"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
CANON = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
EXPECTED_GENERATOR_SHA256 = "9ecf27d709adbefaeb650d7803774baa3e978751000b90af8e9f4f8ff7f5b6ad"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def regions(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        q = deque([start])
        comp = [start]
        while q:
            r, c = q.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    q.append(p)
                    comp.append(p)
        out.append(sorted(comp))
    return out


def area(cells):
    return (max(r for r, _ in cells) - min(r for r, _ in cells) + 1) * (max(c for _, c in cells) - min(c for _, c in cells) + 1)


def recolor(grid, score):
    comps = regions(grid)
    values = [score(c) for c in comps]
    lo, hi = min(values), max(values)
    out = [row[:] for row in grid]
    for comp, value in zip(comps, values):
        color = 1 if value == hi else 8 if value == lo else None
        if color is not None:
            for r, c in comp:
                out[r][c] = color
    return out


def canonical_pairs():
    for line in CANON.read_text().splitlines():
        d = json.loads(line)
        if d.get("task_id") == TASK:
            return list(d["train"]) + list(d["test"])
    raise RuntimeError("canonical task missing")


def main():
    parser = argparse.ArgumentParser(description="Replay this source-bound audit; retained evidence is never overwritten.")
    parser.add_argument("--out", required=True, type=Path, help="New output directory for the replay")
    args = parser.parse_args()
    OUT = args.out.resolve()
    if OUT.exists():
        raise FileExistsError("Choose a new output directory; existing evidence is immutable")
    if hashlib.sha256(GEN_PATH.read_bytes()).hexdigest() != EXPECTED_GENERATOR_SHA256:
        raise ValueError("Generator changed since the audit; use the audited source to reproduce it")
    OUT.mkdir(parents=True)
    gen = load_generator()
    grid = gen.generate(7, 0, difficulty="medium")
    comps = regions(grid)
    cell_output = recolor(grid, len)
    bbox_output = recolor(grid, area)

    pairs = canonical_pairs()
    canonical_bbox_matches = [recolor(p["input"], area) == p["output"] for p in pairs]
    sample = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            g = gen.generate(seed, 0, difficulty=difficulty)
            cs = regions(g)
            sizes = [len(c) for c in cs]
            sample.append({
                "difficulty": difficulty,
                "seed": seed,
                "shape": [len(g), len(g[0])],
                "sizes": sizes,
                "areas": [area(c) for c in cs],
                "self_check": gen.self_check(g),
                "bbox_rival_matches_cell_rule": recolor(g, area) == recolor(g, len),
            })

    override_results = []
    for overrides in ({"n_h_walls": 0}, {"n_h_walls": 3}, {"n_v_walls": 3}):
        try:
            gen.generate(0, 0, difficulty="medium", **overrides)
            override_results.append({"overrides": overrides, "status": "accepted"})
        except Exception as exc:
            override_results.append({
                "overrides": overrides,
                "status": "error",
                "exception": type(exc).__name__,
                "message": str(exc),
            })

    report = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "witness_generation": {"seed": 7, "sample_index": 0, "difficulty": "medium", "overrides": {}},
        "witness_shape": [len(grid), len(grid[0])],
        "witness_self_check": gen.self_check(grid),
        "witness_region_sizes": [len(c) for c in comps],
        "witness_region_bbox_areas": [area(c) for c in comps],
        "cell_count_output": cell_output,
        "bbox_area_rival_output": bbox_output,
        "witness_differing_cells": sum(a != b for ra, rb in zip(cell_output, bbox_output) for a, b in zip(ra, rb)),
        "canonical_pairs": len(pairs),
        "bbox_area_rival_matches_each_canonical_pair": canonical_bbox_matches,
        "bbox_area_rival_matches_all_canonical_pairs": all(canonical_bbox_matches),
        "sample_24": {
            "unique_inputs": len({json.dumps(gen.generate(x["seed"], 0, difficulty=x["difficulty"]), separators=(",", ":")) for x in sample}),
            "repeated_size_draws": sum(len(set(x["sizes"])) < len(x["sizes"]) for x in sample),
            "tied_minimum_draws": sum(x["sizes"].count(min(x["sizes"])) > 1 for x in sample),
            "tied_maximum_draws": sum(x["sizes"].count(max(x["sizes"])) > 1 for x in sample),
            "bbox_rival_agreements": sum(x["bbox_rival_matches_cell_rule"] for x in sample),
            "all_self_checks_empty": all(not x["self_check"] for x in sample),
            "draws": sample,
        },
        "advertised_override_results": override_results,
        "conclusions": [
            "the bounding-box-area rival fits every canonical pair but disagrees on a normal generated input",
            "self_check accepts repeated region sizes although the summary promises distinct sizes and unique extrema",
            "three values advertised as legal wall-count overrides raise before the local clamp can run",
        ],
    }
    (OUT / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (OUT / "rival-output.json").write_text(json.dumps(bbox_output, indent=2) + "\n")
    (OUT / "cell-output.json").write_text(json.dumps(cell_output, indent=2) + "\n")
    (OUT / "probe-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"cell_count_output", "bbox_area_rival_output", "sample_24"}}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
