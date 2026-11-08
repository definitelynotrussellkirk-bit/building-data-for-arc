"""Cheap, explicitly Python-only construction feedback before source freeze."""
import importlib.util
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[2] / "repo"
base = repo / "generators/5f9a2df57599/workspace/parametric"


def load(name):
    spec = importlib.util.spec_from_file_location("wall_preflight_" + name, base / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit, family = load("audit_native"), load("native_family")
rows = []
for seed, demos in ((0, 2), (17, 2), (101, 6)):
    for policy in audit.POLICIES:
        episode = family.generate(seed, {"side_boundary_policy": policy}, demos=demos, queries=4)
        train = episode["train"][:2]
        labels = [pair["output"] for pair in train]
        assert [audit.reference(pair["input"], policy) for pair in train] == labels
        mismatches = {name: [i for i, pair in enumerate(train)
                            if audit.rival_output(pair["input"], policy, name) != pair["output"]]
                      for name in audit.RIVALS}
        unresolved = [name for name, indices in mismatches.items() if not indices
                      and not (audit.structural_equivalence(policy, name) or {}).get("equivalent_to") == "intended"]
        row = {"seed": seed, "policy": policy, "python_only": True,
               "demo_mismatches": mismatches, "unresolved": unresolved,
               "first_two_size_wall_features": audit.teaching_features(train, policy)}
        # Queries are inspected only after the immutable demo results above.
        row["stress"] = []
        for i, pair in enumerate(episode["test"]):
            grid = pair["input"]
            assert audit.reference(grid, policy) == pair["output"]
            if len(grid) == len(grid[0]) == 30:
                regions = audit.facts(grid, policy)
                chosen = [region for region in regions if region["eligible"]]
                row["stress"].append({"query_index": i, "eligible_regions": len(chosen),
                                      "rejected_regions": len(regions) - len(chosen),
                                      "changed_cells": sum(region["size"] for region in chosen),
                                      "quadrants": sorted({(r // 15, c // 15)
                                                           for region in chosen for r, c in region["cells"]})})
        rows.append(row)
path = Path(__file__).with_name("teaching-preflight.json")
path.write_text(json.dumps({"evidence": "Python-only preflight; no Racket execution claim", "rows": rows}, indent=2) + "\n")
print(json.dumps(rows, sort_keys=True))
raise SystemExit(1 if any(row["unresolved"] for row in rows) else 0)
