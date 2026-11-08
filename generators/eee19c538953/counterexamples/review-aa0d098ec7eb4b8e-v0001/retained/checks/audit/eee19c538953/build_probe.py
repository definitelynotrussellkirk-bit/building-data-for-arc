#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "eee19c538953"


def crop_inside_eights(grid: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not cells:
        return [row[:] for row in grid]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 + 1 : c1] for row in grid[r0 + 1 : r1]]


def width_guard_rival(grid: list[list[int]]) -> list[list[int]]:
    cols = [c for row in grid for c, value in enumerate(row) if value == 8]
    if not cols:
        return [row[:] for row in grid]
    outer_width = max(cols) - min(cols) + 1
    if outer_width < 5:
        return [row[:] for row in grid]
    return crop_inside_eights(grid)


def frame_size(grid: list[list[int]]) -> dict[str, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    return {
        "outer_h": max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
        "outer_w": max(c for _, c in cells) - min(c for _, c in cells) + 1,
    }


def main() -> int:
    here = Path(__file__).resolve().parent
    root = find_root(Path(__file__).resolve().parents[3] / "repo")
    module, source_path, source_sha = load_selected_generator(TASK, root=root)
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    inputs = [pair["input"] for pair in pairs]
    rivals = [width_guard_rival(grid) for grid in inputs]
    labels = [pair["output"] for pair in pairs]
    records = []
    for index, (pair, rival) in enumerate(zip(pairs, rivals)):
        records.append(
            {
                "pair_index": index,
                "split": pair.get("split"),
                "frame_size": frame_size(pair["input"]),
                "self_check": module.self_check(pair["input"]),
                "expected_output": pair["output"],
                "width_guard_rival_output": rival,
                "rival_matches_label": rival == pair["output"],
            }
        )
    (here / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (here / "width-guard-rival-outputs.json").write_text(json.dumps(rivals, indent=2) + "\n")
    payload = {
        "schema": "arcpuzzles-audit-width-guard-probe-v1",
        "task_id": TASK,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "prior_return_used_as_lead": "review-889692cba48d68df:v0001",
        "claim": "crop strict interior only when the color-8 frame outer width is at least 5; otherwise return the input unchanged",
        "canonical_records": records,
        "rival_fit_vector": [rival == label for rival, label in zip(rivals, labels)],
        "ordinary_generator_minimum_frame_width_source_line": 82,
        "validator_minimum_frame_width_source_line": 129,
        "command": {
            "cwd": "repo",
            "argv": ["python3", "../checks/audit/eee19c538953/build_probe.py"],
        },
    }
    (here / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"generator_sha256": source_sha, "rival_fit_vector": payload["rival_fit_vector"], "out": str(here / "probe.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
