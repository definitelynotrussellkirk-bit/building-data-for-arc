#!/usr/bin/env python3
"""Task-local diagnostics for f84f23e456ac's generated curriculum.

This is an authoring probe, not an authority check.  It uses the generator's
public structural hooks and Python mirror to measure sampler support, declared
rival refutation, and every cyclic three-example window.  Run the shared Racket
battery and lesson census separately before accepting a change.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "f84f23e456ac"
BANDS = ("easy", "medium", "hard")
MIN_UNIQUE_FRACTION = 0.90


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _source_hash(module: Any) -> str:
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


def _sample_band(module: Any, band: str, count: int, seed: int) -> dict[str, Any]:
    profiles: Counter[str] = Counter()
    motifs: Counter[str] = Counter()
    densities: Counter[str] = Counter()
    colors: Counter[str] = Counter()
    rivals = defaultdict(lambda: {"refuted": 0, "agrees": 0, "errors": 0})
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    invalid: list[dict[str, Any]] = []

    for sample_index in range(count):
        grid = module.generate(seed, sample_index, difficulty=band)
        errors = module.self_check(grid)
        if errors:
            invalid.append({"sample_index": sample_index, "errors": list(errors)})
            continue
        observed = module.observe_overrides(grid)
        profiles[f"{observed['grid_h']}x{observed['grid_w']}+{observed['n_distinct_colors']}"] += 1
        motifs[f"{observed['motif_h']}x{observed['motif_w']}"] += 1
        densities[str(observed["density"])] += 1
        colors[str(observed["n_distinct_colors"])] += 1
        unique_inputs.add(_freeze(grid))
        truth = module.rule_mirror(grid)
        for name, rival in module.SEMANTIC_RIVALS.items():
            try:
                if rival(grid) == truth:
                    rivals[name]["agrees"] += 1
                else:
                    rivals[name]["refuted"] += 1
            except Exception:
                rivals[name]["errors"] += 1

    return {
        "draws": count,
        "valid": count - len(invalid),
        "invalid": invalid,
        "unique_inputs": len(unique_inputs),
        "unique_fraction": len(unique_inputs) / count,
        "profiles": dict(sorted(profiles.items())),
        "motifs": dict(sorted(motifs.items())),
        "densities": dict(sorted(densities.items())),
        "nonzero_color_counts": dict(sorted(colors.items())),
        "rivals": dict(sorted(rivals.items())),
    }


def _sliding_windows(module: Any, band: str, starts: int, seed: int) -> dict[str, Any]:
    width = int(module.EXAMPLES_NEEDED)
    ambiguous: list[dict[str, Any]] = []
    survivor_counts: Counter[str] = Counter()
    for start in range(starts):
        demos = []
        for offset in range(width):
            grid = module.generate(seed, start + offset, difficulty=band)
            demos.append({"input": grid, "output": module.rule_mirror(grid)})
        query_grid = module.generate(seed, start + width, difficulty=band)
        query = {"input": query_grid, "output": module.rule_mirror(query_grid)}
        reasons = module.lesson_identifiable(demos, query)
        survivors = []
        for name, rival in module.LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                survivors.append(name)
                survivor_counts[name] += 1
        if reasons or survivors:
            ambiguous.append({
                "start": start,
                "reasons": list(reasons),
                "survivors": survivors,
            })
    return {
        "starts": starts,
        "window_size": width,
        "ambiguous_count": len(ambiguous),
        "survivor_counts": dict(sorted(survivor_counts.items())),
        "examples": ambiguous[:10],
    }



def _canonical_shortcuts(module: Any) -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    shortcuts: dict[str, Any] = {}
    for name, shortcut in module.CANONICAL_SHORTCUTS.items():
        fits = 0
        errors: list[str] = []
        for index, pair in enumerate(pairs):
            try:
                if shortcut(pair["input"]) == pair["output"]:
                    fits += 1
                else:
                    errors.append(f"pair {index}: output differs")
            except Exception as exc:
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        shortcuts[name] = {
            "canonical_pairs": len(pairs),
            "fits": fits,
            "errors": errors,
        }
    return shortcuts

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--window-starts", type=int, default=60)
    parser.add_argument("--seed", type=int, default=20261004)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band <= 0 or args.window_starts <= 0:
        parser.error("counts must be positive")

    try:
        module = importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        generator_path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"review_probe_{TASK_ID}", generator_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {generator_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    report = {
        "schema": "f84f23e456ac-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _source_hash(module),
        "seed": args.seed,
        "minimum_unique_fraction": MIN_UNIQUE_FRACTION,
        "lesson_assembly_policy": (
            "Three consecutive accepted samples per lesson; probe checks every "
            "requested cyclic start independently in each difficulty band."
        ),
        "authority_note": (
            "Python mirror and declared rivals only; use the shared Racket "
            "battery and lesson census for authority-bound evidence."
        ),
        "bands": {
            band: _sample_band(module, band, args.per_band, args.seed)
            for band in BANDS
        },
        "canonical_shortcuts": _canonical_shortcuts(module),
        "sliding_windows": {
            band: _sliding_windows(
                module, band, args.window_starts, args.seed + 1
            )
            for band in BANDS
        },
    }
    report["passed"] = (
        all(
            not report["bands"][band]["invalid"]
            and report["bands"][band]["unique_fraction"]
            >= MIN_UNIQUE_FRACTION
            and all(
                counts["refuted"] > 0 and counts["errors"] == 0
                for counts in report["bands"][band]["rivals"].values()
            )
            and report["sliding_windows"][band]["ambiguous_count"] == 0
            for band in BANDS
        )
        and all(
            item["fits"] == item["canonical_pairs"] and not item["errors"]
            for item in report["canonical_shortcuts"].values()
        )
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
