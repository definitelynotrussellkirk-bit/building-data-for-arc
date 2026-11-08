#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "df74e338b4f5": "374fbf52b1f9c4606bffd2541c27a15c3c703285c23b8b77919261c705853d00",
    "204213f10aff": "9a459ef53fba3bfde7f64d0adcd117203965346408cd612193048126c21b52b2",
}


def read(path: Path):
    return json.loads(path.read_text())


def write(path: Path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boundary_distance_rival(grid):
    """Wrong rival: infer depth from distance to the canvas edge; never detect frames."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 9):
                distance = min(r, c, h - 1 - r, w - 1 - c)
                out[r][c] = (distance + 1) // 2
    return out


def components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (1 <= nx < h and 0 <= ny < w and
                            grid[nx][ny] == color and (nx, ny) not in seen):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            result.append(cells)
    return result


def crop_component(grid, cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [[grid[r][c] for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]


def pack(parts):
    if not parts:
        return []
    h = max(len(part) for part in parts)
    w = sum(len(part[0]) for part in parts) + len(parts) - 1
    out = [[0 for _ in range(w)] for _ in range(h)]
    left = 0
    for part in parts:
        for r, row in enumerate(part):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(part[0]) + 1
    return out


def contiguous_prefix_legend_rival(grid):
    """Wrong rival: legend is only the nonzero prefix starting at column zero."""
    legend = []
    for value in grid[0]:
        if value == 0:
            break
        legend.append(value)
    parts = []
    for color in legend:
        found = components(grid, color)
        if found:
            parts.append(crop_component(grid, found[0]))
    return pack(parts)


def evaluate(task_id, rival, description, custom_validation):
    target = ROOT / "checks" / "audit" / task_id
    source = ROOT / "repo" / "generators" / task_id / "generator.py"
    generator_sha = sha(source)
    assert generator_sha == EXPECTED[task_id]

    custom = read(target / "racket.json")
    assert custom["generator_sha256"] == generator_sha
    assert len(custom["results"]) == 1
    custom_row = custom["results"][0]
    rival_custom = rival(custom_row["input"])
    assert rival_custom != custom_row["output"]

    generated = read(target / "generated-racket.json")
    assert generated["generator_sha256"] == generator_sha
    comparisons = []
    for row in generated["results"]:
        comparisons.append({
            "index": row["index"],
            "input_sha256": row["input_sha256"],
            "output_sha256": row["output_sha256"],
            "rival_matches": rival(row["input"]) == row["output"],
        })
    matched = sum(row["rival_matches"] for row in comparisons)
    assert matched == len(comparisons) == 64

    build_manifest = read(ROOT / "checks" / "audit" / "input-build-manifest.json")
    sample = build_manifest["targets"][task_id]["generated_sample"]
    counterexample = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "executed_rule_hash": custom["executed_rule_hash"],
        "rule_text_sha256": custom["rule_text_sha256"],
        "reference": custom["reference"],
        "seed": None,
        "sample_index": None,
        "overrides": None,
        "construction": "hand-constructed from the task's documented invariant domain",
        "input": custom_row["input"],
        "actual_racket_output": custom_row["output"],
        "actual_output_sha256": custom_row["output_sha256"],
        "actual_valid_output": custom_row["valid_output"],
        "rival_name": description,
        "rival_output": rival_custom,
        "rival_disagrees": True,
        "target_validator": custom_validation,
        "apply_command": custom["command"],
        "apply_reported_cwd": custom["cwd"],
        "wrapper_command": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
            task_id, "--input", f"../checks/audit/{task_id}/input.json",
            "--out", f"../checks/audit/{task_id}/racket.json",
        ],
        "wrapper_cwd": "packet_root",
    }
    write(target / "counterexample.json", counterexample)

    report = {
        "schema": "arcpuzzles-audit-rival-probe-v1",
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "executed_rule_hash": generated["executed_rule_hash"],
        "rule_text_sha256": generated["rule_text_sha256"],
        "rival_name": description,
        "sample": sample,
        "denominator": len(comparisons),
        "rival_matches": matched,
        "rival_disagreements": len(comparisons) - matched,
        "all_generated_outputs_valid": all(row["valid_output"] for row in generated["results"]),
        "generated_inputs_sha256": sha(target / "generated-inputs.json"),
        "racket_evidence_sha256": sha(target / "generated-racket.json"),
        "comparisons": comparisons,
        "apply_command": generated["command"],
        "apply_reported_cwd": generated["cwd"],
        "wrapper_command": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
            task_id, "--input", f"../checks/audit/{task_id}/generated-inputs.json",
            "--out", f"../checks/audit/{task_id}/generated-racket.json",
        ],
        "wrapper_cwd": "packet_root",
    }
    write(target / "rival-probe.json", report)
    return {
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "rule_hash": generated["executed_rule_hash"],
        "matched": matched,
        "denominator": len(comparisons),
        "counterexample_input_sha256": custom_row["input_sha256"],
        "counterexample_actual_output_sha256": custom_row["output_sha256"],
    }


def main():
    summaries = []
    summaries.append(evaluate(
        "df74e338b4f5",
        boundary_distance_rival,
        "canvas_edge_distance_depth",
        {
            "self_check_present": False,
            "passes_target_validator": None,
            "reason": "the target defines no self_check (also reproduced by lint)",
            "documented_domain": True,
            "domain_reason": (
                "three concentric rectangular color-9 frames, one blank-cell ring apart; "
                "the marker occupies a non-frame 0-cell and is inside all three frames"
            ),
        },
    ))
    summaries.append(evaluate(
        "204213f10aff",
        contiguous_prefix_legend_rival,
        "contiguous_left_prefix_legend",
        {
            "self_check_present": True,
            "passes_target_validator": True,
            "self_check_errors": [],
            "documented_domain": True,
            "domain_reason": (
                "row 0 lists colors 2 then 4 with a zero gap; each color has one separated "
                "connected body component below row 0"
            ),
        },
    ))
    write(ROOT / "checks" / "audit" / "rival-probe-summary.json", {
        "schema": "arcpuzzles-audit-rival-probe-summary-v1",
        "results": summaries,
    })


if __name__ == "__main__":
    main()
