"""Score bounded audit rivals against labels returned by public apply."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from rivals import cap_two_per_column, shared_chains_only_at_edges

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
GENERATOR = ROOT / "WORK/repo/generators/a2d296c74658/generator.py"
sys.path.insert(0, str(ROOT / "WORK/repo/shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_a2d296c74658_score", GENERATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
prepared = json.loads((OUT / "prepared-probe.json").read_text())
authority = json.loads((OUT / "racket.json").read_text())
assert authority["generator_sha256"] == prepared["generator_sha256"]
assert authority["executed_rule_hash"] == prepared["declared_rule_hash"]
assert hashlib.sha256(GENERATOR.read_bytes()).hexdigest() == prepared["generator_sha256"]
assert len(authority["results"]) == len(prepared["cases"])


def differences(expected, actual):
    assert len(expected) == len(actual)
    return [{"row": r, "column": c, "authority": expected[r][c], "rival": actual[r][c]}
            for r in range(len(expected)) for c in range(len(expected[0]))
            if expected[r][c] != actual[r][c]]


cases = []
for original, result in zip(prepared["cases"], authority["results"]):
    assert result["input"] == original["input"]
    assert result["valid_output"] and result["error"] is None
    case = dict(original)
    case["output"] = result["output"]
    case["cap_two_differences"] = differences(case["output"], cap_two_per_column(case["input"]))
    case["edge_chain_differences"] = differences(case["output"], shared_chains_only_at_edges(case["input"]))
    if "supplied_output" in case:
        assert case["supplied_output"] == case["output"]
    cases.append(case)
lookup = {case["name"]: case for case in cases}

ordinary_windows = []
rotation_rows = []
for seed in (0, 1):
    for start in range(5):
        pairs = [lookup[f"ordinary_seed{seed}_index{i}"] for i in range(start, start + 4)]
        matches = [not pair["cap_two_differences"] for pair in pairs]
        ordinary_windows.append({"seed": seed, "difficulty": "easy", "start": start,
                                 "profiles": [pair["profile"] for pair in pairs],
                                 "cap_two_matches": matches,
                                 "ambiguous": all(matches[:3]) and not matches[3],
                                 "declared_hook_reasons": module.lesson_identifiable(pairs[:3], pairs[3])})
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            query = pairs[query_index]
            rotation_rows.append({"seed": seed, "difficulty": "easy", "start": start,
                                  "query_position": query_index,
                                  "ambiguous": all(not d["cap_two_differences"] for d in demos)
                                               and bool(query["cap_two_differences"]),
                                  "declared_hook_reasons": module.lesson_identifiable(demos, query)})

lesson = [lookup[f"ordinary_seed0_index{i}"] for i in range(3, 7)]
(OUT / "reproduced-lesson.json").write_text(json.dumps({"seed": 0, "difficulty": "easy", "start": 3,
                                                         "overrides": {}, "train": lesson[:3], "test": [lesson[3]]}, indent=2) + "\n")
by_kind = {}
for kind in sorted({case["kind"] for case in cases}):
    group = [case for case in cases if case["kind"] == kind]
    by_kind[kind] = {"total": len(group),
                     "cap_two_matches": sum(not case["cap_two_differences"] for case in group),
                     "edge_chain_matches": sum(not case["edge_chain_differences"] for case in group)}
report = {
    "task_id": "a2d296c74658", "classification": "reproduced ordinary-lesson teaching defect",
    "generator_sha256": authority["generator_sha256"],
    "executed_rule_hash": authority["executed_rule_hash"],
    "rule_text_sha256": authority["rule_text_sha256"],
    "rivals_sha256": hashlib.sha256((OUT / "rivals.py").read_bytes()).hexdigest(),
    "reference_applications_valid": len(cases), "case_counts": by_kind,
    "ordinary_windows_checked": len(ordinary_windows),
    "ordinary_ambiguous_windows": sum(row["ambiguous"] for row in ordinary_windows),
    "query_rotations_checked": len(rotation_rows),
    "ambiguous_query_rotations": sum(row["ambiguous"] for row in rotation_rows),
    "declared_hook_rejections_on_ordinary_windows": sum(bool(row["declared_hook_reasons"]) for row in ordinary_windows),
    "declared_hook_rejections_on_rotations": sum(bool(row["declared_hook_reasons"]) for row in rotation_rows),
    "primary_witness": {"seed": 0, "sample_start": 3, "difficulty": "easy", "overrides": {},
                        "profiles": [pair["profile"] for pair in lesson],
                        "cap_two_matches": [not pair["cap_two_differences"] for pair in lesson],
                        "query_differences": lesson[3]["cap_two_differences"],
                        "self_checks": [pair["self_check"] for pair in lesson],
                        "lesson_hook_reasons": module.lesson_identifiable(lesson[:3], lesson[3])},
    "secondary_structural_observation": {
        "classification": "suspected support shortcut; no ordinary-query mismatch observed",
        "rival": "shared_chains_only_at_edges",
        "ordinary_and_canonical_fit": all(not case["edge_chain_differences"] for case in cases if case["kind"] in ("ordinary", "canonical")),
        "authored_input_accepted": lookup["authored_interior_shared_chain"]["self_check"] == [],
        "authored_input_differences": lookup["authored_interior_shared_chain"]["edge_chain_differences"],
    },
    "ordinary_windows": ordinary_windows,
    "query_rotations": rotation_rows,
    "bounded_coverage": "4 canonical pairs; easy seeds 0 and 1, indices 0..7; 8 hard-band override extrema at seed 37/index 1; one authored interior-chain input. No corpus or all-seed claim.",
}
(OUT / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k not in ("ordinary_windows", "query_rotations")}, indent=2))
