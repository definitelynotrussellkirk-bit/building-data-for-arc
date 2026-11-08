#!/usr/bin/env python3
"""Bounded authoring audit for the 5419b6df2873 contact-color relay family.

This tool executes the real adjacent sampler and Python reference semantics.  It
checks matched inputs, demonstration-only finite-rival identification, causal
probe inertness before Step A, distinct inputs, count boundaries, and public
one-query serialization.  Protected-Racket qualification remains a separate
native command and is not claimed here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = (_HERE / "prototype.py").resolve()
_MODULE_NAME = "_arc_5419b6df2873_contact_relay_audit_" + hashlib.sha256(
    str(_PROTOTYPE_PATH).encode("utf-8")
).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent contact-relay prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_MODULE_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _probe_side(info: dict[str, Any]) -> str:
    contacts = info["active_probes"]
    if len(contacts) != 1:
        return "invalid"
    contact = contacts[0]
    if contact["left"] == info["selected_color"] and contact["right"] == 0:
        return "left"
    if contact["right"] == info["selected_color"] and contact["left"] == 0:
        return "right"
    return "invalid"


def _inert_before_step_a(grid: list[list[int]]) -> bool:
    for row in grid[1:]:
        for column, value in enumerate(row):
            if value != 9:
                continue
            left = row[column - 1] if column > 0 else 0
            right = row[column + 1] if column + 1 < len(row) else 0
            if left != 0 or right != 0:
                return False
    return prototype.wrong_order_output(grid) == prototype.columns_only_output(grid)


def run_sweep(
    seeds: Iterable[int] = range(64),
    demo_counts: Sequence[int] = (2, 3, 6),
) -> dict[str, Any]:
    """Run a deterministic finite sweep and return a path-independent report."""
    seed_values = list(seeds)
    demo_values = list(demo_counts)
    if not seed_values or any(type(seed) is not int or seed < 0 for seed in seed_values):
        raise ValueError("seeds must be a nonempty iterable of nonnegative integers")
    if not demo_values or any(type(count) is not int or not 2 <= count <= 6 for count in demo_values):
        raise ValueError("demo_counts must contain integers from 2 through 6")

    failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    selected_colors: set[int] = set()
    contact_sides: set[str] = set()
    grid_shapes: set[tuple[int, int]] = set()
    episodes = 0
    labeled_pairs = 0
    boundary_cases = 0

    for seed in seed_values:
        for demos in demo_values:
            episodes_by_mode = {
                mode: prototype.generate_episode(seed, mode, demos=demos, queries=4)
                for mode in prototype.MODES
            }
            canonical_inputs = [
                pair["input"]
                for pair in episodes_by_mode[prototype.MODES[0]]["train"]
                + episodes_by_mode[prototype.MODES[0]]["test"]
            ]
            for mode, episode in episodes_by_mode.items():
                episodes += 1
                all_pairs = episode["train"] + episode["test"]
                labeled_pairs += len(all_pairs)
                inputs = [pair["input"] for pair in all_pairs]
                if inputs != canonical_inputs:
                    failures.append(
                        {"seed": seed, "demos": demos, "mode": mode, "code": "unmatched_inputs"}
                    )
                if len({_grid_key(grid) for grid in inputs}) != len(inputs):
                    failures.append(
                        {"seed": seed, "demos": demos, "mode": mode, "code": "duplicate_input"}
                    )
                audit = prototype.audit_episode(episode, mode)
                if audit["declared_survivors"] != [mode]:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "code": "declared_setting_ambiguity",
                            "survivors": audit["declared_survivors"],
                        }
                    )
                if audit["ambiguous_query_rivals"]:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "code": "finite_rival_ambiguity",
                            "rivals": audit["ambiguous_query_rivals"],
                        }
                    )
                for pair in all_pairs:
                    grid = pair["input"]
                    unique_inputs.add(_grid_key(grid))
                    grid_shapes.add((len(grid), len(grid[0])))
                    info = prototype.dependency_intermediate(grid)
                    selected_colors.add(info["selected_color"])
                    contact_sides.add(_probe_side(info))
                    if not _inert_before_step_a(grid):
                        failures.append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "mode": mode,
                                "code": "pre_step_a_contact",
                                "shape": [len(grid), len(grid[0])],
                            }
                        )
                    if len(grid) == 30 and len(grid[0]) == 30:
                        nonzero = [
                            (row, column)
                            for row, values in enumerate(grid)
                            for column, value in enumerate(values)
                            if value != 0
                        ]
                        if {
                            min(row for row, _ in nonzero),
                            max(row for row, _ in nonzero),
                        } == {0, 29} and {
                            min(column for _, column in nonzero),
                            max(column for _, column in nonzero),
                        } == {0, 29}:
                            boundary_cases += 1
                        else:
                            failures.append(
                                {
                                    "seed": seed,
                                    "demos": demos,
                                    "mode": mode,
                                    "code": "weak_30x30_boundary_case",
                                }
                            )

    source_names = (
        "audit.py",
        "prototype.py",
        "adapter.py",
        "canonical.rkt",
        "contact_color_rows.rkt",
        "wrong_order.rkt",
        "promotion.json",
    )
    return {
        "schema": "arcpuzzles-contact-relay-audit-v1",
        "status": "failed" if failures else "passed",
        "task_id": prototype.TASK_ID,
        "settings": list(prototype.MODES),
        "seeds": seed_values,
        "demo_counts": demo_values,
        "queries": 4,
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "distinct_inputs": len(unique_inputs),
        "tested_rivals": len(prototype.RIVALS),
        "coverage": {
            "selected_colors": sorted(selected_colors),
            "contact_sides": sorted(contact_sides),
            "grid_shapes": [list(shape) for shape in sorted(grid_shapes)],
            "boundary_30x30_pair_observations": boundary_cases,
        },
        "source_sha256": {name: _sha256(_HERE / name) for name in source_names},
        "failures": failures,
        "limits": (
            "Finite Python-reference sweep over the listed seeds, counts, settings and rivals. "
            "Native qualification separately re-executes labels with protected Racket."
        ),
    }


def write_public_samples(directory: Path, *, seed: int = 0, demos: int = 3) -> list[dict[str, Any]]:
    """Write eight hash-named, one-query public challenges for both settings."""
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"public sample directory is not empty: {directory}")
    directory.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for mode in prototype.MODES:
        episode = prototype.generate_episode(seed, mode, demos=demos, queries=4)
        for row in prototype.write_public_turns(episode, directory):
            rows.append(
                {
                    "mode_for_authoring_only": mode,
                    "query_index": row["query_index"],
                    "path": Path(row["path"]).name,
                    "sha256": row["sha256"],
                    "bytes": row["bytes"],
                }
            )
    return rows


def _positive(value: str) -> int:
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("use a positive integer")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-count", type=_positive, default=64)
    parser.add_argument("--demos", type=int, action="append", dest="demo_counts")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path)
    parser.add_argument("--public-seed", type=int, default=0)
    options = parser.parse_args(argv)
    demo_counts = tuple(options.demo_counts or (2, 3, 6))
    report = run_sweep(range(options.seed_count), demo_counts)
    if options.public_dir is not None:
        report["public_samples"] = write_public_samples(
            options.public_dir, seed=options.public_seed, demos=3
        )
    options.out.parent.mkdir(parents=True, exist_ok=True)
    options.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "episodes", "labeled_pairs", "distinct_inputs")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
