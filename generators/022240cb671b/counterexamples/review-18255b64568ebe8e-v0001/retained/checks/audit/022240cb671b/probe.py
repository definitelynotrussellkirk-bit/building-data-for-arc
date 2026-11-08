#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "022240cb671b"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
CANON = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUT = Path(__file__).with_name("report.json")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def touched_sides(grid):
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    return {
        "top": any(r == 0 for r, _ in cells),
        "bottom": any(r == h - 1 for r, _ in cells),
        "left": any(c == 0 for _, c in cells),
        "right": any(c == w - 1 for _, c in cells),
    }


def canonical_row():
    for line in CANON.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise RuntimeError("canonical row missing")


def main() -> int:
    gen = load_generator()
    counts = {side: 0 for side in ("top", "bottom", "left", "right")}
    combos = {}
    examples = {}
    total = 0
    validator_failures = []
    for seed in range(100):
        for sample_index in range(4):
            grid = gen.generate(seed, sample_index, difficulty=None, texture="border_touch")
            sides = touched_sides(grid)
            issues = gen.self_check(grid, difficulty=None)
            if issues:
                validator_failures.append({"seed": seed, "sample_index": sample_index, "issues": issues})
            total += 1
            key = "+".join(side for side, yes in sides.items() if yes) or "none"
            combos[key] = combos.get(key, 0) + 1
            examples.setdefault(key, {"seed": seed, "sample_index": sample_index, "input": grid})
            for side, yes in sides.items():
                counts[side] += int(yes)

    canon = canonical_row()
    canonical_pairs = []
    for split in ("train", "test"):
        for index, pair in enumerate(canon[split]):
            sides = touched_sides(pair["input"])
            canonical_pairs.append({"split": split, "index": index, "touched_sides": sides})
    heldout_right = [p for p in canonical_pairs if p["split"] == "test" and p["touched_sides"]["right"]]

    report = {
        "schema": "arc-audit-border-coverage-v1",
        "task_id": TASK,
        "status": "coverage_defect_reproduced",
        "finding": "border_touch emits only top/left contact and cannot emit bottom/right contact",
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "sampled_border_touch_draws": total,
        "validator_failures": validator_failures,
        "all_samples_pass_self_check": not validator_failures,
        "belongs_to_documented_generator_domain": True,
        "side_touch_counts": counts,
        "combination_counts": combos,
        "representative_examples": examples,
        "canonical_pair_sides": canonical_pairs,
        "canonical_test_right_touch_count": len(heldout_right),
        "mechanism": {
            "generator": "dr is either -min(rows) or zero; when dr is zero dc is always -min(cols), and dc is otherwise either -min(cols) or zero",
            "effect": "the special profile always moves content to top and/or left; ordinary placement uses margin=1, so no production path reaches bottom/right",
            "canonical_mismatch": "the held-out canonical test contains content touching the right border",
        },
        "limitations": ["Finite census over 400 deterministic border_touch draws; code-path analysis establishes the omitted orientations."],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "draws": total, "side_touch_counts": counts, "combination_counts": combos, "canonical_test_right_touch_count": len(heldout_right)}, indent=2))
    return 0 if counts["bottom"] == 0 and counts["right"] == 0 and heldout_right else 1


if __name__ == "__main__":
    raise SystemExit(main())
