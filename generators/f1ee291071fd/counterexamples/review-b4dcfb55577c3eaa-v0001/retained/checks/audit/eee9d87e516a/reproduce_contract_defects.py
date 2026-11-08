from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID = "eee9d87e516a"
OUT = Path(__file__).with_name("contract_defects.json")
root = find_root(__file__)
gen, path, source_sha = load_selected_generator(TASK_ID, root=root)
seed, sample_index, difficulty = 11, 7, "medium"
variants = {
    "palette_warm": gen.generate(seed, sample_index, difficulty=difficulty, palette_kind="warm"),
    "palette_cool": gen.generate(seed, sample_index, difficulty=difficulty, palette_kind="cool"),
    "texture_warm": gen.generate(seed, sample_index, difficulty=difficulty, texture="warm"),
    "texture_cool": gen.generate(seed, sample_index, difficulty=difficulty, texture="cool"),
}
errors = {}
for name, override in {
    "n_patterns_min": {"n_patterns": 1},
    "n_patterns_max": {"n_patterns": 6},
    "grid_h_min": {"grid_h": 5},
    "grid_w_max": {"grid_w": 14},
}.items():
    try:
        gen.generate(seed, sample_index, difficulty=difficulty, **override)
        errors[name] = None
    except Exception as exc:
        errors[name] = {"type": type(exc).__name__, "message": str(exc), "override": override}
report = {
    "schema": "arcpuzzles-audit-contract-counterexample-v1",
    "task_id": TASK_ID,
    "generator_path": str(path.relative_to(root)),
    "generator_sha256": source_sha,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "declared_axes": gen.AXES,
    "ghost_axis_counterexample": {
        "all_four_outputs_identical": len({json.dumps(v) for v in variants.values()}) == 1,
        "outputs_sha256": {k: hashlib.sha256(json.dumps(v, separators=(",", ":")).encode()).hexdigest() for k, v in variants.items()},
        "grid": variants["palette_warm"],
    },
    "advertised_valid_values_rejected": errors,
    "conclusion": "palette_kind and helpful texture overrides are observationally ignored; several values declared valid by AXES are rejected in medium mode.",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"out": str(OUT), "source_sha256": source_sha, "ghost_axes_identical": report["ghost_axis_counterexample"]["all_four_outputs_identical"], "rejected": sorted(k for k,v in errors.items() if v)}, indent=2))
