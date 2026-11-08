import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

root = find_root(Path.cwd())
gen, source, source_sha = load_selected_generator("c5f62271ea44", root=root)
home = Path(__file__).resolve().parent
report = json.loads((home / "report.json").read_text())
inputs = json.loads((home / "witness-inputs.json").read_text())
actual = json.loads((home / "racket.json").read_text())
assert source_sha == report["generator_sha256"]
assert len(inputs) == len(actual["results"]) == 10
checks = []
for witness in report["witnesses"]:
    left, right = witness["same_projection_different_query_transforms"]
    assert left["query_transform"] != right["query_transform"]
    for key in ("held_out_position", "ordered_demo_transforms", "source_blue_corner", "target_blue_corner"):
        assert left[key] == right[key]
    for row in (left, right):
        index = row["racket_input_index"]
        grid = inputs[index]
        result = actual["results"][index]
        assert result["error"] is None and result["valid_output"]
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid)["symmetry"] == row["query_transform"]
        assert result["output"] == gen.rule_mirror(grid)
        checks.append({"index": index, "held_out_position": row["held_out_position"],
                       "seed": row["seed"], "sample_index": row["sample_index"],
                       "symmetry": row["query_transform"], "racket_matches": True})
receipt = {"status": "passed", "generator_sha256": source_sha, "actual_racket_inputs": 10,
           "collision_pairs": 5, "checks": checks,
           "files_sha256": {name: hashlib.sha256((home / name).read_bytes()).hexdigest()
                            for name in ("report.json", "witness-inputs.json", "racket.json", "verify.py")},
           "scope": "Validates five observed projection collisions, one at each known holdout position; not all shortcuts."}
(home / "verification.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: receipt[k] for k in ("status", "actual_racket_inputs", "collision_pairs", "generator_sha256")}))
