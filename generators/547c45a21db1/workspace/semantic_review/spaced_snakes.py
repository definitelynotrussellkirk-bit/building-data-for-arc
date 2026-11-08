"""Measure contiguous spaced-snake witness support on the minimum 5 by 6 grid."""
from pathlib import Path
import argparse
import hashlib
import json

import probe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("checks/semantic-review/spaced_snakes.json"))
    args = parser.parse_args()
    base = []
    for row in (0, 2, 4):
        cols = range(6) if row % 4 == 0 else range(5, -1, -1)
        if base:
            base.append((row - 1, base[-1][1]))
        base.extend((row, col) for col in cols)
    paths = []
    for flip_h in (False, True):
        for flip_w in (False, True):
            paths.append([(4-r if flip_h else r, 5-c if flip_w else c) for r, c in base])
    vbase = []
    for col in (0, 2, 4):
        rows = range(5) if col % 4 == 0 else range(4, -1, -1)
        if vbase:
            vbase.append((vbase[-1][0], col-1))
        vbase.extend((row, col) for row in rows)
    for flip_h in (False, True):
        for flip_w in (False, True):
            for shift in (0, 1):
                paths.append([(4-r if flip_h else r, 5-(c+shift) if flip_w else c+shift) for r, c in vbase])
    canonical_fitting = tuple(name for name, fn in probe.RIVALS.items()
                             if all(fn(pair["input"]) == pair["output"]
                                    for _, _, pair in probe.canonical(Path("repo"))[2]))
    report = {
        "shape": [5, 6],
        "generator_sha256": hashlib.sha256(Path("repo/generators/547c45a21db1/generator.py").read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rival_probe_sha256": hashlib.sha256(Path(probe.__file__).read_bytes()).hexdigest(),
        "canonical_fitting_rivals": canonical_fitting,
        "sampling": "Contiguous subpaths of full spaced horizontal/vertical serpentine paths on a 5 by 6 grid, both vertical translations where applicable and all horizontal/vertical reflections; both seed orders. Deduplicated exact input grids.",
        "lengths": {},
    }
    for length in range(4, 21):
        seen, hits = set(), []
        counts = {name: 0 for name in probe.RIVALS}
        for path in paths:
            for start in range(len(path) - length + 1):
                for red_at_start in (False, True):
                    grid = probe.make_path(path[start:start+length], shape=(5, 6), red_at_start=red_at_start)
                    key = json.dumps(grid)
                    if key in seen:
                        continue
                    seen.add(key)
                    expected = probe.bfs4(grid)
                    differences = {name: probe.mismatch(fn(grid), expected) for name, fn in probe.RIVALS.items()}
                    for name in counts:
                        counts[name] += bool(differences[name])
                    if all(differences[name] for name in canonical_fitting):
                        hits.append({"input": grid, "bfs4_diagnostic_output": expected,
                                     "refutes_all9": all(differences.values()), "differences": differences})
        report["lengths"][str(length)] = {
            "unique_inputs": len(seen), "rival_refutation_counts": counts,
            "all_five_count": len(hits), "all_nine_count": sum(h["refutes_all9"] for h in hits),
            "first_all_five": hits[:1],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: {name: value for name, value in values.items()
                         if name in ("unique_inputs", "all_five_count", "all_nine_count")}
                      for k, values in report["lengths"].items()}, indent=2))


if __name__ == "__main__":
    main()
