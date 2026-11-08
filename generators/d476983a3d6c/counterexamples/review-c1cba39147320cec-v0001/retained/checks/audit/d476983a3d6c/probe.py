"""Source-bound count-of-object-colors shortcut probe; no source mutations."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "repo" / "shared" / "runtime"))
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "d476983a3d6c"
EXPECTED_SOURCE = "80d94a6e64895839b4da9c63524f47d7ea1568fa2714a8f846933ccd166fb497"


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def rival(grid):
    """Choose orientation from object-color-count parity, not the command."""
    positions = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color and (r, c) != (0, 0):
                positions.setdefault(color, []).append((r, c))
    orientation = 1 if len(positions) % 2 else 2
    result = [list(row) for row in grid]
    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if orientation == 1:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                result[r1][c] = color
            for r in range(min(r1, r2), max(r1, r2) + 1):
                result[r][c2] = color
        else:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                result[r][c1] = color
            for c in range(min(c1, c2), max(c1, c2) + 1):
                result[r2][c] = color
    return result


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK, root=root)
    assert digest == EXPECTED_SOURCE, digest
    canonical = []
    for pair in canonical_pairs(TASK, root=root, labeled_only=True):
        actual = pair["output"]
        predicted = rival(pair["input"])
        canonical.append({
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"],
            "self_check": gen.self_check(pair["input"]),
            "rival_matches_label": predicted == actual,
            "actual_sha256": grid_hash(actual),
            "rival_sha256": grid_hash(predicted),
        })

    draws = []
    lesson = []
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        seed = 476983 + band_index
        for sample_index in range(12):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            actual = gen._rule_mirror(grid)
            predicted = rival(grid)
            object_colors = {color for r, row in enumerate(grid)
                             for c, color in enumerate(row)
                             if color and (r, c) != (0, 0)}
            observations = gen.observe_overrides(grid)
            draws.append({
                "seed": seed, "sample_index": sample_index,
                "difficulty": difficulty, **observations,
                "height": len(grid), "width": len(grid[0]),
                "command": grid[0][0], "object_color_count": len(object_colors),
                "rival_inferred_command": 1 if len(object_colors) % 2 else 2,
                "self_check": gen.self_check(grid),
                "strict_canonical_like": gen.strict_canonical_like(grid),
                "input_sha256": grid_hash(grid),
                "actual_python_mirror_sha256": grid_hash(actual),
                "rival_sha256": grid_hash(predicted),
                "rival_matches_python_mirror": predicted == actual,
            })
            if difficulty == "medium" and sample_index < 5:
                lesson.append({"seed": seed, "sample_index": sample_index,
                               "difficulty": difficulty, "input": grid,
                               "output": actual, "rival_output": predicted})

    witness = [[0] * 8 for _ in range(8)]
    witness[0][0] = 1
    for color, cells in ((3, ((1, 1), (2, 2))), (4, ((4, 4), (5, 5)))):
        for r, c in cells:
            witness[r][c] = color
    dump("input.json", witness)
    dump("rival.json", rival(witness))
    dump("python-mirror.json", gen._rule_mirror(witness))
    dump("lesson.json", {
        "label_authority": "Python mirror; compare official Racket separately",
        "train": lesson[:4], "test": lesson[4:],
        "declared_lesson_identifiable_errors": gen.lesson_identifiable(lesson[:4], lesson[4]["input"]),
        "undeclared_rival_fits_all_four_demos": all(p["output"] == p["rival_output"] for p in lesson[:4]),
        "undeclared_rival_also_fits_query": lesson[4]["output"] == lesson[4]["rival_output"],
    })
    dump("generated-input.json", lesson[0]["input"])
    dump("generated-rival.json", lesson[0]["rival_output"])
    profiles = Counter(item["scene_profile"] for item in draws)
    report = {
        "task_id": TASK, "source_path": str(source.relative_to(root)),
        "source_sha256": digest, "declared_rule_hash": gen.RULE_HASH,
        "canonical": canonical, "canonical_pairs": len(canonical),
        "canonical_rival_matches": sum(item["rival_matches_label"] for item in canonical),
        "draws": draws, "draw_count": len(draws), "profile_counts": dict(profiles),
        "generated_rival_matches": sum(item["rival_matches_python_mirror"] for item in draws),
        "generated_validation_errors": sum(bool(item["self_check"]) for item in draws),
        "profile_invariant": {
            name: {"command": signature[0], "pair_colors": signature[1],
                   "singleton_colors": signature[2], "object_color_count": signature[1] + signature[2],
                   "count_parity_predicts_command": (1 if (signature[1] + signature[2]) % 2 else 2) == signature[0]}
            for name, signature in gen.SCENE_SIGNATURES.items()
        },
        "witness": {
            "construction": "handcrafted counterfactual, not a generated draw",
            "dimensions": [8, 8], "nonzero_cells": 5,
            "command": 1, "pair_count": 2, "singleton_count": 0,
            "self_check": gen.self_check(witness),
            "strict_canonical_like": gen.strict_canonical_like(witness),
            "input_sha256": grid_hash(witness),
            "python_mirror_sha256": grid_hash(gen._rule_mirror(witness)),
            "rival_sha256": grid_hash(rival(witness)),
            "rival_differs_from_python_mirror": rival(witness) != gen._rule_mirror(witness),
        },
    }
    dump("probe.json", report)
    print(json.dumps({key: report[key] for key in (
        "task_id", "source_sha256", "canonical_pairs", "canonical_rival_matches",
        "draw_count", "generated_rival_matches", "generated_validation_errors", "profile_counts", "witness"
    )}, indent=2))
    assert all(not row["self_check"] for row in canonical)
    assert report["canonical_rival_matches"] == len(canonical)
    assert report["generated_rival_matches"] == len(draws)
    assert report["generated_validation_errors"] == 0
    assert report["witness"]["rival_differs_from_python_mirror"]


if __name__ == "__main__":
    main()
