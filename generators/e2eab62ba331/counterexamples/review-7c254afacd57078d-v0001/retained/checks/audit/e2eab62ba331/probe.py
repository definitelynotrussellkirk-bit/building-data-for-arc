from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK = "e2eab62ba331"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


def canonical_source():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise RuntimeError(TASK)


def callable_source(source):
    text = source.strip()
    body = text[len("(rule!") : -1].strip()
    return body if body.startswith("(lambda") else f"(lambda (g) {body})"


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def erase_other_colors(grid):
    target = grid[0][0]
    output = GEN.rule_mirror(grid)
    return [[value if value in (0, target) else 0 for value in row] for row in output]


pairs = []
for index in (7, 8, 9, 10):
    grid = GEN.generate(0, index, difficulty="easy")
    output = GEN.rule_mirror(grid)
    rival = erase_other_colors(grid)
    pairs.append({
        "seed": 0,
        "sample_index": index,
        "difficulty": "easy",
        "scene_profile": GEN.observe_overrides(grid)["scene_profile"],
        "input": grid,
        "output": output,
        "rival_output": rival,
        "rival_matches": rival == output,
        "self_check": GEN.self_check(grid),
    })

if not all(row["rival_matches"] for row in pairs[:3]):
    raise SystemExit("historical three-demo shortcut no longer reproduces")
if pairs[3]["rival_matches"]:
    raise SystemExit("query no longer distinguishes interior-color preservation")

source = canonical_source()
query = pairs[3]
with RacketBridge(timeout=30, max_calls_before_restart=8) as bridge:
    racket = normalize_grid(bridge.eval_text(f"({callable_source(source)} {literal(query['input'])})"))
    runtime = bridge.runtime_identity
if racket != query["output"]:
    raise SystemExit("Python mirror disagrees with Racket authority")

report = {
    "schema": "audit-e2eab62ba331-selector-crop-shortcut-v1",
    "status": "reproduced",
    "task_id": TASK,
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "rule_hash": GEN.RULE_HASH,
    "canonical_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
    "rival": "Crop the selected bounding box but erase every nonzero color other than the selector color.",
    "demos_fit": 3,
    "query_disagrees": True,
    "lesson_hook_declared": hasattr(GEN, "lesson_identifiable"),
    "pairs": pairs,
    "query_racket_output": racket,
    "racket_runtime": runtime,
    "limits": [
        "One exact ordinary easy-band four-item window was checked.",
        "This reproduces a current-source teaching insufficiency; it is not a claim that all lessons are ambiguous.",
    ],
}
(HERE / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "reproduced", "source_sha256": SOURCE_SHA, "profiles": [p["scene_profile"] for p in pairs]}))
