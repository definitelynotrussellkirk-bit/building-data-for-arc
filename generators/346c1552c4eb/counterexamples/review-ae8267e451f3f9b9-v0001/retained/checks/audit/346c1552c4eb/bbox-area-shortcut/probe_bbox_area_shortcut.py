from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "346c1552c4eb"
ROOT = find_root(__file__)
GENERATOR, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
HERE = Path(__file__).resolve().parent


def bbox_area_rival(grid):
    analysis = GENERATOR._analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    ordered = sorted(
        analysis["components"],
        key=lambda component: (
            (max(row for row, _ in component["cells"]) - min(row for row, _ in component["cells"]) + 1)
            * (max(col for _, col in component["cells"]) - min(col for _, col in component["cells"]) + 1),
            component["color"],
        ),
    )
    return [[component["color"] for component in ordered]]


def main():
    grids = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    rivals = [bbox_area_rival(grid) for grid in grids]
    (HERE / "rival.json").write_text(json.dumps(rivals, indent=2) + "\n", encoding="utf-8")
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    canonical_fit = [bbox_area_rival(pair["input"]) == pair["output"] for pair in canonical]
    report = {
        "schema": "audit-346c1552c4eb-bbox-area-shortcut-v2",
        "task_id": TASK_ID,
        "generator_sha256": SOURCE_SHA256,
        "generator_path": SOURCE.relative_to(ROOT).as_posix(),
        "seed": 0,
        "difficulty": "easy",
        "sample_indices": [5, 6, 7, 8],
        "validator_reasons": [GENERATOR.self_check(grid) for grid in grids],
        "python_authority_mirror": [GENERATOR.rule_mirror(grid) for grid in grids],
        "bbox_area_rival": rivals,
        "demonstration_matches": [
            GENERATOR.rule_mirror(grids[index]) == rivals[index] for index in range(3)
        ],
        "query_disagrees": GENERATOR.rule_mirror(grids[3]) != rivals[3],
        "canonical_pairs": len(canonical),
        "canonical_fit_vector": canonical_fit,
        "canonical_rival_matches": sum(canonical_fit),
        "input_sha256": hashlib.sha256((HERE / "input.json").read_bytes()).hexdigest(),
        "rival_sha256": hashlib.sha256((HERE / "rival.json").read_bytes()).hexdigest(),
    }
    (HERE / "probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
