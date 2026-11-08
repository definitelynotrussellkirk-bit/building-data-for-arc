"""Reproduce the ead22faa41ef all-3/all-2 lesson shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "ead22faa41ef"
SEED = 3351
DIFFICULTY = "medium"
SAMPLE_INDICES = [0, 1, 2, 3]


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    repo = Path.cwd()
    out = repo.parent / "checks" / "audit" / TASK_ID
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=repo)
    inputs = [
        generator.generate(SEED, index, difficulty=DIFFICULTY)
        for index in SAMPLE_INDICES
    ]
    checks = [generator.self_check(grid) for grid in inputs]
    if any(checks):
        raise AssertionError(f"generated inputs failed self_check: {checks}")

    features = []
    for index, grid in zip(SAMPLE_INDICES, inputs):
        scene = generator._scene_features(grid)
        counts = scene["counts"]
        features.append(
            {
                "sample_index": index,
                "self_check": [],
                "paired3": len(scene["paired3"]),
                "paired2": len(scene["paired2"]),
                "lone3": counts[3] - len(scene["paired3"]),
                "lone2": counts[2] - len(scene["paired2"]),
                "fives": counts[5],
                "shape": [len(grid), len(grid[0])],
            }
        )
    if not all(row["lone3"] == row["lone2"] == 0 for row in features[:3]):
        raise AssertionError("the three demonstrations no longer lack lone 3/2 cells")
    if features[3]["lone2"] != 3:
        raise AssertionError("the query no longer has the three preserved lone 2s")

    out.mkdir(parents=True, exist_ok=True)
    (out / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    receipt = {
        "schema": "ead22faa41ef-all-cells-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(repo)),
        "generator_sha256": source_sha256,
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": SAMPLE_INDICES,
        "self_check": checks,
        "input_sha256": [hashlib.sha256(canonical_json(grid)).hexdigest() for grid in inputs],
        "features": features,
        "lesson_claim": (
            "replace every 3 with 8 and every 2 with 0 matches the first three "
            "examples because they contain no lone 3/2 cells; the fourth contains three lone 2s"
        ),
    }
    (out / "generation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
