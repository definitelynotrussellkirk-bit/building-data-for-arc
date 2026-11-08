"""Verify focused findings against new public Racket receipts, without source edits."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "shared/runtime"))


def load(task):
    directory = BASE / task
    probe = json.loads((directory / "probe.json").read_text())
    actual = json.loads((directory / "racket.json").read_text())
    source = REPO / "generators" / task / "generator.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash == probe["generator_sha256"] == actual["generator_sha256"]
    spec = importlib.util.spec_from_file_location("verify_" + task, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert actual["executed_rule_hash"] == module.RULE_HASH
    assert actual["rule_hash_matches_catalog"]
    assert len(actual["results"]) == len(probe["cases"])
    for case, result in zip(probe["cases"], actual["results"], strict=True):
        assert result["valid_output"] and result["error"] is None
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        assert case["input"] == result["input"]
        assert case["python_mirror_output"] == result["output"]
        if case.get("canonical_stored_output") is not None:
            assert case["canonical_stored_output"] == result["output"]
    return directory, probe, actual, module


def difference(reference, prediction):
    return [{"row": r, "column": c, "expected_racket": value,
             "rival_actual": prediction[r][c]}
            for r, row in enumerate(reference) for c, value in enumerate(row)
            if value != prediction[r][c]]


def identities(actual):
    return {key: actual[key] for key in ("task_id", "generator_sha256",
            "executed_rule_hash", "rule_text_sha256")}


directory, probe, actual, module = load("8604dc774d22")
rotations = []
ordered = []
for start, band in ((0, "easy"), (5, "medium"), (10, "hard")):
    pairs = [{"input": result["input"], "output": result["output"]}
             for result in actual["results"][start:start + 5]]
    ordered.append({"difficulty": band, "hook_reasons": module.lesson_identifiable(pairs[:4], pairs[4])})
    for query_index in range(5):
        demo_indices = [i for i in range(5) if i != query_index]
        demos = [pairs[i] for i in demo_indices]
        query = pairs[query_index]
        for name, rival in module.SEMANTIC_RIVALS.items():
            if all(rival(demo["input"]) == demo["output"] for demo in demos):
                prediction = rival(query["input"])
                if prediction != query["output"]:
                    rotations.append({"difficulty": band, "seed": 31,
                        "sample_indices": list(range(5)), "overrides": {},
                        "query_sample_index": query_index,
                        "demo_sample_indices": demo_indices, "rival": name,
                        "demonstrations": demos, "query": query,
                        "rival_query_output": prediction,
                        "differing_cells": difference(query["output"], prediction),
                        "lesson_identifiable_reasons": module.lesson_identifiable(demos, query)})
assert all(not item["hook_reasons"] for item in ordered)
assert len(rotations) == 6
assert {(r["difficulty"], r["query_sample_index"], r["rival"]) for r in rotations} == {
    (band, index, rival) for band in ("easy", "medium", "hard")
    for index, rival in ((1, "color_blind_l"), (3, "first_two_green_ls"))}
finding8604 = {**identities(actual), "status": "reproduced_existing_teaching_issue",
    "scope": "Fresh seed 31; five scheduled pairs in each band plus five canonical pairs.",
    "public_racket_cases": 20, "public_domain_valid_cases": 20,
    "mirror_matches_racket": 20, "canonical_pairs_match_racket": 5,
    "ordered_lessons_accepted": 3, "ordered_lessons_checked": 3,
    "held_out_partitions_checked": 15, "ambiguous_partitions": 6,
    "ordered_lessons": ordered, "failures": rotations,
    "limitations": "This confirms arbitrary-query fragility. The ordered sampler retained both required witnesses; no default input or label defect was found in this scope."}
(directory / "finding.json").write_text(json.dumps(finding8604, indent=2) + "\n")

directory, probe, actual, module = load("a76216bfa3e8")
default_indices = [i for i, case in enumerate(probe["cases"]) if case["kind"] == "default"]
canonical_indices = [i for i, case in enumerate(probe["cases"]) if case["kind"] == "canonical"]
assert len(default_indices) == 24 and len(canonical_indices) == 4
default_agreements = sum(probe["cases"][i]["rival_output"] == actual["results"][i]["output"] for i in default_indices)
canonical_agreements = sum(probe["cases"][i]["rival_output"] == actual["results"][i]["output"] for i in canonical_indices)
assert default_agreements == 24 and canonical_agreements == 0
demo_indices = probe["lesson_demo_case_indices"]
qi = probe["legal_override_query_case_index"]
demos = [{"input": actual["results"][i]["input"], "output": actual["results"][i]["output"]} for i in demo_indices]
query = {"input": actual["results"][qi]["input"], "output": actual["results"][qi]["output"]}
assert all(probe["cases"][i]["rival_output"] == demos[n]["output"] for n, i in enumerate(demo_indices))
prediction = probe["cases"][qi]["rival_output"]
assert prediction != query["output"]
hook = module.lesson_identifiable(demos, query)
assert hook == []
query_case = probe["cases"][qi]
assert query_case["seed"] == 31 and query_case["overrides"] == {"marker_col_parity": 1}
findinga762 = {**identities(actual), "status": "reproduced_existing_distribution_and_hook_issue",
    "scope": "Fresh seed 31; eight default profiles in all three bands, four unique canonical pairs, one declared legal parity override.",
    "public_racket_cases": 29, "public_domain_valid_cases": 29,
    "mirror_matches_racket": 29, "canonical_pairs_match_racket": 4,
    "default_morphology_rival_agreements": default_agreements,
    "default_cases": 24, "canonical_morphology_rival_agreements": canonical_agreements,
    "canonical_cases": 4, "morphology_parity_lookup": probe["lookup"],
    "query_generation": {key: query_case[key] for key in ("seed", "sample_index", "difficulty", "overrides", "observed_axes", "source_parity", "morphology_lookup_parity")},
    "demonstration_generation": [{key: probe["cases"][i][key] for key in ("seed", "sample_index", "difficulty", "overrides")} for i in demo_indices],
    "demonstrations": demos, "query": query, "rival_query_output": prediction,
    "differing_cells": difference(query["output"], prediction),
    "lesson_identifiable_reasons": hook,
    "limitations": "The overriding query is lawful but is not emitted by the correlated default schedule. The rival is not canonical-fitting. No wrong Racket label or illegal input was found in these 29 cases."}
(directory / "finding.json").write_text(json.dumps(findinga762, indent=2) + "\n")

print(json.dumps({"verification": "passed", "8604dc774d22": {
    "racket_cases": 20, "ambiguous_rotations": "6/15", "ordered_accepted": "3/3"},
    "a76216bfa3e8": {"racket_cases": 29, "default_rival_agreements": "24/24",
    "canonical_rival_agreements": "0/4", "override_query_hook_reasons": hook,
    "override_query_differing_cells": len(findinga762["differing_cells"])}}))
