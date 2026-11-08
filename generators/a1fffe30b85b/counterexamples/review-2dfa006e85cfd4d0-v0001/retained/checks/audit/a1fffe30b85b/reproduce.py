"""Findings-only, source-bound teaching audit for a1fffe30b85b.

From WORK/:
    python run_with_racket.py python ../checks/audit/a1fffe30b85b/reproduce.py \
        --out ../checks/audit/a1fffe30b85b

The wrapper changes the payload cwd to WORK/repo. All authoritative labels come
from public Catalog.apply; the independent function below is explicitly a rival.
No selected generator or reference source is written.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "a1fffe30b85b"
AUDITED_GENERATOR_SHA256 = "9510e1d9aec50bd081f550697b5ae405f59121867de2deaac54f840894a2cf79"
SEED = 2
START = 11
DIFFICULTY = "easy"


def own_repo() -> Path:
    for ancestor in Path(__file__).resolve().parents:
        for root in (ancestor, ancestor / "repo"):
            if (root / "shared/runtime/reviewer_support.py").is_file():
                return root
    raise FileNotFoundError("No authoring repository within this audit's own workspace")


REPO = own_repo()
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs


def square_height_self_tile(grid):
    """Plausible wrong rule: use input height for both spatial dimensions.

    Treat the template/mask as height x height: crop excess columns, or use zero
    for missing columns. This is ordinary self-tiling on every square input.
    """
    size = len(grid)
    width = len(grid[0])

    def cell(row, col):
        return grid[row][col] if col < width else 0

    return [
        [cell(row % size, col % size)
         if cell(row // size, col // size) != 0 else 0
         for col in range(size * size)]
        for row in range(size * size)
    ]


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    names = ("case.json", "racket.json", "input.json", "authority-inputs.json", "lesson.json", "rival.json")
    for name in names:
        if (out / name).exists():
            parser.error(f"Refusing to overwrite retained evidence: {out / name}")

    source = REPO / "generators" / TASK_ID / "generator.py"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("audited_self_tile_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    n_demos = getattr(module, "EXAMPLES_NEEDED", 3)
    indices = list(range(START, START + n_demos + 1))
    generated = [module.generate(SEED, index, difficulty=DIFFICULTY) for index in indices]
    validator = [module.self_check(deepcopy(grid), difficulty=DIFFICULTY) for grid in generated]
    canonical = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    unique = {}
    for pair in canonical:
        key = json.dumps([pair["input"], pair["output"]], separators=(",", ":"))
        unique.setdefault(key, pair)
    canonical = list(unique.values())
    inputs = [pair["input"] for pair in canonical] + generated
    write_json(out / "input.json", generated[-1])
    write_json(out / "authority-inputs.json", inputs)
    applied = Catalog(REPO).apply(TASK_ID, inputs, reference="canonical", timeout=120)
    write_json(out / "racket.json", applied)
    results = applied["results"]
    if not all(result.get("valid_output") and result.get("output") for result in results):
        raise RuntimeError("Reference execution failed; retained racket.json is not counterexample evidence")
    count = len(canonical)
    canonical_matches = [results[i]["output"] == pair["output"] for i, pair in enumerate(canonical)]
    rival_outputs = [square_height_self_tile(grid) for grid in inputs]
    rival_matches = [prediction == result["output"] for prediction, result in zip(rival_outputs, results)]
    lesson_pairs = [
        {"input": result["input"], "output": result["output"], "sample_index": index}
        for index, result in zip(indices, results[count:])
    ]
    write_json(out / "lesson.json", {
        "task_id": TASK_ID, "seed": SEED, "difficulty": DIFFICULTY,
        "overrides": {}, "sample_indices": indices, "validator_results": validator,
        "train": lesson_pairs[:n_demos], "test": lesson_pairs[n_demos:],
    })
    write_json(out / "rival.json", {
        "name": "square_height_self_tile",
        "description": "Use input height for both template and mask dimensions, cropping or zero-padding columns.",
        "canonical_matches": rival_matches[:count],
        "demonstration_matches": rival_matches[count:count + n_demos],
        "query_match": rival_matches[-1], "query_output": rival_outputs[-1],
        "reference_query_output": results[-1]["output"],
    })
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    source_consistent = before == after == applied["generator_sha256"]
    reproduced = (source_consistent and applied["rule_hash_matches_catalog"]
                  and all(canonical_matches) and all(rival_matches[:count + n_demos])
                  and not rival_matches[-1] and not any(validator))
    case = {
        "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK_ID,
        "finding": "Three square demonstrations leave the square-height self-tile shortcut unrefuted for a rectangular query.",
        "finding_reproduced": reproduced,
        "generator_sha256": before, "generator_unchanged": before == after,
        "matches_assigned_source": before == AUDITED_GENERATOR_SHA256,
        "executed_rule_hash": applied["executed_rule_hash"],
        "rule_text_sha256": applied["rule_text_sha256"],
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_labels": "Public Catalog.apply; no Python-generated labels.",
        "generated_support": {
            "direct_generate_calls": True, "seed": SEED, "difficulty": DIFFICULTY,
            "overrides": {}, "sample_indices": indices,
            "declared_demonstration_count": n_demos,
            "shapes": [[len(grid), len(grid[0])] for grid in generated],
            "validator_results": validator,
            "documented_domain": "Binary 0-background grids; exactly one foreground color; both dimensions within the real easy range 2..3.",
        },
        "canonical": {"unique_labeled_pairs": count, "reference_matches_recorded_labels": canonical_matches,
                      "rival_matches": rival_matches[:count]},
        "lesson": {"demonstration_matches": rival_matches[count:count + n_demos],
                   "query_match": rival_matches[-1],
                   "query_input_sha256": results[-1]["input_sha256"],
                   "query_output_sha256": results[-1]["output_sha256"],
                   "reference_query_shape": [len(results[-1]["output"]), len(results[-1]["output"][0])],
                   "rival_query_shape": [len(rival_outputs[-1]), len(rival_outputs[-1][0])]},
        "context": {
            "payload_argv": sys.argv, "payload_cwd": str(Path.cwd()),
            "bounded_discovery": "The witness was first found at the eighth inspected window: seeds 0..2, starts 0/11/22, stopping at seed 2/start 11. This is discovery, not a prevalence estimate.",
            "prior_audit": "The existing review_index already reports inert fill_ratio and advertised size-domain inconsistencies for this source. This witness concerns lesson identifiability, not that control defect.",
        },
        "limits": [
            "One deterministic generated lesson; no full battery or failure-rate estimate.",
            "The reference output is correct. The finding is a finite-rival teaching ambiguity.",
            "No generator, rule, approval, or existing audit status was changed.",
        ],
    }
    write_json(out / "case.json", case)
    print(json.dumps({"finding_reproduced": reproduced, "generator_sha256": before,
                      "executed_rule_hash": applied["executed_rule_hash"],
                      "canonical_pairs": count, "demonstration_matches": case["lesson"]["demonstration_matches"],
                      "query_shapes": {"reference": case["lesson"]["reference_query_shape"], "rival": case["lesson"]["rival_query_shape"]},
                      "validator_results": validator, "out": str(out)}, sort_keys=True))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
