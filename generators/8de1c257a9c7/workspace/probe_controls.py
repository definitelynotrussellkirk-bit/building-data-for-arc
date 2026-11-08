#!/usr/bin/env python3
"""Probe the generator's exact-control contract without private labels.

The report is intentionally JSON-serializable so a future reviewer can compare
control behavior across revisions without rerunning the full generator battery.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "8de1c257a9c7"
_INVALID_INTEGER_OVERRIDES = (
    ("grid_h", 13.9),
    ("grid_h", "13"),
    ("grid_w", 13.9),
    ("grid_w", "13"),
    ("n_reds", True),
    ("n_reds", 3.5),
    ("n_reds", "3"),
)


def runtime_search_paths(generator_path: str | Path) -> tuple[Path, ...]:
    """Return source-tree runtime roots needed to import the generator."""
    path = Path(generator_path).resolve()
    candidates: list[Path] = []
    for parent in path.parents:
        runtime = parent / "shared/runtime"
        if (runtime / "puzzle_generators").is_dir():
            candidates.append(runtime)
            break
    return tuple(candidates)


def _load_generator(path: Path):
    path = path.resolve()
    for runtime in reversed(runtime_search_paths(path)):
        runtime_text = str(runtime)
        if runtime_text not in sys.path:
            sys.path.insert(0, runtime_text)
    spec = importlib.util.spec_from_file_location(
        f"control_probe_generator_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _failure(
    failures: list[dict[str, Any]],
    check: str,
    *,
    seed: int | None = None,
    slot: int | None = None,
    axis: str | None = None,
    detail: str,
) -> None:
    row: dict[str, Any] = {"check": check, "detail": detail}
    if seed is not None:
        row["seed"] = seed
    if slot is not None:
        row["slot"] = slot
    if axis is not None:
        row["axis"] = axis
    failures.append(row)


def run_probe(
    generator_path: str | Path,
    *,
    seeds: Iterable[int] = (17, 421),
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Return a deterministic report for all declared schedule profiles."""
    path = Path(generator_path).resolve()
    generator = _load_generator(path)
    seed_values = tuple(int(seed) for seed in seeds)
    slots = tuple(int(slot) for slot in generator.SCHEDULE_PROFILES)
    failures: list[dict[str, Any]] = []
    counts = {
        "none_override_noop": 0,
        "same_value_override_identity": 0,
        "dimension_override_axis_isolation": 0,
        "invalid_integer_rejection": 0,
    }

    for seed in seed_values:
        for slot in slots:
            baseline = generator.generate(seed, slot, difficulty=difficulty)
            observed = generator.observe_overrides(baseline)

            for axis in generator.AXES:
                actual = generator.generate(
                    seed,
                    slot,
                    difficulty=difficulty,
                    **{axis: None},
                )
                counts["none_override_noop"] += 1
                if actual != baseline:
                    _failure(
                        failures,
                        "none_override_noop",
                        seed=seed,
                        slot=slot,
                        axis=axis,
                        detail="explicit None changed the scheduled grid",
                    )
            actual = generator.generate(
                seed,
                slot,
                difficulty=difficulty,
                **{axis: None for axis in generator.AXES},
            )
            counts["none_override_noop"] += 1
            if actual != baseline:
                _failure(
                    failures,
                    "none_override_noop",
                    seed=seed,
                    slot=slot,
                    detail="all-None override mapping changed the scheduled grid",
                )

            for axis, value in observed.items():
                actual = generator.generate(
                    seed,
                    slot,
                    difficulty=difficulty,
                    **{axis: value},
                )
                counts["same_value_override_identity"] += 1
                if actual != baseline:
                    _failure(
                        failures,
                        "same_value_override_identity",
                        seed=seed,
                        slot=slot,
                        axis=axis,
                        detail="pinning the observed value changed another draw",
                    )

            for axis, upper in (("grid_h", 22), ("grid_w", 22)):
                requested = upper if observed[axis] != upper else upper - 1
                changed = generator.generate(
                    seed,
                    slot,
                    difficulty=difficulty,
                    **{axis: requested},
                )
                after = generator.observe_overrides(changed)
                counts["dimension_override_axis_isolation"] += 1
                if after[axis] != requested:
                    _failure(
                        failures,
                        "dimension_override_axis_isolation",
                        seed=seed,
                        slot=slot,
                        axis=axis,
                        detail=f"requested {requested}, observed {after[axis]!r}",
                    )
                for other_axis in generator.AXES:
                    if other_axis == axis:
                        continue
                    if after[other_axis] != observed[other_axis]:
                        _failure(
                            failures,
                            "dimension_override_axis_isolation",
                            seed=seed,
                            slot=slot,
                            axis=axis,
                            detail=(
                                f"unpinned {other_axis} changed from "
                                f"{observed[other_axis]!r} to {after[other_axis]!r}"
                            ),
                        )

    # Type rejection does not depend on the schedule, so test each malformed
    # override once and keep the report count stable across seed sets.
    for axis, value in _INVALID_INTEGER_OVERRIDES:
        counts["invalid_integer_rejection"] += 1
        try:
            generator.generate(seed_values[0], slots[0], **{axis: value})
        except TypeError:
            pass
        except Exception as exc:  # wrong exception class is part of the contract
            _failure(
                failures,
                "invalid_integer_rejection",
                axis=axis,
                detail=f"raised {type(exc).__name__}, expected TypeError",
            )
        else:
            _failure(
                failures,
                "invalid_integer_rejection",
                axis=axis,
                detail=f"accepted coercive value {value!r}",
            )

    return {
        "schema": "arc-generator-control-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(path),
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "generator_version": str(generator.VERSION),
        "difficulty": difficulty,
        "seeds": list(seed_values),
        "schedule_profiles": list(slots),
        "schedule_slots_checked": len(seed_values) * len(slots),
        "checks": counts,
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generator", type=Path)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--difficulty", default="medium")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_probe(
        args.generator,
        seeds=tuple(args.seeds) if args.seeds else (17, 421),
        difficulty=args.difficulty,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
