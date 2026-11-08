#!/usr/bin/env python3
"""Fast, hash-bound curriculum probe for generator 040bfb038c65.

This intentionally uses the generator's public semantic contracts rather than
reimplementing the task.  It checks the strongest known canonical-fitting
rival across every declared schedule start and every four-pair query rotation.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
from typing import Any, Iterable

TASK_ID = "040bfb038c65"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs  # noqa: E402


def _load_generator():
    path = TASK_HOME / "generator.py"
    spec = spec_from_file_location(f"curriculum_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def _labeled(generator, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def evaluate(
    *,
    seed: int = 0,
    bands: Iterable[str] = ("easy", "medium", "hard"),
    starts: int | None = None,
) -> dict[str, Any]:
    """Return a deterministic report; empty ambiguity/error lists mean green."""
    generator, generator_path = _load_generator()
    bands = tuple(bands)
    if starts is None:
        starts = generator.LESSON_SCHEDULE_PERIOD
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(starts) is not int or starts <= 0:
        raise ValueError("starts must be a positive literal integer")

    rival_name = "largest_yellow_blob"
    rival = generator.LESSON_COMPETITORS[rival_name]
    canonical = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    canonical_matches = sum(
        rival(pair["input"]) == pair["output"] for pair in canonical
    )

    errors: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    lessons_checked = 0
    rotations_checked = 0
    first_counterexample: dict[str, Any] | None = None

    for band in bands:
        for start in range(starts):
            lesson = []
            for sample_index in range(start, start + 4):
                try:
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    findings = generator.self_check(grid, difficulty=band)
                    if findings:
                        errors.append(
                            {
                                "band": band,
                                "start": start,
                                "sample_index": sample_index,
                                "kind": "self_check",
                                "messages": findings,
                            }
                        )
                    pair = _labeled(generator, grid)
                    lesson.append(pair)
                    rival_output = rival(grid)
                    if first_counterexample is None and rival_output != pair["output"]:
                        first_counterexample = {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "schedule_profile": generator.schedule_profile(
                                seed, sample_index, band
                            ),
                            "input": grid,
                            "intended_output": pair["output"],
                            "rival_output": rival_output,
                        }
                except Exception as exc:  # report all residues in one run
                    errors.append(
                        {
                            "band": band,
                            "start": start,
                            "sample_index": sample_index,
                            "kind": "exception",
                            "message": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    lesson = []
                    break

            if len(lesson) != 4:
                continue
            lessons_checked += 1
            for query_index, query in enumerate(lesson):
                rotations_checked += 1
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                reasons = generator.lesson_identifiable(demos, query)
                if reasons:
                    ambiguous.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

    if first_counterexample is None:
        errors.append(
            {
                "kind": "missing_counterexample",
                "message": f"no emitted input refuted {rival_name}",
            }
        )
        first_counterexample = {
            "input": None,
            "intended_output": None,
            "rival_output": None,
        }

    return {
        "schema": "arcpuzzles-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "declared_rule_hash": generator.RULE_HASH,
        "rival": rival_name,
        "canonical_shortcut_fit": {
            "matched": canonical_matches,
            "total": len(canonical),
        },
        "seed": seed,
        "bands": list(bands),
        "schedule_period": generator.LESSON_SCHEDULE_PERIOD,
        "starts_per_band": starts,
        "lessons_checked": lessons_checked,
        "query_rotations_checked": rotations_checked,
        "ambiguous_rotations": ambiguous,
        "errors": errors,
        "counterexample": first_counterexample,
        "status": "pass" if not errors and not ambiguous else "fail",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--bands",
        nargs="+",
        default=["easy", "medium", "hard"],
        choices=["easy", "medium", "hard"],
    )
    parser.add_argument("--starts", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = evaluate(seed=args.seed, bands=args.bands, starts=args.starts)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
