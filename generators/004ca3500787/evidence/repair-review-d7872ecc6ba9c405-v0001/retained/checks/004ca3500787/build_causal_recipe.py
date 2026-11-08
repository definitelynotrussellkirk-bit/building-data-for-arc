"""Execute stored intermediate tags before constructing a wrong-tag witness."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from arcpuzzles.review_witness import _qualified

DESCRIPTIONS = {
    "step_a": "Extract red four-connected objects and compute each full D4 canonical shape-key once, storing object/signature pairs.",
    "intermediate": "The executed object/signature list, including a repeated F5 key and singleton W5 key; the witness also records executed translation-only counterfactual tags.",
    "step_b": "Count stored signatures, select the first object whose stored signature has frequency one, and render its observed normalized cyan crop without recomputing the signatures.",
    "why_b_depends_on_a": "Changing only A's stored signature from full D4 to translation-only splits the reflected common pair. Byte-identical B then selects the first common object instead of the middle singleton. Reversing stages would not be a valid control because B consumes tags supplied by A.",
}
ACTUAL = "(shape-key (canonical (obj-cells obj)))"
WRONG = "(shape-key (normalize-cells (obj-cells obj)))"
BOUNDARY = "    (define counts"


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def instrument(program):
    if program.count(BOUNDARY) != 1:
        raise ValueError("Expected one explicit stored-tag/counting boundary")
    return program.split(BOUNDARY, 1)[0] + """    (map (lambda (item)
      (list (sort (obj-cells (first item)) cell<?) (second item))) tagged)))"""


def build(qualification):
    root = Path.cwd()
    qualified, execution = _qualified(root, qualification)
    if qualified["task_id"] != "004ca3500787":
        raise ValueError("Expected this shape family's current native qualification")
    cases, evaluations = [], 0
    runtime = root / "shared/runtime"
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for seed in (0, 17):
                index, episode = next((i, e) for i, e in enumerate(execution["episodes"])
                                      if e["seed"] == seed and e["settings"] == {"pose": "observed"})
                pair, program = episode["train"][0], episode["program"]
                if program.count(ACTUAL) != 1:
                    raise ValueError("The intervention must replace exactly one A expression")
                counterfactual = program.replace(ACTUAL, WRONG, 1)
                assert program.split(BOUNDARY, 1)[1] == counterfactual.split(BOUNDARY, 1)[1]
                actual_program, wrong_program = instrument(program), instrument(counterfactual)
                actual, wrong = apply(actual_program, pair["input"]), apply(wrong_program, pair["input"])
                evaluations += 2
                if len(actual) != len(wrong) or [item[0] for item in actual] != [item[0] for item in wrong]:
                    raise ValueError("The intervention must preserve every observed component")
                actual_counts = Counter(item[1] for item in actual)
                wrong_counts = Counter(item[1] for item in wrong)
                actual_choice = next(i for i, item in enumerate(actual) if actual_counts[item[1]] == 1)
                wrong_choice = next(i for i, item in enumerate(wrong) if wrong_counts[item[1]] == 1)
                assert sorted(actual_counts.values()) == [1, 2]
                assert sorted(wrong_counts.values()) == [1, 1, 1]
                assert (actual_choice, wrong_choice) == (1, 0)
                cases.append({
                    "episode_index": index, "split": "train", "pair_index": 0,
                    "counterfactual_program": counterfactual, "ablation": "wrong_intermediate",
                    "intermediate_value": {
                        "schema": "executed-shape-tags-v1", "seed": seed,
                        "actual": actual, "counterfactual": wrong,
                        "actual_counts": dict(actual_counts), "counterfactual_counts": dict(wrong_counts),
                        "actual_selected_component_index": actual_choice,
                        "counterfactual_selected_component_index": wrong_choice,
                        "program": actual_program, "program_sha256": sha(actual_program),
                        "counterfactual_program": wrong_program, "counterfactual_program_sha256": sha(wrong_program),
                        "racket": identity,
                        "scope": "Protected execution of the unchanged prefix ending after A's stored tags. Full labels are separately constructed and replayed by review_witness."
                    }
                })
            assert {k: bridge.runtime_identity[k] for k in identity} == identity
        finally:
            bridge.close()
    assert _qualified(root, qualification)[0] == qualified
    return {**DESCRIPTIONS, "cases": cases, "intermediate_protected_evaluations": evaluations}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    result = build(args.qualification)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"cases": len(result["cases"]), "intermediate_protected_evaluations": result["intermediate_protected_evaluations"], "out": str(args.out)}))
