#!/usr/bin/env python3
"""Reproduce lesson-window ambiguity in generator 27f5eba1051c."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

TASK = "27f5eba1051c"
PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))


def load_generator():
    path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_27f5eba1051c", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def decode(rows):
    return [[int(ch) for ch in row] for row in rows]


def canonical_pairs():
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            pairs = row["train"] + ([row["test"]] if isinstance(row["test"], dict) else row["test"])
            return [{"input": decode(p["input"]), "output": decode(p["output"])} for p in pairs]
    raise KeyError(TASK)


def crop(clean, obj):
    top, bottom, left, right = obj["bbox"]
    return [row[left:right + 1] for row in clean[top:bottom + 1]]


def rival(module, grid, mode):
    analysis = module._inspect_scene(grid)
    if analysis is None:
        raise ValueError("generator validator rejected its own grid")
    clean = [row[:] for row in grid]
    clean[0][0] = 0
    if mode == "area_then_top_row_then_left_column":
        ordered = sorted(
            analysis["objects"],
            key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][2], obj["color"]),
        )
    elif mode == "area_then_color_then_left_column":
        ordered = sorted(
            analysis["objects"],
            key=lambda obj: (-obj["size"], obj["color"], obj["bbox"][2]),
        )
    else:
        raise KeyError(mode)
    return crop(clean, ordered[analysis["rank"] - 1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module, source = load_generator()
    modes = ("area_then_top_row_then_left_column", "area_then_color_then_left_column")
    pairs = canonical_pairs()
    canonical_fit = {
        mode: all(rival(module, p["input"], mode) == p["output"] for p in pairs)
        for mode in modes
    }
    report = {
        "schema": "27f5eba1051c-shortcut-window-probe-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "examples_needed": module.EXAMPLES_NEEDED,
        "lesson_policy": "one seed; sample_index 0..EXAMPLES_NEEDED are four demos plus one query",
        "seed_range": [0, args.seeds - 1],
        "canonical_pairs": len(pairs),
        "canonical_fit": canonical_fit,
        "bands": {},
    }
    for band in ("easy", "medium", "hard"):
        counts = {mode: 0 for mode in modes}
        first_seed = {mode: None for mode in modes}
        for seed in range(args.seeds):
            grids = [module.generate(seed, i, difficulty=band) for i in range(module.EXAMPLES_NEEDED + 1)]
            truth = [module.rule_mirror(grid) for grid in grids]
            for mode in modes:
                predictions = [rival(module, grid, mode) for grid in grids]
                ambiguous = (
                    all(predictions[i] == truth[i] for i in range(module.EXAMPLES_NEEDED))
                    and predictions[-1] != truth[-1]
                )
                if ambiguous:
                    counts[mode] += 1
                    if first_seed[mode] is None:
                        first_seed[mode] = seed
        report["bands"][band] = {
            "lesson_windows": args.seeds,
            "ambiguous_windows": counts,
            "first_seed": first_seed,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
