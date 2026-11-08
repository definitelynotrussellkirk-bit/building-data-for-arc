#!/usr/bin/env python3
"""Task-local cyclic-window audit for eb3171637821.

This complements the shared source-bound lesson census by cheaply checking every
consecutive query rotation in a bounded period.  It uses the independent
geometry oracle from ``reference_probe`` and iterates the generator's live
``LESSON_COMPETITORS`` declarations rather than copying rival names.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_probe import geometry_output, load_generator


def grid_hash(grid):
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def audit(*, seeds, starts, n_demos):
    gen = load_generator()
    rivals = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    if not rivals:
        raise RuntimeError("generator declares no LESSON_COMPETITORS")

    rows = []
    for band in ("easy", "medium", "hard"):
        for seed in range(seeds):
            for start in range(starts):
                grids = [
                    gen.generate(seed, start + offset, difficulty=band)
                    for offset in range(n_demos + 1)
                ]
                expected = [geometry_output(grid) for grid in grids]
                for name, rival in rivals.items():
                    rival_outputs = [rival(grid) for grid in grids]
                    demo_fit = all(
                        predicted == actual
                        for predicted, actual in zip(rival_outputs[:-1], expected[:-1])
                    )
                    query_differs = rival_outputs[-1] != expected[-1]
                    rows.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "rival": name,
                            "demo_fit": demo_fit,
                            "query_differs": query_differs,
                            "ambiguous": demo_fit and query_differs,
                            "input_sha256": [grid_hash(grid) for grid in grids],
                        }
                    )

    ambiguous = [row for row in rows if row["ambiguous"]]
    return {
        "schema": "eb3171637821-cyclic-lesson-audit-v1",
        "generator_sha256": hashlib.sha256(
            Path(gen.__file__).read_bytes()
        ).hexdigest(),
        "generator_version": gen.VERSION,
        "n_demos": n_demos,
        "seeds": seeds,
        "starts_per_seed": starts,
        "lessons": seeds * starts * 3,
        "rivals": sorted(rivals),
        "ambiguous_count": len(ambiguous),
        "status": "pass" if not ambiguous else "ambiguous",
        "ambiguous": ambiguous,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--n-demos", type=int, default=3)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(seeds=args.seeds, starts=args.starts, n_demos=args.n_demos)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
