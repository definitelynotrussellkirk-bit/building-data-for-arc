"""Select matched qualified one/two-pass pairs for a skip-A intervention."""
import argparse
import json
from pathlib import Path

DESCRIPTIONS = {
    "step_a": "Run one complete canonical snapshot pass, inspecting the original grid and accumulating row-major writes.",
    "intermediate": "The completed first-pass grid, including newly filled corners and resolved original-window write conflicts.",
    "step_b": "Run the same local diagonal-completion rule on the first-pass grid, recomputing every eligibility predicate and conflict from that updated input.",
    "why_b_depends_on_a": "The first pass creates diagonals that do not exist in the original input. Skipping A and applying B directly to the original grid changes both teaching outputs. The one-pass counterfactual retains the exact operation used by B; reversing identical A/B operations would be an invalid causal control.",
}


def build(qualification):
    report = json.loads(qualification.read_text())
    if report["status"] != "qualified" or report["task_id"] != "01bb2cbe1309":
        raise ValueError("Expected this family's current successful qualification")
    execution = json.loads(qualification.with_name("execution.json").read_text())
    first = next(e for e in execution["episodes"] if e["seed"] == 0 and e["settings"] == {"passes": 1})
    index, second = next((i, e) for i, e in enumerate(execution["episodes"]) if e["seed"] == 0 and e["settings"] == {"passes": 2})
    cases = []
    for pair_index in (0, 1):
        a, b = first["train"][pair_index], second["train"][pair_index]
        if a["input"] != b["input"] or a["output"] == b["output"]:
            raise ValueError("Expected matched inputs with a real second-pass effect")
        cases.append({"episode_index": index, "split": "train", "pair_index": pair_index,
                      "intermediate_value": {"after_first_pass": a["output"], "skip_a_supplies": a["input"]},
                      "counterfactual_program": first["program"], "ablation": "skip_a"})
    return {**DESCRIPTIONS, "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.qualification)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"cases": len(result["cases"]), "racket_executed": False, "out": str(args.out)}))
