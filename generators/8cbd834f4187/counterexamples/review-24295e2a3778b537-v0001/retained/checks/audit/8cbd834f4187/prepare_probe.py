from __future__ import annotations
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK = "8cbd834f4187"
REPO = Path.cwd()
OUT = REPO.parent / "checks/audit" / TASK
GEN, GEN_PATH, GEN_SHA = load_selected_generator(TASK, root=REPO)

seed = 1
start = 7
difficulty = "easy"
query_index = 3
lesson = []
for offset in range(GEN.EXAMPLES_NEEDED + 1):
    sample_index = start + offset
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    lesson.append(
        {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "input": grid,
            "self_check": GEN.self_check(grid, difficulty=difficulty),
            "seed_sequence": [value for value in grid[1] if value != 0],
            "mirror_output": GEN.rule_mirror(grid),
            "sorted_rival_output": GEN._competitor_sorted_colors(grid),
        }
    )
assert all(not row["self_check"] for row in lesson)
pairs = [{"input": row["input"], "output": row["mirror_output"]} for row in lesson]
query = pairs[query_index]
demos = [pair for index, pair in enumerate(pairs) if index != query_index]
reasons = GEN.lesson_identifiable(demos, query)
assert any("sort seed colors" in reason for reason in reasons)

(OUT / "input.json").write_text(
    json.dumps({"inputs": [row["input"] for row in lesson]}, indent=2) + "\n"
)
(OUT / "probe-pre-racket.json").write_text(
    json.dumps(
        {
            "schema": "arcpuzzles-audit-probe-v1",
            "task_id": TASK,
            "generator_sha256": GEN_SHA,
            "generator_path": str(GEN_PATH.relative_to(REPO)),
            "seed": seed,
            "start_sample_index": start,
            "difficulty": difficulty,
            "examples_needed": GEN.EXAMPLES_NEEDED,
            "query_index": query_index,
            "lesson_identifiable_reasons": reasons,
            "lesson": lesson,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        indent=2,
        sort_keys=True,
    )
    + "\n"
)
print(json.dumps({"generator_sha256": GEN_SHA, "query_index": query_index, "reasons": reasons, "sequences": [row["seed_sequence"] for row in lesson]}, indent=2))
