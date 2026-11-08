"""Findings-only audit: expose the sampler's rectangle-only teaching shortcut."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "a286d31d63fb"
EXPECTED_SOURCE = "a831e29015bb5b1fb90332adedd799655969ce0d925970debdd90d5d2eca5ac2"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def components(grid):
    """Independent monochromatic four-connected object extraction."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        stack = [start]
        cells = set()
        while stack:
            point = stack.pop()
            if point not in unseen or grid[point[0]][point[1]] != color:
                continue
            unseen.remove(point)
            cells.add(point)
            r, c = point
            stack.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
        result.append((color, sorted(cells)))
    return result


def describe(cells):
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    counts = Counter(r for r, _ in cells)
    profile = [counts[r] for r in range(r0, r1 + 1)]
    return {"row_profile": profile, "flat": len(set(profile)) == 1,
            "solid_rectangle": len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1),
            "cells": cells}


def transform(grid, *, rectangles_only):
    output = [row[:] for row in grid]
    for _color, cells in components(grid):
        facts = describe(cells)
        if facts["solid_rectangle" if rectangles_only else "flat"]:
            for r, c in cells:
                output[r][c] = 8
    return output


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    generator, source, digest = load_selected_generator(TASK_ID, root=ROOT)
    assert digest == EXPECTED_SOURCE
    records = [row for line in canonical_path(ROOT).read_text().splitlines()
               if (row := json.loads(line)).get("task_id") == TASK_ID]
    assert len(records) == 1
    rule = records[0]["program_solution"]
    targets = {key for key, value in json.loads((ROOT / "catalog/authority_files.json").read_text()).items()
               if value == TASK_ID}
    authorities = []
    for entry in json.loads((ROOT / "catalog/runtime_files.json").read_text()):
        if entry["target"] in targets:
            path = ROOT / entry["path"]
            active = json.loads(path.read_text())["racket_target"]["target_code"]
            assert active == rule
            authorities.append({"path": entry["path"], "file_sha256": sha256(path.read_bytes()),
                                "rule_sha256": sha256(active.encode())})

    template_facts = []
    for group in ("_FLAT", "_NON_FLAT"):
        for index, cells in enumerate(getattr(generator, group)):
            template_facts.append({"group": group, "index": index, **describe(cells)})
    assert all(item["flat"] == item["solid_rectangle"] for item in template_facts)

    train = [pair for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
             if pair["split"] == "train"]
    canonical_results = [
        {"variant": pair["variant"], "pair_index": pair["pair_index"],
         "rectangle_rival_fits": transform(pair["input"], rectangles_only=True) == pair["output"]}
        for pair in train
    ]
    assert len(canonical_results) == 2 and all(item["rectangle_rival_fits"] for item in canonical_results)

    sample_results = []
    for band in ("easy", "medium", "hard"):
        for seed in range(5):
            grid = generator.generate(seed, 0, difficulty=band)
            sample_results.append({"seed": seed, "sample_index": 0, "difficulty": band,
                                   "input_sha256": sha256(json.dumps(grid, separators=(",", ":")).encode()),
                                   "self_check": generator.self_check(grid),
                                   "rival_matches_row_profile_model":
                                   transform(grid, rectangles_only=True) == transform(grid, rectangles_only=False)})
    assert all(not item["self_check"] and item["rival_matches_row_profile_model"] for item in sample_results)

    # One flat nonrectangle and two ordinary nonflat shapes. All are distinct
    # colors, four-connected, one-cell separated, and inside the easy 10x12 size.
    witness = [[0] * 12 for _ in range(10)]
    planted = {2: [(1, 1), (1, 2), (2, 2), (2, 3)],
               3: [(1, 7), (2, 7), (2, 8), (2, 9)],
               4: [(6, 5), (7, 4), (7, 5), (7, 6)]}
    for color, cells in planted.items():
        for r, c in cells:
            witness[r][c] = color
    errors = generator.self_check(witness, difficulty="easy")
    assert errors == []
    expected = transform(witness, rectangles_only=False)
    rival = transform(witness, rectangles_only=True)
    assert expected != rival
    write_json("input.json", witness)
    write_json("expected_row_profile.json", expected)
    write_json("rectangle_rival.json", rival)
    write_json("canonical_rule.json", {"task_id": TASK_ID, "source": rule, "sha256": sha256(rule.encode())})
    report = {
        "schema": "a286d31d63fb-findings-only-probe-v1", "task_id": TASK_ID,
        "source_path": str(source), "source_sha256": digest,
        "canonical_rule_sha256": sha256(rule.encode()), "authorities": authorities,
        "counts": {"templates": len(template_facts), "canonical_train_pairs": len(train),
                   "ordinary_generated_cases": len(sample_results), "constructed_witnesses": 1},
        "template_facts": template_facts, "canonical_train_results": canonical_results,
        "sample_results": sample_results,
        "generated_label_source": "independent Python row-profile model; not an executed-label claim",
        "witness": {"shape": [10, 12], "self_check": errors,
                    "components": [{"color": color, **describe(cells)} for color, cells in components(witness)],
                    "expected_changed_cells": [[r, c] for r in range(10) for c in range(12)
                                               if expected[r][c] != witness[r][c]],
                    "rival_is_identity": rival == witness},
        "source_unchanged": sha256(source.read_bytes()) == digest,
    }
    write_json("probe.json", report)
    print(json.dumps({"source_sha256": digest, "rule_sha256": sha256(rule.encode()),
                      "counts": report["counts"], "witness_self_check": errors,
                      "expected_changed_cells": report["witness"]["expected_changed_cells"],
                      "source_unchanged": report["source_unchanged"]}))


if __name__ == "__main__":
    main()
