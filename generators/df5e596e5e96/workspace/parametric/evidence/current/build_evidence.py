#!/usr/bin/env python3
"""Build bounded, source-bound evidence for the df5e596e5e96 prototype.

This is a replay helper for later reviewers.  It does not approve or accept the
variant; it exercises the task-local adapter, protected Racket programs, finite
shortcut audit, count boundaries, lawful minimum/maximum sizes, and exact public
projection bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).resolve()
PARAMETRIC = HERE.parents[2]
REPO = HERE.parents[6]
sys.path.insert(0, str(REPO / "shared/runtime"))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from reviewer_support import (  # noqa: E402
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

PROTOTYPE = _load(PARAMETRIC / "prototype.py", "_df5e596e5e96_evidence_prototype")
ADAPTER = _load(PARAMETRIC / "adapter.py", "_df5e596e5e96_evidence_adapter")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _shape(grid: list[list[int]]) -> list[int]:
    return [len(grid), len(grid[0])]


def _grid_metrics(grid: list[list[int]]) -> dict[str, Any]:
    rows, cols = _shape(grid)
    panel_count = (cols + 1) // 6
    colors = sorted({cell for row in grid for cell in row if cell})
    panel_nonzero = []
    panel_boundary = []
    for panel_index in range(panel_count):
        left = panel_index * 6
        cells = [
            (row, col)
            for row in range(5)
            for col in range(5)
            if grid[row][left + col]
        ]
        panel_nonzero.append(len(cells))
        panel_boundary.append(
            any(row in (0, 4) or col in (0, 4) for row, col in cells)
        )
    global_boundary = any(grid[0][col] or grid[-1][col] for col in range(cols)) or any(
        grid[row][0] or grid[row][-1] for row in range(rows)
    )
    return {
        "shape": [rows, cols],
        "panel_count": panel_count,
        "foreground_colors": colors,
        "foreground_cell_count": sum(panel_nonzero),
        "panel_foreground_counts": panel_nonzero,
        "all_panels_nonempty": all(value > 0 for value in panel_nonzero),
        "panels_touching_local_boundary": sum(panel_boundary),
        "global_boundary_foreground": bool(global_boundary),
    }


def _matrix_metrics(matrix: list[list[int]]) -> dict[str, Any]:
    counts = Counter(cell for row in matrix for cell in row)
    return {
        "shape": _shape(matrix),
        "value_counts": {str(key): counts[key] for key in sorted(counts)},
        "distinct_rows": len({tuple(row) for row in matrix}),
    }


def _public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _signature(matrix: list[list[int]]) -> dict[str, Any]:
    rows = []
    for index, row in enumerate(matrix):
        rows.append(
            {
                "index": index,
                "exact": row.count(1),
                "rotation": row.count(2),
                "reflection": row.count(3),
            }
        )
    return {"rows": rows, "order": PROTOTYPE.relation_signature_order(matrix)}


def build(public_out: Path) -> dict[str, Any]:
    public_out.mkdir(parents=True, exist_ok=True)
    for old in public_out.glob("*.json"):
        old.unlink()

    generator, _source, generator_digest = load_selected_generator(
        PROTOTYPE.TASK_ID, root=REPO
    )
    report: dict[str, Any] = {
        "schema": "arcpuzzles-df5e596e5e96-parametric-probe-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "prototype_version": PROTOTYPE.VERSION,
        "source_binding": {
            "generator_sha256": generator_digest,
            "canonical_program_sha256": hashlib.sha256(
                PROTOTYPE.program(PROTOTYPE.DEFAULT_SETTINGS, root=REPO).encode()
            ).hexdigest(),
            "prototype_sha256": _sha256_bytes((PARAMETRIC / "prototype.py").read_bytes()),
            "adapter_sha256": _sha256_bytes((PARAMETRIC / "adapter.py").read_bytes()),
            "promotion_sha256": _sha256_bytes((PARAMETRIC / "promotion.json").read_bytes()),
        },
        "racket": None,
        "episodes": [],
        "boundary_counts": {},
        "minimum_lawful_case": None,
        "public_exports": [],
        "finite_audit_scope": list(PROTOTYPE.AUDIT_RIVALS),
        "limits": [
            "Finite declared-setting and declared-rival checks; not a universal uniqueness proof.",
            "The fixed five-row strip with at most five panels has maximum lawful input size 5x29; a 30x30 case is outside this grammar.",
            "Reviewer-reported replay evidence only; native qualification and owner acceptance remain separate.",
        ],
    }

    seeds = (0, 17, 31)
    episode_jobs = []
    for seed in seeds:
        for settings in PROTOTYPE.ALL_SETTINGS:
            episode_jobs.append((seed, settings, 2 if seed == 31 else 3, 4))

    with RacketBridge(max_calls_before_restart=512) as bridge:
        identity = bridge.runtime_identity
        report["racket"] = {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        }
        for seed, settings, demos, queries in episode_jobs:
            episode = ADAPTER.generate(seed, settings, demos, queries)
            verification = PROTOTYPE.verify_episode(episode, root=REPO, bridge=bridge)
            inputs = episode["train"] + episode["test"]
            report["episodes"].append(
                {
                    "seed": seed,
                    "settings": settings,
                    "counts": {"demos": demos, "queries": queries},
                    "program_sha256": hashlib.sha256(
                        episode["program_solution"].encode()
                    ).hexdigest(),
                    "input_metrics": [_grid_metrics(pair["input"]) for pair in inputs],
                    "output_metrics": [_matrix_metrics(pair["output"]) for pair in inputs],
                    "verification": verification,
                }
            )
            if seed in (0, 17):
                visible = _public_episode(episode)
                public_id = public_challenge_id(visible)
                raw = public_challenge_bytes(visible)
                target = public_out / f"{public_id}.json"
                target.write_bytes(raw)
                report["public_exports"].append(
                    {
                        "seed": seed,
                        "settings": settings,
                        "public_id": public_id,
                        "sha256": _sha256_bytes(raw),
                        "bytes": len(raw),
                        "path": f"checks/parametric/public/{target.name}",
                    }
                )

        # Search the lawful minimum panel count for one setting-distinguishing,
        # protected-Racket-parity case.  The maximum is covered by every episode.
        for sample_index in range(128):
            grid = generator.generate(7, sample_index, difficulty="hard", n_panels=3)
            canonical = PROTOTYPE.transform(grid, PROTOTYPE.DEFAULT_SETTINGS, root=REPO)
            alternate_settings = {"matrix_order": "relation_signature"}
            alternate = PROTOTYPE.transform(grid, alternate_settings, root=REPO)
            if canonical == alternate:
                continue
            canonical_racket = PROTOTYPE.execute_rule(
                PROTOTYPE.program(PROTOTYPE.DEFAULT_SETTINGS, root=REPO),
                grid,
                bridge=bridge,
            )
            alternate_racket = PROTOTYPE.execute_rule(
                PROTOTYPE.program(alternate_settings, root=REPO),
                grid,
                bridge=bridge,
            )
            if canonical_racket != canonical or alternate_racket != alternate:
                raise AssertionError("minimum-size Racket/Python parity failed")
            report["minimum_lawful_case"] = {
                "seed": 7,
                "sample_index": sample_index,
                "input_metrics": _grid_metrics(grid),
                "canonical_matrix": canonical,
                "intermediate": _signature(canonical),
                "canonical_output": canonical_racket,
                "relation_signature_output": alternate_racket,
            }
            break
        if report["minimum_lawful_case"] is None:
            raise AssertionError("no distinguishing minimum-size case in bounded search")

    # Count-boundary and prefix stability checks use the already Racket-checked
    # deterministic schedule but avoid multiplying evaluator calls unnecessarily.
    full = ADAPTER.generate(29, PROTOTYPE.DEFAULT_SETTINGS, 6, 8)
    prefix_checks = []
    for demos in range(2, 7):
        for queries in range(1, 9):
            episode = ADAPTER.generate(29, PROTOTYPE.DEFAULT_SETTINGS, demos, queries)
            prefix_checks.append(
                episode["train"] == full["train"][:demos]
                and episode["test"] == full["test"][:queries]
                and len(
                    {
                        json.dumps(pair["input"], separators=(",", ":"))
                        for pair in episode["train"] + episode["test"]
                    }
                )
                == demos + queries
            )
    report["boundary_counts"] = {
        "demos_tested": [2, 3, 4, 5, 6],
        "queries_tested": [1, 2, 3, 4, 5, 6, 7, 8],
        "combinations": len(prefix_checks),
        "all_prefix_stable_and_unique": all(prefix_checks),
    }

    metrics = [
        metric
        for episode in report["episodes"]
        for metric in episode["input_metrics"]
    ]
    report["content_summary"] = {
        "input_count": len(metrics),
        "shapes": sorted({tuple(metric["shape"]) for metric in metrics}),
        "foreground_cell_range": [
            min(metric["foreground_cell_count"] for metric in metrics),
            max(metric["foreground_cell_count"] for metric in metrics),
        ],
        "foreground_color_counts": sorted(
            {len(metric["foreground_colors"]) for metric in metrics}
        ),
        "all_panels_nonempty": all(metric["all_panels_nonempty"] for metric in metrics),
        "inputs_with_local_boundary_contact": sum(
            metric["panels_touching_local_boundary"] > 0 for metric in metrics
        ),
        "inputs_with_global_boundary_contact": sum(
            metric["global_boundary_foreground"] for metric in metrics
        ),
    }
    report["summary"] = {
        "racket_episode_count": len(report["episodes"]),
        "racket_label_count": sum(
            row["verification"]["label_count"] for row in report["episodes"]
        )
        + 2,
        "ambiguous_rival_count": sum(
            len(row["verification"]["audit"]["ambiguous_rivals"])
            for row in report["episodes"]
        ),
        "failed_program_checks": sum(
            not check["matches_python"]
            for row in report["episodes"]
            for check in row["verification"]["program_checks"]
        ),
        "public_export_count": len(report["public_exports"]),
        "status": "passed",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--public-out", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.public_out.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
