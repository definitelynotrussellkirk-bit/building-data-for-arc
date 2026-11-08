"""Compact independent-oracle lesson audit for ``cf787ae40567``.

This is an authoring/review tool, not label authority.  It reads the selected
module's live rival declarations, builds cyclic four-demo/one-query windows,
and checks all outputs against ``reference_probe``'s independent plus-union
implementation.  The selected Racket rule remains authority and is exercised by
the normal battery/census commands.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from reference_probe import canonical_shortcuts_fit, intended_output, load_generator

BANDS = ("easy", "medium", "hard")


def _grid_digest(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_probe(*, seed_roots: Iterable[int], starts: Iterable[int]) -> dict:
    """Return a compact, JSON-serializable cyclic lesson audit report."""
    seeds = [int(value) for value in seed_roots]
    offsets = [int(value) for value in starts]
    if not seeds:
        raise ValueError("seed_roots must not be empty")
    if not offsets:
        raise ValueError("starts must not be empty")

    generator = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
    source = Path(generator.__file__).resolve()
    probe_source = Path(__file__).with_name("reference_probe.py").resolve()

    failures: list[dict] = []
    profile_counts: Counter[tuple[str, str | None]] = Counter()
    width_counts: Counter[int] = Counter()
    rival_refutations: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    lessons = 0
    pair_visits = 0

    for band in BANDS:
        for seed in seeds:
            for start in offsets:
                pairs = []
                for offset in range(5):
                    grid = generator.generate(seed, start + offset, difficulty=band)
                    pair_visits += 1
                    profile = generator.observe_overrides(grid).get("profile")
                    profile_counts[(band, profile)] += 1
                    expected = intended_output(grid)
                    actual = generator.rule_mirror(grid)
                    grammar_errors = generator.self_check(grid)
                    if actual != expected:
                        failures.append(
                            {
                                "kind": "independent_oracle_mismatch",
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "offset": offset,
                            }
                        )
                    if grammar_errors:
                        failures.append(
                            {
                                "kind": "grammar_reject",
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "offset": offset,
                                "errors": grammar_errors,
                            }
                        )
                    width_counts[len(expected[0])] += 1
                    unique_inputs.add(_grid_digest(grid))
                    pairs.append({"input": grid, "output": expected})

                demos, query = pairs[:4], pairs[4]
                reasons = generator.lesson_identifiable(demos, query)
                if reasons:
                    failures.append(
                        {
                            "kind": "unidentifiable_lesson",
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "reasons": reasons,
                        }
                    )
                for name, rival in generator.LESSON_COMPETITORS.items():
                    if all(rival(pair["input"]) == pair["output"] for pair in demos):
                        failures.append(
                            {
                                "kind": "declared_rival_survives",
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "rival": name,
                            }
                        )
                    else:
                        rival_refutations[name] += 1
                lessons += 1

    shortcut_fit = canonical_shortcuts_fit()
    if not all(shortcut_fit.values()):
        failures.append(
            {"kind": "declared_canonical_shortcut_does_not_fit", "values": shortcut_fit}
        )

    return {
        "schema": "cf787ae40567-independent-lesson-probe-v1",
        "task_id": generator.TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(probe_source.read_bytes()).hexdigest(),
        "bands": list(BANDS),
        "seed_roots": seeds,
        "cyclic_starts": offsets,
        "lessons": lessons,
        "pair_visits": pair_visits,
        "unique_inputs": len(unique_inputs),
        "profile_counts": {
            f"{band}:{profile}": count
            for (band, profile), count in sorted(profile_counts.items())
        },
        "output_widths_observed": sorted(width_counts),
        "canonical_shortcuts_fit": shortcut_fit,
        "rival_refutations": dict(sorted(rival_refutations.items())),
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "limits": [
            "Finite declared-rival and scheduled-window probe; not proof of universal induction.",
            "Uses an independent Python geometry oracle; Racket authority parity belongs to the standard battery.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64, help="seed roots 0..N-1")
    parser.add_argument("--starts", type=int, default=4, help="cyclic starts 0..N-1")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.starts < 1:
        parser.error("--seeds and --starts must be positive")

    report = run_probe(seed_roots=range(args.seeds), starts=range(args.starts))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "task_id": report["task_id"],
                "status": report["status"],
                "lessons": report["lessons"],
                "unique_inputs": report["unique_inputs"],
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
