from __future__ import annotations

from copy import deepcopy
import hashlib
from itertools import permutations
import json
from pathlib import Path
import sys

TASK = "9fc0b6db96fe"
BAND = "easy"
SEED = 3
START = 3
QUERY_INDEX = 0
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
WORKSPACE = ROOT / "generators" / TASK / "workspace"
RUNTIME = ROOT / "shared" / "runtime"
for path in (str(WORKSPACE), str(RUNTIME)):
    if path not in sys.path:
        sys.path.insert(0, path)

from reference_probe import (  # noqa: E402
    component_crop,
    legend_entries,
    load_generator,
    nonzero_components,
    pack_gallery,
)

SOURCE = ROOT / "generators" / TASK / "generator.py"
INTENDED_MAPPING = {1: 1, 2: 2, 3: 3, 4: 4}
# This one-to-one rival swaps identity and half-turn while preserving cw and lr.
RIVAL_MAPPING = {1: 3, 2: 2, 3: 1, 4: 4}


def transform(crop, operation):
    if operation == 1:
        return [list(row) for row in crop]
    if operation == 2:
        return [list(row) for row in zip(*crop[::-1])]
    if operation == 3:
        return [list(reversed(row)) for row in reversed(crop)]
    if operation == 4:
        return [list(reversed(row)) for row in crop]
    raise ValueError(operation)


def gallery_with_mapping(grid, mapping):
    body = grid[2:]
    components = nonzero_components(grid)
    by_color = {
        body[cells[0][0]][cells[0][1]]: cells
        for cells in components
    }
    key = grid[0][0]
    parts = [
        transform(component_crop(grid, by_color[color]), mapping[key])
        for _, color in legend_entries(grid)
    ]
    return pack_gallery(parts)


gen = load_generator(SOURCE)
grids = [gen.generate(SEED, START + offset, difficulty=BAND) for offset in range(4)]
intended_outputs = [gallery_with_mapping(grid, INTENDED_MAPPING) for grid in grids]
rival_outputs = [gallery_with_mapping(grid, RIVAL_MAPPING) for grid in grids]
pairs = [
    {"input": deepcopy(grid), "output": deepcopy(output)}
    for grid, output in zip(grids, intended_outputs)
]
demos = [pair for index, pair in enumerate(pairs) if index != QUERY_INDEX]
query = pairs[QUERY_INDEX]

all_survivors = []
for values in permutations((1, 2, 3, 4)):
    mapping = dict(zip((1, 2, 3, 4), values))
    if mapping == INTENDED_MAPPING:
        continue
    if all(gallery_with_mapping(pair["input"], mapping) == pair["output"] for pair in demos):
        if gallery_with_mapping(query["input"], mapping) != query["output"]:
            all_survivors.append(mapping)

(HERE / "inputs.json").write_text(json.dumps(grids, indent=2) + "\n")
(HERE / "intended_outputs_python.json").write_text(json.dumps(intended_outputs, indent=2) + "\n")
(HERE / "rival_outputs.json").write_text(json.dumps(rival_outputs, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "band": BAND,
    "seed": SEED,
    "sample_indices": list(range(START, START + 4)),
    "query_index": QUERY_INDEX,
    "keys": [grid[0][0] for grid in grids],
    "self_check_errors": [list(gen.self_check(deepcopy(grid))) for grid in grids],
    "lesson_hook_reasons": list(gen.lesson_identifiable(deepcopy(demos), deepcopy(query))),
    "intended_mapping": INTENDED_MAPPING,
    "rival_mapping": RIVAL_MAPPING,
    "rival_is_bijection": sorted(RIVAL_MAPPING.values()) == [1, 2, 3, 4],
    "rival_matches_demos": [rival_outputs[index] == intended_outputs[index] for index in range(4) if index != QUERY_INDEX],
    "rival_changes_query": rival_outputs[QUERY_INDEX] != intended_outputs[QUERY_INDEX],
    "surviving_query_changing_bijections": all_survivors,
    "explanation": "The key-1 demonstration is invariant under a half-turn, so swapping the identity and half-turn meanings fits all three demonstrations; the key-3 query is not invariant and changes.",
    "inputs_path": "checks/audit/9fc0b6db96fe/inputs.json",
    "rival_outputs_path": "checks/audit/9fc0b6db96fe/rival_outputs.json",
}
(HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
