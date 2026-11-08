#!/usr/bin/env python3
"""Source-bound distribution, shortcut, and cyclic-rotation probe.

This is intentionally task-local.  It consumes the generator's declared
profiles/rivals instead of copying their names, so future schedule edits can be
rechecked with the same command.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d476983a3d6c"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
GENERATOR_PATH = HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"profile_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def build_report(*, per_band: int = 100, window_starts: int = 16) -> dict[str, Any]:
    if per_band <= 0 or window_starts <= 0:
        raise ValueError("per_band and window_starts must be positive")
    gen = _load_generator()
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    per_band_report: dict[str, Any] = {}

    for band_index, band in enumerate(("easy", "medium", "hard")):
        profiles: Counter = Counter()
        grids: Counter = Counter()
        commands: Counter = Counter()
        aligned = singleton = overlap = 0
        distinct_inputs: set[str] = set()
        for index in range(per_band):
            seed = 480_000 + band_index * 100_000 + index
            try:
                grid = gen.generate(seed, index, difficulty=band)
                analysis = gen._analyze(grid)
                if analysis["errors"]:
                    errors.append(
                        f"{band}[{index}] generated invalid grid: "
                        + "; ".join(analysis["errors"])
                    )
                    continue
                facts = analysis["facts"]
                observed = gen.observe_overrides(grid)
                truth = gen._rule_mirror(grid)
                row = {
                    "band": band,
                    "seed": seed,
                    "sample_index": index,
                    "input": grid,
                    "output": truth,
                    "observed": observed,
                }
                rows.append(row)
                profiles[observed["scene_profile"]] += 1
                grids[observed["grid_profile"]] += 1
                commands[facts["command"]] += 1
                aligned += int(bool(facts["aligned_colors"]))
                singleton += int(bool(facts["singleton_colors"]))
                overlap += int(bool(facts["overlap_cells"]))
                distinct_inputs.add(_grid_key(grid))
            except Exception as exc:  # retained as evidence, never swallowed
                errors.append(f"{band}[{index}] generation error: {type(exc).__name__}: {exc}")
        per_band_report[band] = {
            "requested": per_band,
            "materialized": sum(profiles.values()),
            "distinct_inputs": len(distinct_inputs),
            "scene_profiles": _counter_dict(profiles),
            "grid_profiles": _counter_dict(grids),
            "commands": _counter_dict(commands),
            "aligned_scenes": aligned,
            "singleton_scenes": singleton,
            "overlap_scenes": overlap,
        }

    canonical = canonical_pairs(TASK_ID, root=ROOT)
    canonical_train = [pair for pair in canonical if pair["split"] == "train"]
    shortcut_summary: dict[str, Any] = {}
    train_fitting: list[str] = []
    counterexamples: dict[str, Any] = {}
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        try:
            fits_train = all(
                rival(pair["input"]) == pair["output"] for pair in canonical_train
            )
            fits_all = all(rival(pair["input"]) == pair["output"] for pair in canonical)
        except Exception as exc:
            fits_train = fits_all = False
            errors.append(f"shortcut {name!r} errored on canonical data: {exc}")
        if fits_train:
            train_fitting.append(name)
        witness = None
        for row in rows:
            try:
                rival_output = rival(row["input"])
            except Exception:
                continue
            if rival_output != row["output"]:
                witness = {
                    "band": row["band"],
                    "seed": row["seed"],
                    "sample_index": row["sample_index"],
                    "observed": row["observed"],
                    "input": row["input"],
                    "intended_output": row["output"],
                    "rival_output": rival_output,
                }
                break
        shortcut_summary[name] = {
            "fits_canonical_train": fits_train,
            "fits_all_canonical_pairs": fits_all,
            "generated_counterexample_found": witness is not None,
        }
        counterexamples[name] = witness

    rotation_failures: list[dict[str, Any]] = []
    rotation_checks = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(window_starts):
            seed = 830_000 + band_index * 100_000 + start
            pairs = []
            try:
                for offset in range(5):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": gen._rule_mirror(grid)})
            except Exception as exc:
                errors.append(
                    f"rotation materialization {band=} {start=}: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue
            for held_out in range(5):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                reasons = gen.lesson_identifiable(demos, pairs[held_out]["input"])
                rotation_checks += 1
                if reasons:
                    rotation_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "held_out": held_out,
                            "reasons": reasons,
                        }
                    )

    return {
        "schema": "d476983a3d6c-profile-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "sampler": {
            "per_band": per_band,
            "bands": ["easy", "medium", "hard"],
            "seed_formula": "480000 + 100000*band_index + sample_index",
            "sample_indices": [0, per_band - 1],
            "window_starts": window_starts,
            "window_pair_count": 5,
            "held_out_rotations_per_window": 5,
        },
        "draws_total": len(rows),
        "per_band": per_band_report,
        "canonical_pairs": len(canonical),
        "canonical_train_pairs": len(canonical_train),
        "canonical_train_fitting_shortcuts": train_fitting,
        "shortcut_summary": shortcut_summary,
        "shortcut_counterexamples": counterexamples,
        "rotation_checks": rotation_checks,
        "rotation_failures": rotation_failures,
        "errors": errors,
        "limits": [
            "Finite declared-rival evidence; undeclared hypotheses remain untested.",
            "Cyclic probe covers the requested starts only, not every random seed.",
            "Python mirror outputs are task-local diagnostics; the official census and battery execute Racket authority.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--window-starts", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(per_band=args.per_band, window_starts=args.window_starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 1 if report["errors"] or report["rotation_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
