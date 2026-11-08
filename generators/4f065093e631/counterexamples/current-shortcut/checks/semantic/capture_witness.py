"""Reproduce one lawful rarity-shortcut counterexample with canonical Racket."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator


TASK_ID = "4f065093e631"
parser = argparse.ArgumentParser()
parser.add_argument("--suffix", default="", choices=("", "_v2"))
suffix = parser.parse_args().suffix
ROOT = find_root(__file__)
generator, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
settings = {
    "seed": 817,
    "sample_index": 1,
    "difficulty": "medium",
    "scene_profile": "frame_4x5_balanced",
}
grid = generator.generate(**settings)
assert generator.self_check(grid) == []
assert generator.SEMANTIC_WITNESSES["rare_color_decoy"](grid) is True
rival = generator.CANONICAL_SHORTCUTS["rarest_color_bbox"](grid)
applied = Catalog(ROOT).apply(
    TASK_ID,
    [grid],
    reference="canonical",
    check_generator_domain=True,
    timeout=60,
)
output = applied["results"][0]["output"]
assert output is not None
assert output == generator.rule_mirror(grid)
assert rival != output
assert applied["generator_sha256"] == source_sha256
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha256

counterexample = {
    "schema": "task-local-shortcut-counterexample-v1",
    "task_id": TASK_ID,
    "generator_version": generator.VERSION,
    "generator_sha256": source_sha256,
    "settings": settings,
    "rival": "rarest_color_bbox",
    "witness": "rare_color_decoy",
    "label_authority": "canonical Racket via public Catalog.apply",
    "executed_rule_hash": applied["executed_rule_hash"],
    "rule_text_sha256": applied["rule_text_sha256"],
    "input": grid,
    "intended_output": output,
    "rival_output": rival,
    "input_sha256": applied["results"][0]["input_sha256"],
    "intended_output_sha256": applied["results"][0]["output_sha256"],
    "input_color_counts": dict(sorted(Counter(value for row in grid for value in row).items())),
    "differing_output_cells": [
        [row, col] for row in range(len(grid)) for col in range(len(grid[0]))
        if output[row][col] != rival[row][col]
    ],
    "declared_rival_disagreement_counts": {
        name: sum(a != b for row_a, row_b in zip(output, solve(grid))
                  for a, b in zip(row_a, row_b))
        for name, solve in generator.LESSON_COMPETITORS.items()
    },
    "scope": (
        "One full-size lawful generated witness. The 21x21 calibration and role "
        "structure are retained. This refutes the declared rarity rival on this "
        "input; it is not universal lesson-identifiability evidence."
    ),
}
evidence = Path(__file__).resolve().parent
(evidence / f"rare_color_racket{suffix}.json").write_text(json.dumps(applied, indent=2) + "\n")
destination = ROOT / "generators" / TASK_ID / "counterexamples" / f"rare_color_shortcut{suffix}.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(counterexample, indent=2) + "\n")
print(json.dumps({
    "generator_sha256": source_sha256,
    "executed_rule_hash": applied["executed_rule_hash"],
    "racket_matches_python_mirror": True,
    "rival_disagrees": True,
    "differing_output_cells": len(counterexample["differing_output_cells"]),
    "input_color_counts": counterexample["input_color_counts"],
    "declared_rival_disagreement_counts": counterexample["declared_rival_disagreement_counts"],
    "elapsed_seconds": applied["elapsed_seconds"],
    "counterexample": str(destination),
}, indent=2))
