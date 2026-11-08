#!/usr/bin/env python3
"""Verify declared shortcuts/rivals and retain source-bound counterexamples.

The probe discovers rules from the generator's live ``CANONICAL_SHORTCUTS``
and ``LESSON_COMPETITORS`` declarations.  It never copies a rival-name list.
Each retained witness is checked against the independent Python reconstruction
and the selected Racket authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Callable

from reference_probe import (
    GENERATOR_HOME,
    TASK_ID,
    canonical_pairs,
    load_generator,
    nested_palette_output,
    observed,
    racket_outputs,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rules(module) -> dict[str, Callable]:
    combined: dict[str, Callable] = {}
    for declaration in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        value = getattr(module, declaration, {})
        if not isinstance(value, dict):
            raise TypeError(f"{declaration} must be a dict")
        for name, fn in value.items():
            if not callable(fn):
                raise TypeError(f"{declaration}[{name!r}] is not callable")
            previous = combined.get(str(name))
            if previous is not None and previous is not fn:
                raise ValueError(f"rival {name!r} has conflicting declarations")
            combined[str(name)] = fn
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-draws", type=int, default=300,
                        help="ordinary draws scanned per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.max_draws < 1:
        parser.error("--max-draws must be positive")

    module = load_generator()
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    rules = _rules(module)
    pairs = canonical_pairs()

    canonical_results: dict[str, dict] = {}
    failures: list[str] = []
    for name, shortcut in shortcuts.items():
        matches = []
        errors = []
        for index, pair in enumerate(pairs):
            try:
                matches.append(shortcut(pair["input"]) == pair["output"])
            except Exception as exc:
                matches.append(False)
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        canonical_results[name] = {
            "usable_pairs": len(pairs),
            "matches": sum(matches),
            "fits_every_canonical_pair": bool(matches) and all(matches),
            "errors": errors,
        }
        if not matches or not all(matches):
            failures.append(f"declared canonical shortcut {name!r} does not fit canonical")

    witnesses: dict[str, dict] = {}
    bands = ("easy", "medium", "hard")
    scanned = 0
    for band_index, band in enumerate(bands):
        for index in range(args.max_draws):
            seed = 19001 + band_index * 100000 + index * 97
            sample_index = index
            grid = module.generate(seed, sample_index, difficulty=band)
            intended = nested_palette_output(grid)
            scanned += 1
            for name, rival in rules.items():
                if name in witnesses:
                    continue
                rival_output = rival(grid)
                if rival_output != intended:
                    witnesses[name] = {
                        "task_id": TASK_ID,
                        "rule_hash": module.RULE_HASH,
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "overrides": {},
                        "observed_axes": observed(grid),
                        "schedule_profile": module.schedule_profile(
                            seed, sample_index, difficulty=band
                        ) if callable(getattr(module, "schedule_profile", None)) else None,
                        "input": grid,
                        "independent_expected_output": intended,
                        "rival_output": rival_output,
                    }
            if len(witnesses) == len(rules):
                break
        if len(witnesses) == len(rules):
            break

    missing = sorted(set(rules) - set(witnesses))
    if missing:
        failures.append(f"no generated counterexample found for rivals: {missing}")

    ordered_names = sorted(witnesses)
    grids = [witnesses[name]["input"] for name in ordered_names]
    try:
        authoritative = racket_outputs(grids) if grids else []
    except Exception as exc:
        authoritative = []
        failures.append(f"Racket authority check failed: {type(exc).__name__}: {exc}")

    for name, output in zip(ordered_names, authoritative):
        row = witnesses[name]
        row["racket_output"] = output
        row["racket_matches_independent"] = (
            output == row["independent_expected_output"]
        )
        if not row["racket_matches_independent"]:
            failures.append(f"independent oracle disagrees with Racket for {name}")

    strongest_name = next(iter(shortcuts), None)
    report = {
        "schema": f"{TASK_ID}-declared-shortcut-probe-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "generator_sha256": _sha(GENERATOR_HOME / "generator.py"),
        "probe_sha256": _sha(Path(__file__)),
        "rule_hash": module.RULE_HASH,
        "declaration_sources": ["CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"],
        "declared_canonical_shortcuts": sorted(shortcuts),
        "declared_rules_tested": sorted(rules),
        "canonical_fit": canonical_results,
        "scan": {
            "sampler": "ordinary generate(seed, sample_index, difficulty=band)",
            "bands": list(bands),
            "max_draws_per_band": args.max_draws,
            "draws_examined_until_all_found": scanned,
        },
        "witnesses": witnesses,
        "strongest_shortcut": {
            "name": strongest_name,
            "basis": (
                "declared in CANONICAL_SHORTCUTS and fits every usable canonical pair"
                if strongest_name is not None else None
            ),
            "witness": witnesses.get(strongest_name) if strongest_name else None,
        },
        "failures": failures,
    }
    args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.out.resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "declared_rules_tested": report["declared_rules_tested"],
        "canonical_fit": canonical_results,
        "draws_examined": scanned,
        "output": str(args.out.resolve()),
    }, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
