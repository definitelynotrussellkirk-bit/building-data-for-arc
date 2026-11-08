from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, load_selected_generator, normalize_grid

TASK_ID = "2920da6abe8a"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"
gen, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)


def value_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def marker(grid):
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if len(cells) != 1:
        raise ValueError(f"expected one marker, got {cells}")
    return cells[0]


def canonical_program():
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one authority, got {len(sources)}")
    return sources.pop()


def apply(bridge, program, grid):
    text = program.strip()
    body = text[len("(rule!") : -1].strip()
    bridge.define_grid("g", grid)
    return normalize_grid(bridge.eval_text(f"({body} g)"))


def colorize(mask, color):
    return [[color if value else 0 for value in row] for row in mask]


seed = None
inputs = None
for candidate in range(1000):
    trial = [gen.generate(candidate, index, difficulty="easy") for index in range(4)]
    train_positions = {(marker(grid)[0], marker(grid)[1]) for grid in trial[:3]}
    query_position = marker(trial[3])[:2]
    if query_position not in train_positions:
        seed = candidate
        inputs = trial
        break
if seed is None or inputs is None:
    raise RuntimeError("no unseen-query witness found")

program = canonical_program()
with RacketBridge(timeout=15, startup_timeout=60) as bridge:
    outputs = [apply(bridge, program, grid) for grid in inputs]

lookup = {}
for grid, output in zip(inputs[:3], outputs[:3]):
    r, c, color = marker(grid)
    lookup[(r, c)] = [[1 if value != 0 else 0 for value in row] for row in output]

r, c, color = marker(inputs[3])
rival_output = colorize(lookup[(r, c)], color) if (r, c) in lookup else [[0] * 9 for _ in range(9)]
rival_train = []
for grid, output in zip(inputs[:3], outputs[:3]):
    rr, cc, train_color = marker(grid)
    prediction = colorize(lookup[(rr, cc)], train_color)
    rival_train.append(prediction == output)

diffs = [
    [row, col, outputs[3][row][col], rival_output[row][col]]
    for row in range(9)
    for col in range(9)
    if outputs[3][row][col] != rival_output[row][col]
]
report = {
    "schema": "audit-teaching-lookup-probe-v1",
    "task_id": TASK_ID,
    "finding_id": "A-2920-POSITION-LOOKUP-1",
    "source_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "authority_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "seed": seed,
    "difficulty": "easy",
    "train_positions": [list(marker(grid)[:2]) for grid in inputs[:3]],
    "query_position": list(marker(inputs[3])[:2]),
    "rival": (
        "Memorize the output mask for each marker position shown in the three demonstrations; "
        "for an unseen position predict blank. This finite position lookup fits every demonstration."
    ),
    "rival_fits_all_demonstrations": all(rival_train),
    "rival_query_differs": rival_output != outputs[3],
    "query_difference_count": len(diffs),
    "first_query_differences": diffs[:12],
    "train": [
        {"input": grid, "output": output, "input_sha256": value_hash(grid), "output_sha256": value_hash(output)}
        for grid, output in zip(inputs[:3], outputs[:3])
    ],
    "query": {
        "input": inputs[3],
        "authority_output": outputs[3],
        "rival_output": rival_output,
        "input_sha256": value_hash(inputs[3]),
        "authority_output_sha256": value_hash(outputs[3]),
        "rival_output_sha256": value_hash(rival_output),
    },
    "limitation": "One exact four-pair production-style window; this demonstrates a concrete ambiguity, not its frequency.",
}
out = Path(__file__).with_name("teaching_lookup_probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: report[k] for k in ["finding_id", "seed", "train_positions", "query_position", "rival_fits_all_demonstrations", "rival_query_differs", "query_difference_count", "source_sha256"]}, indent=2, sort_keys=True))
