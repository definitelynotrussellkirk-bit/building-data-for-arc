from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "df0d6baae973"
SEED = 5
START = 60
DIFFICULTY = "hard"


def perimeter(cells):
    occupied = {tuple(cell) for cell in cells}
    return sum(
        (row + dr, col + dc) not in occupied
        for row, col in occupied
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def perimeter_rival(module, grid):
    facts = module._components(grid)
    values = []
    for row_index, first in enumerate(facts):
        first_perimeter = perimeter(first["cells"])
        row = []
        for col_index, second in enumerate(facts):
            second_perimeter = perimeter(second["cells"])
            if row_index == col_index or first_perimeter == second_perimeter:
                row.append(0)
            elif first_perimeter > second_perimeter:
                row.append(first["color"])
            else:
                row.append(second["color"])
        values.append(row)
    return values


def facts(module, grid):
    analysis = module._analysis(grid)
    return [
        {
            "color": fact["color"],
            "area": fact["size"],
            "perimeter": perimeter(fact["cells"]),
        }
        for fact in analysis["components"]
    ]


def main():
    root = Path.cwd()
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_checks = []
    for index, pair in enumerate(canonical):
        rival = perimeter_rival(module, pair["input"])
        canonical_checks.append(
            {
                "index": index,
                "facts": facts(module, pair["input"]),
                "expected": pair["output"],
                "rival": rival,
                "rival_matches": rival == pair["output"],
            }
        )

    pairs = []
    for offset in range(4):
        sample_index = START + offset
        grid = module.generate(SEED, sample_index, difficulty=DIFFICULTY)
        official = module.rule_mirror(grid)
        rival = perimeter_rival(module, grid)
        analysis = module._analysis(grid)
        pairs.append(
            {
                "seed": SEED,
                "sample_index": sample_index,
                "difficulty": DIFFICULTY,
                "scene_profile": analysis["scene_profile"],
                "input": grid,
                "facts": facts(module, grid),
                "self_check": module.self_check(grid),
                "official_mirror": official,
                "perimeter_rival": rival,
                "rival_matches": rival == official,
            }
        )

    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": module.RULE_HASH,
        "rival": (
            "Sort colors numerically as intended, but compare each component by "
            "4-neighbor boundary perimeter instead of occupied-cell area; emit zero "
            "when perimeters tie."
        ),
        "canonical_fit": all(item["rival_matches"] for item in canonical_checks),
        "canonical_checks": canonical_checks,
        "lesson_policy_tested": "three consecutive demos at sample indexes 60..62; query index 63",
        "demos_fit": all(pair["rival_matches"] for pair in pairs[:3]),
        "query_disagrees": not pairs[3]["rival_matches"],
        "pairs": pairs,
        "command": [
            "python3",
            "review.py",
            "run",
            "python3",
            "../checks/audit/df0d6baae973/probe_perimeter_shortcut.py",
        ],
        "cwd": "packet_root",
    }
    out = root.parent / "checks" / "audit" / TASK_ID / "perimeter_shortcut_window.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    query = root.parent / "checks" / "audit" / TASK_ID / "query_input.json"
    query.write_text(json.dumps(pairs[3]["input"], indent=2) + "\n")
    print(json.dumps({
        "out": str(out),
        "canonical_fit": report["canonical_fit"],
        "demos_fit": report["demos_fit"],
        "query_disagrees": report["query_disagrees"],
        "query_profile": pairs[3]["scene_profile"],
        "source_sha256": source_sha256,
    }, indent=2))


if __name__ == "__main__":
    main()
