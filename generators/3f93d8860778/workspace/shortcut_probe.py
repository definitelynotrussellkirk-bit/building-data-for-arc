#!/usr/bin/env python3
"""Source-bound lesson probe for the selected span-fill generator.

The probe deliberately reads the generator's *actual* public rival declarations
instead of maintaining a second rival-name list.  It verifies that every
``CANONICAL_SHORTCUTS`` rule fits every usable canonical pair, samples each
band for concrete refutations, and exhausts every cyclic schedule start and
query rotation supported by the deterministic teaching period.

A finite pass is a regression certificate for the declared rivals, not proof of
universal rule identifiability.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _grid_sha(grid: list[list[int]]) -> str:
    return _sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_generator(path: Path):
    root = path.parents[2]
    runtime = root / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("selected_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


def _declarations(gen) -> dict[str, dict[str, Callable]]:
    result: dict[str, dict[str, Callable]] = {}
    for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        value = getattr(gen, name, None)
        if not isinstance(value, dict) or not value:
            raise ValueError(f"{name} must be a nonempty dictionary")
        bad = [key for key, fn in value.items() if not isinstance(key, str) or not callable(fn)]
        if bad:
            raise ValueError(f"{name} contains invalid entries: {bad!r}")
        result[name] = dict(value)
    return result


def _call(rival: Callable, grid: list[list[int]]) -> tuple[Any, str | None]:
    try:
        return rival([row[:] for row in grid]), None
    except Exception as exc:  # evidence, never an implicit refutation
        return None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--seed", type=int, default=930_001)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")

    generator_path = args.generator.resolve()
    gen, root = load_generator(generator_path)
    from reviewer_support import canonical_pairs, find_root

    declarations = _declarations(gen)
    canonical = canonical_pairs(gen.TASK_ID, root=find_root(generator_path))
    errors: list[str] = []

    canonical_fit: dict[str, bool] = {}
    canonical_failures: dict[str, list[dict[str, Any]]] = {}
    for name, rival in declarations["CANONICAL_SHORTCUTS"].items():
        failures = []
        for pair_index, pair in enumerate(canonical):
            actual, failure = _call(rival, pair["input"])
            if failure or actual != pair["output"]:
                failures.append({
                    "pair_index": pair_index,
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "source_pair_index": pair["pair_index"],
                    "error": failure,
                    "input_sha256": _grid_sha(pair["input"]),
                    "expected_sha256": _grid_sha(pair["output"]),
                    "actual_sha256": _grid_sha(actual) if isinstance(actual, list) else None,
                })
        canonical_fit[name] = not failures
        if failures:
            canonical_failures[name] = failures
            errors.append(f"canonical shortcut {name!r} does not fit every canonical pair")

    band_reports: dict[str, Any] = {}
    shortcut_refutations = Counter()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        unique_inputs: set[str] = set()
        profile_counts = Counter()
        guard_signatures = Counter()
        declaration_stats: dict[str, dict[str, dict[str, Any]]] = {
            scope: {
                name: {"agreements": 0, "refutations": 0, "errors": 0, "first_refutation": None}
                for name in rivals
            }
            for scope, rivals in declarations.items()
        }
        for sample_index in range(args.per_band):
            seed = args.seed + 100_000 * band_index
            grid = gen.generate(seed, sample_index, difficulty=band)
            expected = gen.rule_mirror(grid)
            unique_inputs.add(_grid_sha(grid))
            profile_counts[gen.schedule_profile(seed, sample_index, band)] += 1
            info = gen._analysis(grid)
            signature = tuple(sorted(Counter(d["kind"] for d in info["decoys"]).items()))
            guard_signatures[str(signature)] += 1

            for scope, rivals in declarations.items():
                for name, rival in rivals.items():
                    actual, failure = _call(rival, grid)
                    stats = declaration_stats[scope][name]
                    if failure:
                        stats["errors"] += 1
                        if stats["first_refutation"] is None:
                            stats["first_refutation"] = {
                                "sample_index": sample_index,
                                "kind": "error",
                                "error": failure,
                                "input_sha256": _grid_sha(grid),
                            }
                    elif actual == expected:
                        stats["agreements"] += 1
                    else:
                        stats["refutations"] += 1
                        if scope == "CANONICAL_SHORTCUTS":
                            shortcut_refutations[name] += 1
                        if stats["first_refutation"] is None:
                            stats["first_refutation"] = {
                                "sample_index": sample_index,
                                "kind": "different_output",
                                "input": grid,
                                "expected": expected,
                                "rival": actual,
                            }

        band_reports[band] = {
            "samples": args.per_band,
            "unique_inputs": len(unique_inputs),
            "profiles": dict(sorted(profile_counts.items())),
            "guard_signatures": dict(sorted(guard_signatures.items())),
            "declarations": declaration_stats,
        }

    for name in declarations["CANONICAL_SHORTCUTS"]:
        if shortcut_refutations[name] == 0:
            errors.append(f"canonical shortcut {name!r} was never refuted in sampled defaults")

    examples_needed = int(getattr(gen, "EXAMPLES_NEEDED", 3))
    profiles = tuple(getattr(gen, "SCHEDULE_PROFILES", ()))
    period = len(profiles) or 1
    cyclic_failures: list[dict[str, Any]] = []
    cyclic_checked = 0
    cyclic_seed = args.seed + 777_777
    competitors = declarations["LESSON_COMPETITORS"]
    for band in ("easy", "medium", "hard"):
        for start in range(period):
            pairs = []
            for sample_index in range(start, start + examples_needed + 1):
                grid = gen.generate(cyclic_seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                survivors = []
                rival_errors = []
                for name, rival in competitors.items():
                    survived = True
                    for pair in demos:
                        actual, failure = _call(rival, pair["input"])
                        if failure:
                            rival_errors.append({"rival": name, "error": failure})
                            survived = False
                            break
                        if actual != pair["output"]:
                            survived = False
                            break
                    if survived:
                        survivors.append(name)
                hook_reasons = gen.lesson_identifiable(demos, query)
                cyclic_checked += 1
                if survivors or rival_errors or hook_reasons:
                    cyclic_failures.append({
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "survivors": survivors,
                        "rival_errors": rival_errors,
                        "hook_reasons": hook_reasons,
                        "profiles": [
                            gen.schedule_profile(cyclic_seed, start + offset, band)
                            for offset in range(examples_needed + 1)
                        ],
                    })
    if cyclic_failures:
        errors.append(f"{len(cyclic_failures)} cyclic query rotation(s) remain ambiguous or errored")

    report = {
        "schema": "3f93d8860778-shortcut-probe-v2",
        "task_id": gen.TASK_ID,
        "generator": str(generator_path),
        "generator_sha256": _sha_bytes(generator_path.read_bytes()),
        "version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "per_band": args.per_band,
        "declarations": {scope: sorted(rivals) for scope, rivals in declarations.items()},
        "canonical_pairs": len(canonical),
        "canonical_rival_fit": canonical_fit,
        "canonical_failures": canonical_failures,
        "bands": band_reports,
        "cyclic_rotations": {
            "policy": f"{examples_needed} demos from every {examples_needed + 1}-pair bundle; every held-out query",
            "schedule_period": period,
            "checked": cyclic_checked,
            "failures": cyclic_failures,
        },
        "errors": errors,
        "status": "pass" if not errors else "fail",
        "limits": [
            "Finite declared-rival regression only; unmodeled rules may remain.",
            "Default schedule and exact public declarations are tested; arbitrary override lessons are not promised identifiable.",
        ],
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
