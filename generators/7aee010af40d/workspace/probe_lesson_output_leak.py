#!/usr/bin/env python3
"""Measure cross-example answer leakage in generated five-demo lessons.

The probe is intentionally task-local. It checks whether the query's normalized
answer can be copied verbatim from any demonstration (and separately from the
first demonstration, which was the original period-five defect) and whether the
existing lesson hook still accepts each sampled window.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "shared/runtime/puzzle_generators").is_dir():
            return candidate
    raise FileNotFoundError("could not locate repo/shared/runtime")


def _load_generator(path: Path):
    path = path.resolve()
    spec = importlib.util.spec_from_file_location(
        f"lesson_output_leak_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    here = Path(__file__).resolve()
    repo = _repo_root(here.parent)
    sys.path.insert(0, str(repo / "shared/runtime"))

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=here.parents[1] / "generator.py",
        help="generator.py to inspect (default: selected task implementation)",
    )
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--starts", type=int, default=10)
    parser.add_argument(
        "--bands", nargs="+", default=["easy", "medium", "hard"]
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--fail-on-finding", action="store_true")
    args = parser.parse_args()
    if args.seeds < 1 or args.starts < 1:
        parser.error("--seeds and --starts must be positive")

    generator_path = args.generator.resolve()
    gen = _load_generator(generator_path)
    demos = int(gen.EXAMPLES_NEEDED)
    checked = 0
    exact_clones = 0
    any_demo_clones = 0
    hook_failures = 0
    examples: list[dict] = []

    for band in args.bands:
        for seed in range(args.seeds):
            for start in range(args.starts):
                pairs = []
                for offset in range(demos + 1):
                    grid = gen.generate(seed, start + offset, difficulty=band)
                    pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                checked += 1
                matching_demo_indices = [
                    index
                    for index, pair in enumerate(pairs[:-1])
                    if pair["output"] == pairs[-1]["output"]
                ]
                clone = 0 in matching_demo_indices
                any_clone = bool(matching_demo_indices)
                reasons = gen.lesson_identifiable(pairs[:-1], pairs[-1])
                exact_clones += int(clone)
                any_demo_clones += int(any_clone)
                hook_failures += int(bool(reasons))
                if (any_clone or reasons) and len(examples) < 20:
                    examples.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "first_output_sha256": _digest(pairs[0]["output"]),
                            "query_output_sha256": _digest(pairs[-1]["output"]),
                            "first_output": pairs[0]["output"],
                            "query_output": pairs[-1]["output"],
                            "matching_demo_indices": matching_demo_indices,
                            "lesson_reasons": reasons,
                        }
                    )

    report = {
        "schema": "7aee010af40d-lesson-output-leak-v2",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "examples_needed": demos,
        "bands": args.bands,
        "seeds_per_band": args.seeds,
        "starts_per_seed": args.starts,
        "lessons_checked": checked,
        "query_equals_first_demo_output": exact_clones,
        "query_equals_first_demo_rate": exact_clones / checked,
        "query_equals_any_demo_output": any_demo_clones,
        "query_equals_any_demo_rate": any_demo_clones / checked,
        "lesson_hook_failures": hook_failures,
        "finding_examples": examples,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 1 if args.fail_on_finding and (any_demo_clones or hook_failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
