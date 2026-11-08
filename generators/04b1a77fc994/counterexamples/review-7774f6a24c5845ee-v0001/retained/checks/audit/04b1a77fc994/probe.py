from pathlib import Path
import sys, json, hashlib
REPO = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import find_root, canonical_path, canonical_pairs, load_selected_generator
TASK = "04b1a77fc994"
OUT = Path(__file__).resolve().parent
root = find_root(REPO)
mod, source, source_hash = load_selected_generator(TASK, root=root)
rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if json.loads(line).get("task_id") == TASK]
assert len(rows) == 1
rule = rows[0]["program_solution"]
rule_sha = hashlib.sha256(rule.encode()).hexdigest()
def rival(grid):
    result = [[0 for c in row] for row in grid]
    for obj in mod._components(grid):
        for r, c in obj["cells"]:
            result[r][c] = obj["touch_count"] + 1
    return result
records = []
for pair in canonical_pairs(TASK, root=root):
    grid = pair["input"]
    records.append({"kind": "canonical", "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"], "input": grid, "canonical_output": pair["output"], "self_check": mod.self_check(grid), "mirror": mod.rule_mirror(grid), "rival": rival(grid)})
for difficulty in ("easy", "medium", "hard"):
    for sample_index in range(12):
        grid = mod.generate(0, sample_index, difficulty=difficulty)
        records.append({"kind": "generated", "seed": 0, "sample_index": sample_index, "difficulty": difficulty, "overrides": {}, "input": grid, "self_check": mod.self_check(grid, difficulty=difficulty, meta={}), "facts": mod.profile_facts(grid), "mirror": mod.rule_mirror(grid), "rival": rival(grid)})
assert all(row["self_check"] == [] for row in records)
assert all(row["mirror"] == row["canonical_output"] == row["rival"] for row in records if row["kind"] == "canonical")
manifest = {"task_id": TASK, "generator_source_path": str(source.relative_to(root)), "generator_sha256": source_hash, "declared_rule_hash": mod.RULE_HASH, "canonical_rule_text_sha256": rule_sha, "canonical_pairs": 4, "generated_draws": 36, "seed": 0, "sample_index_range": [0, 11], "bands": ["easy", "medium", "hard"], "overrides": {}, "rival": "monochromatic 4-connected object color = touched outer borders + 1", "records": records}
(OUT / "instances.json").write_text(json.dumps(manifest, indent=2) + "\n")
(OUT / "input.json").write_text(json.dumps([row["input"] for row in records]) + "\n")
print(json.dumps({k:v for k,v in manifest.items() if k != "records"}, indent=2))
