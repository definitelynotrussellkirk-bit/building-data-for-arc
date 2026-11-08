"""Read-only source-bound reproduction of advertised texture rejection."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "b04b3279e593"
SOURCE = REPO / "generators" / TASK / "generator.py"
EXPECTED = "2999b33833dde5deb4e45f0048935b9de1abcfcbf7833b04f56de7ff97888bcd"
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(SOURCE.read_bytes()) == EXPECTED
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audited_generator_b04b3279e593", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
seed, sample_index = 0, 0
overrides = {"texture": "single_marker"}
assert "single_marker" in mod.AXES["texture"]["valid"].split("|")
grid = mod.generate(seed, sample_index, **overrides)
errors = mod.self_check(grid)
assert errors == ["expected 2-4 top-row markers, found 1"]
canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
rows = [json.loads(line) for line in canonical_path.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK]
assert len(rows) == 1
rule = rows[0]["program_solution"]
data = {
    "schema": "source-bound-generator-contract-counterexample-v1",
    "target": TASK,
    "generator_sha256": EXPECTED,
    "canonical_file_sha256": sha(canonical_path.read_bytes()),
    "canonical_record_content_hash": rows[0]["content_hash"],
    "canonical_rule_exact_sha256": sha(rule.encode()),
    "canonical_rule_hash_12": sha(" ".join(rule.split()).encode())[:12],
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": None,
    "overrides": overrides,
    "input": grid,
    "self_check_result": errors,
    "specific_defect": "AXES.texture advertises single_marker as valid, but generate(texture=single_marker) emits a grid rejected by the same source's self_check.",
    "written_rule_expected_output": [grid[0][:] for _ in grid],
    "relationship_to_prior_finding": "Independent confirmation of current needs_triage audit review-d5c9325712268b53:v0001 on the same generator source; no new semantic mismatch claim.",
}
(HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(HERE / "counterexample.json").write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"target": TASK, "generator_sha256": EXPECTED,
                  "overrides": overrides, "self_check_result": errors,
                  "canonical_rule_hash_12": data["canonical_rule_hash_12"]}))
