#!/usr/bin/env python3
"""Probe declared lesson rivals across seeds, cyclic starts, and query rotations.

This is task-local review tooling, not a proof of unique induction. It labels
examples with the selected generator's Python rule mirror and tests only rivals
that the generator actually declares in CANONICAL_SHORTCUTS,
LESSON_COMPETITORS, or SEMANTIC_RIVALS.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{GENERATOR_PATH.parent.name}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _declared_rivals(generator):
    rivals: dict[str, Any] = {}
    origins: dict[str, list[str]] = {}
    for declaration in (
        "CANONICAL_SHORTCUTS",
        "LESSON_COMPETITORS",
        "SEMANTIC_RIVALS",
    ):
        values = getattr(generator, declaration, {})
        if not isinstance(values, dict):
            continue
        for name, rival in values.items():
            key = str(name)
            if key in rivals and rivals[key] is not rival:
                key = f"{declaration}:{name}"
            rivals[key] = rival
            origins.setdefault(key, []).append(declaration)
    return rivals, origins


def probe(
    *,
    seeds: Iterable[int],
    bands: Iterable[str],
    starts: Iterable[int],
    rotate_query: bool,
    max_examples: int = 3,
) -> dict[str, Any]:
    generator = _load_generator()
    rivals, origins = _declared_rivals(generator)
    if not rivals:
        raise RuntimeError("generator declares no lesson rivals")
    if not hasattr(generator, "rule_mirror"):
        raise RuntimeError("generator has no rule_mirror")

    seed_values = tuple(int(value) for value in seeds)
    band_values = tuple(str(value) for value in bands)
    start_values = tuple(int(value) for value in starts)
    summary = {
        "lesson_windows": 0,
        "evaluated_queries": 0,
        "ambiguous_queries": 0,
        "ambiguous_rival_events": 0,
        "hook_warning_queries": 0,
        "generation_errors": 0,
        "unique_inputs": 0,
    }
    per_rival = {
        name: {"ambiguous_events": 0, "refuted_queries": 0, "equivalent_queries": 0}
        for name in rivals
    }
    unique_inputs: set[str] = set()
    examples: list[dict[str, Any]] = []
    generation_errors: list[dict[str, Any]] = []

    for band in band_values:
        for seed in seed_values:
            for start in start_values:
                summary["lesson_windows"] += 1
                try:
                    pairs = []
                    for offset in range(5):
                        sample_index = start + offset
                        grid = generator.generate(
                            seed,
                            sample_index,
                            difficulty=band,
                        )
                        output = generator.rule_mirror(grid)
                        unique_inputs.add(_sha256_json(grid))
                        pairs.append(
                            {
                                "sample_index": sample_index,
                                "input": grid,
                                "output": output,
                            }
                        )
                except Exception as exc:  # retained as evidence, not hidden
                    summary["generation_errors"] += 1
                    if len(generation_errors) < max_examples:
                        generation_errors.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                    continue

                query_indexes = range(5) if rotate_query else (4,)
                for query_index in query_indexes:
                    summary["evaluated_queries"] += 1
                    query = pairs[query_index]
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    ambiguous_names: list[str] = []
                    rival_query_outputs: dict[str, Any] = {}
                    for name, rival in rivals.items():
                        fits = all(
                            rival(pair["input"]) == pair["output"]
                            for pair in demos
                        )
                        differs = rival(query["input"]) != query["output"]
                        if fits and differs:
                            ambiguous_names.append(name)
                            rival_query_outputs[name] = rival(query["input"])
                            per_rival[name]["ambiguous_events"] += 1
                            summary["ambiguous_rival_events"] += 1
                        elif not fits:
                            per_rival[name]["refuted_queries"] += 1
                        else:
                            per_rival[name]["equivalent_queries"] += 1

                    hook_reasons: list[str] = []
                    hook = getattr(generator, "lesson_identifiable", None)
                    if callable(hook):
                        hook_reasons = list(hook(demos, query) or [])
                    if hook_reasons:
                        summary["hook_warning_queries"] += 1
                    if ambiguous_names:
                        summary["ambiguous_queries"] += 1

                    if (ambiguous_names or hook_reasons) and len(examples) < max_examples:
                        examples.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "query_sample_index": query["sample_index"],
                                "demo_sample_indices": [pair["sample_index"] for pair in demos],
                                "ambiguous_rivals": ambiguous_names,
                                "hook_reasons": hook_reasons,
                                "pairs": pairs,
                                "rival_query_outputs": rival_query_outputs,
                            }
                        )

    summary["unique_inputs"] = len(unique_inputs)
    return {
        "schema": "arcpuzzles-task-local-rival-probe-v1",
        "task_id": getattr(generator, "TASK_ID", GENERATOR_PATH.parent.name),
        "generator_version": getattr(generator, "VERSION", None),
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "sampler": {
            "seeds": list(seed_values),
            "bands": list(band_values),
            "cyclic_starts": list(start_values),
            "pairs_per_window": 5,
            "rotate_query": bool(rotate_query),
        },
        "declared_rivals": {
            name: {"origins": origins[name]}
            for name in sorted(rivals)
        },
        "summary": summary,
        "per_rival": per_rival,
        "examples": examples,
        "generation_errors": generation_errors,
        "limits": [
            "Only declared executable rivals are tested.",
            "Finite seeds and cyclic starts do not prove universal identifiability.",
            "Labels use rule_mirror; use the supported Racket apply command for authority evidence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100, help="number of consecutive seeds")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--starts", type=int, default=4, help="number of cyclic sample starts")
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--rotate-query", action="store_true")
    parser.add_argument("--max-examples", type=int, default=3)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()

    report = probe(
        seeds=range(args.seed_start, args.seed_start + args.seeds),
        bands=tuple(value.strip() for value in args.bands.split(",") if value.strip()),
        starts=range(args.starts),
        rotate_query=args.rotate_query,
        max_examples=max(0, args.max_examples),
    )
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(json.dumps({"out": str(args.out), "summary": report["summary"]}, indent=2))
    else:
        print(text, end="")

    failed = (
        report["summary"]["ambiguous_queries"]
        or report["summary"]["hook_warning_queries"]
        or report["summary"]["generation_errors"]
    )
    return 1 if args.require_clean and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
