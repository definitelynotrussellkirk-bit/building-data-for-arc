"""Verify saved live labels and retain compact audit conclusions."""
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import find_root


folder = Path(__file__).resolve().parent
probe = json.loads((folder / "probe.json").read_text())
live = json.loads((folder / "racket.json").read_text())
assert live["generator_sha256"] == probe["generator_sha256"]
assert live["executed_rule_hash"] == live["catalog_rule_hash"] == probe["rule_hash"]
assert len(live["results"]) == len(probe["samples"]) == 31
assert not probe["rejections"] and not probe["override_mismatches"]
assert all(not row["validator_errors"] and row["independent_oracle_matches"] for row in probe["canonical_results"])
names = ("center_pivot", "first_color_only", "largest_component_only")
refuted = {name: 0 for name in names}
for sample, row in zip(probe["samples"], live["results"]):
    assert row["error"] is None and row["output"] == sample["independent_output"]
    for name in names:
        refuted[name] += row["output"] != sample["rival_outputs"][name]
lessons = []
for start in (0, 5, 10):
    for query in range(start, start + 5):
        demos = [i for i in range(start, start + 5) if i != query]
        survivors = [name for name in names
                     if all(probe["samples"][i]["rival_outputs"][name] == live["results"][i]["output"] for i in demos)
                     and probe["samples"][query]["rival_outputs"][name] != live["results"][query]["output"]]
        assert not survivors
        lessons.append({"difficulty": probe["samples"][start]["difficulty"], "query_index": query, "surviving_declared_rivals": survivors})
source = find_root(Path.cwd()) / "generators" / probe["task_id"] / "generator.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == probe["generator_sha256"]
spec = importlib.util.spec_from_file_location("audit_target_checked", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
bad_calls = [{"grid_h": True}, {"grid_w": 6.0}, {"foreground_size": "3"}, {"grid_h": 5},
             {"grid_w": 11}, {"foreground_size": 9}, {"profile": "typo"}, {"unknown_axis": 1}]
invalid_results = []
for overrides in bad_calls:
    try:
        module.generate(17, 0, **overrides)
    except (ValueError, TypeError) as error:
        invalid_results.append({"overrides": overrides, "exception": type(error).__name__, "message": str(error)})
    else:
        raise AssertionError(("invalid override silently accepted", overrides))
witness = dict(probe["samples"][18])
witness.update(task_id=probe["task_id"], generator_sha256=probe["generator_sha256"],
               rule_hash=live["executed_rule_hash"], rule_text_sha256=live["rule_text_sha256"],
               actual_live_racket_output=live["results"][18]["output"])
assert all(out != witness["actual_live_racket_output"] for out in witness["rival_outputs"].values())
(folder / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")
summary = {"task_id": probe["task_id"], "generator_sha256": probe["generator_sha256"],
           "rule_hash": live["executed_rule_hash"], "rule_text_sha256": live["rule_text_sha256"],
           "reproduced_defects": [], "generated_live_matches": 31, "canonical_pairs_checked": 3,
           "validator_rejections": 0, "override_mismatches": 0, "rival_refutations": refuted,
           "default_all_query_rotations": lessons, "invalid_override_rejections": invalid_results,
           "witness_index": 18}
(folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: summary[k] for k in ("task_id", "generated_live_matches", "reproduced_defects", "rival_refutations")}))
