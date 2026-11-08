"""Prepare bounded audit inputs; reference outputs come from public apply."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
TASK = "a2d296c74658"
GENERATOR = ROOT / "WORK/repo/generators" / TASK / "generator.py"
sys.path.insert(0, str(ROOT / "WORK/repo/shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_a2d296c74658", GENERATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def norm(grid):
    return [[int(v) for v in row] if isinstance(row, str) else list(row) for row in grid]


canonical = None
for line in (ROOT / "WORK/repo/shared/data/canonical/puzzles.jsonl").open():
    row = json.loads(line)
    if row.get("task_id") == TASK:
        assert canonical is None
        canonical = row
assert canonical is not None
tests = canonical["test"] if isinstance(canonical["test"], list) else [canonical["test"]]
canonical_pairs = [*canonical["train"], *tests]
cases = []
for index, pair in enumerate(canonical_pairs):
    cases.append({"name": f"canonical_{index}", "kind": "canonical",
                  "input": norm(pair["input"]), "supplied_output": norm(pair["output"])})

for seed in (0, 1):
    for index in range(8):
        grid = module.generate(seed, index, difficulty="easy")
        cases.append({"name": f"ordinary_seed{seed}_index{index}", "kind": "ordinary",
                      "seed": seed, "sample_index": index, "difficulty": "easy", "overrides": {},
                      "profile": module.schedule_profile(seed, index, "easy"), "input": grid})

for h, w, count in itertools.product((7, 10), (6, 9), (2, 4)):
    overrides = {"grid_h": h, "grid_w": w, "num_triplets": count}
    cases.append({"name": f"override_h{h}_w{w}_n{count}", "kind": "override",
                  "seed": 37, "sample_index": 1, "difficulty": "hard", "overrides": overrides,
                  "input": module.generate(37, 1, difficulty="hard", **overrides)})

# Same structural controls as an ordinary contrast, but the shared-endpoint
# chain is moved from a border column to an interior column. This is an
# authored domain probe, not a claimed ordinary generator output.
interior = [[0] * 9 for _ in range(9)]
for r, c, value in [(0,2,7),(2,2,7),(4,2,7),(6,2,7),
                    (0,4,7),(2,4,7),(5,4,7),
                    (0,8,7),(1,8,3),(2,8,7),(5,8,6),(7,8,6)]:
    interior[r][c] = value
cases.append({"name": "authored_interior_shared_chain", "kind": "authored_domain_probe", "input": interior})

for case in cases:
    case["self_check"] = module.self_check(case["input"])
    case["observed_overrides"] = module.observe_overrides(case["input"])
    if case["kind"] == "override":
        case["exact_override_match"] = case["observed_overrides"] == case["overrides"]

invalid_calls = []
for overrides in ({"unknown_axis": 1}, {"grid_h": 6}, {"grid_w": True}, {"num_triplets": 5}):
    record = {"overrides": overrides}
    try:
        module.generate(0, 1, difficulty="easy", **overrides)
        record["status"] = "accepted"
    except Exception as error:
        record.update({"status": "rejected", "exception_type": type(error).__name__, "error": str(error)})
    invalid_calls.append(record)

source = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "declared_rule_hash": module.RULE_HASH,
    "canonical_program_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
    "canonical_normalized_rule_hash": hashlib.sha256(" ".join(canonical["program_solution"].split()).encode()).hexdigest()[:12],
    "canonical_written_solution": canonical.get("written_solution"),
    "canonical_program_solution": canonical["program_solution"],
    "reference_labels_pending": True,
    "cases": cases,
    "invalid_override_calls": invalid_calls,
}
(OUT / "prepared-probe.json").write_text(json.dumps(source, indent=2) + "\n")
(OUT / "inputs.json").write_text(json.dumps([case["input"] for case in cases]) + "\n")
print(json.dumps({"generator_sha256": source["generator_sha256"],
                  "rule_hash": source["declared_rule_hash"], "case_count": len(cases),
                  "case_kinds": {kind: sum(c["kind"] == kind for c in cases) for kind in sorted({c["kind"] for c in cases})},
                  "invalid_inputs": [c["name"] for c in cases if c["self_check"]],
                  "override_mismatches": [c["name"] for c in cases if c.get("exact_override_match") is False],
                  "invalid_override_calls": invalid_calls,
                  "canonical_written_solution": source["canonical_written_solution"],
                  "canonical_program_solution": source["canonical_program_solution"]}, indent=2))
