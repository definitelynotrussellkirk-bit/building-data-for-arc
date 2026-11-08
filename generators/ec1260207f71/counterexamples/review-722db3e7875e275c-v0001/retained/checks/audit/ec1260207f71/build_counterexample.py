from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = ROOT / "repo/generators/ec1260207f71/generator.py"
spec = importlib.util.spec_from_file_location("audit_ec1260207f71", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

seed = 2
sample_index = 33
difficulty = "easy"
grids = [mod.generate(seed, sample_index + i, difficulty=difficulty) for i in range(5)]
observed = [mod.observe_overrides(grid) for grid in grids]
assert [item["dot_band"] for item in observed[:4]] == ["upper"] * 4
assert observed[4]["dot_band"] == "lower"
assert all(mod.self_check(grid) == [] for grid in grids)

out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
metadata = {
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "declared_rule_hash": mod.RULE_HASH,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "n_train": 4,
    "n_test": 1,
    "observed": observed,
    "validator_errors": [mod.self_check(grid) for grid in grids],
    "rival": "upper_only: apply the selected offset-transfer rule only when the dotted bar is upper; otherwise leave the input unchanged",
}
(out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps(metadata, indent=2))
