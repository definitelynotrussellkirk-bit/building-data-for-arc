"""Fill a native witness recipe from exact qualified block-sort pairs.

Run from the repository with the packet wrapper. This creates authored metadata;
arcpuzzles.review_witness build independently executes and replays both rules.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    qualification = json.loads(args.qualification.read_bytes())
    execution_path = args.qualification.with_name("execution.json")
    if qualification.get("status") != "qualified" or qualification.get("task_id") != "3108da8bf9e8":
        raise ValueError("A native qualified receipt for this task is required")
    if qualification["execution"] != {
        "path": "execution.json",
        "sha256": hashlib.sha256(execution_path.read_bytes()).hexdigest(),
    }:
        raise ValueError("Execution does not match the qualification")
    execution = json.loads(execution_path.read_bytes())
    root = Path(__file__).resolve().parents[2] / "repo"
    path = root / "generators/3108da8bf9e8/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("_blocksort_causal_recipe", path)
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    settings = {"rank_basis": "components_then_cells"}
    index = next(i for i, episode in enumerate(execution["episodes"])
                 if episode["settings"] == settings)
    episode = execution["episodes"][index]
    if episode["program"] != prototype.program(settings):
        raise ValueError("Current alternative program differs from qualification")
    recipe = {
        "step_a": "Extract the nine zero-separated blocks; count four-connected color-1 components and color-1 cells in each block, then derive their lexicographic rank order.",
        "intermediate": "Nine input-dependent (four-connected component count, blue-cell count) keys, indexed by source block, and the source-index permutation obtained by sorting those keys.",
        "step_b": "Use that derived permutation to select which whole source block fills each bottom-first target position, preserving its exact texture and all separator cells.",
        "why_b_depends_on_a": "The block destinations depend on the component topology computed in A. Source positions or cell counts alone cannot choose the same permutation on these inputs. Replacing A with area-only statistics or eight-neighbor connectivity changes the intermediate while the target geometry and whole-block copying in B stay fixed. This demonstrates a derived-statistic dependency, not iterative grid-state simulation.",
        "cases": [],
    }
    for split, pair_index, intervention in (("train", 0, "area_only"), ("test", 3, "eight_neighbors")):
        pair = episode[split][pair_index]
        grid = pair["input"]
        if prototype.solve(grid, rank_basis=settings["rank_basis"]) != pair["output"]:
            raise ValueError("Authored intermediate does not correspond to qualified output")
        blocks = prototype.extract_blocks(grid)
        counts = [sum(v == 1 for row in block for v in row) for block in blocks]
        components4 = [prototype.component_count(block) for block in blocks]
        components8 = [prototype.component_count(block, connectivity=8) for block in blocks]
        actual_keys = list(zip(components4, counts))
        wrong_keys = counts if intervention == "area_only" else list(zip(components8, counts))
        actual_order = sorted(range(9), key=lambda i: actual_keys[i])
        wrong_order = sorted(range(9), key=lambda i: wrong_keys[i])
        if actual_order == wrong_order:
            raise ValueError("Selected counterfactual leaves the rank order unchanged")
        counterfactual = (prototype.rule_program("cells") if intervention == "area_only"
                          else prototype.rule_program("components_then_cells", connectivity=8))
        recipe["cases"].append({
            "episode_index": index, "split": split, "pair_index": pair_index,
            "ablation": "wrong_intermediate", "counterfactual_program": counterfactual,
            "intermediate_value": {
                "source_indices": list(range(9)), "color1_cell_counts": counts,
                "component4_counts": components4, "component8_counts": components8,
                "actual_rank_keys": actual_keys, "actual_source_rank_order": actual_order,
                "counterfactual": intervention, "counterfactual_rank_keys": wrong_keys,
                "counterfactual_source_rank_order": wrong_order,
            },
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(recipe, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "authored_recipe", "cases": len(recipe["cases"]),
                      "qualification": str(args.qualification), "out": str(args.out)}))


if __name__ == "__main__":
    main()
