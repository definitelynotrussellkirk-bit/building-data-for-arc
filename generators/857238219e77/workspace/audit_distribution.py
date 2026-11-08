#!/usr/bin/env python3
"""Reproducible deep audit for generator 857238219e77.

This is reviewer tooling, not label authority.  It exhausts the declared joint
control space, probes default lessons and every held-out query rotation against
the generator's own declared rivals, and checks a bounded batch against both an
independent Python transcription and the canonical Racket program.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

from reference_probe import (canonical_pairs, intended_output, load_generator,
                             observed, racket_outputs)

BANDS = (None, "easy", "medium", "hard")


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def run() -> dict:
    gen = load_generator()
    source = Path(gen.__file__).resolve()
    controls = {
        "grid_h": range(6, 16),
        "grid_w": range(8, 18),
        "target_count": range(1, 6),
        "n_distinct_colors": (2, 3, 4),
        "edge_side": ("left", "right"),
    }
    failures = []
    generated = 0
    parity_grids = [pair["input"] for pair in canonical_pairs()]
    for band_index, band in enumerate(BANDS):
        for index, values in enumerate(itertools.product(*controls.values())):
            requested = dict(zip(controls, values))
            try:
                grid = gen.generate(857238 + band_index, index,
                                    difficulty=band, **requested)
                errors = gen.self_check(grid)
                realized = gen.observe_overrides(grid)
                if errors or realized != requested:
                    failures.append({
                        "band": band, "index": index, "requested": requested,
                        "realized": realized, "self_check": errors,
                    })
                if len(parity_grids) < 68 and index % 193 == 0:
                    parity_grids.append(grid)
            except Exception as exc:  # fail loud in retained report
                failures.append({
                    "band": band, "index": index, "requested": requested,
                    "exception": f"{type(exc).__name__}: {exc}",
                })
            generated += 1

    default_counts = {}
    lesson_failures = []
    retained_pairs = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        stats = Counter()
        unique = set()
        pairs = []
        for index in range(400):
            grid = gen.generate(20261005 + band_index, index, difficulty=band)
            out = intended_output(grid)
            obs = observed(grid)
            unique.add(digest(grid))
            stats[f"shape:{obs['grid_h']}x{obs['grid_w']}"] += 1
            stats[f"targets:{obs['target_count']}"] += 1
            stats[f"colors:{obs['n_distinct_colors']}"] += 1
            stats[f"edge:{obs['edge_side']}"] += 1
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                stats[f"witness:{name}"] += int(bool(predicate(grid)))
            for name, rival in gen.LESSON_COMPETITORS.items():
                if rival(grid) == out:
                    lesson_failures.append({
                        "kind": "single_pair_rival_survived", "band": band,
                        "sample_index": index, "rival": name,
                    })
            pairs.append({"input": grid, "output": out})
            if len(retained_pairs) < 64 and index % 19 == 0:
                retained_pairs.append(grid)
        # Exhaust every cyclic four-pair window and each query position.
        for start in range(len(pairs)):
            window = [pairs[(start + offset) % len(pairs)] for offset in range(4)]
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(window) if i != query_index]
                reasons = gen.lesson_identifiable(demos, window[query_index])
                if reasons:
                    lesson_failures.append({
                        "kind": "rotation_not_identifiable", "band": band,
                        "start": start, "query_index": query_index,
                        "reasons": reasons,
                    })
        default_counts[band] = {
            "samples": len(pairs), "unique_inputs": len(unique),
            "histogram": dict(sorted(stats.items())),
            "cyclic_windows": len(pairs), "query_rotations": len(pairs) * 4,
        }

    canonical_shortcuts = {}
    canonical = canonical_pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        canonical_shortcuts[name] = all(
            rival(pair["input"]) == pair["output"] for pair in canonical)

    parity_grids.extend(retained_pairs[:max(0, 68 - len(parity_grids))])
    racket = racket_outputs(parity_grids)
    expected = [intended_output(grid) for grid in parity_grids]
    parity_failures = [
        {"index": i, "input_hash": digest(grid),
         "expected_hash": digest(expected[i]), "racket_hash": digest(racket[i])}
        for i, grid in enumerate(parity_grids) if racket[i] != expected[i]
    ]

    return {
        "schema": "857238219e77_distribution_audit/1",
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "version": gen.VERSION,
        "declared_rule_hash": gen.RULE_HASH,
        "joint_control_audit": {
            "bands": list(BANDS), "tuples_per_band": 3000,
            "generated": generated, "failures": failures,
        },
        "default_lesson_audit": {
            "samples_per_band": 400,
            "window_size": 4, "demos_per_rotation": 3,
            "bands": default_counts, "failures": lesson_failures,
        },
        "canonical_shortcuts_fit_all_pairs": canonical_shortcuts,
        "racket_parity": {
            "grids": len(parity_grids), "failures": parity_failures,
        },
        "status": "pass" if not failures and not lesson_failures
                  and not parity_failures and all(canonical_shortcuts.values())
                  else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = run()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {
        "status": report["status"],
        "generator_sha256": report["generator_sha256"],
        "joint_draws": report["joint_control_audit"]["generated"],
        "joint_failures": len(report["joint_control_audit"]["failures"]),
        "lesson_rotations": sum(
            band["query_rotations"]
            for band in report["default_lesson_audit"]["bands"].values()),
        "lesson_failures": len(report["default_lesson_audit"]["failures"]),
        "racket_parity_grids": report["racket_parity"]["grids"],
        "racket_parity_failures": len(report["racket_parity"]["failures"]),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
