"""Run through the packet wrapper (effective cwd: repo); no private runners."""
from pathlib import Path
import hashlib
import importlib.util
import json

from reviewer_support import canonical_pairs, find_root

task = "8e7f766c96bf"
root = find_root(Path.cwd())
source = root / "generators" / task / "generator.py"
spec = importlib.util.spec_from_file_location("question_generator", source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
out = root.parent / "checks" / "question"
out.mkdir(parents=True, exist_ok=True)
overrides = {"grid_h": 11, "grid_w": 17, "n_squares": 1, "texture": "contrast"}
grid = gen.generate(17, 1, difficulty="medium", **overrides)
pairs = canonical_pairs(task, root=root)
fits = {name: {"matched": sum(rival(p["input"]) == p["output"] for p in pairs),
               "total": len(pairs)} for name, rival in gen.CANONICAL_SHORTCUTS.items()}
record = {"task_id": task, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "rule_hash": gen.RULE_HASH, "seed": 17, "sample_index": 1,
          "difficulty": "medium", "overrides": overrides,
          "self_check": gen.self_check(grid), "observed": gen.observe_overrides(grid),
          "canonical_shortcut_fit": fits,
          "rival_outputs": {name: rival(grid) for name, rival in gen.LESSON_COMPETITORS.items()}}
(out / "input.json").write_text(json.dumps(grid) + "\n")
(out / "witness.json").write_text(json.dumps(record, indent=2) + "\n")
assert not record["self_check"]
assert all(item["matched"] == item["total"] for item in fits.values())
print(json.dumps({"canonical_shortcut_fit": fits, "source_sha256": record["generator_sha256"]}))
