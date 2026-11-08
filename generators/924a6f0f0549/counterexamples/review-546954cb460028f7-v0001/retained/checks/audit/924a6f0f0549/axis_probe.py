from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "924a6f0f0549"
root = find_root(Path.cwd())
module, source_path, source_sha256 = load_selected_generator(TASK, root=root)

bands = ("easy", None, "hard")
comparisons = {
    "palette_kind": ("default", "warm", "cool", "varied"),
    "texture_helpful": ("default", "warm", "cool", "varied"),
}
rows = []
for band in bands:
    label = band or "medium"
    for seed in range(20):
        index = seed % 5
        palette_outputs = [module.generate(seed, index, difficulty=band, palette_kind=v) for v in comparisons["palette_kind"]]
        texture_outputs = [module.generate(seed, index, difficulty=band, texture=v) for v in comparisons["texture_helpful"]]
        small = module.generate(seed, index, difficulty=band, target_size=3)
        large = module.generate(seed, index, difficulty=band, target_size=8)
        rows.append({
            "band": label,
            "seed": seed,
            "sample_index": index,
            "palette_kind_all_identical": all(g == palette_outputs[0] for g in palette_outputs[1:]),
            "helpful_texture_all_identical": all(g == texture_outputs[0] for g in texture_outputs[1:]),
            "target_size_3_equals_8": small == large,
        })

rejections = []
for band, key, value in [
    ("easy", "grid_h", 16),
    ("easy", "grid_w", 17),
    ("hard", "grid_h", 7),
    ("hard", "grid_w", 9),
]:
    try:
        module.generate(0, 0, difficulty=band, **{key: value})
    except Exception as exc:
        rejections.append({"band": band, "axis": key, "declared_value": value, "error": f"{type(exc).__name__}: {exc}"})
    else:
        rejections.append({"band": band, "axis": key, "declared_value": value, "error": None})

report = {
    "schema": "review-audit-axis-probe-v1",
    "task_id": TASK,
    "generator_path": str(source_path.relative_to(root)),
    "generator_sha256": source_sha256,
    "draws": len(rows),
    "ignored_axis_counts": {
        "palette_kind_all_identical": sum(r["palette_kind_all_identical"] for r in rows),
        "helpful_texture_all_identical": sum(r["helpful_texture_all_identical"] for r in rows),
        "target_size_3_equals_8": sum(r["target_size_3_equals_8"] for r in rows),
    },
    "declared_cross_band_values_rejected": rejections,
    "rows": rows,
}
out = Path("../checks/audit/924a6f0f0549/axis-probe.json")
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "draws", "ignored_axis_counts", "declared_cross_band_values_rejected")}, indent=2))
