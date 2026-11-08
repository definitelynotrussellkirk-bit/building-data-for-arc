"""Prepare the six eligible easy-band inputs used by the shared defect heuristic."""
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator
root = find_root(__file__)
gen, source, sha = load_selected_generator("75ba893e1e36", root=root)
out = root.parent / "checks/mutation-lawfulness/linter-final-inputs"
out.mkdir()
rows = [{"seed": seed, "sample_index": seed, "difficulty": "easy", "overrides": {},
         "input": gen.generate(seed, seed, difficulty="easy")} for seed in range(1, 7)]
assert all(gen.self_check(row["input"], difficulty="easy") == [] for row in rows)
(out / "inputs.json").write_text(json.dumps({"inputs": [row["input"] for row in rows]}, indent=2) + "\n")
(out / "settings.json").write_text(json.dumps({"task_id": "75ba893e1e36", "generator_sha256": sha,
    "generator_path": str(source), "source": rows,
    "scope": "First six accepted default easy draws, seed=sample_index=1..6, as in generator_defect_lint."}, indent=2) + "\n")
print(json.dumps({"inputs": len(rows), "generator_sha256": sha, "out": str(out)}))
