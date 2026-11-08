from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator
from puzzle_generators.helpers.selfcheck import components

TASK_ID = "f1ee291071fd"
OUT = Path(__file__).with_name("n_blobs_override.json")
root = find_root(__file__)
gen, path, source_sha = load_selected_generator(TASK_ID, root=root)
seed, sample_index, difficulty = 11, 7, "hard"
overrides = {"two": 2, "six": 6, "invalid_999": 999, "invalid_text": "not-an-int"}
grids = {name: gen.generate(seed, sample_index, difficulty=difficulty, n_blobs=value) for name, value in overrides.items()}
base = grids["two"]
report = {
    "schema": "arcpuzzles-audit-override-counterexample-v1",
    "task_id": TASK_ID,
    "generator_path": str(path.relative_to(root)),
    "generator_sha256": source_sha,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "declared_axis": gen.AXES["n_blobs"],
    "requested_values": overrides,
    "all_outputs_identical": len({json.dumps(v) for v in grids.values()}) == 1,
    "outputs_sha256": {k: hashlib.sha256(json.dumps(v, separators=(",", ":")).encode()).hexdigest() for k, v in grids.items()},
    "observed_color1_components": len(components(base, colors={1})),
    "self_check": gen.self_check(base, difficulty=difficulty),
    "grid": base,
    "conclusion": "n_blobs is declared as an exact axis but is never consumed; valid, out-of-range, and wrong-type overrides all return the identical grid.",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"out": str(OUT), "source_sha256": source_sha, "all_outputs_identical": report["all_outputs_identical"], "observed_color1_components": report["observed_color1_components"]}, indent=2))
