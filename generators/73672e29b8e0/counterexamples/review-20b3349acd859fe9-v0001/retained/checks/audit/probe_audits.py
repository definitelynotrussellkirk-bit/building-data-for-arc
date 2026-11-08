#!/usr/bin/env python3
"""Reproduce the two audit findings from current source bytes.

Run from packet root with:
  PYTHONPATH=repo/shared/runtime:repo/src python3 checks/audit/probe_audits.py
The 6d678... Racket output must already have been produced by the supported
`arcpuzzles apply` command recorded in its evidence directory.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

SCRIPT = Path(__file__).resolve()

def locate_repo() -> Path:
    for ancestor in (SCRIPT.parent, *SCRIPT.parents):
        candidate = ancestor / "repo"
        if (candidate / "shared" / "runtime" / "reviewer_support.py").is_file():
            return find_root(candidate / "README.md")
    raise FileNotFoundError(f"cannot locate packet repo above {SCRIPT}")

REPO = locate_repo()
PACKET = REPO.parent
OUTROOT = PACKET / "checks" / "audit"


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_digest(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def grid_stats(grid) -> dict[str, int]:
    nonzero = [value for row in grid for value in row if value]
    return {
        "h": len(grid),
        "w": len(grid[0]) if grid else 0,
        "nonzero_cells": len(nonzero),
        "nonzero_colors": len(set(nonzero)),
    }


def connected_components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def component_bbox_rival(grid):
    output = [row[:] for row in grid]
    for color, cells in connected_components(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        if (
            len(cells) == 3
            and max(rows) - min(rows) == 1
            and max(cols) - min(cols) == 1
        ):
            for row in range(min(rows), max(rows) + 1):
                for col in range(min(cols), max(cols) + 1):
                    if output[row][col] == 0:
                        output[row][col] = color
    return output


def partial_window_mirror(grid):
    output = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height - 1):
        for col in range(width - 1):
            values = [
                grid[row][col],
                grid[row + 1][col],
                grid[row][col + 1],
                grid[row + 1][col + 1],
            ]
            nonzero = [value for value in values if value]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                color = nonzero[0]
                for dr in (0, 1):
                    for dc in (0, 1):
                        if grid[row + dr][col + dc] == 0:
                            output[row + dr][col + dc] = color
    return output


def audit_73672e29b8e0() -> dict:
    task_id = "73672e29b8e0"
    module, source = load_generator(task_id)
    canonical = canonical_pairs(task_id, root=REPO, labeled_only=True)
    canonical_stats = [grid_stats(pair["input"]) for pair in canonical]

    samples = []
    errors = []
    seed_base = 73672000
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(100):
            try:
                grid = module.generate(
                    seed_base + sample_index,
                    sample_index,
                    difficulty=difficulty,
                )
                samples.append(
                    {
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "stats": grid_stats(grid),
                        "input_sha256": grid_digest(grid),
                    }
                )
            except Exception as exc:  # evidence should retain generator failures
                errors.append(
                    {
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "error": repr(exc),
                    }
                )

    false_grid = module.generate(
        73672999, 17, difficulty="medium", anchor_corner=False
    )
    true_grid = module.generate(
        73672999, 17, difficulty="medium", anchor_corner=True
    )
    outdir = OUTROOT / task_id
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "input.json").write_text(
        json.dumps([false_grid, true_grid], indent=2) + "\n",
        encoding="utf-8",
    )

    shape_counts = Counter(
        (sample["stats"]["h"], sample["stats"]["w"]) for sample in samples
    )
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": task_id,
        "finding_type": "reproduced_distribution_and_dead_axis",
        "generator_sha256": sha256(source),
        "sample_seed_base": seed_base,
        "samples_per_band": 100,
        "sample_count": len(samples),
        "unique_input_count": len({sample["input_sha256"] for sample in samples}),
        "generation_errors": errors,
        "canonical_stats": canonical_stats,
        "generated_summary": {
            "exact_10x10": sum(
                sample["stats"]["h"] == 10 and sample["stats"]["w"] == 10
                for sample in samples
            ),
            "nonzero_cells_min": min(
                sample["stats"]["nonzero_cells"] for sample in samples
            ),
            "nonzero_cells_max": max(
                sample["stats"]["nonzero_cells"] for sample in samples
            ),
            "nonzero_colors_min": min(
                sample["stats"]["nonzero_colors"] for sample in samples
            ),
            "nonzero_colors_max": max(
                sample["stats"]["nonzero_colors"] for sample in samples
            ),
            "shape_counts": {
                f"{height}x{width}": count
                for (height, width), count in sorted(shape_counts.items())
            },
        },
        "anchor_corner_witness": {
            "seed": 73672999,
            "sample_index": 17,
            "difficulty": "medium",
            "overrides_a": {"anchor_corner": False},
            "overrides_b": {"anchor_corner": True},
            "inputs_identical": false_grid == true_grid,
            "input_a": false_grid,
            "input_b": true_grid,
            "self_check_a": module.self_check(false_grid, difficulty="medium"),
            "self_check_b": module.self_check(true_grid, difficulty="medium"),
        },
        "commands": [
            {
                "cwd": "packet_root",
                "argv": [
                    "env",
                    "PYTHONPATH=repo/shared/runtime:repo/src",
                    "python3",
                    "checks/audit/probe_audits.py",
                ],
            },
            {
                "cwd": "packet_root",
                "argv": [
                    "python3",
                    "run_with_racket.py",
                    "python3",
                    "-m",
                    "arcpuzzles",
                    "apply",
                    task_id,
                    "--input",
                    f"../checks/audit/{task_id}/input.json",
                    "--out",
                    f"../checks/audit/{task_id}/racket.json",
                ],
            },
        ],
    }
    racket_path = outdir / "racket.json"
    if racket_path.is_file():
        racket = json.loads(racket_path.read_text(encoding="utf-8"))
        report["executed_rule_hash"] = racket["executed_rule_hash"]
        witness = report["anchor_corner_witness"]
        witness["actual_racket_outputs"] = [
            result["output"] for result in racket["results"]
        ]
        witness["racket_outputs_identical"] = (
            len(racket["results"]) == 2
            and racket["results"][0]["output"] == racket["results"][1]["output"]
        )
        witness["input_sha256"] = [
            result["input_sha256"] for result in racket["results"]
        ]
        witness["output_sha256"] = [
            result["output_sha256"] for result in racket["results"]
        ]

    (outdir / "probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def audit_6d678fbbe87e() -> dict:
    task_id = "6d678fbbe87e"
    module, source = load_generator(task_id)
    canonical = canonical_pairs(task_id, root=REPO, labeled_only=True)
    canonical_fit = [
        {
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "rival_matches": component_bbox_rival(pair["input"])
            == pair["output"],
        }
        for pair in canonical
    ]

    outdir = OUTROOT / task_id
    witness = json.loads((outdir / "input.json").read_text(encoding="utf-8"))
    rival_output = component_bbox_rival(witness)
    (outdir / "rival.json").write_text(
        json.dumps(rival_output, indent=2) + "\n", encoding="utf-8"
    )

    samples = []
    errors = []
    seed_base = 66780000
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(100):
            try:
                grid = module.generate(
                    seed_base + sample_index,
                    sample_index,
                    difficulty=difficulty,
                )
                components = connected_components(grid)
                structural = all(
                    len(cells) == 3
                    and max(row for row, _ in cells)
                    - min(row for row, _ in cells)
                    == 1
                    and max(col for _, col in cells)
                    - min(col for _, col in cells)
                    == 1
                    for _, cells in components
                )
                samples.append(
                    {
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "self_check": module.self_check(
                            grid, difficulty=difficulty
                        ),
                        "structural_rival_domain": structural,
                        "rival_matches_python_rule_mirror": (
                            component_bbox_rival(grid)
                            == partial_window_mirror(grid)
                        ),
                        "input_sha256": grid_digest(grid),
                    }
                )
            except Exception as exc:
                errors.append(
                    {
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "error": repr(exc),
                    }
                )

    racket = json.loads((outdir / "racket.json").read_text(encoding="utf-8"))
    actual_output = racket["results"][0]["output"]
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "finding_type": "plausible_component_bbox_shortcut",
        "generator_sha256": sha256(source),
        "executed_rule_hash": racket["executed_rule_hash"],
        "shortcut": (
            "For each 4-connected monochrome component that has exactly "
            "three cells and a 2x2 bounding box, fill the missing "
            "bounding-box corner."
        ),
        "canonical_fit": canonical_fit,
        "canonical_fit_all": all(item["rival_matches"] for item in canonical_fit),
        "default_sample_probe": {
            "seed_base": seed_base,
            "samples_per_band": 100,
            "sample_count": len(samples),
            "generation_errors": errors,
            "self_check_pass_count": sum(not item["self_check"] for item in samples),
            "structural_rival_domain_count": sum(
                item["structural_rival_domain"] for item in samples
            ),
            "rival_matches_python_rule_mirror_count": sum(
                item["rival_matches_python_rule_mirror"] for item in samples
            ),
            "unique_input_count": len(
                {item["input_sha256"] for item in samples}
            ),
        },
        "counterexample": {
            "input": witness,
            "validator_errors": module.self_check(witness, difficulty="medium"),
            "documented_default_domain": False,
            "actual_racket_output": actual_output,
            "rival_output": rival_output,
            "outputs_disagree": actual_output != rival_output,
            "input_sha256": racket["results"][0]["input_sha256"],
            "actual_output_sha256": racket["results"][0]["output_sha256"],
            "rival_output_sha256": grid_digest(rival_output),
        },
        "commands": [
            {
                "cwd": "packet_root",
                "argv": [
                    "python3",
                    "run_with_racket.py",
                    "python3",
                    "-m",
                    "arcpuzzles",
                    "apply",
                    task_id,
                    "--input",
                    f"../checks/audit/{task_id}/input.json",
                    "--out",
                    f"../checks/audit/{task_id}/racket.json",
                ],
            },
            {
                "cwd": "packet_root",
                "argv": [
                    "env",
                    "PYTHONPATH=repo/shared/runtime:repo/src",
                    "python3",
                    "checks/audit/probe_audits.py",
                ],
            },
        ],
    }
    (outdir / "counterexample.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    first = audit_73672e29b8e0()
    second = audit_6d678fbbe87e()
    print(
        json.dumps(
            {
                "73672e29b8e0": {
                    "generator_sha256": first["generator_sha256"],
                    "canonical_stats": first["canonical_stats"],
                    "generated_summary": first["generated_summary"],
                    "anchor_corner_inputs_identical": first[
                        "anchor_corner_witness"
                    ]["inputs_identical"],
                },
                "6d678fbbe87e": {
                    "generator_sha256": second["generator_sha256"],
                    "executed_rule_hash": second["executed_rule_hash"],
                    "canonical_fit_all": second["canonical_fit_all"],
                    "default_sample_probe": second["default_sample_probe"],
                    "counterexample_outputs_disagree": second[
                        "counterexample"
                    ]["outputs_disagree"],
                    "counterexample_validator_errors": second[
                        "counterexample"
                    ]["validator_errors"],
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
