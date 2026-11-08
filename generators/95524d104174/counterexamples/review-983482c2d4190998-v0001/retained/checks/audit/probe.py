#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(task: str):
    path = REPO / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canonical(task: str) -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task:
                return row
    raise KeyError(task)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def probe_d8() -> None:
    task = "d8c1699fa902"
    mod = load(task)
    kwargs = dict(seed=1701, sample_index=9, difficulty="medium")
    warm = mod.generate(**kwargs, palette_kind="warm")
    cool = mod.generate(**kwargs, palette_kind="cool")
    density_sparse = mod.generate(**kwargs, density="sparse")
    density_nonsense = mod.generate(**kwargs, density="not-a-real-density")
    out_dir = PACKET / "checks" / "audit" / task
    write_json(out_dir / "input.json", warm)
    evidence = {
        "task_id": task,
        "finding": "advertised exact controls are placebo and public rule summary is stale",
        "generator_sha256": sha(REPO / "generators" / task / "generator.py"),
        "summary_sha256": sha(REPO / "generators" / task / "SUMMARY.md"),
        "reproducer": {
            **kwargs,
            "warm_override": {"palette_kind": "warm"},
            "cool_override": {"palette_kind": "cool"},
            "warm_equals_cool": warm == cool,
            "sparse_equals_invalid_density": density_sparse == density_nonsense,
            "input_grid": warm,
        },
        "observed_palette": sorted({v for row in warm for v in row if v}),
        "documented_but_unconsumed_axes": [
            "palette_kind", "palette_size", "position_bias",
            "n_distinct_colors", "density"
        ],
        "source_comment_acknowledges_actual_rule": "count color-2 cells in row 0 and crop k-th component by column",
        "public_summary_still_claims": "size-ranked component selected by corner key and transformed by a transform key",
        "command": ["python3", "checks/audit/probe.py"],
        "cwd": "packet_root",
    }
    write_json(out_dir / "probe.json", evidence)


def intersection(grid: list[list[int]]) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    full_cols = [c for c in range(w) if grid[0][c] and len({grid[r][c] for r in range(h)}) == 1]
    dense_rows = [r for r in range(h) if sum(v != 0 for v in grid[r]) >= w - 1]
    if len(full_cols) != 1 or len(dense_rows) != 1:
        raise ValueError((full_cols, dense_rows))
    return dense_rows[0], full_cols[0]


def probe_955() -> None:
    task = "95524d104174"
    mod = load(task)
    row = canonical(task)
    canonical_pair = next(pair for pair in row["train"] if len(pair["input"]) == 4)
    inp = canonical_pair["input"]
    expected = canonical_pair["output"]
    out_dir = PACKET / "checks" / "audit" / task
    write_json(out_dir / "input.json", inp)

    # Literal rival described by the public SUMMARY: paint only four diagonals.
    rival = [r[:] for r in inp]
    rr, cc = 1, 1
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rival[rr + dr][cc + dc] = 4
    write_json(out_dir / "rival-diagonal-only.json", rival)

    samples = []
    for band in ("easy", "medium", "hard"):
        for index in range(100):
            grid = mod.generate(2026, index, difficulty=band)
            r, c = intersection(grid)
            h, w = len(grid), len(grid[0])
            samples.append({
                "band": band,
                "h": h,
                "w": w,
                "edge_margin": min(r, c, h - 1 - r, w - 1 - c),
            })
    evidence = {
        "task_id": task,
        "finding": "generator excludes a canonical 4x4 / margin-1 profile and SUMMARY describes only four diagonal writes although authority writes the full eight-cell ring",
        "generator_sha256": sha(REPO / "generators" / task / "generator.py"),
        "summary_sha256": sha(REPO / "generators" / task / "SUMMARY.md"),
        "canonical_4x4_input": inp,
        "canonical_output": expected,
        "diagonal_only_rival": rival,
        "diagonal_only_matches_authority": rival == expected,
        "sample_census": {
            "seed": 2026,
            "indices_per_band": 100,
            "bands": ["easy", "medium", "hard"],
            "denominator": len(samples),
            "min_h": min(s["h"] for s in samples),
            "min_w": min(s["w"] for s in samples),
            "min_intersection_edge_margin": min(s["edge_margin"] for s in samples),
            "count_h4_or_w4": sum(s["h"] == 4 or s["w"] == 4 for s in samples),
            "count_margin1": sum(s["edge_margin"] == 1 for s in samples),
        },
        "ignored_axes_checked_by_source": ["anchor_corner", "asymmetry_force", "palette_size"],
        "command": ["python3", "checks/audit/probe.py"],
        "cwd": "packet_root",
    }
    write_json(out_dir / "probe.json", evidence)


if __name__ == "__main__":
    probe_d8()
    probe_955()
    print("wrote audit probes")
