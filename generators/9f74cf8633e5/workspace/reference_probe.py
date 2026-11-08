#!/usr/bin/env python3
"""Portable source-bound probe for the 9f74cf8633e5 teaching generator.

The probe checks canonical authority support, generated self-consistency,
observable scheduled controls, determinism, declared shortcut validity on the
canonical training pairs, and every query rotation of sampled six-pair lesson
blocks.  Rival names are read from the live generator registries rather than
copied into this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "9f74cf8633e5"
HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "generator.py"


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file():
            return candidate
    raise RuntimeError("could not locate shared/data/canonical/puzzles.jsonl")


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


def _canonical_pairs(root: Path) -> list[dict[str, Any]]:
    try:
        from reviewer_support import canonical_pairs  # type: ignore

        return list(canonical_pairs(TASK_ID, root=root, labeled_only=True))
    except (ImportError, ModuleNotFoundError):
        path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                if record.get("task_id", record.get("id")) != TASK_ID:
                    continue
                task = record.get("task", record)
                pairs: list[dict[str, Any]] = []
                for split in ("train", "test"):
                    for pair_index, pair in enumerate(task.get(split, [])):
                        if "input" in pair and "output" in pair:
                            pairs.append(
                                {
                                    "split": split,
                                    "pair_index": pair_index,
                                    "input": pair["input"],
                                    "output": pair["output"],
                                }
                            )
                return pairs
        raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def _pair(gen, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def run_probe(*, quick: bool, seeds: int | None, starts: int | None) -> dict[str, Any]:
    gen = _load_generator()
    root = _find_repo_root(HOME)
    seed_count = seeds if seeds is not None else (2 if quick else 12)
    start_count = starts if starts is not None else (2 if quick else 12)
    bands = ("easy", "medium", "hard")

    canonical = _canonical_pairs(root)
    canonical_failures: list[dict[str, Any]] = []
    for pair in canonical:
        diagnostics = list(gen.strict_canonical_like(pair["input"]))
        label_matches = gen.rule_mirror(pair["input"]) == pair["output"]
        if diagnostics or not label_matches:
            canonical_failures.append(
                {
                    "split": pair.get("split"),
                    "pair_index": pair.get("pair_index"),
                    "diagnostics": diagnostics,
                    "label_matches": label_matches,
                }
            )

    train_pairs = [pair for pair in canonical if pair.get("split") == "train"]
    shortcut_failures: list[dict[str, Any]] = []
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        bad = [
            int(pair.get("pair_index", index))
            for index, pair in enumerate(train_pairs)
            if rival(pair["input"]) != pair["output"]
        ]
        if bad:
            shortcut_failures.append({"rival": name, "nonfitting_train_pairs": bad})

    generated_failures: list[dict[str, Any]] = []
    observed_textures: set[str] = set()
    observed_modes: set[str] = set()
    generated_total = 0
    samples_per_band = max(6, start_count + gen.EXAMPLES_NEEDED)
    for seed in range(seed_count):
        for band in bands:
            for sample_index in range(samples_per_band):
                generated_total += 1
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    repeated = gen.generate(seed, sample_index, difficulty=band)
                    diagnostics = list(gen.self_check(grid, difficulty=band))
                    generated_diagnostics = list(gen._generated_errors(grid, difficulty=band))
                    observed = gen.observe_overrides(grid)
                    expected_texture, expected_mode = gen.schedule_profile(
                        seed, sample_index, band
                    )
                    problems: list[str] = []
                    if grid != repeated:
                        problems.append("nondeterministic generation")
                    if diagnostics:
                        problems.append("self_check: " + "; ".join(diagnostics))
                    if generated_diagnostics:
                        problems.append("generated_errors: " + "; ".join(generated_diagnostics))
                    if observed.get("texture") != expected_texture:
                        problems.append(
                            f"texture expected {expected_texture!r}, observed {observed.get('texture')!r}"
                        )
                    if observed.get("color_mode") != expected_mode:
                        problems.append(
                            f"color_mode expected {expected_mode!r}, observed {observed.get('color_mode')!r}"
                        )
                    observed_textures.add(str(observed.get("texture")))
                    observed_modes.add(str(observed.get("color_mode")))
                    if problems:
                        generated_failures.append(
                            {
                                "seed": seed,
                                "difficulty": band,
                                "sample_index": sample_index,
                                "problems": problems,
                                "observed": observed,
                            }
                        )
                except Exception as exc:
                    generated_failures.append(
                        {
                            "seed": seed,
                            "difficulty": band,
                            "sample_index": sample_index,
                            "problems": [f"{type(exc).__name__}: {exc}"],
                        }
                    )

    lesson_failures: list[dict[str, Any]] = []
    lesson_rotations = 0
    rival_names = sorted(gen.LESSON_COMPETITORS)
    block_size = gen.EXAMPLES_NEEDED + 1
    for seed in range(seed_count):
        for band in bands:
            for start in range(start_count):
                try:
                    pairs = [
                        _pair(gen, gen.generate(seed, start + offset, difficulty=band))
                        for offset in range(block_size)
                    ]
                    for query_index, query in enumerate(pairs):
                        lesson_rotations += 1
                        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                        diagnostics = list(gen.lesson_identifiable(demos, query))
                        unrefuted = [
                            name
                            for name, rival in gen.LESSON_COMPETITORS.items()
                            if all(rival(pair["input"]) == pair["output"] for pair in demos)
                        ]
                        if diagnostics or unrefuted:
                            lesson_failures.append(
                                {
                                    "seed": seed,
                                    "difficulty": band,
                                    "start": start,
                                    "query_index": query_index,
                                    "diagnostics": diagnostics,
                                    "unrefuted_rivals": sorted(unrefuted),
                                }
                            )
                except Exception as exc:
                    lesson_failures.append(
                        {
                            "seed": seed,
                            "difficulty": band,
                            "start": start,
                            "query_index": None,
                            "diagnostics": [f"{type(exc).__name__}: {exc}"],
                            "unrefuted_rivals": [],
                        }
                    )

    expected_textures = set(gen.TEXTURES)
    expected_modes = set(gen.COLOR_MODES)
    coverage_failures: list[str] = []
    if observed_textures != expected_textures:
        coverage_failures.append(
            f"textures expected {sorted(expected_textures)}, observed {sorted(observed_textures)}"
        )
    if observed_modes != expected_modes:
        coverage_failures.append(
            f"color modes expected {sorted(expected_modes)}, observed {sorted(observed_modes)}"
        )

    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "parameters": {
            "quick": quick,
            "seeds": seed_count,
            "starts_per_band": start_count,
            "samples_per_band": samples_per_band,
            "difficulties": list(bands),
        },
        "canonical": {
            "total": len(canonical),
            "passed": len(canonical) - len(canonical_failures),
            "failed": len(canonical_failures),
            "failures": canonical_failures,
        },
        "canonical_shortcuts": {
            "total": len(gen.CANONICAL_SHORTCUTS),
            "passed": len(gen.CANONICAL_SHORTCUTS) - len(shortcut_failures),
            "failed": len(shortcut_failures),
            "failures": shortcut_failures,
        },
        "generated": {
            "total": generated_total,
            "passed": generated_total - len(generated_failures),
            "failed": len(generated_failures),
            "textures": sorted(observed_textures),
            "color_modes": sorted(observed_modes),
            "coverage_failures": coverage_failures,
            "failures": generated_failures,
        },
        "lessons": {
            "rotations": lesson_rotations,
            "passed": lesson_rotations - len(lesson_failures),
            "failed": len(lesson_failures),
            "demonstrations_per_rotation": gen.EXAMPLES_NEEDED,
            "rivals": rival_names,
            "failures": lesson_failures,
        },
    }
    report["ok"] = not (
        report["canonical"]["failed"]
        or report["canonical_shortcuts"]["failed"]
        or report["generated"]["failed"]
        or report["generated"]["coverage_failures"]
        or report["lessons"]["failed"]
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="run a compact CI-sized census")
    parser.add_argument("--seeds", type=int, default=None, help="override seed count")
    parser.add_argument("--starts", type=int, default=None, help="override starts per band")
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args(argv)
    if args.seeds is not None and args.seeds < 1:
        parser.error("--seeds must be >= 1")
    if args.starts is not None and args.starts < 1:
        parser.error("--starts must be >= 1")
    report = run_probe(quick=args.quick, seeds=args.seeds, starts=args.starts)
    json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
