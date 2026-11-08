#!/usr/bin/env python3
"""Bounded source-bound probe of one predeclared unseen transform-key rival."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "shared/runtime"))

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import load_selected_generator

TID = "9fc0b6db96fe"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main():
    manifest_path = ROOT.parent / "PACKET-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    generator, source, source_sha = load_selected_generator(TID, root=ROOT)
    expected_source = manifest["files"]["repo/generators/" + TID + "/generator.py"]
    audited_source = source
    if source_sha != expected_source:
        audited_source = HERE / "generator-before.py"
        source_sha = sha(audited_source.read_bytes())
        assert source_sha == expected_source, "Retained baseline differs from supplied packet bytes"
        spec = importlib.util.spec_from_file_location("retained_peer_baseline_9fc0b6db96fe", audited_source)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
    assert source_sha == expected_source, "Audited generator differs from supplied packet bytes"
    catalog = Catalog(ROOT)
    described = catalog.describe(TID)
    rule_id = described.get("rule_task_id", TID)
    variants = catalog._variants()[rule_id]
    assert len({row["program_solution"] for row in variants}) == 1
    original = variants[0]
    program = original["program_solution"]
    old_branch = "((= key 4) (flip-lr grid))"
    new_branch = "((= key 4) (flip-ud grid))"
    assert program.count(old_branch) == 1
    rival = program.replace(old_branch, new_branch)
    assert described["rule_hash"] == generator.RULE_HASH == manifest["generators"][TID]["rule_hash"]
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    ledger_sha = sha(ledger.read_bytes())
    assert ledger_sha == manifest["files"]["repo/shared/data/canonical/puzzles.jsonl"]
    binding = {
        "task_id": TID, "generator_path": source.relative_to(ROOT).as_posix(),
        "generator_sha256": source_sha, "packet_generator_sha256": expected_source,
        "rule_task_id": rule_id, "rule_hash": described["rule_hash"],
        "canonical_program_sha256": sha(program.encode()),
        "rival_program_sha256": sha(rival.encode()),
        "canonical_ledger_sha256": ledger_sha,
        "packet_manifest_sha256": sha(manifest_path.read_bytes()),
    }
    evaluations = 0
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        def execute(rule, grid):
            nonlocal evaluations
            evaluations += 1
            return _grid(apply(rule, grid))
        def lesson_evidence(train_inputs, query_input, supplied=None):
            demos = [{"input": grid, "output": execute(program, grid)} for grid in train_inputs]
            query = {"input": query_input, "output": execute(program, query_input)}
            rival_demos = [execute(rival, pair["input"]) for pair in demos]
            rival_query = execute(rival, query_input)
            if supplied is not None:
                assert [pair["output"] for pair in demos] == [pair["output"] for pair in supplied["train"]]
                assert query["output"] == supplied["test"][0]["output"]
            return {
                "source_binding": binding, "racket": identity,
                "rival_name": "key4_means_vertical_reflection",
                "rival_description": "Use the selected rule except key 4 reflects top-bottom instead of left-right.",
                "program": program, "rival_program": rival,
                "train": demos, "test": [query],
                "rival_demo_outputs": rival_demos, "rival_query_output": rival_query,
                "demo_keys": [grid[0][0] for grid in train_inputs], "query_key": query_input[0][0],
                "rival_fits_every_demo": all(pair["output"] == answer for pair, answer in zip(demos, rival_demos)),
                "rival_changes_query": query["output"] != rival_query,
            }
        try:
            original_test = original["test"] if isinstance(original["test"], list) else [original["test"]]
            canonical = lesson_evidence([pair["input"] for pair in original["train"]],
                                       original_test[0]["input"],
                                       supplied={"train": original["train"], "test": original_test})
            canonical["origin"] = "supplied canonical visible lesson; all provided demonstrations"
            write("canonical-counterexample.json", canonical)
            found, searched = None, 0
            for seed in range(16):
                searched += 1
                grids = [generator.generate(seed, index, difficulty="hard") for index in range(4)]
                assert all(generator.self_check(grid) == [] for grid in grids)
                if grids[3][0][0] != 4:
                    continue
                candidate = lesson_evidence(grids[:3], grids[3])
                if candidate["rival_fits_every_demo"] and candidate["rival_changes_query"]:
                    found = {**candidate, "origin": "selected default generator; consecutive indices 0,1,2,3",
                             "seed": seed, "difficulty": "hard", "sample_indices": [0, 1, 2, 3],
                             "examples_needed": generator.EXAMPLES_NEEDED,
                             "lesson_identifiable_reasons": generator.lesson_identifiable(candidate["train"], candidate["test"][0])}
                    write("generated-counterexample.json", found)
                    break
        finally:
            bridge.close()
    assert source_sha == sha(audited_source.read_bytes()), "Audited source changed during probe"
    result = {
        "schema": "arcpuzzles-bounded-peer-learnability-probe-v1", "task_id": TID,
        "status": "finding" if found is not None else "bounded_no_generated_finding",
        "outcome": "unchanged", "source_binding": binding, "racket": identity,
        "racket_evaluations": evaluations, "seeds_examined": searched, "seed_bound": 16,
        "predeclared_rivals": ["key4_means_vertical_reflection"],
        "canonical_demo_keys": canonical["demo_keys"], "canonical_query_key": canonical["query_key"],
        "canonical_rival_fits_every_demo": canonical["rival_fits_every_demo"],
        "canonical_rival_changes_query": canonical["rival_changes_query"],
        "generated_finding": None if found is None else {
            "seed": found["seed"], "difficulty": found["difficulty"],
            "demo_keys": found["demo_keys"], "query_key": found["query_key"],
            "examples_needed": found["examples_needed"],
            "lesson_identifiable_reasons": found["lesson_identifiable_reasons"]},
        "limits": ["One fixed alternative key interpretation; no full battery or exhaustive rival search.",
                   "Canonical and selected generated labels were executed through protected Racket.",
                   "Generator and rule remain unchanged; no approval or training-admission claim.",
                   "Teaching repair needs explicit demonstration coverage for query-key semantics or an appropriate learned mapping contract."],
    }
    write("report.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
