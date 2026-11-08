"""Replay the retained teaching failure and inspect current declared rivals.

Authoring tool: reads canonical labels and invokes the public reference API.
Run through review.py run; never use during a visible-only solve.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "48283e01e8ab"


def probe():
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    saved_path = Path(__file__).resolve().parents[1] / "counterexamples/baseline_seed61.json"
    saved = json.loads(saved_path.read_text())
    declarations = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        for name, rival in getattr(generator, namespace, {}).items():
            declarations[f"{namespace}:{name}"] = rival
    if not declarations or not getattr(generator, "CANONICAL_SHORTCUTS", {}):
        raise ValueError("Missing executable current rival declarations")

    canonical = list(canonical_pairs(TASK_ID, root=root))
    if not canonical:
        raise ValueError("No labeled canonical pairs")
    canonical_fit = {
        name: {"occurrences": len(canonical), "fits": sum(
            rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical
        )}
        for name, rival in declarations.items()
    }
    seed, band = saved["seed"], saved["difficulty"]
    current_inputs = [generator.generate(seed, index, difficulty=band) for index in range(5)]
    inputs = saved["inputs"] + current_inputs
    reference = Catalog(root).apply(TASK_ID, inputs, reference="canonical", timeout=120)
    if reference["generator_sha256"] != digest or not reference["rule_hash_matches_catalog"]:
        raise RuntimeError("Reference receipt source identity disagrees")
    outputs = []
    for row in reference["results"]:
        if row.get("error") or not row.get("valid_output"):
            raise RuntimeError(f"Reference execution failed: {row}")
        outputs.append(row["output"])
    if len(outputs) != len(inputs):
        raise RuntimeError("Reference result count mismatch")

    rival = generator.CANONICAL_SHORTCUTS[saved["rival"]]
    old_count = len(saved["inputs"])
    old_predictions = [rival(deepcopy(grid)) for grid in saved["inputs"]]
    baseline = {
        "generator_sha256": saved["generator_sha256"],
        "seed": seed, "difficulty": band,
        "demonstrations": saved["n_train"], "query_index": old_count - 1,
        "rival": saved["rival"],
        "fits_all_demonstrations": old_predictions[:-1] == outputs[:old_count - 1],
        "query_disagrees": old_predictions[-1] != outputs[old_count - 1],
        "retained_labels_reconfirmed": outputs[:old_count] == saved["outputs"],
        "query_input": saved["inputs"][-1],
        "reference_output": outputs[old_count - 1],
        "rival_output": old_predictions[-1],
    }
    pairs = [{"input": grid, "output": output}
             for grid, output in zip(current_inputs, outputs[old_count:])]
    rotations = []
    for held_out, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != held_out]
        ambiguous = [name for name, candidate in declarations.items()
                     if all(candidate(deepcopy(pair["input"])) == pair["output"] for pair in demos)
                     and candidate(deepcopy(query["input"])) != query["output"]]
        rotations.append({"query_index": held_out, "ambiguous_rivals": ambiguous,
                          "hook_reasons": generator.lesson_identifiable(deepcopy(demos), deepcopy(query))})
    checks = {
        "canonical_shortcuts_fit_all": all(row["fits"] == len(canonical) for name, row in canonical_fit.items()
                                          if name.startswith("CANONICAL_SHORTCUTS:")),
        "baseline_failure_reproduced": all(baseline[key] for key in
            ("fits_all_demonstrations", "query_disagrees", "retained_labels_reconfirmed")),
        "current_inputs_accepted": all(generator.self_check(grid) == [] for grid in inputs),
        "current_all_holdouts_identifiable": all(not row["ambiguous_rivals"] and not row["hook_reasons"]
                                                 for row in rotations),
        "source_unchanged": hashlib.sha256(source.read_bytes()).hexdigest() == digest,
    }
    return {
        "schema": "arcpuzzles-task-shortcut-probe-v1", "task_id": TASK_ID,
        "status": "passed" if all(checks.values()) else "failed", "checks": checks,
        "generator_sha256": digest, "rule_hash": generator.RULE_HASH,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "retained_counterexample_sha256": hashlib.sha256(saved_path.read_bytes()).hexdigest(),
        "canonical_fit": canonical_fit, "baseline": baseline,
        "current_lesson": {"seed": seed, "difficulty": band, "sample_indices": list(range(5)),
                           "demonstrations": 4, "pairs": pairs, "rotations": rotations},
        "reference": reference,
        "scope": "One retained old lesson and one current five-pair window, not a census or universal induction proof.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Choose a fresh output path; evidence is never overwritten")
    result = probe()
    result["invocation"] = {"argv": sys.argv, "cwd": str(Path.cwd())}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "checks": result["checks"], "out": str(args.out)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
