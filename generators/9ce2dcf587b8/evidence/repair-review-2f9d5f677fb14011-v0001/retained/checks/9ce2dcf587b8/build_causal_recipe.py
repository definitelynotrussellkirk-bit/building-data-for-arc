"""Prepare two minimal wrong-endpoint interventions from qualified episodes.

This writes a recipe only. arcpuzzles.review_witness executes both programs and
binds/replays their labels. Descriptions and intermediate interpretation remain
reviewer-authored. Run from WORK/repo; no adapter import or Racket execution here.
"""
import argparse
import ast
import json
from pathlib import Path

TASK = "9ce2dcf587b8"
DESCRIPTIONS = {
    "step_a": "Trace each original marker along NW-SE to its two in-bounds boundary endpoints, and paint the main-ray grid.",
    "intermediate": "The input-dependent list of boundary endpoints together with the painted main-ray grid.",
    "step_b": "Paint anti-diagonal continuations exactly once from those frozen endpoints onto the main-ray grid.",
    "why_b_depends_on_a": "Continuation origins depend on each marker's position and the canvas boundary. Substituting the original marker positions for A's endpoints, while retaining A's painted grid, changes the final answer. This establishes a derived geometric dependency, not iterative simulation.",
}


def build(qualification):
    qualification = Path(qualification)
    q = json.loads(qualification.read_text())
    if q["task_id"] != TASK or q["status"] != "qualified":
        raise ValueError("Expected this task's successful native qualification")
    execution = json.loads(qualification.with_name("execution.json").read_text())
    source = Path("generators") / TASK / "workspace/parametric/native_family.py"
    syntax = ast.parse(source.read_text())
    expression = next(ast.literal_eval(node.value) for node in syntax.body
                      if isinstance(node, ast.Assign) and any(
                          isinstance(target, ast.Name) and target.id == "ENDPOINT_EXPRESSION"
                          for target in node.targets))
    index, episode = next((i,e) for i,e in enumerate(execution["episodes"])
                          if e["settings"] == {"ray_rule":"one_bounce"} and e["seed"] == 0)
    needle = "(ends " + expression + ")"
    if episode["program"].count(needle) != 1:
        raise ValueError("Expected one exact computed-endpoint binding")
    wrong = episode["program"].replace(needle,"(ends sources)",1)
    cases = []
    for pair_index in (0,1):
        grid = episode["train"][pair_index]["input"]
        h,w = len(grid),len(grid[0])
        sources = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
        ends = []
        for r,c in sources:
            nw,se = min(r,c),min(h-1-r,w-1-c)
            ends.extend(((r-nw,c-nw),(r+se,c+se)))
        cases.append({"episode_index":index,"split":"train","pair_index":pair_index,
                      "intermediate_value":{"correct_boundary_endpoints":ends,
                                            "counterfactual_origins":sources},
                      "counterfactual_program":wrong,"ablation":"wrong_intermediate"})
    return {**DESCRIPTIONS,"cases":cases}


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--qualification",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=build(args.qualification)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result,handle,indent=2)
        handle.write("\n")
    print(json.dumps({"cases":len(result["cases"]),"out":str(args.out),"racket_executed":False}))
