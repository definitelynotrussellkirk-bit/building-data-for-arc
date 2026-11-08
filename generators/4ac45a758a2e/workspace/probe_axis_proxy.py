#!/usr/bin/env python3
"""Probe whether one generated axis can replace another in complete lessons.

This is intentionally small and task-agnostic: it imports a generator by task
ID, reads axes through ``observe_overrides``, and checks both marginal support
and an adaptive dictionary predictor learned only from each lesson's demos.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def _source_sha(module: Any) -> str:
    path = Path(module.__file__).resolve()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_bands(raw: str) -> tuple[str, ...]:
    bands = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not bands:
        raise argparse.ArgumentTypeError("at least one difficulty band is required")
    return bands


def _load_generator(task_id: str):
    """Load from a portable runtime or directly from a reviewer checkout."""
    module_name = f"puzzle_generators.per_puzzle.{task_id}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        repo_root = Path(__file__).resolve().parents[3]
        source = repo_root / "generators" / task_id / "generator.py"
        if not source.is_file():
            raise error
        spec = importlib.util.spec_from_file_location(
            f"axis_proxy_probe_{task_id}", source
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load generator source {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def probe(
    *,
    task_id: str,
    target_axis: str,
    proxy_axis: str,
    seed: int,
    period: int,
    lesson_starts: int,
    lesson_size: int,
    query_offset: int,
    bands: tuple[str, ...],
    require_equal_support: bool,
) -> dict[str, Any]:
    module = _load_generator(task_id)
    if not callable(getattr(module, "observe_overrides", None)):
        raise RuntimeError(f"{task_id} has no observe_overrides(grid) hook")

    band_reports: dict[str, Any] = {}
    failures: list[dict[str, Any]] = []
    total_survivors = 0

    for band_index, band in enumerate(bands):
        band_seed = seed + 100_000 * band_index
        proxy_by_target: dict[str, set[Any]] = {}
        for sample_index in range(period):
            facts = module.observe_overrides(
                module.generate(band_seed, sample_index, difficulty=band)
            )
            target = str(facts[target_axis])
            proxy_by_target.setdefault(target, set()).add(facts[proxy_axis])

        normalized_support = {
            target: sorted(values) for target, values in sorted(proxy_by_target.items())
        }
        union = set().union(*proxy_by_target.values()) if proxy_by_target else set()
        equal_support = all(values == union for values in proxy_by_target.values())
        if require_equal_support and not equal_support:
            failures.append(
                {
                    "band": band,
                    "kind": "unequal_proxy_support",
                    "proxy_by_target": normalized_support,
                }
            )

        survivors: list[dict[str, Any]] = []
        for start in range(lesson_starts):
            demos = []
            for offset in range(lesson_size):
                demos.append(
                    module.observe_overrides(
                        module.generate(
                            band_seed,
                            start + offset,
                            difficulty=band,
                        )
                    )
                )
            query = module.observe_overrides(
                module.generate(
                    band_seed,
                    start + query_offset,
                    difficulty=band,
                )
            )

            proxy_to_target: dict[Any, Any] = {}
            contradictory = False
            for facts in demos:
                proxy = facts[proxy_axis]
                target = facts[target_axis]
                previous = proxy_to_target.setdefault(proxy, target)
                contradictory |= previous != target
            prediction = proxy_to_target.get(query[proxy_axis])
            if not contradictory and prediction == query[target_axis]:
                survivors.append(
                    {
                        "start": start,
                        "mapping": {
                            str(key): value
                            for key, value in sorted(proxy_to_target.items())
                        },
                        "query": {
                            proxy_axis: query[proxy_axis],
                            target_axis: query[target_axis],
                        },
                    }
                )

        total_survivors += len(survivors)
        if survivors:
            failures.append(
                {
                    "band": band,
                    "kind": "demo_learned_proxy_predicts_query",
                    "survivor_count": len(survivors),
                    "first_survivor": survivors[0],
                }
            )
        band_reports[band] = {
            "seed": band_seed,
            "proxy_values_by_target": normalized_support,
            "equal_proxy_support": equal_support,
            "lesson_windows": lesson_starts,
            "proxy_predictor_survivors": len(survivors),
            "survivors": survivors,
        }

    return {
        "schema": "arc-axis-proxy-probe-v1",
        "task_id": task_id,
        "generator_sha256": _source_sha(module),
        "target_axis": target_axis,
        "proxy_axis": proxy_axis,
        "period_draws_per_band": period,
        "lesson_starts_per_band": lesson_starts,
        "lesson_size": lesson_size,
        "query_offset": query_offset,
        "bands": band_reports,
        "total_lesson_windows": lesson_starts * len(bands),
        "total_proxy_predictor_survivors": total_survivors,
        "require_equal_support": require_equal_support,
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--target-axis", required=True)
    parser.add_argument("--proxy-axis", required=True)
    parser.add_argument("--seed", type=int, default=31_000)
    parser.add_argument("--period", type=int, default=32)
    parser.add_argument("--lesson-starts", type=int, default=32)
    parser.add_argument("--lesson-size", type=int, default=8)
    parser.add_argument("--query-offset", type=int, default=8)
    parser.add_argument("--bands", type=_parse_bands, default=("easy", "medium", "hard"))
    parser.add_argument("--require-equal-support", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.out and (args.out.exists() or args.out.is_symlink()):
        parser.error("--out must be a new report path; existing evidence is preserved")

    report = probe(
        task_id=args.task_id,
        target_axis=args.target_axis,
        proxy_axis=args.proxy_axis,
        seed=args.seed,
        period=args.period,
        lesson_starts=args.lesson_starts,
        lesson_size=args.lesson_size,
        query_offset=args.query_offset,
        bands=args.bands,
        require_equal_support=args.require_equal_support,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Exclusive creation also protects an output introduced after preflight.
            with args.out.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        except FileExistsError:
            parser.error("--out already exists; existing evidence is preserved")
    else:
        print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
