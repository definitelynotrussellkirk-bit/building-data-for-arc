"""Read-only morphology/parity support audit; reference labels come from public apply."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "a76216bfa3e8"
SOURCE = REPO / "generators" / TASK / "generator.py"
SHA = "0d4fe803e3bc4897819aabd6f32acea8b56fe1aa8ff3215b11782ce9f8f2bed6"
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(SOURCE.read_bytes()) == SHA
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_a76216bfa3e8", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# This rival uses morphology to choose destination parity, rather than reading
# the actual source-cell parity. The schedule supplies this fixed lookup.
lookup = {name: (i % 4 // 2, i % 2) for i, name in enumerate(mod._PATTERN_NAMES)}
def rival(grid):
    return mod._stamp_with_selector(
        grid, lambda row, col, info:
        (row % 2, col % 2) == lookup[info["marker_pattern"]])

canonical = REPO / "shared/data/canonical/puzzles.jsonl"
rows = [json.loads(line) for line in canonical.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK]
assert rows and len({row["program_solution"] for row in rows}) == 1
rule = rows[0]["program_solution"]
cases = []
def add(kind, grid, seed=None, sample_index=None, difficulty=None, overrides=None,
        canonical_output=None):
    info = mod._analysis(grid)
    assert mod.self_check(grid) == []
    cases.append({"kind": kind, "seed": seed, "sample_index": sample_index,
                  "difficulty": difficulty, "overrides": overrides or {},
                  "input": grid, "self_check_result": mod.self_check(grid),
                  "observed_axes": mod.observe_overrides(grid),
                  "source_parity": [info["marker_row_parity"], info["marker_col_parity"]],
                  "morphology_lookup_parity": list(lookup[info["marker_pattern"]]),
                  "rival_output": rival(grid), "python_mirror_output": mod.rule_mirror(grid),
                  "canonical_stored_output": canonical_output})

for band in ("easy", "medium", "hard"):
    for index in range(8):
        add("default", mod.generate(17, index, difficulty=band), 17, index, band)
seen = set()
for row in rows:
    for split in ("train", "test"):
        for pair in row[split]:
            key = json.dumps(pair, sort_keys=True)
            if key not in seen:
                seen.add(key)
                add("canonical", pair["input"], canonical_output=pair["output"])
overrides = {"marker_col_parity": 1}
add("declared_legal_override", mod.generate(17, 0, difficulty="medium", **overrides),
    17, 0, "medium", overrides)
counter = cases[-1]
assert counter["source_parity"] == [0, 1]
assert counter["morphology_lookup_parity"] == [0, 0]
assert counter["rival_output"] != counter["python_mirror_output"]
demos = [{"input": case["input"], "output": case["python_mirror_output"]}
         for case in cases[8:12]]
query = {"input": counter["input"], "output": counter["python_mirror_output"]}
data = {"schema": "source-bound-morphology-parity-audit-v1", "target": TASK,
        "generator_sha256": SHA, "canonical_file_sha256": sha(canonical.read_bytes()),
        "canonical_rule_exact_sha256": sha(rule.encode()),
        "canonical_rule_hash_12": sha(" ".join(rule.split()).encode())[:12],
        "lookup": {name: list(parity) for name, parity in lookup.items()},
        "cases": cases, "lesson_demo_case_indices": list(range(8, 12)),
        "legal_override_query_case_index": len(cases) - 1,
        "lesson_identifiable_with_legal_override_query": mod.lesson_identifiable(demos, query),
        "review_index_present": (REPO / "generators" / TASK / "evidence/review_index.json").exists()}
(HERE / "inputs.json").write_text(json.dumps({"inputs": [case["input"] for case in cases]}) + "\n")
(HERE / "probe.json").write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"target": TASK, "generator_sha256": SHA, "cases": len(cases),
                  "default_mirror_rival_agreements": sum(c["rival_output"] == c["python_mirror_output"] for c in cases if c["kind"] == "default"),
                  "canonical_stored_rival_agreements": sum(c["rival_output"] == c["canonical_stored_output"] for c in cases if c["kind"] == "canonical"),
                  "legal_override_query_diverges_from_rival": True,
                  "lesson_identifiable": data["lesson_identifiable_with_legal_override_query"]}))
