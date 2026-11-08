from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src")]
path = REPO / "generators/a290047cba7e/generator.py"
spec = importlib.util.spec_from_file_location("audit_a290047cba7e", path)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

pairs = []
for seed in range(20):
    warm = mod.generate(seed, 3, difficulty="medium", palette_kind="warm")
    cool = mod.generate(seed, 3, difficulty="medium", palette_kind="cool")
    pairs.append({"seed": seed, "warm_sha256": digest(warm), "cool_sha256": digest(cool),
                  "identical": warm == cool,
                  "nonzero_palette": sorted({v for row in warm for v in row if v})})

degenerates = {}
for name in mod.DEGENERATE_TEXTURES:
    grid = mod.generate(1, 0, texture=name)
    degenerates[name] = {"self_check": mod.self_check(grid),
                         "nonzero_palette": sorted({v for row in grid for v in row if v})}
result = {
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "advertised_palette_axis_draws": len(pairs),
    "warm_equals_cool_all_draws": all(row["identical"] for row in pairs),
    "draws": pairs,
    "summary_claims_distinct_random_colors": "DISTINCT non-{0, 7} color" in mod.SUMMARY,
    "ordinary_generated_palette": pairs[0]["nonzero_palette"],
    "degenerate_self_checks": degenerates,
}
assert result["warm_equals_cool_all_draws"]
assert result["ordinary_generated_palette"] == [1]
assert any(info["self_check"] for info in degenerates.values())
out = Path(__file__).with_name("dead_axes.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({
    "task_id": result["task_id"],
    "warm_equals_cool_all_draws": result["warm_equals_cool_all_draws"],
    "ordinary_generated_palette": result["ordinary_generated_palette"],
    "degenerate_self_checks": result["degenerate_self_checks"],
}, indent=2))
