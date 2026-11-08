#!/usr/bin/env python3
"""Small source-bound semantic probe for ``fc41c9b3a565``.

This is intentionally cheaper than the shared battery.  It samples the three
production bands, reports structural/profile/witness/rival coverage, and checks
both the ordered four-demonstration lesson and every query rotation in the same
five-pair window.  It never reads private query answers: labels are produced by
the generator's public Python rule mirror and remain subject to the separate
Racket authority checks in the review battery.

Run from the packet's ``repo`` directory, normally through ``run_with_racket``::

    python3 generators/fc41c9b3a565/workspace/semantic_probe.py \
        --seeds 1301,1302 --per-band 20 --lesson-starts 12 \
        --out ../checks/task-semantic-probe.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Sequence

TASK_ID = "fc41c9b3a565"
BANDS = ("easy", "medium", "hard")
DEFAULT_DEMONSTRATIONS = 4


def _source_hash(module: ModuleType) -> str | None:
    source = getattr(module, "__file__", None)
    if not source:
        return None
    path = Path(source)
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pair(module: ModuleType, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = module.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": module.rule_mirror(grid)}


def _failure(
    *,
    seed: int,
    band: str,
    start: int,
    query_position: int,
    reasons: Iterable[str],
) -> dict[str, Any]:
    return {
        "seed": seed,
        "band": band,
        "start": start,
        "query_position": query_position,
        "reasons": list(reasons),
    }


def run_probe(
    module: ModuleType,
    *,
    seeds: Sequence[int] = (1301, 1302),
    per_band: int = 20,
    lesson_starts: int = 12,
    demonstrations: int = DEFAULT_DEMONSTRATIONS,
) -> dict[str, Any]:
    """Return a JSON-safe report for profile and teaching-contract coverage."""
    seeds = tuple(int(seed) for seed in seeds)
    if not seeds:
        raise ValueError("at least one seed is required")
    if per_band < 1:
        raise ValueError("per_band must be positive")
    if lesson_starts < 0:
        raise ValueError("lesson_starts cannot be negative")
    if demonstrations < 1:
        raise ValueError("demonstrations must be positive")

    profiles = tuple(module._PROFILE_OPTIONS)
    witness_names = tuple(module.SEMANTIC_WITNESSES)
    rival_names = tuple(module.SEMANTIC_RIVALS)
    report: dict[str, Any] = {
        "schema": "fc41c9b3a565-semantic-probe-v1",
        "task_id": getattr(module, "TASK_ID", TASK_ID),
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "generator_sha256": _source_hash(module),
        "parameters": {
            "seeds": list(seeds),
            "per_band": per_band,
            "lesson_starts": lesson_starts,
            "demonstrations": demonstrations,
        },
        "bands": {},
        "lessons": {
            "production_policy": (
                f"{demonstrations} consecutive demonstrations followed by the next query"
            ),
            "rotation_policy": (
                f"hold each of {demonstrations + 1} consecutive pairs out once as query"
            ),
            "production_checked": 0,
            "rotations_checked": 0,
            "production_failures": [],
            "rotation_failures": [],
        },
    }

    for band in BANDS:
        section = {
            "draws": 0,
            "self_check_failures": [],
            "strict_canonical_count": 0,
            "profiles": {name: 0 for name in profiles},
            "witness_counts": {name: 0 for name in witness_names},
            "rival_disagreements": {name: 0 for name in rival_names},
        }
        for seed in seeds:
            for sample_index in range(per_band):
                grid = module.generate(seed, sample_index, difficulty=band)
                section["draws"] += 1
                errors = list(module.self_check(grid))
                if errors:
                    section["self_check_failures"].append(
                        {
                            "seed": seed,
                            "sample_index": sample_index,
                            "reasons": errors,
                        }
                    )
                    continue
                if not module.strict_canonical_like(grid):
                    section["strict_canonical_count"] += 1
                observed = module.observe_overrides(grid)
                profile = observed.get("scene_profile")
                if profile not in section["profiles"]:
                    section["profiles"][str(profile)] = 0
                section["profiles"][str(profile)] += 1
                intended = module.rule_mirror(grid)
                for name, witness in module.SEMANTIC_WITNESSES.items():
                    if witness(grid):
                        section["witness_counts"][name] += 1
                for name, rival in module.SEMANTIC_RIVALS.items():
                    if rival(grid) != intended:
                        section["rival_disagreements"][name] += 1
        report["bands"][band] = section

    lessons = report["lessons"]
    width = demonstrations + 1
    for band in BANDS:
        for seed in seeds:
            for block in range(lesson_starts):
                start = block * width
                pairs = [_pair(module, seed, start + offset, band) for offset in range(width)]

                production_reasons = module.lesson_identifiable(
                    pairs[:demonstrations], pairs[demonstrations]
                )
                lessons["production_checked"] += 1
                if production_reasons:
                    lessons["production_failures"].append(
                        _failure(
                            seed=seed,
                            band=band,
                            start=start,
                            query_position=demonstrations,
                            reasons=production_reasons,
                        )
                    )

                for query_position, query in enumerate(pairs):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_position]
                    reasons = module.lesson_identifiable(demos, query)
                    lessons["rotations_checked"] += 1
                    if reasons:
                        lessons["rotation_failures"].append(
                            _failure(
                                seed=seed,
                                band=band,
                                start=start,
                                query_position=query_position,
                                reasons=reasons,
                            )
                        )

    report["ok"] = not any(
        (
            section["self_check_failures"]
            for section in report["bands"].values()
        )
    ) and not report["lessons"]["production_failures"] and not report["lessons"][
        "rotation_failures"
    ]
    return report


def _load_generator(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_seeds(text: str) -> tuple[int, ...]:
    try:
        seeds = tuple(int(part.strip()) for part in text.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("seeds must be comma-separated integers") from exc
    if not seeds:
        raise argparse.ArgumentTypeError("at least one seed is required")
    return seeds


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=_parse_seeds, default=(1301, 1302))
    parser.add_argument("--per-band", type=int, default=20)
    parser.add_argument("--lesson-starts", type=int, default=12)
    parser.add_argument("--demonstrations", type=int, default=DEFAULT_DEMONSTRATIONS)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    module = _load_generator(generator_path)
    report = run_probe(
        module,
        seeds=args.seeds,
        per_band=args.per_band,
        lesson_starts=args.lesson_starts,
        demonstrations=args.demonstrations,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
