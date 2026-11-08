from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "6c16d20079af"
root = find_root(Path.cwd())
gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
pairs = canonical_pairs(TASK_ID, root=root)
canonical = []
for index, pair in enumerate(pairs):
    errors = gen.self_check(pair["input"])
    canonical.append({"index": index, "errors": errors})

grid = gen.generate(123, 5, difficulty="easy", n_solid=3)
components = gen._components(grid)
holes = [
    i for i, (_color, cells, bbox) in enumerate(components)
    if gen._has_bbox_hole(grid, cells, bbox)
]
solid_count = len(components) - len(holes)
report = {
    "schema": "audit-probe-v1",
    "task_id": TASK_ID,
    "source": str(source.relative_to(root)),
    "source_sha256": source_sha,
    "canonical_pair_count": len(pairs),
    "canonical_self_check": canonical,
    "canonical_rejections": [row for row in canonical if row["errors"]],
    "override_probe": {
        "call": {"seed": 123, "sample_index": 5, "difficulty": "easy", "n_solid": 3},
        "observed_component_count": len(components),
        "observed_hole_indices": holes,
        "observed_solid_count": solid_count,
        "override_honored": solid_count == 3,
        "input": grid,
    },
}
out = root.parent / "checks" / "audit" / TASK_ID / "probe.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
