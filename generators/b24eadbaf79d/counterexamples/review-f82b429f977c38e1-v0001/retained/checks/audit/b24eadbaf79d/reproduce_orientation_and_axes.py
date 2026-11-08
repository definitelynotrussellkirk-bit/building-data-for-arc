from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "b24eadbaf79d"
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_b24", SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

from reviewer_support import canonical_pairs


def facts(grid):
    marker = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    template = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v >= 2]
    return {
        "shape": [len(grid), len(grid[0])],
        "marker": marker,
        "template_row_range": [min(r for r, _ in template), max(r for r, _ in template)],
        "marker_below_template": bool(marker and marker[0][0] > max(r for r, _ in template)),
    }

sample_rows = []
for band in ("easy", "medium", "hard"):
    for index in range(100):
        grid = mod.generate(12000 + index, index, difficulty=band)
        sample_rows.append({"band": band, "index": index, **facts(grid)})

pairs = canonical_pairs(TASK, root=ROOT, variant=0)
canonical_counterexamples = []
for pair in pairs:
    row = facts(pair["input"])
    if not row["marker_below_template"]:
        canonical_counterexamples.append({
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "facts": row,
            "input": pair["input"],
            "output": pair["output"],
        })

base_kwargs = {"seed": 314159, "sample_index": 7, "difficulty": "medium"}
variant_a = mod.generate(**base_kwargs, variant="a")
variant_b = mod.generate(**base_kwargs, variant="b")
palette_default = mod.generate(**base_kwargs, palette_kind="default")
palette_cool = mod.generate(**base_kwargs, palette_kind="cool")
grid_h_9 = mod.generate(**base_kwargs, grid_h=9)
unknown = mod.generate(**base_kwargs, typo_axis=1)

report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "generated_samples": len(sample_rows),
    "generated_marker_below_template": sum(r["marker_below_template"] for r in sample_rows),
    "generated_opposite_orientation": sum(not r["marker_below_template"] for r in sample_rows),
    "canonical_opposite_orientation_examples": canonical_counterexamples,
    "exact_axis_reproductions": {
        "variant_a_equals_variant_b": variant_a == variant_b,
        "palette_default_equals_palette_cool": palette_default == palette_cool,
        "declared_grid_h_9_observed_height": len(grid_h_9),
        "unknown_override_accepted": isinstance(unknown, list),
        "seed": base_kwargs["seed"],
        "sample_index": base_kwargs["sample_index"],
        "difficulty": base_kwargs["difficulty"],
    },
}
out = Path(__file__).with_name("orientation_and_axes.json")
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "canonical_opposite_orientation_examples"}, indent=2))
print(f"wrote {out}")
