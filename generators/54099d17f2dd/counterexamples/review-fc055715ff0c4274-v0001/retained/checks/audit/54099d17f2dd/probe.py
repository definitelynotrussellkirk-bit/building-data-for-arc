from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "54099d17f2dd"
ROOT = Path.cwd()
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def grid_sha(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def conditioned_cardinality_rival(grid: list[list[int]]) -> list[list[int]]:
    """Copy all cells only for leftward five-cell sources; otherwise at most four."""
    info = gen._valid_info(grid)
    offsets = info["offsets"]
    is_leftward_five = len(offsets) == 5 and info["marker"][1] < info["source_anchor"][1]
    selected = offsets if is_leftward_five else offsets[:4]
    return gen._paint_offsets(info["grid_h"], info["grid_w"], info["marker"], selected)


canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
canonical_fit = [conditioned_cardinality_rival(pair["input"]) == pair["output"] for pair in canonical]

ordinary_records: list[dict[str, Any]] = []
for difficulty in ("easy", "medium", "hard"):
    for seed in (0, 17, 20261020):
        for sample_index in range(32):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            intended = gen.rule_mirror(grid)
            rival = conditioned_cardinality_rival(grid)
            info = gen._valid_info(grid)
            ordinary_records.append({
                "difficulty": difficulty,
                "seed": seed,
                "sample_index": sample_index,
                "profile": gen.schedule_profile(seed, sample_index, difficulty),
                "template_shape": info["template_shape"],
                "relation": info["relation"],
                "template_cells": len(info["offsets"]),
                "rival_matches": rival == intended,
                "input_sha256": grid_sha(grid),
            })

witness_seed = 5409901
witness_index = 1
witness_difficulty = "easy"
witness_overrides = {"template_shape": "zigzag5"}
witness_input = gen.generate(
    witness_seed,
    witness_index,
    difficulty=witness_difficulty,
    **witness_overrides,
)
witness_info = gen._valid_info(witness_input)
intended = gen.rule_mirror(witness_input)
rival = conditioned_cardinality_rival(witness_input)
differences = [
    [r, c, intended[r][c], rival[r][c]]
    for r in range(len(intended))
    for c in range(len(intended[0]))
    if intended[r][c] != rival[r][c]
]

input_path = Path("../checks/audit/54099d17f2dd/input.json")
input_path.write_text(json.dumps(witness_input, separators=(",", ":")) + "\n")
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_source": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "rule_hash": gen.RULE_HASH,
    "rival": {
        "id": "copy_fifth_cell_only_for_leftward_five_cell_templates",
        "description": (
            "Copy every source offset only when the source has five cells and the marker "
            "is left of it; otherwise copy at most the first four normalized offsets."
        ),
    },
    "canonical": {
        "pairs": len(canonical),
        "fits": sum(canonical_fit),
        "all_fit": all(canonical_fit),
    },
    "ordinary_sweep": {
        "records": len(ordinary_records),
        "unique_inputs": len({item["input_sha256"] for item in ordinary_records}),
        "rival_matches": sum(item["rival_matches"] for item in ordinary_records),
        "all_match": all(item["rival_matches"] for item in ordinary_records),
        "bands": ["easy", "medium", "hard"],
        "seeds": [0, 17, 20261020],
        "sample_indices": [0, 31],
        "profile_shape_relation_support": sorted({
            (item["profile"], item["template_shape"], item["relation"], item["template_cells"])
            for item in ordinary_records
        }),
    },
    "legal_override_counterexample": {
        "seed": witness_seed,
        "sample_index": witness_index,
        "difficulty": witness_difficulty,
        "overrides": witness_overrides,
        "profile": gen.schedule_profile(witness_seed, witness_index, witness_difficulty),
        "observed": gen.observe_overrides(witness_input),
        "relation": witness_info["relation"],
        "self_check": gen.self_check(witness_input),
        "input": witness_input,
        "intended_output": intended,
        "rival_output": rival,
        "difference_cells": differences,
        "input_sha256": grid_sha(witness_input),
        "intended_output_sha256": grid_sha(intended),
        "rival_output_sha256": grid_sha(rival),
    },
}
Path("../checks/audit/54099d17f2dd/probe.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": source_sha256,
    "canonical_fit": f"{sum(canonical_fit)}/{len(canonical_fit)}",
    "ordinary_fit": f"{sum(item['rival_matches'] for item in ordinary_records)}/{len(ordinary_records)}",
    "ordinary_unique_inputs": report["ordinary_sweep"]["unique_inputs"],
    "witness_self_check": report["legal_override_counterexample"]["self_check"],
    "witness_relation": witness_info["relation"],
    "witness_difference_cells": differences,
}, indent=2))
