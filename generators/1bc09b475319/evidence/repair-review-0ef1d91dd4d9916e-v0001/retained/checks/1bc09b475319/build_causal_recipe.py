"""Make a minimal new-cap versus old-cyan intervention from qualified pairs.

Recipe interpretation is authored metadata. The native witness helper performs
the protected-Racket construction and replay. Run from WORK/repo.
"""
import argparse
import json
from pathlib import Path

TASK = "1bc09b475319"
DESCRIPTIONS = {
    "step_a": "Derive the new horizontal bar-cap positions from the input and paint those positions cyan in a capped grid.",
    "intermediate": "The input-dependent new-cap position mask together with the capped grid.",
    "step_b": "Within each column, join consecutive positions from that mask only when their complete intervening segment in the capped grid is zero.",
    "why_b_depends_on_a": "The bridge anchors are newly computed bar ends, not cyan cells visible in the original input. Replacing only the anchor mask with input-cyan positions while retaining the correctly capped grid changes which clear segments are filled. This is a spatial-mask dependency; no iterative-state or training-gain claim is made.",
}


def build(qualification):
    qualification = Path(qualification)
    report = json.loads(qualification.read_text())
    if report["task_id"] != TASK or report["status"] != "qualified":
        raise ValueError("Expected this family's successful qualification")
    execution = json.loads(qualification.with_name("execution.json").read_text())
    index, episode = next((i, e) for i, e in enumerate(execution["episodes"])
                          if e["settings"] == {"cap_mode": "bridge_caps"} and e["seed"] == 0)
    program = episode["program"]
    if program.count("(anchors new-caps)") != 1:
        raise ValueError("Expected one exact new-cap anchor binding")
    counterfactual = program.replace("(anchors new-caps)", "(anchors old-cyan)", 1)
    cases = []
    for pair_index in (0, 1):
        grid = episode["train"][pair_index]["input"]
        width = len(grid[0])
        new_caps = []
        for row, values in enumerate(grid):
            for column, value in enumerate(values):
                if value == 0 and ((column >= 2 and values[column-2:column] == [6, 6])
                                   or (column + 2 < width and values[column+1:column+3] == [6, 6])):
                    new_caps.append([row, column])
        old_cyan = [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
        cases.append({"episode_index": index, "split": "train", "pair_index": pair_index,
                      "intermediate_value": {"new_cap_anchors": new_caps,
                                             "counterfactual_input_cyan_anchors": old_cyan},
                      "counterfactual_program": counterfactual, "ablation": "wrong_intermediate"})
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
