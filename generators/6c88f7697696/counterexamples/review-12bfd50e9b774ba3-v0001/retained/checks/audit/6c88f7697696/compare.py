"""Check retained public Racket outputs and complete finite lesson windows."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import probe


def main():
    gen, source, source_hash = probe.selected()
    directory = Path(__file__).resolve().parent
    prepared = json.loads((directory / "probe.json").read_text())
    inputs = json.loads((directory / "input.json").read_text())
    receipt = json.loads((directory / "racket.json").read_text())
    assert receipt["task_id"] == probe.TASK
    assert receipt["generator_sha256"] == source_hash == prepared["generator_sha256"]
    assert receipt["executed_rule_hash"] == prepared["rule_hash"]
    # apply hashes its executable callable separately from canonical source text.
    assert receipt["rule_hash_matches_catalog"]
    assert receipt["catalog_rule_hash"] == prepared["rule_hash"]
    assert receipt["reference"] == "canonical"
    outputs = receipt["results"]
    assert len(outputs) == len(inputs)
    for index, entry in enumerate(outputs):
        assert entry["index"] == index and entry["input"] == inputs[index]
        assert entry["valid_output"] and entry["error"] is None, entry
        assert not gen.self_check(entry["input"])
    rivals, declarations = probe.named_rivals(gen)
    canonical_indices = [i for i, record in enumerate(prepared["authority_input_order"]) if record["kind"] == "canonical"]
    generated_indices = [i for i, record in enumerate(prepared["authority_input_order"]) if record["kind"] == "scheduled"]
    rival_report = {}
    for name, function in rivals.items():
        predictions = [function(grid) for grid in inputs]
        canonical_matches = sum(predictions[i] == outputs[i]["output"] for i in canonical_indices)
        rival_report[name] = {
            "canonical_matches": canonical_matches, "canonical_denominator": len(canonical_indices),
            "declared_canonical_shortcut": name in declarations["CANONICAL_SHORTCUTS"],
            "generated_matches": sum(predictions[i] == outputs[i]["output"] for i in generated_indices),
            "generated_denominator": len(generated_indices), "predictions": predictions,
        }
    pairs = probe.canonical_pairs(probe.TASK, root=probe.ROOT, labeled_only=True)
    canonical_matches = sum(outputs[i]["output"] == pairs[j]["output"] for j, i in enumerate(canonical_indices))
    if probe.TASK == "17a429a40b62":
        def mirror(grid):
            mapping = {source: destination for source, destination in zip(grid[0], grid[1]) if source}
            return [list(row) if r < 2 else [mapping.get(value, value) for value in row] for r, row in enumerate(grid)]
    else:
        mirror = gen.rule_mirror
    mirror_mismatches = [i for i, entry in enumerate(outputs) if mirror(entry["input"]) != entry["output"]]
    lookup = {(record["difficulty"], record["sample_index"]): i
              for i, record in enumerate(prepared["authority_input_order"]) if record["kind"] == "scheduled"}
    policy = prepared["lesson_policy"]
    period = policy["schedule_period_derived_from_source"]
    demonstrations = policy["demonstrations"]
    hook = getattr(gen, "lesson_identifiable", None)
    production_count = 0
    rotation_count = 0
    production_failures = []
    rotation_failures = []
    for band in probe.BANDS:
        for start in range(period):
            indices = [lookup[(band, start + offset)] for offset in range(demonstrations + 1)]
            for query_position in range(demonstrations + 1):
                query_index = indices[query_position]
                demo_indices = [index for position, index in enumerate(indices) if position != query_position]
                demos = [{"input": inputs[index], "output": outputs[index]["output"]} for index in demo_indices]
                query = {"input": inputs[query_index], "output": outputs[query_index]["output"]}
                reasons = list(hook(demos, query)) if hook else []
                survivors = [name for name, function in rivals.items()
                             if all(function(demo["input"]) == demo["output"] for demo in demos)
                             and function(query["input"]) != query["output"]]
                is_production = query_position == demonstrations
                rotation_count += 1
                production_count += int(is_production)
                if reasons or survivors:
                    failure = {"seed": policy["schedule_seed"], "difficulty": band, "cyclic_start": start,
                               "query_position": query_position, "demo_input_indices": demo_indices,
                               "query_input_index": query_index, "hook_reasons": reasons, "surviving_rivals": survivors}
                    rotation_failures.append(failure)
                    if is_production:
                        production_failures.append(failure)
    report = {
        "schema": "racket-bound-adversarial-audit-v1", "task_id": probe.TASK,
        "generator_sha256": source_hash, "rule_hash": receipt["executed_rule_hash"],
        "rule_source_sha256": prepared["rule_source_sha256"],
        "rule_callable_sha256": receipt["rule_text_sha256"],
        "racket_receipt": "checks/audit/" + probe.TASK + "/racket.json",
        "racket_receipt_sha256": probe.hashlib.sha256((directory / "racket.json").read_bytes()).hexdigest(),
        "racket_input_count": len(inputs), "racket_valid_outputs": len(outputs),
        "canonical_matches": canonical_matches, "canonical_denominator": len(canonical_indices),
        "python_mirror_matches": len(outputs) - len(mirror_mismatches), "python_mirror_denominator": len(outputs),
        "python_mirror_mismatch_indices": mirror_mismatches,
        "rivals": rival_report,
        "invalid_declared_canonical_shortcuts": [name for name, result in rival_report.items()
            if result["declared_canonical_shortcut"] and result["canonical_matches"] != result["canonical_denominator"]],
        "lesson_policy": policy, "lesson_hook_present": bool(hook),
        "lesson_scope": "declared hook and actual declared rivals" if hook else "two explicitly authored audit rivals only; no generator lesson contract declared",
        "production_windows": production_count, "production_failures": production_failures,
        "rotation_cases": rotation_count, "rotation_failures": rotation_failures,
        "windows_overlap": True, "rotation_cases_include_production": True,
        "command": {"cwd": "repo", "argv": [sys.executable, "-B", *sys.argv],
                    "env": {"PYTHONPATH": "src:shared/runtime"}, "exit_code": 0},
        "public_apply_command": {"cwd": "packet_root", "argv": [sys.executable, "-B", "review.py", "run", sys.executable,
            "-B", "-m", "arcpuzzles", "apply", probe.TASK, "--input", "../checks/audit/" + probe.TASK + "/input.json",
            "--out", "../checks/audit/" + probe.TASK + "/racket.json"], "exit_code": 0},
        "admission": "Findings only. No generator approval or training admission is granted by these checks.",
    }
    if probe.TASK == "17a429a40b62":
        plain = gen.generate(probe.SCHEDULE_SEED, 0)
        unknown = gen.generate(probe.SCHEDULE_SEED, 0, ignored_control=123)
        report["unknown_override_changes_canonical_schedule"] = {
            "seed": probe.SCHEDULE_SEED, "sample_index": 0, "calls": 2,
            "default_observed": probe.observe(gen, plain), "unknown_override_observed": probe.observe(gen, unknown),
            "same_input": plain == unknown, "unknown_override_self_check": gen.self_check(unknown),
        }
    probe.write("comparison.json", report)
    print(json.dumps({"task_id": probe.TASK, "racket_outputs": len(outputs),
        "canonical_matches": [canonical_matches, len(canonical_indices)],
        "python_mirror_matches": [len(outputs) - len(mirror_mismatches), len(outputs)],
        "invalid_declared_canonical_shortcuts": report["invalid_declared_canonical_shortcuts"],
        "production_failures": [len(production_failures), production_count],
        "rotation_failures": [len(rotation_failures), rotation_count]}))


if __name__ == "__main__":
    main()
