"""Reproduce a three-demo lesson where per-column gravity survives."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs  # noqa: E402

TASK = "8343e384cd7c"
GENERATOR = REPO / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_gravity_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rigid_gravity(grid):
    h, w = len(grid), len(grid[0])
    cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    shift = h - 1 - max(r for r, _, _ in cells)
    output = [[0] * w for _ in range(h)]
    for r, c, value in cells:
        output[r + shift][c] = value
    return output


def per_column_gravity(grid):
    h, w = len(grid), len(grid[0])
    output = [[0] * w for _ in range(h)]
    for c in range(w):
        cells = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if not cells:
            continue
        shift = h - 1 - max(r for r, _ in cells)
        for r, value in cells:
            output[r + shift][c] = value
    return output


def main():
    gen = load_generator()
    canonical = canonical_pairs(TASK, root=REPO, labeled_only=True)
    assert all(rigid_gravity(pair["input"]) == pair["output"] for pair in canonical)

    counts = {}
    for band in ("easy", "medium", "hard"):
        matches = 0
        for index in range(1000):
            grid = gen.generate(100_000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            matches += rigid_gravity(grid) == per_column_gravity(grid)
        counts[band] = {"samples": 1000, "per_column_rival_matches": matches}

    band, seed, start = "easy", 10000, 6
    grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(4)]
    assert all(rigid_gravity(grid) == per_column_gravity(grid) for grid in grids[:3])
    assert rigid_gravity(grids[3]) != per_column_gravity(grids[3])

    pairs = []
    for offset, grid in enumerate(grids):
        intended = rigid_gravity(grid)
        rival = per_column_gravity(grid)
        pairs.append(
            {
                "role": "demo" if offset < 3 else "query",
                "sample_index": start + offset,
                "input": grid,
                "authority_python": intended,
                "per_column_rival": rival,
                "rival_matches": rival == intended,
                "self_check": gen.self_check(grid),
            }
        )

    report = {
        "schema": "8343e384cd7c-audit-v1",
        "finding": "A production three-demo lesson can leave per-column gravity unfalsified while the next query distinguishes it.",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "canonical_pairs_checked": len(canonical),
        "ordinary_draw_census": counts,
        "replay": {"difficulty": band, "seed": seed, "sample_index": start, "n_train": 3, "n_test": 1},
        "pairs": pairs,
        "racket_parity": "pending apply output",
    }
    out = Path(__file__).with_name("report.json")
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(__file__).with_name("inputs.json").write_text(json.dumps({"inputs": grids}, indent=2) + "\n")
    print(json.dumps({"census": counts, "replay": report["replay"], "rival_matches": [p["rival_matches"] for p in pairs]}, indent=2))


if __name__ == "__main__":
    main()
