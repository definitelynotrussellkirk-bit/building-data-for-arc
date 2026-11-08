#!/usr/bin/env python3
"""Replayable diagnostic probe for an ARC generator review.

The probe deliberately stays outside the selected generator.  It exercises the
public review contract that future agents most often miss:

* every canonical pair is accepted and mirrored correctly;
* every exact Cartesian combination of declared integer axes is constructible
  in every difficulty band;
* exact observations, freshness, deterministic replay, and global RNG purity
  hold; and
* complete lessons remain identifiable for every cyclic start and every query
  position against the generator's *actual* declared competitors.

This is a finite Python-mirror diagnostic, not label authority.  Run the packet's
Racket-backed checks separately before accepting a generator.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import random
import re
import sys
from typing import Any

from reviewer_support import canonical_pairs, find_root


BANDS = (None, "easy", "medium", "hard")
_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*$")


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"review_probe_{path.parent.name}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _integer_axis_domains(module) -> dict[str, tuple[int, ...]]:
    axes = getattr(module, "AXES", None)
    if not isinstance(axes, dict) or not axes:
        raise ValueError("generator must declare a non-empty AXES mapping")
    domains: dict[str, tuple[int, ...]] = {}
    for name, spec in axes.items():
        if not isinstance(spec, dict) or spec.get("type") != "int":
            raise ValueError(
                f"review_probe only enumerates integer axes; {name!r} is unsupported"
            )
        match = _RANGE_RE.fullmatch(str(spec.get("valid", "")))
        if match is None:
            raise ValueError(f"axis {name!r} must declare valid as 'low..high'")
        low, high = map(int, match.groups())
        if low > high:
            raise ValueError(f"axis {name!r} has descending range {low}..{high}")
        domains[name] = tuple(range(low, high + 1))
    return domains


def _record(failures: list[dict[str, Any]], kind: str, **details: Any) -> None:
    failures.append({"kind": kind, **details})


def _check_canonical(module, generator_path: Path, failures: list[dict[str, Any]]) -> int:
    root = find_root(generator_path)
    pairs = canonical_pairs(module.TASK_ID, root=root, labeled_only=True)
    for pair in pairs:
        label = f"{pair.get('split', '?')}:{pair.get('pair_index', '?')}"
        original = deepcopy(pair["input"])
        findings = module.self_check(pair["input"])
        if findings:
            _record(failures, "canonical_rejected", pair=label, findings=findings)
        predicted = module.rule_mirror(pair["input"])
        if predicted != pair["output"]:
            _record(failures, "canonical_mirror_mismatch", pair=label)
        if pair["input"] != original:
            _record(failures, "canonical_input_mutated", pair=label)
    return len(pairs)


def _check_exact_axes(
    module,
    domains: dict[str, tuple[int, ...]],
    seeds_per_case: int,
    failures: list[dict[str, Any]],
) -> int:
    names = tuple(domains)
    values = tuple(domains[name] for name in names)
    cases = 0
    case_index = 0
    for band in BANDS:
        for combination in product(*values):
            overrides = dict(zip(names, combination, strict=True))
            for seed_offset in range(seeds_per_case):
                cases += 1
                seed = 710_000 + 10_000 * seed_offset + case_index
                sample_index = case_index + seed_offset
                random.seed(991_731)
                before = random.getstate()
                try:
                    first = module.generate(
                        seed, sample_index, difficulty=band, **overrides
                    )
                    second = module.generate(
                        seed, sample_index, difficulty=band, **overrides
                    )
                except Exception as exc:  # diagnostic boundary
                    _record(
                        failures,
                        "override_generation_error",
                        band=band,
                        overrides=overrides,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                    continue
                if random.getstate() != before:
                    _record(
                        failures,
                        "global_rng_mutated",
                        band=band,
                        overrides=overrides,
                    )
                if first != second:
                    _record(
                        failures,
                        "nondeterministic_replay",
                        band=band,
                        overrides=overrides,
                    )
                if first is second or any(a is b for a, b in zip(first, second)):
                    _record(
                        failures,
                        "nonfresh_replay",
                        band=band,
                        overrides=overrides,
                    )
                findings = module.self_check(first, difficulty=band)
                if findings:
                    _record(
                        failures,
                        "self_check_failed",
                        band=band,
                        overrides=overrides,
                        findings=findings,
                    )
                try:
                    observed = module.observe_overrides(first)
                except Exception as exc:  # diagnostic boundary
                    _record(
                        failures,
                        "override_observer_error",
                        band=band,
                        overrides=overrides,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                else:
                    if observed != overrides:
                        _record(
                            failures,
                            "override_observation_mismatch",
                            band=band,
                            overrides=overrides,
                            observed=observed,
                        )
                truth = module.rule_mirror(first)
                for name, competitor in module.LESSON_COMPETITORS.items():
                    try:
                        rival_output = competitor(first)
                    except Exception as exc:  # diagnostic boundary
                        _record(
                            failures,
                            "competitor_error",
                            competitor=name,
                            band=band,
                            overrides=overrides,
                            error=f"{type(exc).__name__}: {exc}",
                        )
                        continue
                    if rival_output == truth:
                        _record(
                            failures,
                            "single_example_semantic_collision",
                            competitor=name,
                            band=band,
                            overrides=overrides,
                        )
            case_index += 1
    return cases


def _check_lessons(
    module,
    lesson_starts: int,
    failures: list[dict[str, Any]],
) -> int:
    examples_needed = int(module.EXAMPLES_NEEDED)
    lesson_size = examples_needed + 1
    query_checks = 0
    for band_index, band in enumerate(BANDS):
        for start in range(lesson_starts):
            pairs = []
            for offset in range(lesson_size):
                sample_index = start + offset
                grid = module.generate(
                    820_000 + 1_000 * band_index + start,
                    sample_index,
                    difficulty=band,
                )
                pairs.append(
                    {"input": deepcopy(grid), "output": module.rule_mirror(grid)}
                )
            for query_index, query in enumerate(pairs):
                query_checks += 1
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                reasons = module.lesson_identifiable(demos, query)
                if reasons:
                    _record(
                        failures,
                        "lesson_not_identifiable",
                        band=band,
                        start=start,
                        query_index=query_index,
                        reasons=reasons,
                    )
                truth = module.rule_mirror(query["input"])
                for name, competitor in module.LESSON_COMPETITORS.items():
                    fits = all(
                        competitor(demo["input"]) == demo["output"]
                        for demo in demos
                    )
                    if fits and competitor(query["input"]) != truth:
                        _record(
                            failures,
                            "undeclared_lesson_ambiguity",
                            competitor=name,
                            band=band,
                            start=start,
                            query_index=query_index,
                        )
    return query_checks


def run_probe(
    generator_path: Path,
    *,
    seeds_per_case: int = 1,
    lesson_starts: int = 16,
) -> dict[str, Any]:
    if seeds_per_case < 1:
        raise ValueError("seeds_per_case must be at least 1")
    if lesson_starts < 1:
        raise ValueError("lesson_starts must be at least 1")
    generator_path = generator_path.resolve()
    module = _load_module(generator_path)
    domains = _integer_axis_domains(module)
    failures: list[dict[str, Any]] = []
    canonical_count = _check_canonical(module, generator_path, failures)
    override_count = _check_exact_axes(
        module, domains, seeds_per_case, failures
    )
    lesson_count = _check_lessons(module, lesson_starts, failures)
    digest = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    return {
        "task_id": module.TASK_ID,
        "generator": str(generator_path),
        "generator_sha256": digest,
        "status": "pass" if not failures else "fail",
        "parameters": {
            "bands": list(BANDS),
            "axis_domains": {name: list(values) for name, values in domains.items()},
            "seeds_per_case": seeds_per_case,
            "lesson_starts_per_band": lesson_starts,
            "query_positions_per_lesson": int(module.EXAMPLES_NEEDED) + 1,
        },
        "summary": {
            "canonical_pairs": canonical_count,
            "competitors": len(module.LESSON_COMPETITORS),
            "lesson_queries": lesson_count,
            "override_cases": override_count,
        },
        "failures": failures,
        "limitations": [
            "Uses the generator's Python rule_mirror for finite diagnostics; the canonical Racket rule remains label authority.",
            "Enumerates declared integer axes and finite seeds/lesson starts, not every possible random seed.",
            "Tests declared LESSON_COMPETITORS; it cannot prove absence of an undeclared hypothesis.",
        ],
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    default_generator = Path(__file__).resolve().parents[1] / "generator.py"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=default_generator)
    parser.add_argument("--seeds-per-case", type=int, default=1)
    parser.add_argument("--lesson-starts", type=int, default=16)
    parser.add_argument("--out", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    payload = run_probe(
        args.generator,
        seeds_per_case=args.seeds_per_case,
        lesson_starts=args.lesson_starts,
    )
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    print(encoded, end="")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
