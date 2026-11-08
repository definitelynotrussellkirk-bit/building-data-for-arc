from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog

ROOT = Path.cwd()
TASK = "0b6b3a286ad0"
SEED = 20261002
SAMPLE_INDEX = 4
DIFFICULTY = "medium"
OVERRIDES = {"texture": "wildcard", "panel_h": 6}
OUT = ROOT.parent / "checks" / f"{TASK}-shortcut-counterexample.json"

sys.path.insert(0, str(ROOT / "shared" / "runtime"))
gen_path = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"counterexample_{TASK}", gen_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

# Check the shortcut declarations against every usable canonical pair.
canonical_row = None
for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == TASK:
        canonical_row = row
        break
assert canonical_row is not None
canonical_pairs = list(canonical_row["train"])
test = canonical_row["test"]
canonical_pairs.extend([test] if isinstance(test, dict) else list(test))
canonical_fit = {}
for name, rival in module.CANONICAL_SHORTCUTS.items():
    canonical_fit[name] = [rival(pair["input"]) == pair["output"] for pair in canonical_pairs]

# Use the public generation API so the output below is executed by canonical Racket.
catalog = Catalog(ROOT)
episode = catalog.generate(
    TASK,
    count=1,
    seed=SEED,
    sample_index=SAMPLE_INDEX,
    difficulty=DIFFICULTY,
    n_train=1,
    n_test=1,
    overrides=OVERRIDES,
    allow_unapproved=True,
    timeout=240,
)[0]
pair = episode["train"][0]
input_grid = pair["input"]
actual = pair["output"]
shortcut_outputs = {
    name: rival(input_grid)
    for name, rival in module.CANONICAL_SHORTCUTS.items()
}
disagreements = {
    name: output != actual for name, output in shortcut_outputs.items()
}
facts = module.semantic_observables(input_grid)

record = {
    "schema": "arc-review-shortcut-counterexample-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(gen_path.read_bytes()).hexdigest(),
    "rule_hash": episode["provenance"]["rule_hash"],
    "seed": SEED,
    "sample_index": SAMPLE_INDEX,
    "difficulty": DIFFICULTY,
    "overrides": OVERRIDES,
    "canonical_pair_count": len(canonical_pairs),
    "canonical_shortcuts_declared": list(module.CANONICAL_SHORTCUTS),
    "canonical_fit_by_pair": canonical_fit,
    "input": input_grid,
    "actual_racket_output": actual,
    "rival_outputs": shortcut_outputs,
    "rival_disagrees": disagreements,
    "validator_errors": module.self_check(input_grid, difficulty=DIFFICULTY),
    "strict_canonical_like_errors": module.strict_canonical_like(input_grid),
    "belongs_to_documented_generator_domain": facts.get("texture") == "wildcard",
    "semantic_observables": {
        "texture": facts.get("texture"),
        "branch": facts.get("branch"),
        "key1_matches": facts.get("key1_matches"),
        "strict_key1_matches": facts.get("strict_key1_matches"),
        "key2_matches": facts.get("key2_matches"),
        "wildcard_noise_cells": facts.get("wildcard_noise_cells"),
    },
    "command": [
        "python3", "run_with_racket.py", "python3",
        "../checks/make_0b6b3a286ad0_shortcut_counterexample.py"
    ],
    "cwd": "packet_root",
}
if not all(all(results) for results in canonical_fit.values()):
    raise SystemExit("A declared canonical shortcut does not fit every canonical pair")
if record["validator_errors"] or record["strict_canonical_like_errors"]:
    raise SystemExit("Counterexample is outside the validated strict generator domain")
if not all(disagreements.values()):
    raise SystemExit("Generated wildcard case did not refute every declared canonical shortcut")
OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(OUT)
print(json.dumps({
    "generator_sha256": record["generator_sha256"],
    "rule_hash": record["rule_hash"],
    "canonical_fit_by_pair": canonical_fit,
    "rival_disagrees": disagreements,
    "semantic_observables": record["semantic_observables"],
}, indent=2))
