#!/usr/bin/env python3
"""Portable source-bound probe for the ee5295e1813b teaching generator.

The probe checks canonical acceptance/labels, generated self-consistency,
observable overrides, determinism, three-example lesson identifiability, and
named shortcut separation.  It imports the adjacent source file directly and
bootstraps the packet's shared runtime, so a fresh checkout needs no PYTHONPATH.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "ee5295e1813b"
HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "generator.py"


def _load_generator():
    root = _find_repo_root(HOME)
    runtime = root / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location(f"task_{TASK_ID}_probe", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file():
            return candidate
    raise RuntimeError("could not locate shared/data/canonical/puzzles.jsonl")


def _canonical_pairs(root: Path) -> list[dict[str, Any]]:
    # Prefer the repo helper when available, but keep a tiny fallback so the
    # probe remains source-local and readable to future reviewers.
    try:
        from reviewer_support import canonical_pairs  # type: ignore

        return list(canonical_pairs(TASK_ID, root=root, labeled_only=True))
    except (ImportError, ModuleNotFoundError):
        path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                record_id = record.get("task_id", record.get("id"))
                if record_id != TASK_ID:
                    continue
                pairs: list[dict[str, Any]] = []
                task = record.get("task", record)
                for split in ("train", "test"):
                    for index, pair in enumerate(task.get(split, [])):
                        if "input" in pair and "output" in pair:
                            pairs.append(
                                {
                                    "split": split,
                                    "pair_index": index,
                                    "input": pair["input"],
                                    "output": pair["output"],
                                }
                            )
                return pairs
        raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def _pair(gen, grid):
    return {"input": grid, "output": gen._apply_rule(grid)}


def run_probe(*, quick: bool, seeds: int | None, samples: int | None) -> dict[str, Any]:
    gen = _load_generator()
    root = _find_repo_root(HOME)
    seed_count = seeds if seeds is not None else (2 if quick else 12)
    sample_count = samples if samples is not None else (6 if quick else 24)

    canonical_failures: list[dict[str, Any]] = []
    canonical = _canonical_pairs(root)
    for pair in canonical:
        diagnostics = list(gen.strict_canonical_like(pair["input"]))
        label_matches = gen._apply_rule(pair["input"]) == pair["output"]
        if diagnostics or not label_matches:
            canonical_failures.append(
                {
                    "split": pair.get("split"),
                    "pair_index": pair.get("pair_index"),
                    "diagnostics": diagnostics,
                    "label_matches": label_matches,
                }
            )

    generated_failures: list[dict[str, Any]] = []
    textures: set[str] = set()
    color_modes: set[str] = set()
    generated_total = 0
    difficulties = (None, "easy", "medium", "hard")
    for seed in range(seed_count):
        for difficulty in difficulties:
            for sample_index in range(sample_count):
                generated_total += 1
                try:
                    grid = gen.generate(seed, sample_index, difficulty=difficulty)
                    repeated = gen.generate(seed, sample_index, difficulty=difficulty)
                    diagnostics = list(gen.self_check(grid, difficulty=difficulty))
                    observed = gen.observe_overrides(grid)
                    textures.add(str(observed.get("texture")))
                    color_modes.add(str(observed.get("color_mode")))
                    expected_texture, expected_mode = gen.schedule_profile(
                        seed, sample_index, difficulty
                    )
                    problems: list[str] = []
                    if grid != repeated:
                        problems.append("nondeterministic generation")
                    if diagnostics:
                        problems.append("self_check: " + "; ".join(diagnostics))
                    if observed.get("texture") != expected_texture:
                        problems.append(
                            f"texture expected {expected_texture!r}, observed {observed.get('texture')!r}"
                        )
                    if observed.get("color_mode") != expected_mode:
                        problems.append(
                            f"color_mode expected {expected_mode!r}, observed {observed.get('color_mode')!r}"
                        )
                    if problems:
                        generated_failures.append(
                            {
                                "seed": seed,
                                "difficulty": difficulty,
                                "sample_index": sample_index,
                                "problems": problems,
                                "observed": observed,
                            }
                        )
                except Exception as exc:  # keep a complete machine-readable census
                    generated_failures.append(
                        {
                            "seed": seed,
                            "difficulty": difficulty,
                            "sample_index": sample_index,
                            "problems": [f"{type(exc).__name__}: {exc}"],
                        }
                    )

    lesson_failures: list[dict[str, Any]] = []
    lesson_total = 0
    rival_names = sorted(gen.LESSON_COMPETITORS)
    for seed in range(seed_count):
        for start in range(max(1, sample_count - gen.EXAMPLES_NEEDED)):
            lesson_total += 1
            try:
                demos = [
                    _pair(gen, gen.generate(seed, start + offset, difficulty="medium"))
                    for offset in range(gen.EXAMPLES_NEEDED)
                ]
                query = _pair(
                    gen,
                    gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty="medium"),
                )
                diagnostics = list(gen.lesson_identifiable(demos, query))
                if diagnostics:
                    lesson_failures.append(
                        {"seed": seed, "start": start, "diagnostics": diagnostics}
                    )
            except Exception as exc:
                lesson_failures.append(
                    {
                        "seed": seed,
                        "start": start,
                        "diagnostics": [f"{type(exc).__name__}: {exc}"],
                    }
                )

    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report = {
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "source_sha256": source_hash,
        "parameters": {
            "quick": quick,
            "seeds": seed_count,
            "samples_per_difficulty": sample_count,
            "difficulties": list(difficulties),
        },
        "canonical": {
            "total": len(canonical),
            "passed": len(canonical) - len(canonical_failures),
            "failed": len(canonical_failures),
            "failures": canonical_failures,
        },
        "generated": {
            "total": generated_total,
            "passed": generated_total - len(generated_failures),
            "failed": len(generated_failures),
            "textures": sorted(textures),
            "color_modes": sorted(color_modes),
            "failures": generated_failures,
        },
        "lessons": {
            "total": lesson_total,
            "passed": lesson_total - len(lesson_failures),
            "failed": len(lesson_failures),
            "rivals": rival_names,
            "failures": lesson_failures,
        },
    }
    report["ok"] = not (
        report["canonical"]["failed"]
        or report["generated"]["failed"]
        or report["lessons"]["failed"]
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="run a compact CI-sized census")
    parser.add_argument("--seeds", type=int, default=None, help="override seed count")
    parser.add_argument(
        "--samples", type=int, default=None, help="override samples per difficulty"
    )
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args(argv)
    if args.seeds is not None and args.seeds < 1:
        parser.error("--seeds must be >= 1")
    if args.samples is not None and args.samples < 4:
        parser.error("--samples must be >= 4 to form a lesson")
    report = run_probe(quick=args.quick, seeds=args.seeds, samples=args.samples)
    json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
