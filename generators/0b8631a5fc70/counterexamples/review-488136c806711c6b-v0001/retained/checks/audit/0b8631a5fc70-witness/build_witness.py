#!/usr/bin/env python3
"""Reproduce the first-vs-last marker lesson ambiguity from a generated episode."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EPISODE_PATH = HERE / "episode.jsonl"


def canonical_json_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def marker_positions(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def translate_with_marker_choice(grid: list[list[int]], *, use_last: bool) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    eights = marker_positions(grid, 8)
    nines = marker_positions(grid, 9)
    if not eights or not nines:
        raise ValueError("grid must contain both color-8 and color-9 markers")
    p8 = eights[-1] if use_last else eights[0]
    p9 = nines[-1] if use_last else nines[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    out = [[0] * w for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 8, 9):
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def main() -> None:
    rows = [line for line in EPISODE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one episode, found {len(rows)}")
    episode = json.loads(rows[0])
    train = episode["train"]
    test = episode["test"]
    if len(train) != 3 or len(test) != 1:
        raise ValueError("expected three demonstrations and one query")

    demo_checks = []
    for pair in train:
        grid = pair["input"]
        first = translate_with_marker_choice(grid, use_last=False)
        last = translate_with_marker_choice(grid, use_last=True)
        demo_checks.append(
            {
                "marker_counts": {
                    "8": len(marker_positions(grid, 8)),
                    "9": len(marker_positions(grid, 9)),
                },
                "first_matches_label": first == pair["output"],
                "last_matches_label": last == pair["output"],
            }
        )

    query = test[0]["input"]
    canonical_from_python = translate_with_marker_choice(query, use_last=False)
    rival = translate_with_marker_choice(query, use_last=True)

    lesson = {
        "train": train,
        "test": [{"input": query, "output": test[0]["output"]}],
    }
    (HERE / "lesson.json").write_text(json.dumps(lesson, indent=2) + "\n", encoding="utf-8")
    (HERE / "input.json").write_text(json.dumps(query, indent=2) + "\n", encoding="utf-8")
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n", encoding="utf-8")
    (HERE / "canonical_python.json").write_text(
        json.dumps(canonical_from_python, indent=2) + "\n", encoding="utf-8"
    )

    report = {
        "schema": "arcpuzzles-audit-shortcut-probe-v1",
        "status": "preapply",
        "task_id": episode["task_id"],
        "generator_sha256": episode["provenance"]["generator_sha256"],
        "generator_version": episode["generator_version"],
        "executed_rule_hash": episode["executed_rule_hash"],
        "seed": episode["seed"],
        "sample_indices": episode["sample_indices"],
        "demonstration_sample_indices": episode["sample_indices"][:3],
        "query_sample_index": episode["sample_indices"][3],
        "rival": "Use the last row-major 8 and last row-major 9 to define the translation vector; erase all markers.",
        "demonstrations": demo_checks,
        "rival_fits_all_demonstrations": all(x["last_matches_label"] for x in demo_checks),
        "query_marker_counts": {
            "8": len(marker_positions(query, 8)),
            "9": len(marker_positions(query, 9)),
        },
        "rival_disagrees_with_generated_canonical_label": rival != test[0]["output"],
        "generated_label_matches_first_marker_python": canonical_from_python == test[0]["output"],
        "input_sha256": canonical_json_sha(query),
        "generated_label_sha256": canonical_json_sha(test[0]["output"]),
        "canonical_python_sha256": canonical_json_sha(canonical_from_python),
        "rival_sha256": canonical_json_sha(rival),
        "source_episode": "checks/audit/0b8631a5fc70-witness/episode.jsonl",
    }
    (HERE / "probe-preapply.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["rival_fits_all_demonstrations"]:
        raise AssertionError("last-marker rival does not fit all demonstrations")
    if not report["rival_disagrees_with_generated_canonical_label"]:
        raise AssertionError("last-marker rival does not disagree on query")
    if not report["generated_label_matches_first_marker_python"]:
        raise AssertionError("generated label does not match first-marker Python implementation")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
