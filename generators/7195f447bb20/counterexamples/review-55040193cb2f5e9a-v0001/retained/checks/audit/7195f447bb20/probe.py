from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
SOURCE = REPO / "generators" / "7195f447bb20" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_7195f447bb20", SOURCE)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def no_guard_rival(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 2):
        for c in range(w - 2):
            if grid[r][c] == 4 and grid[r + 1][c + 1] == 0 and grid[r + 2][c + 2] == 4:
                out[r + 1][c + 1] = 4
    return out


def has_guard_witness(grid):
    h, w = len(grid), len(grid[0])
    for r in range(h - 2):
        for c in range(w - 2):
            if not (grid[r][c] == 4 and grid[r + 1][c + 1] == 0 and grid[r + 2][c + 2] == 4):
                continue
            predecessor = r > 0 and c > 0 and grid[r - 1][c - 1] == 4
            successor = r + 3 < h and c + 3 < w and grid[r + 3][c + 3] == 4
            if predecessor or successor:
                return True
    return False


def main():
    here = Path(__file__).resolve().parent
    counterexample = json.loads((here / "input.json").read_text())
    sampled = 0
    witnesses = 0
    by_band = {}
    for band in ("easy", "medium", "hard"):
        band_sampled = 0
        band_witnesses = 0
        for seed in (1, 7, 91):
            for index in range(100):
                grid = mod.generate(seed, index, difficulty=band)
                band_sampled += 1
                band_witnesses += int(has_guard_witness(grid))
        sampled += band_sampled
        witnesses += band_witnesses
        by_band[band] = {"sampled": band_sampled, "guard_witnesses": band_witnesses}

    report = {
        "schema": "review-audit-probe-v1",
        "task_id": "7195f447bb20",
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "self_check": mod.self_check(counterexample),
        "counterexample": counterexample,
        "no_guard_rival_output": no_guard_rival(counterexample),
        "candidate_midpoint": [2, 2],
        "sampled": sampled,
        "guard_witnesses": witnesses,
        "by_band": by_band,
    }
    (here / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"sampled": sampled, "guard_witnesses": witnesses, "self_check": report["self_check"]}))


if __name__ == "__main__":
    main()
