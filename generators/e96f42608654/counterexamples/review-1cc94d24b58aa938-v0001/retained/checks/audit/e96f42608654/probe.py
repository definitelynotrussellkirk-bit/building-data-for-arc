"""Findings-only audit; import the selected generator through a public snapshot."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime

TASK = "e96f42608654"
OUT = Path(__file__).resolve().parent
REPO = Path.cwd()


def components(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
               if v and (r, c) != (0, 0)}
    found = []
    while pending:
        start = min(pending)
        pending.remove(start)
        part, stack = [start], [start]
        while stack:
            r, c = stack.pop()
            for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nb in pending:
                    pending.remove(nb)
                    part.append(nb)
                    stack.append(nb)
        found.append(sorted(part))
    return found


def largest_component_rival(grid):
    # Crop the original grid to the bbox of its largest nonmarker component.
    # Ties are resolved by the row-major first cell (no tie in this witness).
    part = sorted(components(grid), key=lambda p: (-len(p), p[0]))[0]
    r0, r1 = min(r for r, c in part), max(r for r, c in part)
    c0, c1 = min(c for r, c in part), max(c for r, c in part)
    frame = grid[0][0]
    width = c1 - c0 + 3
    return [[frame] * width] + [
        [frame] + row[c0:c1 + 1] + [frame] for row in grid[r0:r1 + 1]
    ] + [[frame] * width]


catalog = Catalog(REPO)
selected = catalog.describe(TASK)
row = next(json.loads(line) for line in
           (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
           if json.loads(line)["task_id"] == TASK)
canonical = [[int(v) for v in line] for line in row["train"][2]["input"]]
with tempfile.TemporaryDirectory(prefix="audit-e96f-") as tmp:
    runtime = Path(tmp)
    prepare_runtime(catalog, runtime, TASK)
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("audit_generator", runtime / selected["runtime_generator"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    override_small = {"grid_h": 6, "grid_w": 6, "motif_h": 3, "motif_w": 3}
    override_large = {**override_small, "grid_h": 20, "grid_w": 20}
    small = module.generate(0, 0, **override_small)
    large = module.generate(0, 0, **override_large)
    records = [
        {"kind": "canonical_training", "train_index": 2,
         "seed": None, "sample_index": None, "overrides": None,
         "input": canonical, "self_check": module.self_check(canonical),
         "domain_membership": "Authoritative canonical training pair index 2; valid task input.",
         "rival_output": largest_component_rival(canonical),
         "component_sizes": [len(p) for p in components(canonical)]},
        {"kind": "generated_override", "seed": 0, "sample_index": 0,
         "overrides": override_small, "input": small,
         "self_check": module.self_check(small),
         "domain_membership": "Generated input satisfies all selected self_check invariants.",
         "rival_output": largest_component_rival(small),
         "component_sizes": [len(p) for p in components(small)]},
    ]
    evidence = {
        "task_id": TASK, "generator_sha256": selected["generator_sha256"],
        "rule_hash": selected["rule_hash"],
        "rule_sha256_normalized": hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest(),
        "records": records,
        "ignored_dimensions": {"seed": 0, "sample_index": 0,
                               "overrides_a": override_small, "overrides_b": override_large,
                               "outputs_identical": small == large,
                               "actual_grid_shape": [len(small), len(small[0])],
                               "self_check_b": module.self_check(large)},
        "rival": "Remove command marker from component analysis; crop the original input to the bbox of the largest 4-connected nonzero component and frame it using input[0][0].",
    }
(OUT / "input.json").write_text(json.dumps([r["input"] for r in records], indent=2) + "\n")
(OUT / "probe.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"generator_sha256": evidence["generator_sha256"], "rule_hash": evidence["rule_hash"],
                  "self_checks": [r["self_check"] for r in records],
                  "ignored_dimensions": evidence["ignored_dimensions"]}, indent=2))
