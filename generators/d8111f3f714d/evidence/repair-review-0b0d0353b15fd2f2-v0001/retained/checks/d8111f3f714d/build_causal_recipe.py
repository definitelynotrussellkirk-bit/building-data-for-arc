#!/usr/bin/env python3
"""Prepare exact-program trunk-line interventions for native witness replay."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def build(qualification):
    qpath = Path(qualification).resolve()
    q = json.loads(qpath.read_bytes())
    execution_path = qpath.parent / q["execution"]["path"]
    assert hashlib.sha256(execution_path.read_bytes()).hexdigest() == q["execution"]["sha256"]
    execution = json.loads(execution_path.read_bytes())
    path = Path.cwd() / "generators/d8111f3f714d/workspace/parametric/native_family.py"
    spec = importlib.util.spec_from_file_location("_branch_causal_family", path)
    family = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(family)
    recipe = {
        "step_a": "Find the unique row- or column-aligned pair of red cells, then derive its trunk orientation, line and span from the current input.",
        "intermediate": "The input-derived trunk endpoints, orientation, perpendicular line coordinate and endpoint span; these give each remaining red cell its branch role and side of the trunk.",
        "step_b": "Fill the inferred trunk span and connect each branch along the perpendicular axis, toward the inferred trunk line or away from that line to the canvas edge according to the episode setting.",
        "why_b_depends_on_a": "The same branch position can lie on either side of a trunk found elsewhere in the input. Replacing the inferred line by the canvas midpoint changes both trunk pixels and the later branch routing. The exact intervention retains red scanning, pair selection, orientation and painting code; it changes only the consumed line coordinate. This is a geometry-derived dependency, not iterative state simulation.",
        "cases": [],
    }
    for setting, pair_index in [("toward_trunk", 0), ("away_to_edge", 1)]:
        index, episode = next((i, e) for i, e in enumerate(execution["episodes"])
                              if e["seed"] == 0 and e["settings"] == {"branch_direction": setting})
        grid = episode["train"][pair_index]["input"]
        facts = family.analyze_scene(grid)
        source = episode["program"]
        assert source == family.program(episode["settings"])
        changes = [("(tc (second t1))", "(tc (/ w 2))"),
                   ("(tr (first t1))", "(tr (/ h 2))")]
        counterfactual = source
        for before, after in changes:
            assert counterfactual.count(before) == 1
            counterfactual = counterfactual.replace(before, after, 1)
        midpoint = (facts["width"] if facts["orientation"] == "v" else facts["height"]) // 2
        assert midpoint != facts["trunk_line"]
        recipe["cases"].append({
            "episode_index": index, "split": "train", "pair_index": pair_index,
            "ablation": "wrong_intermediate", "counterfactual_program": counterfactual,
            "intermediate_value": {
                "actual_trunk": {key: facts[key] for key in ["trunk", "orientation", "trunk_line", "trunk_start", "trunk_end"]},
                "wrong_line": midpoint,
                "unchanged": ["red scanning", "unique aligned pair", "orientation", "endpoint span", "branch set", "painting code"],
                "program_substitutions": changes,
                "interpretation": "Author-derived geometry. Native witness construction and replay verify both final labels; they do not independently certify this causal interpretation.",
            },
        })
    return recipe


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.qualification)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"cases": len(result["cases"]), "recipe": str(args.out), "status": "authored_for_native_replay"}))
