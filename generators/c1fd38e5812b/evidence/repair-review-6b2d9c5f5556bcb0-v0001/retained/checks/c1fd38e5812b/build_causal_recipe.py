"""Select concrete normalization/topology counterfactuals from native qualification."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


TASK = "c1fd38e5812b"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    q = json.loads(args.qualification.read_bytes())
    ep = args.qualification.with_name("execution.json")
    if q.get("status") != "qualified" or q.get("task_id") != TASK:
        raise ValueError("Expected this task's native qualification")
    if q.get("execution") != {"path": "execution.json", "sha256": hashlib.sha256(ep.read_bytes()).hexdigest()}:
        raise ValueError("Execution does not match qualification")
    execution = json.loads(ep.read_bytes())
    root = Path(__file__).resolve().parents[2] / "repo"
    home = root / "generators" / TASK / "workspace/parametric"
    family = module(home / "prototype.py", "_compression_causal_family")
    audit = module(home / "audit_native.py", "_compression_causal_audit")
    settings = {"view": "largest_component_crop"}
    pairs = []
    for index, episode in enumerate(execution["episodes"]):
        if episode["settings"] != settings:
            continue
        if episode["program"] != family.program(settings):
            raise ValueError("Current rule differs from qualified program")
        for split in ("train", "test"):
            for pi, pair in enumerate(episode[split]):
                if audit.reference(pair["input"], settings) != pair["output"]:
                    raise ValueError("Independent interpretation differs from qualified label")
                pairs.append((index, split, pi, pair))
    recipe = {
        "step_a": "Collapse adjacent identical input rows and columns into the logical grid, discover all four-connected monochrome logical components including color zero, and count their logical cells.",
        "intermediate": "The normalized logical grid, its component memberships and logical areas, and the area ranking with lexicographic bounding-box tie breaks.",
        "step_b": "Choose the largest logical component from that ranking and crop the original logical grid to its bounding box, preserving every color inside the crop.",
        "why_b_depends_on_a": "Nonuniform replication weights logical cells by different pixel areas, so a component chosen from expanded pixels can differ from the logical-cell winner. Eight-neighbor merging can also change component membership and the winning bounding box. B needs the normalized four-connected component census to choose its target and output bounds. This is an input-derived normalization and selection dependency, not iterative physical motion.",
        "cases": [],
    }
    for rival in ("physical_area", "connectivity8"):
        ordered = sorted(pairs, key=lambda item: (
            0 if (item[1] == "train" if rival == "physical_area" else
                  len(item[3]["input"]) == len(item[3]["input"][0]) == 30) else 1,
            item[0], item[1], item[2]))
        selected = next((item for item in ordered
                         if audit.rival_reference(item[3]["input"], settings, rival) != item[3]["output"]), None)
        if selected is None:
            raise ValueError(f"Qualified pairs lack a distinguishing {rival} case")
        index, split, pi, pair = selected
        recipe["cases"].append({
            "episode_index": index, "split": split, "pair_index": pi,
            "ablation": "wrong_intermediate",
            "counterfactual_program": audit.rival_program(settings, rival),
            "intermediate_value": {"intended": audit.facts(pair["input"]),
                                   "counterfactual": rival,
                                   "counterfactual_interpretation": (
                                       "Replace logical-cell areas by sums of original run-height times run-width for each component."
                                       if rival == "physical_area" else
                                       "Merge same-color cells through diagonals before ranking component areas.")},
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(recipe, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "authored_recipe", "cases": len(recipe["cases"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
