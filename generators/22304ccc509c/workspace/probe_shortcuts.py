#!/usr/bin/env python3
"""Reproducible task-local shortcut and cyclic-lesson probe.

This is deliberately independent of the Racket runner: it checks the generator's
published Python mirror, declared rivals, canonical fit, witness frequencies, and
all query rotations over deterministic cyclic windows.  Pair it with the official
battery/census for authoritative Racket-labelled evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "22304ccc509c"
BANDS = ("easy", "medium", "hard")


def load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HERE.parent / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("probe_22304ccc509c", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def digest_grid(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def episode(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--starts", type=int, default=25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 1 or args.starts < 1:
        parser.error("--per-band and --starts must be positive")

    gen, source = load_generator()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    canonical_fit = {}
    errors: list[str] = []
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        canonical_fit[name] = {"fits": fits, "pairs": len(pairs)}
        if fits != len(pairs):
            errors.append(f"declared canonical shortcut {name} fits {fits}/{len(pairs)}")

    per_band = {}
    for band in BANDS:
        witness_hits = Counter()
        rival_disagreements = Counter()
        profiles = Counter()
        unique = set()
        invalid = 0
        for index in range(args.per_band):
            seed = int(
                hashlib.sha256(
                    f"22304ccc509c-shortcut-probe-v1:{band}:{index}".encode()
                ).hexdigest()[:8],
                16,
            )
            grid = gen.generate(seed, index, difficulty=band)
            unique.add(digest_grid(grid))
            invalid += int(bool(gen.self_check(grid, difficulty=band)))
            profiles[gen.schedule_profile(seed, index, difficulty=band)] += 1
            truth = gen.rule_mirror(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += int(bool(witness(grid)))
            for name, rival in gen.SEMANTIC_RIVALS.items():
                rival_disagreements[name] += int(rival(grid) != truth)
        per_band[band] = {
            "draws": args.per_band,
            "unique_inputs": len(unique),
            "self_check_failures": invalid,
            "profiles": dict(sorted(profiles.items())),
            "witness_hits": dict(sorted(witness_hits.items())),
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
        }
        if invalid:
            errors.append(f"{band}: {invalid} generated input(s) failed self_check")
        for name in gen.SEMANTIC_WITNESSES:
            if witness_hits[name] != args.per_band:
                errors.append(
                    f"{band}: witness {name} fired {witness_hits[name]}/{args.per_band}"
                )
        for name in gen.SEMANTIC_RIVALS:
            if rival_disagreements[name] != args.per_band:
                errors.append(
                    f"{band}: rival {name} differed {rival_disagreements[name]}/{args.per_band}"
                )

    rotation_checks = 0
    ambiguous_rotations = []
    lesson_size = int(gen.EXAMPLES_NEEDED) + 1
    for band in BANDS:
        for start in range(args.starts):
            seed = int(
                hashlib.sha256(
                    f"22304ccc509c-window-probe-v1:{band}:{start}".encode()
                ).hexdigest()[:8],
                16,
            )
            pairs_window = [
                episode(gen, gen.generate(seed, start + offset, difficulty=band))
                for offset in range(lesson_size)
            ]
            for query_index, query in enumerate(pairs_window):
                demos = pairs_window[:query_index] + pairs_window[query_index + 1 :]
                reasons = gen.lesson_identifiable(demos, query)
                rotation_checks += 1
                if reasons:
                    ambiguous_rotations.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )
    if ambiguous_rotations:
        errors.append(f"{len(ambiguous_rotations)} cyclic query rotation(s) ambiguous")

    report = {
        "schema": "22304ccc509c-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "parameters": {"per_band": args.per_band, "starts": args.starts},
        "canonical_shortcut_fit": canonical_fit,
        "per_band": per_band,
        "cyclic_lessons": {
            "lesson_size": lesson_size,
            "rotation_checks": rotation_checks,
            "ambiguous": len(ambiguous_rotations),
            "examples": ambiguous_rotations[:10],
        },
        "errors": errors,
        "limits": [
            "Uses the published Python mirror; the official Racket battery/census remains authoritative.",
            "Finite declared-rival testing is not proof against undeclared hypotheses.",
        ],
        "status": "pass" if not errors else "fail",
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
