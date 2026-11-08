"""Score the retained audit inputs only against the public apply receipt."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root
from audit_364829da8490 import TASK, digest, load_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, required=True)
    args = parser.parse_args()
    prepared = json.loads((args.audit_dir / "prepared.json").read_text())
    receipt = json.loads((args.audit_dir / "racket.json").read_text())
    root = find_root(__file__)
    gen, source = load_generator(root)
    assert prepared["generator_sha256"] == receipt["generator_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(prepared["rows"]) == len(receipt["results"])
    pairs = []
    for row, result in zip(prepared["rows"], receipt["results"]):
        assert result["input"] == row["input"] and result["error"] is None and result["valid_output"]
        pairs.append({"input": row["input"], "output": result["output"]})
    canonical = canonical_pairs(TASK, root=root)
    assert all(pair == {"input": old["input"], "output": old["output"]} for pair, old in zip(pairs[:len(canonical)], canonical))
    identity = {key: receipt[key] for key in ("task_id", "generator_sha256", "catalog_rule_hash",
                "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")}
    group_counts = Counter(row["kind"] for row in prepared["rows"])
    match_counts = Counter()
    declared = {}
    for row, pair in zip(prepared["rows"], pairs):
        if row["rival_8_connected_output"] == pair["output"]:
            match_counts[row["kind"]] += 1
        for name, output_hash in row["declared_rival_output_sha256"].items():
            counts = declared.setdefault(name, Counter())
            counts[row["kind"] + "_count"] += 1
            counts[row["kind"] + "_matches"] += output_hash == digest(pair["output"])
    mutated_index = next(i for i, row in enumerate(prepared["rows"]) if row["kind"] == "validator_accepted_corner_mutation")
    fractional_index = next(i for i, row in enumerate(prepared["rows"]) if row["kind"] == "invalid_fractional_override_accepted")
    mutated = prepared["rows"][mutated_index]
    demonstration_indices = [i for i, row in enumerate(prepared["rows"])
        if row["kind"] == "generated_default" and row["replay"]["seed"] == 17 and row["replay"]["difficulty"] == "medium"]
    demos = [deepcopy(pairs[i]) for i in demonstration_indices]
    query = deepcopy(pairs[mutated_index])
    hook_reasons = gen.lesson_identifiable(demos, query)
    assert len(demos) == 4 and hook_reasons == []
    assert all(prepared["rows"][i]["rival_8_connected_output"] == pairs[i]["output"] for i in demonstration_indices)
    assert mutated["rival_8_connected_output"] != query["output"]
    differences = [{"row": r, "col": c, "racket": query["output"][r][c],
                    "rival": mutated["rival_8_connected_output"][r][c]}
                   for r in range(len(query["input"])) for c in range(len(query["input"][0]))
                   if query["output"][r][c] != mutated["rival_8_connected_output"][r][c]]
    commands = [
        {"cwd": "packet_root", "effective_cwd": "repo", "argv": ["python3", "run_with_racket.py", "python3",
          "generators/b86607f34b8b/workspace/audit_support/audit_364829da8490.py", "--out-dir", "../checks/audit/364829da8490"], "exit_code": 0},
        {"cwd": "packet_root", "effective_cwd": "repo", "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
          "--input", "../checks/audit/364829da8490/inputs.json", "--out", "../checks/audit/364829da8490/racket.json"], "exit_code": 0},
        {"cwd": "packet_root", "effective_cwd": "repo", "argv": ["python3", "run_with_racket.py", "python3",
          "generators/b86607f34b8b/workspace/audit_support/score_364829da8490.py", "--audit-dir", "../checks/audit/364829da8490"], "exit_code": 0},
    ]
    witness = {**identity, "finding": "accepted-domain diagonal-connectivity shortcut", "sampling": mutated["replay"],
               "input": query["input"], "actual_racket_output": query["output"],
               "rival_name": "eight_connected_background_with_cardinal_color_boundary",
               "rival_output": mutated["rival_8_connected_output"], "different_cells": differences,
               "self_check": mutated["self_check"], "strict_canonical_like": mutated["strict_canonical_like"],
               "observed": mutated["observed"], "domain": "Validator-accepted rect_pair; corner mutation is outside current generated templates.",
               "authoritative_apply_result_index": mutated_index, "commands": commands}
    fractional = {**identity, "finding": "invalid fractional override silently truncated", "sampling": prepared["rows"][fractional_index]["replay"],
                  "input": pairs[fractional_index]["input"], "actual_racket_output": pairs[fractional_index]["output"],
                  "observed": prepared["rows"][fractional_index]["observed"],
                  "self_check": prepared["rows"][fractional_index]["self_check"],
                  "self_check_original_override": prepared["rows"][fractional_index]["self_check_original_override"],
                  "domain": "Malformed control outside advertised integer9..16; returned grid is lawful.", "commands": commands}
    lesson = {**identity, "assembly": "Four consecutive generated demonstrations plus a validator-accepted, corner-mutated query; not a production-sampled lesson.",
              "demonstration_source_indices": demonstration_indices, "query_source_index": mutated_index,
              "train": demos, "test": [query], "rival_query_output": mutated["rival_8_connected_output"],
              "rival_fits_every_demonstration": True, "rival_disagrees_on_query": True,
              "lesson_identifiable_reasons": hook_reasons}
    summary = {**identity, "counts": dict(group_counts), "racket_error_count": 0,
               "self_check_rejections": sum(bool(row["self_check"]) for row in prepared["rows"]),
               "strict_rejections": sum(bool(row["strict_canonical_like"]) for row in prepared["rows"]),
               "rule_mirror_matches": sum(gen.rule_mirror(pair["input"]) == pair["output"] for pair in pairs),
               "canonical_pairs_accepted_and_label_matching": len(canonical),
               "rival_8_connected_match_counts": dict(match_counts), "declared_rival_counts": declared,
               "unknown_override": prepared["unknown_override"], "diagonal_difference_count": len(differences),
               "commands": commands, "scoring_command": [sys.executable, *sys.argv], "scoring_cwd": str(Path.cwd()),
               "scoring_probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "limitations": ["No full battery or production lesson census was run.", "32 valid generated draws are finite evidence.",
                 "The diagonal witness is within the accepted validator domain but outside the current template sampler."]}
    for name, value in (("witness.json", witness), ("fractional-override.json", fractional), ("accepted-domain-lesson.json", lesson), ("summary.json", summary)):
        path = args.audit_dir / name
        if path.exists():
            raise FileExistsError(path)
        path.write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"total_inputs": len(pairs), "racket_errors": 0, "canonical_pairs": len(canonical),
                      "generated_draws": 32, "diagonal_difference_count": len(differences), "lesson_hook_reasons": hook_reasons}))


if __name__ == "__main__":
    main()
