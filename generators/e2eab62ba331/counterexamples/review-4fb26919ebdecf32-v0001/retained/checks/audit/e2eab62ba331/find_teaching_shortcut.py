from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / "e2eab62ba331" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_e2eab62ba331", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def target_mask_only(grid):
    facts = mod._rule_facts(grid)
    target = facts["target"]
    return [[value if value in (0, target) else 0 for value in row] for row in facts["output"]]

record = None
for band in ("easy", "medium", "hard"):
    for seed in range(5000):
        for start in range(25):
            grids = [mod.generate(seed, start + i, difficulty=band) for i in range(4)]
            outputs = [mod.rule_mirror(grid) for grid in grids]
            if not all(target_mask_only(grid) == out for grid, out in zip(grids[:3], outputs[:3])):
                continue
            if target_mask_only(grids[3]) == outputs[3]:
                continue
            record = {
                "task_id": mod.TASK_ID,
                "generator_version": mod.VERSION,
                "band": band,
                "seed": seed,
                "start_sample_index": start,
                "n_demos": 3,
                "shortcut": "crop the selected object's bounding box, but erase every nonzero color other than the selector color",
                "profiles": [mod.observe_overrides(grid)["scene_profile"] for grid in grids],
                "demos": [
                    {"input": grid, "authority_output": out, "shortcut_output": target_mask_only(grid)}
                    for grid, out in zip(grids[:3], outputs[:3])
                ],
                "query": {
                    "input": grids[3],
                    "authority_output": outputs[3],
                    "shortcut_output": target_mask_only(grids[3]),
                },
            }
            break
        if record:
            break
    if record:
        break
if record is None:
    raise SystemExit("no counterexample found")
out = Path(__file__).with_name("teaching_shortcut.json")
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({k: record[k] for k in ("band", "seed", "start_sample_index", "profiles")}, indent=2))
print(out)
