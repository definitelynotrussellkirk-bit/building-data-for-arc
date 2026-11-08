from __future__ import annotations

import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

ROOT = Path.cwd()
OUT = ROOT.parent / "checks/audit-probes.json"


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(task):
    path = ROOT / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_" + task, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


catalog = Catalog(ROOT)
report = {"schema": "assigned-audit-probes-v1", "targets": {}}

# 356cdd4a2386: exact-two versus at-least-two shortcut.
task = "356cdd4a2386"
gen, path = load(task)
custom = [[0] * 5 for _ in range(5)]
for row in (0, 2, 4):
    custom[row][2] = 7
applied = catalog.apply(task, [custom], reference="canonical", timeout=120)
intended = applied["results"][0]["output"]
rival = deepcopy(custom)
for row in range(5):
    rival[row][2] = 7
pairs = canonical_pairs(task, root=find_root(ROOT))
def rival_fill_at_least_two(grid):
    out = deepcopy(grid)
    for col in range(len(grid[0])):
        hits = [row for row in range(len(grid)) if grid[row][col] == 7]
        if len(hits) >= 2:
            for row in range(hits[0], hits[-1] + 1):
                out[row][col] = 7
    return out
canonical_fit = all(rival_fill_at_least_two(pair["input"]) == pair["output"] for pair in pairs)
emits_three = False
for seed in range(1, 101):
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(seed, seed, difficulty=band)
        if any(sum(grid[row][col] == 7 for row in range(len(grid))) >= 3 for col in range(len(grid[0]))):
            emits_three = True
report["targets"][task] = {
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "canonical_pairs": len(pairs),
    "rival": "fill between topmost and bottommost whenever a column has at least two orange cells",
    "canonical_fit": canonical_fit,
    "counterexample_input": custom,
    "reference_output": intended,
    "rival_output": rival,
    "outputs_differ": intended != rival,
    "self_check_counterexample": gen.self_check(custom),
    "emitted_three_endpoint_column_in_300_default_draws": emits_three,
    "reference_receipt": {k: applied.get(k) for k in ("rule_text_sha256", "executed_rule_hash", "rule_hash_matches_catalog")},
}

# 00c8541fe800: a concrete four-demo identity ambiguity.
task = "00c8541fe800"
gen, path = load(task)
seed = 866
grids = [gen.generate(seed, index, difficulty="medium") for index in range(5)]

def split(grid):
    height = len(grid)
    dividers = [col for col in range(len(grid[0])) if all(grid[row][col] == 9 for row in range(height))]
    assert len(dividers) == 2
    bounds = ((0, dividers[0]), (dividers[0] + 1, dividers[1]), (dividers[1] + 1, len(grid[0])))
    return [
        [[grid[row][col] for col in range(lo, hi)] for row in range(height)]
        for lo, hi in bounds
    ]
transforms = []
queries = []
for grid in grids:
    a, b, query = split(grid)
    transforms.append(gen._first_match(a, b))
    queries.append(query)
applied = catalog.apply(task, grids, reference="canonical", timeout=120)
outputs = [row["output"] for row in applied["results"]]
identity_matches = [query == output for query, output in zip(queries, outputs)]
report["targets"][task] = {
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_indices": list(range(5)),
    "difficulty": "medium",
    "transform_sequence": transforms,
    "identity_rival_matches": identity_matches,
    "identity_fits_all_four_demos": all(identity_matches[:4]),
    "identity_changes_query_answer": not identity_matches[4],
    "instance_hashes": [sha(grid) for grid in grids],
    "grids": grids,
    "reference_outputs": outputs,
    "identity_outputs": queries,
    "reference_receipt": {k: applied.get(k) for k in ("rule_text_sha256", "executed_rule_hash", "rule_hash_matches_catalog")},
}

OUT.write_text(json.dumps(report, indent=2) + "\n")
print(OUT)
print(json.dumps({task: {k: v for k, v in data.items() if k not in {"grids", "reference_outputs", "identity_outputs"}} for task, data in report["targets"].items()}, indent=2))
