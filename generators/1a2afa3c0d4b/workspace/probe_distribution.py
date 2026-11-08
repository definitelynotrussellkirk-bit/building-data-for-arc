"""Compare source-bound transform coverage and motif diversity before/after.

Run through review.py run. Labels are NOT generated here: transform checks use
independent NumPy geometry. Use the public Racket checks for output authority.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from reviewer_support import find_root


def forms(panel):
    a = np.asarray(panel)
    return dict(zip(("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr"),
                    (v.tolist() for v in (a, np.rot90(a, -1), np.rot90(a, 2),
                     np.rot90(a, 1), np.fliplr(a), np.flipud(a), a.T,
                     np.rot90(a.T, 2)))))


def key(grid):
    return tuple(tuple(row) for row in grid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output already exists; preserve earlier evidence")
    root = find_root(__file__)
    source = next(p for p in (root / "generators/1a2afa3c0d4b/generator.py",
                             root / "puzzle_generators/per_puzzle/1a2afa3c0d4b/generator.py")
                  if p.is_file())
    spec = importlib.util.spec_from_file_location("distribution_subject", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    report = {"task_id": "1a2afa3c0d4b", "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "version": gen.VERSION, "authority": "independent NumPy diagnostics, not Racket labels",
              "sampling": "per band: seed=i, sample_index=i, i=0..49", "per_band": {},
              "requested_transforms": [], "generation_errors": []}
    for band in ("easy", "medium", "hard"):
        shapes, masks, exact, codes, headers, profiles = set(), set(), Counter(), Counter(), Counter(), 0
        for i in range(50):
            g = gen.generate(i, i, difficulty=band)
            s = len(g) - 1
            a = [row[:s] for row in g[1:]]
            b = [row[s+1:2*s+1] for row in g[1:]]
            aa = [[int(v != 0) for v in row] for row in a]
            shapes.add((len(g), len(g[0])))
            masks.add(key(aa))
            exact[len({key(x) for x in forms(a).values()})] += 1
            code = next(t for t, x in forms(a).items() if x == b)
            codes[code] += 1
            headers[next(c for c, v in enumerate(g[0]) if v)] += 1
            profiles += (len(g), len(g[0])) == (5, 14) and len({v for row in g for v in row}) in (4, 5)
        report["per_band"][band] = {"draws": 50, "input_shapes": sorted(shapes),
            "unique_a_supports": len(masks), "exact_orbit_size_counts": dict(exact),
            "inferred_transform_counts": dict(codes), "header_column_counts": dict(headers),
            "canonical_profile_hits": profiles}
    for code in ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr"):
        try:
            grid = gen.generate(271, 5, panel_side=4, transform=code)
        except (TypeError, ValueError) as exc:
            report["requested_transforms"].append({"code": code, "status": "rejected", "error": str(exc)})
            continue
        a = [row[:4] for row in grid[1:]]
        b = [row[5:9] for row in grid[1:]]
        expected = forms(a)[code]
        row = {"code": code, "status": "matched" if b == expected else "mismatch"}
        if b != expected:
            row.update(input=grid, expected_b=expected, actual_b=b, seed=271, sample_index=5,
                       overrides={"panel_side": 4, "transform": code})
        report["requested_transforms"].append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
