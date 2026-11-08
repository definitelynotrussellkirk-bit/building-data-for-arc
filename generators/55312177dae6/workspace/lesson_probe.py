#!/usr/bin/env python3
"""Source-bound curriculum probe for ARC generator 55312177dae6.

The probe imports the exact generator file named on the command line, iterates
its declared competitors/shortcuts, and records aggregate evidence only.  It
uses all cyclic schedule starts evenly and never reads private query labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from reference_probe import authority_output, canonical_pairs  # noqa: E402


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("lesson_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_key(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=HERE.parent / "generator.py",
    )
    parser.add_argument("--lessons-per-band", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = args.generator.resolve()
    source = generator_path.read_bytes()
    gen = load_module(generator_path)
    profiles = tuple(gen.SCHEDULE_PROFILES)
    examples = int(gen.EXAMPLES_NEEDED)
    rivals = dict(gen.LESSON_COMPETITORS)
    witnesses = dict(gen.SEMANTIC_WITNESSES)
    shortcuts = dict(gen.CANONICAL_SHORTCUTS)

    canonical = canonical_pairs()
    shortcut_fit = {
        name: [shortcut(pair["input"]) == pair["output"] for pair in canonical]
        for name, shortcut in shortcuts.items()
    }

    report: dict[str, Any] = {
        "task_id": gen.TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "lessons_per_band": args.lessons_per_band,
        "examples_per_lesson": examples,
        "query_inputs_per_lesson": 1,
        "schedule_profiles": list(profiles),
        "assembly_policy": (
            "For lesson L, start=L mod profile_count; generate four consecutive "
            "sample_index values start..start+3 with seed base+L, then query at "
            "start+4 with the same seed. Thus every cyclic schedule start occurs "
            "equally often when lessons_per_band is divisible by profile_count."
        ),
        "domain_limits": {
            "axes": gen.AXES,
            "helpful_textures": list(gen.HELPFUL_TEXTURES),
            "degenerate_textures": list(gen.DEGENERATE_TEXTURES),
            "strict_claim": gen.MIN_STRICT_FRAC,
            "scope_note": (
                "This is a deterministic sample of the declared generator domain, "
                "not a proof of universal human/model induction."
            ),
        },
        "canonical_shortcut_fit": shortcut_fit,
        "bands": {},
    }

    bases = {"easy": 310_000, "medium": 410_000, "hard": 510_000}
    any_failure = not all(all(results) for results in shortcut_fit.values())
    for band, base in bases.items():
        input_hashes: set[str] = set()
        profile_starts = Counter()
        witness_hits = Counter()
        rival_discriminated = Counter()
        rival_total_disagreements = Counter()
        lesson_failures: list[dict[str, Any]] = []
        strict_failures = 0
        mirror_mismatches = 0
        generated_inputs = 0

        for lesson_index in range(args.lessons_per_band):
            start = lesson_index % len(profiles)
            seed = base + lesson_index
            profile_starts[profiles[start]] += 1
            demos: list[dict[str, Any]] = []
            lesson_disagreements = {name: 0 for name in rivals}
            for offset in range(examples):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                generated_inputs += 1
                input_hashes.add(grid_key(grid))
                if gen.strict_canonical_like(grid):
                    strict_failures += 1
                expected = gen.rule_mirror(grid)
                if expected != authority_output(grid):
                    mirror_mismatches += 1
                demos.append({"input": grid, "output": expected})
                for name, predicate in witnesses.items():
                    if predicate(grid):
                        witness_hits[name] += 1
                for name, rival in rivals.items():
                    if rival(grid) != expected:
                        lesson_disagreements[name] += 1
                        rival_total_disagreements[name] += 1
            query = gen.generate(seed, start + examples, difficulty=band)
            generated_inputs += 1
            input_hashes.add(grid_key(query))
            if gen.strict_canonical_like(query):
                strict_failures += 1
            if gen.rule_mirror(query) != authority_output(query):
                mirror_mismatches += 1
            errors = gen.lesson_identifiable(demos, {"input": query})
            for name, count in lesson_disagreements.items():
                if count:
                    rival_discriminated[name] += 1
            if errors or any(count == 0 for count in lesson_disagreements.values()):
                lesson_failures.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "start_profile": profiles[start],
                        "hook_errors": errors,
                        "rival_disagreements": lesson_disagreements,
                    }
                )

        band_report = {
            "seed_first": base,
            "seed_last": base + args.lessons_per_band - 1,
            "lessons": args.lessons_per_band,
            "generated_inputs": generated_inputs,
            "unique_inputs": len(input_hashes),
            "cyclic_start_counts": dict(profile_starts),
            "strict_failures": strict_failures,
            "rule_mirror_authority_mismatches": mirror_mismatches,
            "lesson_failures": len(lesson_failures),
            "first_lesson_failures": lesson_failures[:5],
            "witness_input_hits": {
                name: witness_hits[name] for name in witnesses
            },
            "rival_lessons_discriminated": {
                name: rival_discriminated[name] for name in rivals
            },
            "rival_demo_disagreements": {
                name: rival_total_disagreements[name] for name in rivals
            },
        }
        report["bands"][band] = band_report
        any_failure = any_failure or bool(
            strict_failures
            or mirror_mismatches
            or lesson_failures
            or any(rival_discriminated[name] != args.lessons_per_band for name in rivals)
        )

    report["passed"] = not any_failure
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "passed": report["passed"],
        "generator_sha256": report["generator_sha256"],
        "bands": {
            band: {
                "lessons": row["lessons"],
                "unique_inputs": row["unique_inputs"],
                "lesson_failures": row["lesson_failures"],
            }
            for band, row in report["bands"].items()
        },
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
