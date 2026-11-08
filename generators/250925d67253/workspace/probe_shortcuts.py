#!/usr/bin/env python3
"""Reproduce canonical-fitting centroid shortcuts and an emitted counterexample.

The probe deliberately separates two claims:

* retained canonical labels show which declared shortcut rivals fit every public pair;
* the selected generator's Python mirror finds an exact emitted disagreement.

Use the public ``arcpuzzles apply`` command on the emitted ``input.json`` to bind
that disagreement to the Racket authority.  This script never imports a private
Racket runner or silently substitutes the Python mirror for authority evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "250925d67253"
SELECTED_RIVAL = "bounding_box_center"


def _load_generator():
    """Load the selected generator in a source checkout or copied check runtime."""
    try:
        return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ModuleNotFoundError as exc:
        if not (exc.name or "").startswith("puzzle_generators.per_puzzle"):
            raise
        source = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(f"source_generator_{TASK_ID}", source)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load selected generator from {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def _differences(
    intended: list[list[int]], rival: list[list[int]]
) -> list[dict[str, int]]:
    if len(intended) != len(rival) or any(
        len(left) != len(right) for left, right in zip(intended, rival)
    ):
        raise ValueError("cannot compare outputs with different shapes")
    return [
        {
            "row": row,
            "column": column,
            "intended": intended[row][column],
            "rival": rival[row][column],
        }
        for row in range(len(intended))
        for column in range(len(intended[row]))
        if intended[row][column] != rival[row][column]
    ]


def build_report(
    *,
    seed: int = 0,
    sample_index: int = 0,
    difficulty: str | None = "medium",
    overrides: dict[str, str] | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Return canonical-fit scores and one exact generated rival disagreement."""
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    selected_overrides = dict(overrides or {
        "permutation_kind": "mixed_fixed",
        "marker_density": "dense",
        "palette_band": "low",
    })

    declared = getattr(GEN, "CANONICAL_SHORTCUTS", None)
    if not isinstance(declared, dict) or SELECTED_RIVAL not in declared:
        raise TypeError(
            f"CANONICAL_SHORTCUTS must declare {SELECTED_RIVAL!r}"
        )

    pairs = canonical_pairs(TASK_ID, root=resolved_root)
    canonical_fit: dict[str, dict[str, Any]] = {}
    for name, rival in declared.items():
        records = []
        for pair in pairs:
            prediction = rival(pair["input"])
            records.append({
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _grid_sha256(pair["input"]),
                "expected_output_sha256": _grid_sha256(pair["output"]),
                "prediction_sha256": _grid_sha256(prediction),
                "matches": prediction == pair["output"],
            })
        canonical_fit[name] = {
            "matches": sum(record["matches"] for record in records),
            "total": len(records),
            "records": records,
        }

    grid = GEN.generate(
        seed,
        sample_index,
        difficulty=difficulty,
        **selected_overrides,
    )
    intended = GEN.rule_mirror(grid)
    rival_output = declared[SELECTED_RIVAL](grid)
    differences = _differences(intended, rival_output)
    if not differences:
        raise AssertionError(
            f"generated specimen does not distinguish {SELECTED_RIVAL}"
        )

    generator_source = Path(GEN.__file__).resolve()
    probe_source = Path(__file__).resolve()
    return {
        "schema": "250925d67253-shortcut-probe-v1",
        "task_id": TASK_ID,
        "selected_rival": SELECTED_RIVAL,
        "generator": {
            "version": GEN.VERSION,
            "rule_hash": GEN.RULE_HASH,
            "source_sha256": _sha256_bytes(generator_source.read_bytes()),
        },
        "probe_sha256": _sha256_bytes(probe_source.read_bytes()),
        "canonical_pair_count": len(pairs),
        "canonical_fit": canonical_fit,
        "generated_witness": {
            "generator_call": {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": difficulty,
                "overrides": selected_overrides,
            },
            "input": grid,
            "input_sha256": _grid_sha256(grid),
            "self_check_errors": GEN.self_check(grid),
            "observed_overrides": GEN.observe_overrides(grid),
            "intended_output": intended,
            "intended_output_sha256": _grid_sha256(intended),
            "rival_output": rival_output,
            "rival_output_sha256": _grid_sha256(rival_output),
            "outputs_differ": intended != rival_output,
            "differing_cell_count": len(differences),
            "differing_cells": differences,
        },
        "authority": {
            "executed_by_this_probe": False,
            "label_source": "generator.rule_mirror pending public arcpuzzles apply receipt",
            "recommended_command": [
                "python3",
                "run_with_racket.py",
                "python3",
                "-m",
                "arcpuzzles",
                "apply",
                TASK_ID,
                "--input",
                "../checks/generator-shortcut-final/input.json",
                "--out",
                "../checks/generator-shortcut-final/racket.json",
            ],
        },
        "limits": [
            "Canonical fit is measured only on the eight usable public pairs returned by reviewer_support.canonical_pairs.",
            "The emitted witness refutes declared rivals, not every conceivable program consistent with the demonstrations.",
            "Authoritative Racket agreement must be recorded separately with the public apply command.",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--permutation-kind", choices=("derangement", "mixed_fixed"), default="mixed_fixed")
    parser.add_argument("--marker-density", choices=("sparse", "dense"), default="dense")
    parser.add_argument("--palette-band", choices=("low", "high"), default="low")
    args = parser.parse_args()

    report = build_report(
        seed=args.seed,
        sample_index=args.sample_index,
        difficulty=args.difficulty,
        overrides={
            "permutation_kind": args.permutation_kind,
            "marker_density": args.marker_density,
            "palette_band": args.palette_band,
        },
    )
    out_dir = args.out_dir
    if out_dir.exists():
        parser.error(f"refusing to overwrite existing evidence directory: {out_dir}")
    out_dir.mkdir(parents=True)
    witness = report["generated_witness"]
    _write_json(out_dir / "python_report.json", report)
    _write_json(out_dir / "input.json", witness["input"])
    _write_json(out_dir / "intended_python.json", witness["intended_output"])
    _write_json(out_dir / "rival_bounding_box_center.json", witness["rival_output"])
    print(json.dumps({
        "report": str(out_dir / "python_report.json"),
        "input": str(out_dir / "input.json"),
        "canonical_fit": {
            name: f"{row['matches']}/{row['total']}"
            for name, row in report["canonical_fit"].items()
        },
        "selected_rival": report["selected_rival"],
        "differing_cell_count": witness["differing_cell_count"],
        "first_differing_cell": witness["differing_cells"][0],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
