from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "2d4e8c8fa10e"
ROOT = find_root(__file__)
gen, source_path, source_sha256 = load_selected_generator(TASK, root=ROOT)


def bbox_dims(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


canonical = canonical_pairs(TASK, root=ROOT)
rival = gen.CANONICAL_SHORTCUTS["keep_size4_height2"]
canonical_rival_fit = [rival(pair["input"]) == pair["output"] for pair in canonical]
assert all(canonical_rival_fit)

ordinary_total = 0
tetromino_total = 0
tetromino_both_orientations = 0
tetromino_rival_refuted = 0
orientation_histogram = {}
lesson_windows = 0
lesson_failures = []

for difficulty in ("easy", "medium", "hard"):
    for seed in range(100):
        for sample_index in range(12):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            ordinary_total += 1
            assert gen.self_check(grid) == []
            analysis = gen._analysis_or_raise(grid)
            if analysis["distractor_profile"] == "tetromino":
                tetromino_total += 1
                dims = tuple(sorted(bbox_dims(cells) for cells in analysis["distractors"]))
                orientation_histogram[str(dims)] = orientation_histogram.get(str(dims), 0) + 1
                if (2, 3) in dims and (3, 2) in dims:
                    tetromino_both_orientations += 1
                if rival(grid) != gen.rule_mirror(grid):
                    tetromino_rival_refuted += 1

        for start in range(9):
            grids = [gen.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
            demos = [{"input": g, "output": gen.rule_mirror(g)} for g in grids[:3]]
            query = {"input": grids[3], "output": gen.rule_mirror(grids[3])}
            reasons = gen.lesson_identifiable(demos, query)
            lesson_windows += 1
            if reasons:
                lesson_failures.append({
                    "difficulty": difficulty,
                    "seed": seed,
                    "start": start,
                    "reasons": reasons,
                })

assert tetromino_total == tetromino_both_orientations == tetromino_rival_refuted
assert not lesson_failures

override_axes = {
    "grid_h": range(8, 11),
    "grid_w": range(9, 12),
    "square_count": range(1, 4),
    "distractor_count": range(1, 4),
    "distractor_profile": ("triomino", "tetromino", "square_tail"),
}
keys = tuple(override_axes)
override_cases = 0
horizontal_singletons = 0
vertical_singletons = 0
for sample_index in (0, 1):
    for values in itertools.product(*(override_axes[key] for key in keys)):
        overrides = dict(zip(keys, values))
        grid = gen.generate(10_000 + override_cases, sample_index, difficulty="hard", **overrides)
        override_cases += 1
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        if overrides["distractor_profile"] == "tetromino" and overrides["distractor_count"] == 1:
            dims = bbox_dims(gen._analysis_or_raise(grid)["distractors"][0])
            horizontal_singletons += dims == (2, 3)
            vertical_singletons += dims == (3, 2)

assert horizontal_singletons and vertical_singletons

invalid_identity_rejections = {}
for label, args in {
    "seed_true": (True, 0),
    "seed_float": (1.5, 0),
    "index_true": (1, True),
    "index_float": (1, 1.5),
    "index_negative": (1, -1),
}.items():
    try:
        gen.generate(*args)
    except (TypeError, ValueError) as exc:
        invalid_identity_rejections[label] = f"{type(exc).__name__}: {exc}"
    else:
        raise AssertionError(f"{label} was accepted")

report = {
    "schema": "arcpuzzles-task-probe-v1",
    "task_id": TASK,
    "source_path": str(source_path.relative_to(ROOT)),
    "source_sha256": source_sha256,
    "rule_hash": gen.RULE_HASH,
    "canonical_pairs": len(canonical),
    "canonical_height2_rival_fit": canonical_rival_fit,
    "ordinary_draws": ordinary_total,
    "ordinary_seed_range": [0, 99],
    "ordinary_sample_index_range": [0, 11],
    "difficulties": ["easy", "medium", "hard"],
    "tetromino_scenes": tetromino_total,
    "tetromino_scenes_with_both_orientations": tetromino_both_orientations,
    "tetromino_scenes_refuting_height2_rival": tetromino_rival_refuted,
    "orientation_histogram": orientation_histogram,
    "lesson_windows": lesson_windows,
    "lesson_failures": lesson_failures,
    "override_cases": override_cases,
    "override_sample_indices": [0, 1],
    "single_tetromino_horizontal_cases": horizontal_singletons,
    "single_tetromino_vertical_cases": vertical_singletons,
    "invalid_identity_rejections": invalid_identity_rejections,
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}

out = ROOT.parent / "checks" / "repair-probe.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
