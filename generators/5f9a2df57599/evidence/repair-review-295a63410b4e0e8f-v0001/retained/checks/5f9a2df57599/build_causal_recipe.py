"""Select two qualified cases; the native witness command executes both rules."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.review_witness import _qualified


def main():
    root = Path.cwd().resolve()
    checks = root.parent / "checks/5f9a2df57599"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, default=checks / "qualification/qualification.json")
    parser.add_argument("--out", type=Path, default=checks / "witness-recipe.json")
    args = parser.parse_args()
    out = args.out
    if out.exists():
        raise FileExistsError(out)
    path = root / "generators/5f9a2df57599/workspace/parametric/audit_native.py"
    spec = importlib.util.spec_from_file_location("wall_causal_audit", path)
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)
    qualification, execution = _qualified(root, args.qualification)
    recipe = {
        "step_a": "Discover orthogonally connected black regions and derive each region's actual cell set, bounding box and complete side-wall facts from the current input.",
        "intermediate": "The input-derived region partition and geometry. It determines both which complete rows/columns must be inspected and which actual cells can be painted.",
        "step_b": "Apply the episode's side-boundary policy plus the top/bottom walls and column-zero exception to each derived region, then paint only the cells of qualifying regions yellow.",
        "why_b_depends_on_a": "Changing the region partition can merge a rejected L with a diagonal singleton, changing its bounding box, wall tests and later paint decision. Replacing actual membership by a filled bounding box can also paint gray cells. The policy alone does not identify the selected cells; this is a geometry-derived dependency, not iterative state simulation.",
        "cases": [],
    }
    selections = []
    for policy, wanted_split, large in [("gray_walls", "train", False), ("canvas_edges", "test", True)]:
        found = None
        for rival in ["eight_connected", "bbox_paint"]:
            for index, episode in enumerate(execution["episodes"]):
                if episode["settings"] != {"side_boundary_policy": policy}:
                    continue
                for pair_index, pair in enumerate(episode[wanted_split]):
                    grid = pair["input"]
                    if large and (len(grid) != 30 or len(grid[0]) != 30):
                        continue
                    alternate = audit.rival_output(grid, policy, rival)
                    if alternate == pair["output"]:
                        continue
                    regions = audit.facts(grid, policy)
                    changed = sum(a != b for row_a, row_b in zip(pair["output"], alternate) for a, b in zip(row_a, row_b))
                    found = {
                        "episode_index": index, "split": wanted_split, "pair_index": pair_index,
                        "counterfactual_program": audit.rival_program(policy, rival, root=root),
                        "ablation": "wrong_intermediate",
                        "intermediate_value": {
                            "actual_four_connected_regions": regions,
                            "counterfactual_intermediate": (audit.facts(grid, policy, connectivity=8)
                                if rival == "eight_connected" else [{"actual_cells": region["cells"],
                                    "replaced_by_bbox": region["bbox"]} for region in regions if region["eligible"]]),
                            "counterfactual_name": rival,
                            "expected_difference_cells_from_independent_python": changed,
                            "metadata_status": "Reviewer-authored intermediate; native helper verifies final labels separately.",
                        },
                    }
                    selections.append({"policy": policy, "shape": [len(grid), len(grid[0])],
                        "rival": rival, "expected_changed_cells": changed,
                        "episode_index": index, "split": wanted_split, "pair_index": pair_index})
                    break
                if found:
                    break
            if found:
                break
        if found is None:
            raise ValueError("No changed-output qualified case for " + policy)
        recipe["cases"].append(found)
    out.write_text(json.dumps(recipe, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"qualification_status": qualification["status"], "recipe": str(out), "selected": selections}, indent=2))


if __name__ == "__main__":
    main()
