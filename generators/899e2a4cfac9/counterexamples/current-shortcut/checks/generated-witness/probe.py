"""Extract and directly replay a small final-source rival witness from a public census.

Run from WORK: python3 checks/generated-witness/probe.py
Then obtain a separate public Racket receipt using the argv saved in witness.json.
The saved census labels are observations, never recomputed by a Python mirror.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    work = Path.cwd()
    source = work / "repo/generators/899e2a4cfac9/generator.py"
    census_path = work / "checks/lesson-census-final.json"
    destination = work / "checks/generated-witness"
    sys.path.insert(0, str(work / "repo/shared/runtime"))
    spec = importlib.util.spec_from_file_location("reviewed_border_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    census = json.loads(census_path.read_text())
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash == census["generator_sha256"], "Census is stale for this generator"
    candidates = []
    for lesson in census["lessons"]:
        instance = lesson["instance"]
        for accepted in instance["sampling"]["accepted_pairs"]:
            pair = instance[accepted["split"]][accepted["pair_index"]]
            if all(rival(pair["input"]) != pair["output"]
                   for rival in module.LESSON_COMPETITORS.values()):
                candidates.append((len(pair["input"]) * len(pair["input"][0]),
                                   lesson, accepted, pair))
    _, lesson, accepted, pair = min(candidates, key=lambda item: item[0])
    kwargs = {"seed": lesson["seed"], "sample_index": accepted["sample_index"],
              "difficulty": lesson["band"]}
    actual = module.generate(**kwargs)
    assert actual == pair["input"], "Direct generator call did not reproduce census input"
    assert module.self_check(actual) == []
    predictions = {name: rival(actual) for name, rival in module.LESSON_COMPETITORS.items()}
    receipt = {
        "schema": "arc-review-generated-witness-v1", "task_id": "899e2a4cfac9",
        "generator_sha256": source_hash, "rule_hash": module.RULE_HASH,
        "census_path": str(census_path.relative_to(work)),
        "census_sha256": hashlib.sha256(census_path.read_bytes()).hexdigest(),
        "lesson_index": lesson["index"], "band": lesson["band"],
        "generate_kwargs": kwargs, "overrides": {}, "accepted_pair": accepted,
        "input": actual, "census_racket_output": pair["output"],
        "self_check": module.self_check(actual), "direct_generation_equal": True,
        "rival_outputs": predictions,
        "rival_differing_cells": {
            name: [[r, c] for r, row in enumerate(prediction)
                   for c, value in enumerate(row) if value != pair["output"][r][c]]
            for name, prediction in predictions.items()
        },
        "probe_command": {"cwd": ".", "argv": ["python3", "checks/generated-witness/probe.py"]},
        "reference_command": {"cwd": ".", "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", "899e2a4cfac9", "--input", "../checks/generated-witness/input.json", "--out", "../checks/generated-witness/racket.json"]},
        "scope": "One exactly reproduced generated grid; all rivals enumerated from the actual LESSON_COMPETITORS declaration. Separate Racket receipt supplies direct reference verification."
    }
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "input.json").write_text(json.dumps(actual) + "\n")
    (destination / "witness.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"generate_kwargs": kwargs, "shape": [len(actual),len(actual[0])],
                      "rivals_refuted": len(predictions), "input": actual,
                      "census_racket_output": pair["output"],
                      "erase_domino_output": predictions["erase_domino"]}))


if __name__ == "__main__":
    main()
