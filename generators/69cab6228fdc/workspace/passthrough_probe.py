#!/usr/bin/env python3
"""Audit passthrough-cardinality teaching for generator 69cab6228fdc.

This is intentionally task-local and standard-library-only.  It catches the
specific failure mode where generated lessons show at most one unmapped color,
allowing a wrong "preserve only the first unmapped color" rule to survive.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

TASK_ID = "69cab6228fdc"
SCHEMA = "arcpuzzles-passthrough-probe-v1"
BANDS = ("easy", "medium", "hard")

EXACT_WITNESS = [
    [1, 2, 0, 0, 0, 0],
    [3, 4, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [1, 5, 6, 0, 0, 0],
    [2, 6, 5, 0, 0, 0],
    [1, 2, 5, 6, 0, 0],
    [2, 1, 6, 5, 0, 0],
]


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (
            (candidate / "shared" / "runtime" / "puzzle_generators" / "base.py").is_file()
            and (candidate / "generators" / TASK_ID / "generator.py").is_file()
        ):
            return candidate
    raise RuntimeError("could not locate repository root from passthrough_probe.py")


def load_generator() -> ModuleType:
    """Load the selected generator both inside and outside the check runtime."""
    module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        root = _repo_root()
        runtime = root / "shared" / "runtime"
        if str(runtime) not in sys.path:
            sys.path.insert(0, str(runtime))
        source = root / "generators" / TASK_ID / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"task_generator_{TASK_ID}", source
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load generator source at {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def unmapped_body_colors(generator: ModuleType, grid: list[list[int]]) -> list[int]:
    sources = {source for source, _ in generator._pairs(grid)}
    return sorted(
        {value for row in grid[3:] for value in row if value and value not in sources}
    )


def _lesson_window(generator: ModuleType, seed: int, start: int, band: str) -> list[str]:
    examples = []
    for sample_index in range(start, start + generator.EXAMPLES_NEEDED + 1):
        grid = generator.generate(seed, sample_index, difficulty=band)
        examples.append({"input": grid, "output": generator.rule_mirror(grid)})
    return generator.lesson_identifiable(examples[:-1], examples[-1])


def run_probe(
    *,
    generator: ModuleType | None = None,
    canonical_pairs: list[dict[str, Any]] | None = None,
    per_band: int = 40,
    seed: int = 20261004,
) -> dict[str, Any]:
    """Audit supplied evidence; an omitted canonical check is explicitly unrun.

    ``None`` requests generated-scene checks only. An explicitly supplied empty
    canonical list is missing evidence, never a successful shortcut fit.
    """
    if per_band < 1:
        raise ValueError("per_band must be at least 1")
    generator = generator or load_generator()
    failures: list[str] = []
    bands: dict[str, Any] = {}

    shortcut_results: dict[str, dict[str, Any]] = {}
    canonical_evidence = {"status": "not_provided", "pairs": 0}
    if canonical_pairs is not None:
        total = len(canonical_pairs)
        canonical_evidence = {
            "status": "checked" if total else "empty",
            "pairs": total,
        }
        if not total:
            failures.append("canonical evidence is empty; shortcut fits are unverified")
        for name, rival in sorted(generator.CANONICAL_SHORTCUTS.items()):
            fits = sum(
                rival(pair["input"]) == pair["output"]
                for pair in canonical_pairs
            )
            status = "unverified" if not total else "fits_all" if fits == total else "refuted"
            shortcut_results[name] = {
                "fits": fits,
                "pairs": total,
                "status": status,
            }
            if status == "refuted":
                failures.append(
                    f"declared canonical shortcut {name} fits {fits}/{total} pairs"
                )

    for band_offset, band in enumerate(BANDS):
        band_seed = seed + 100_000 * band_offset
        cardinality: Counter[int] = Counter()
        rival_refutations = {
            name: 0 for name in sorted(generator.CANONICAL_SHORTCUTS)
        }

        for sample_index in range(per_band):
            grid = generator.generate(band_seed, sample_index, difficulty=band)
            errors = generator.self_check(grid)
            if errors:
                failures.append(
                    f"{band}[{sample_index}] self_check failed: {'; '.join(errors)}"
                )
                continue

            expected_mode = generator.schedule_profile(
                band_seed, sample_index, band
            )
            observed_mode = generator.observe_overrides(grid)["passthrough"]
            colors = unmapped_body_colors(generator, grid)
            cardinality[len(colors)] += 1
            if observed_mode != expected_mode:
                failures.append(
                    f"{band}[{sample_index}] schedule={expected_mode} observed={observed_mode}"
                )

            intended = generator.rule_mirror(grid)
            if expected_mode == "absent":
                if colors:
                    failures.append(
                        f"{band}[{sample_index}] absent branch exposed {colors}"
                    )
            else:
                if len(colors) < 2:
                    failures.append(
                        f"{band}[{sample_index}] present branch exposed only {colors}"
                    )
                for rival_name in rival_refutations:
                    rival_output = generator.CANONICAL_SHORTCUTS[rival_name](grid)
                    if rival_output != intended:
                        rival_refutations[rival_name] += 1
                    else:
                        failures.append(
                            f"{band}[{sample_index}] did not refute {rival_name}"
                        )

        ambiguous_windows = 0
        ambiguity_examples: list[dict[str, Any]] = []
        for start in range(per_band):
            reasons = _lesson_window(generator, band_seed, start, band)
            if reasons:
                ambiguous_windows += 1
                if len(ambiguity_examples) < 5:
                    ambiguity_examples.append({"start": start, "reasons": reasons})
                failures.append(
                    f"{band} lesson window {start} ambiguous: {'; '.join(reasons)}"
                )

        bands[band] = {
            "seed": band_seed,
            "samples": per_band,
            "passthrough_cardinality": {
                str(key): cardinality[key] for key in sorted(cardinality)
            },
            "rival_refutations": rival_refutations,
            "lesson_windows_checked": per_band,
            "ambiguous_windows": ambiguous_windows,
            "ambiguity_examples": ambiguity_examples,
        }

    witness_errors = generator.self_check(EXACT_WITNESS)
    intended_output = generator.rule_mirror(EXACT_WITNESS)
    first_unmapped_output = generator.SEMANTIC_RIVALS["first_unmapped_only"](
        EXACT_WITNESS
    )
    witness_colors = unmapped_body_colors(generator, EXACT_WITNESS)
    if witness_errors:
        failures.append("exact witness rejected: " + "; ".join(witness_errors))
    if witness_colors != [5, 6]:
        failures.append(f"exact witness unmapped colors were {witness_colors}, expected [5, 6]")
    if intended_output == first_unmapped_output:
        failures.append("exact witness does not distinguish first_unmapped_only")

    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_rule_hash": generator.RULE_HASH,
        "seed": seed,
        "per_band": per_band,
        "canonical_evidence": canonical_evidence,
        "canonical_shortcuts": shortcut_results,
        "bands": bands,
        "exact_witness": {
            "input": EXACT_WITNESS,
            "unmapped_colors": witness_colors,
            "self_check_errors": witness_errors,
            "intended_output": intended_output,
            "first_unmapped_only_output": first_unmapped_output,
        },
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20261004)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    generator = load_generator()
    root = _repo_root()
    runtime = root / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    from reviewer_support import canonical_pairs as read_canonical_pairs

    report = run_probe(
        generator=generator,
        canonical_pairs=read_canonical_pairs(TASK_ID, root=root, variant=0),
        per_band=args.per_band,
        seed=args.seed,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload)
    print(payload, end="")
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
