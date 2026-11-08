"""Bounded Python-mirror teaching regression; not protected-Racket evidence."""
import hashlib, importlib.util, json
from pathlib import Path

SOURCE = Path("generators/9ce2dcf587b8/workspace/parametric/native_family.py")
spec = importlib.util.spec_from_file_location("rays_review", SOURCE)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)

def rival(grid, rule):
    points = native.validate_grid(grid)
    keep = []
    for r, c in points:
        row = [cc for rr, cc in points if rr == r]
        col = [rr for rr, cc in points if cc == c]
        if c in (min(row), max(row)) and r in (min(col), max(col)):
            keep.append((r, c))
    reduced = [[v if (r, c) in keep else 0 for c, v in enumerate(row)]
               for r, row in enumerate(grid)]
    output = native.apply_python(reduced, rule)
    for r, c in points:
        output[r][c] = grid[r][c]
    return output

cases = []
for rule in native.RULES:
    episode = native.generate(0, {"ray_rule": rule}, 2, 4)
    query = episode["test"][2]
    cases.append({
        "seed": 0, "settings": {"ray_rule": rule},
        "demos": episode["train"],
        "demos_fit": all(rival(p["input"], rule) == p["output"] for p in episode["train"]),
        "query_index": 2, "query": query,
        "rival_output": rival(query["input"], rule),
    })
receipt = {
    "status": "python_mirror_only_not_acceptance",
    "rival": "Emit only from markers extremal in BOTH occupied row and column; retain all original markers.",
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "cases": cases,
}
out = Path("../checks/9ce2dcf587b8/review/row-column-extrema-python.json")
out.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps([{"rule": c["settings"]["ray_rule"], "demos_fit": c["demos_fit"],
                  "query_differs": c["rival_output"] != c["query"]["output"]} for c in cases]))
