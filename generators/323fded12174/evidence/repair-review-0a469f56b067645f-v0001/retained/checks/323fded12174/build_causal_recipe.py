"""Choose source-qualified row-cue counterfactuals for the native witness builder."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK = "323fded12174"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    q = json.loads(args.qualification.read_bytes())
    execution_path = args.qualification.with_name("execution.json")
    if q.get("status") != "qualified" or q.get("task_id") != TASK:
        raise ValueError("Expected this task's completed native qualification")
    if q["execution"] != {"path": "execution.json", "sha256": hashlib.sha256(execution_path.read_bytes()).hexdigest()}:
        raise ValueError("Execution does not match qualification")
    execution = json.loads(execution_path.read_bytes())
    root = Path(__file__).resolve().parents[2] / "repo"
    home = root / "generators" / TASK / "workspace/parametric"
    family = module(home / "prototype.py", "_row_cue_witness_family")
    audit = module(home / "audit_native.py", "_row_cue_witness_audit")
    settings = {"rank_by": "anchor_color"}
    pairs = []
    for episode_index, episode in enumerate(execution["episodes"]):
        if episode["settings"] != settings:
            continue
        if episode["program"] != family.program(settings):
            raise ValueError("Current program differs from qualified program")
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                if audit.reference(pair["input"], settings) != pair["output"]:
                    raise ValueError("Independent meaning differs from qualified output")
                pairs.append((episode_index, split, pair_index, pair))
    recipe = {
        "step_a": "Count nonzero cells in each input row, select the unique densest row, and find its unique most frequent nonzero color.",
        "intermediate": "The selected anchor row index, its foreground color-frequency table, and the resulting input-derived target color.",
        "step_b": "Count occurrences of that target color in every original input row, then stable-sort the complete unchanged rows by those counts in descending order.",
        "why_b_depends_on_a": "The row-scoring color is supplied by the densest row's contents. Choosing the second-densest row or the globally most frequent color can produce a different color, a different score vector, and a different final row permutation. Original occupancy alone, input position, or a fixed global cue does not provide B's required key. This is an input-derived reference selection dependency, not an iterative physical simulation.",
        "cases": [],
    }
    used = set()
    for rival in ("second_occupancy_anchor", "global_color"):
        ordered = sorted(pairs, key=lambda item: (
            0 if (len(item[3]["input"]) == len(item[3]["input"][0]) == 30
                  if rival == "second_occupancy_anchor" else item[1] == "train") else 1,
            item[0], item[1], item[2]))
        selected = next((item for item in ordered
                         if (item[0], item[1], item[2]) not in used
                         and audit.rival_reference(item[3]["input"], settings, rival) != item[3]["output"]), None)
        if selected is None:
            raise ValueError(f"Qualified pairs lack a distinct distinguishing {rival} case")
        episode_index, split, pair_index, pair = selected
        used.add((episode_index, split, pair_index))
        wrong_color = audit.selected_color(pair["input"], rival)
        wrong_counts = [row.count(wrong_color) for row in pair["input"]]
        recipe["cases"].append({
            "episode_index": episode_index, "split": split, "pair_index": pair_index,
            "ablation": "wrong_intermediate",
            "counterfactual_program": audit.rival_program(settings, rival),
            "intermediate_value": {
                "intended": audit.facts(pair["input"]),
                "counterfactual": rival, "counterfactual_color": wrong_color,
                "counterfactual_row_scores": wrong_counts,
                "counterfactual_row_order": sorted(range(len(wrong_counts)), key=lambda i: (-wrong_counts[i], i)),
                "interpretation": ("Use the second-highest occupancy row's nonzero modal color."
                                   if rival == "second_occupancy_anchor" else
                                   "Use the most frequent nonzero color across the entire input."),
            },
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(recipe, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "authored_recipe", "cases": len(recipe["cases"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
