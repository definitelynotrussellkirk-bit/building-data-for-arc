"""Inspect only the three retained grids; no sampling or reference execution."""
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

out = Path(__file__).resolve().parent
root = find_root(__file__)
generator, path, source_sha = load_selected_generator("e3bf7e173449", root=root)
witness = json.loads((out / "witness.json").read_text())
assert source_sha == witness["generator_sha256"]
card = [(-1, 0), (1, 0), (0, -1), (0, 1)]
rows = []
for pair in witness["train"] + witness["test"]:
    grid = pair["input"]
    height, width = len(grid), len(grid[0])

    def frames(colors):
        found = []
        for r in range(height):
            for c in range(width):
                if grid[r][c] != colors[0]:
                    continue
                for x in card:
                    for y in card:
                        if x[0] * y[0] + x[1] * y[1]:
                            continue
                        def at(v):
                            return grid[r+v[0]][c+v[1]] if 0 <= r+v[0] < height and 0 <= c+v[1] < width else None
                        if at(x) == colors[1] and at(y) == colors[2]:
                            found.append(((r, c), x, y))
        return sorted(found)

    def signature(frame):
        (rr, cc), x, y = frame
        points = []
        for r in range(height):
            for c in range(width):
                if grid[r][c] != 8:
                    continue
                dr, dc = r-rr, c-cc
                u, v = dr*x[0]+dc*x[1], dr*y[0]+dc*y[1]
                if max(abs(u), abs(v)) <= 3:
                    points.append((u, v))
        return sorted(points)

    source = signature(frames((2, 3, 4))[0])
    rotated = sorted((-v, u) for u, v in source)
    candidates = [signature(frame) for frame in frames((5, 6, 7))]
    rows.append({"sample_index": pair["sample_index"], "self_check_errors": generator.self_check(grid),
                 "source_signature": source, "rotated_source_signature": rotated,
                 "candidate_signatures": candidates,
                 "matching_candidate_indices": [i for i, sig in enumerate(candidates) if sig == rotated],
                 "canonical_output": pair["output"], "count_only_output": pair["rival_output"]})
report = {"schema": "arcpuzzles-retained-witness-inspection-v1", "generator_sha256": source_sha,
          "witness_sha256": hashlib.sha256((out / "witness.json").read_bytes()).hexdigest(),
          "inspection_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "pairs": rows,
          "limits": "Independent Python geometry inspection of retained seed4 grids only; no new generation or Racket execution. Radius3 reproduces the explicit canonical extraction window."}
(out / "inspection.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2))
