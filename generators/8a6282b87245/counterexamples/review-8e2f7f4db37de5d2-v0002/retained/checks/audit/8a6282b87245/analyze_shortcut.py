from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
GENERATOR_PATH = REPO / "generators" / "8a6282b87245" / "generator.py"


def load_json(name: str) -> Any:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def dump_json(name: str, value: Any) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            rim = {
                (rr, cc)
                for rr in range(r0, r1 + 1)
                for cc in range(c0, c1 + 1)
                if rr in (r0, r1) or cc in (c0, c1)
            }
            out.append(
                {
                    "color": color,
                    "cells": sorted(cells),
                    "top": r0,
                    "bottom": r1,
                    "left": c0,
                    "right": c1,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "is_exact_frame": set(cells) == rim and r1 > r0 and c1 > c0,
                }
            )
    return sorted(out, key=lambda o: (o["top"], o["left"], o["color"]))


def column_overlap_count(objs: list[dict[str, Any]]) -> int:
    return sum(
        1
        for i, a in enumerate(objs)
        for b in objs[i + 1 :]
        if max(a["left"], b["left"]) <= min(a["right"], b["right"])
    )


def independent_edge_rival(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: no collision search; snap each object independently to one edge."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for obj in components(grid):
        target_top = 0 if obj["is_exact_frame"] else h - obj["height"]
        dr = target_top - obj["top"]
        for r, c in obj["cells"]:
            # Painting order resolves collisions; generated data never reaches this branch.
            out[r + dr][c] = obj["color"]
    return out


def differing_cells(a: list[list[int]], b: list[list[int]]) -> list[dict[str, int]]:
    return [
        {"row": r, "col": c, "selected": a[r][c], "rival": b[r][c]}
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_target_8a6282b87245", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    generated_inputs = load_json("generated_inputs.json")
    generated_receipt = load_json("generated_racket.json")
    generated_outputs = [x["output"] for x in generated_receipt["results"]]
    assert len(generated_inputs) == len(generated_outputs) == 60

    per_sample: list[dict[str, Any]] = []
    rival_matches = 0
    overlap_samples = 0
    object_counts: list[int] = []
    frame_counts: list[int] = []
    nonframe_counts: list[int] = []
    for index, (grid, expected) in enumerate(zip(generated_inputs, generated_outputs)):
        objs = components(grid)
        overlap_pairs = column_overlap_count(objs)
        rival = independent_edge_rival(grid)
        matches = rival == expected
        rival_matches += int(matches)
        overlap_samples += int(overlap_pairs > 0)
        object_counts.append(len(objs))
        frame_counts.append(sum(o["is_exact_frame"] for o in objs))
        nonframe_counts.append(sum(not o["is_exact_frame"] for o in objs))
        per_sample.append(
            {
                "index": index,
                "object_count": len(objs),
                "frame_count": frame_counts[-1],
                "nonframe_count": nonframe_counts[-1],
                "overlapping_column_pairs": overlap_pairs,
                "rival_matches_selected_rule": matches,
            }
        )

    manual_input = load_json("input.json")
    manual_selected = load_json("racket.json")["results"][0]["output"]
    manual_rival = independent_edge_rival(manual_input)
    dump_json("rival.json", manual_rival)

    generator = load_generator()
    self_check_errors = generator.self_check(manual_input, difficulty="hard", meta=None)
    manual_objects = components(manual_input)
    manual_overlap_pairs = column_overlap_count(manual_objects)
    differences = differing_cells(manual_selected, manual_rival)

    generator_sha = sha256_file(GENERATOR_PATH)
    assert generator_sha == generated_receipt["generator_sha256"]
    assert generated_receipt["executed_rule_hash"] == "af694b46412a"
    assert overlap_samples == 0
    assert rival_matches == 60
    assert self_check_errors == []
    assert manual_overlap_pairs > 0
    assert differences

    reproduction = {
        "schema": "arcpuzzles-audit-reproduction-v1",
        "task_id": "8a6282b87245",
        "finding": "collision-aware packing is absent from generated support",
        "status": "reproduced",
        "generator_path": "generators/8a6282b87245/generator.py",
        "generator_sha256": generator_sha,
        "executed_rule_hash": generated_receipt["executed_rule_hash"],
        "selected_rule_reference": generated_receipt["reference"],
        "rival": {
            "name": "independent_edge_snap",
            "description": (
                "Classify each connected object as exact rectangular frame or non-frame; "
                "snap frames independently to row 0 and non-frames independently to the "
                "bottom edge, with no collision search or dense packing."
            ),
        },
        "generated_probe": {
            "sample_count": len(generated_inputs),
            "samples_per_band": 20,
            "overlapping_column_samples": overlap_samples,
            "rival_matches_selected_rule": rival_matches,
            "object_count_range": [min(object_counts), max(object_counts)],
            "frame_count_range": [min(frame_counts), max(frame_counts)],
            "nonframe_count_range": [min(nonframe_counts), max(nonframe_counts)],
            "all_object_column_extents_pairwise_disjoint": overlap_samples == 0,
            "all_rival_outputs_match": rival_matches == len(generated_inputs),
            "per_sample": per_sample,
        },
        "counterexample": {
            "input_file": "checks/audit/8a6282b87245/input.json",
            "selected_output_file": "checks/audit/8a6282b87245/racket.json",
            "rival_output_file": "checks/audit/8a6282b87245/rival.json",
            "self_check_errors": self_check_errors,
            "object_count": len(manual_objects),
            "overlapping_column_pairs": manual_overlap_pairs,
            "selected_and_rival_differ": manual_selected != manual_rival,
            "differing_cell_count": len(differences),
            "differing_cells": differences,
            "input": manual_input,
            "selected_output": manual_selected,
            "rival_output": manual_rival,
        },
        "commands": [
            "python3 review.py run python3 -m arcpuzzles apply 8a6282b87245 --input ../checks/audit/8a6282b87245/generated_inputs.json --out ../checks/audit/8a6282b87245/generated_racket.json",
            "python3 review.py run python3 -m arcpuzzles apply 8a6282b87245 --input ../checks/audit/8a6282b87245/input.json --out ../checks/audit/8a6282b87245/racket.json",
            "python3 review.py run python3 ../checks/audit/8a6282b87245/analyze_shortcut.py",
        ],
    }
    dump_json("reproduction.json", reproduction)
    print(json.dumps({
        "generated_samples": len(generated_inputs),
        "overlap_samples": overlap_samples,
        "rival_matches": rival_matches,
        "manual_self_check_errors": self_check_errors,
        "manual_overlap_pairs": manual_overlap_pairs,
        "manual_differing_cells": len(differences),
        "generator_sha256": generator_sha,
        "rule_hash": generated_receipt["executed_rule_hash"],
    }, indent=2))


if __name__ == "__main__":
    main()
