#!/usr/bin/env python3
"""Source-bound semantic/override probe for generator 9af68e46cf69.

This is intentionally task-local.  It discovers the selected generator via the
portable reviewer API, checks every labeled canonical pair, then samples each
published difficulty band against all declared witnesses and rivals.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9af68e46cf69"
BANDS = ("easy", "medium", "hard")


def run_probe(*, per_band: int = 8) -> dict:
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive literal integer")

    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    errors: list[str] = []

    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    for index, pair in enumerate(pairs):
        check = list(gen.self_check(pair["input"]))
        if check:
            errors.append(f"canonical pair {index} rejected: {check}")
        if gen._apply_rule(pair["input"]) != pair["output"]:
            errors.append(f"canonical pair {index} disagrees with Python oracle")

    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    rival_disagreements = {name: 0 for name in gen.SEMANTIC_RIVALS}
    generated_samples = 0
    samples = []

    for band_index, band in enumerate(BANDS):
        for offset in range(per_band):
            seed = band_index * 100_000 + offset
            sample_index = 37 + offset * 101
            grid = gen.generate(seed, sample_index, difficulty=band)
            generated_samples += 1
            check = list(gen.self_check(grid, difficulty=band))
            if check:
                errors.append(
                    f"generated {band} seed={seed} sample={sample_index} rejected: {check}"
                )
            selected = gen._apply_rule(grid)
            sample_witnesses = []
            sample_rivals = []
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    witness_hits[name] += 1
                    sample_witnesses.append(name)
                else:
                    errors.append(
                        f"generated {band} seed={seed} lacks witness {name!r}"
                    )
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if rival(grid) != selected:
                    rival_disagreements[name] += 1
                    sample_rivals.append(name)
                else:
                    errors.append(
                        f"generated {band} seed={seed} does not refute rival {name!r}"
                    )
            observed = gen.observe_overrides(grid)
            samples.append(
                {
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "observed": observed,
                    "witnesses": sorted(sample_witnesses),
                    "refuted_rivals": sorted(sample_rivals),
                }
            )

    return {
        "schema": "arcpuzzles-task-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(Path(source).resolve()),
        "generator_sha256": source_sha256,
        "rule_hash": gen.RULE_HASH,
        "bands": list(BANDS),
        "per_band": per_band,
        "canonical_pairs": len(pairs),
        "generated_samples": generated_samples,
        "witness_hits": witness_hits,
        "rival_disagreements": rival_disagreements,
        "errors": errors,
        "passed": not errors,
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(per_band=args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
