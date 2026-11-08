#!/usr/bin/env python3
"""Reproduce the compact acceptance evidence for generator f7b828a70061.

Run from the packet with:

    python3 review.py run python3 generators/f7b828a70061/workspace/qualify.py

This is deliberately independent of the battery controller.  It checks the
canonical-fitting shortcut, generated witness coverage, deterministic replay,
strict validation, canonical profile signatures, and one joint exact-control
probe.  It does not replace the official check receipts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "f7b828a70061"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, _ = load_selected_generator(TASK, root=ROOT)
BANDS = ("easy", "medium", "hard")


def _profile(grid: list[list[int]]) -> str:
    colors = len({value for row in grid for value in row})
    return f"{len(grid)}x{len(grid[0])}/c{colors}"


def run_qualification(*, seed: int = 91, per_band: int = 20) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(per_band) is not int or per_band <= 0:
        raise ValueError("per_band must be a positive literal Python integer")

    rival = GEN.CANONICAL_SHORTCUTS["largest_bbox_area"]
    witness = GEN.SEMANTIC_WITNESSES["bbox_area_tie"]
    canon = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    canonical_passed = sum(rival(pair["input"]) == pair["output"] for pair in canon)

    count = strict_passed = ties = disagreements = deterministic = 0
    profiles: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []
    band_offsets = {"easy": 0, "medium": 10_000, "hard": 20_000}

    for band in BANDS:
        for index in range(per_band):
            draw_seed = seed + band_offsets[band] + index
            grid = GEN.generate(draw_seed, index, difficulty=band)
            replay = GEN.generate(draw_seed, index, difficulty=band)
            count += 1
            profiles[_profile(grid)] += 1

            strict_ok = not GEN.strict_canonical_like(grid)
            tie_ok = bool(witness(grid))
            disagreement_ok = rival(grid) != GEN.intended_output(grid)
            replay_ok = grid == replay
            strict_passed += int(strict_ok)
            ties += int(tie_ok)
            disagreements += int(disagreement_ok)
            deterministic += int(replay_ok)
            if not all((strict_ok, tie_ok, disagreement_ok, replay_ok)):
                failures.append({
                    "band": band,
                    "seed": draw_seed,
                    "sample_index": index,
                    "strict_ok": strict_ok,
                    "bbox_area_tie": tie_ok,
                    "rival_disagreed": disagreement_ok,
                    "deterministic": replay_ok,
                })

    requested = {
        "grid_h": 7,
        "grid_w": 9,
        "command": 5,
        "main_size": 8,
        "main_shape": "stair",
        "palette_size": 2,
    }
    probe = GEN.generate(seed, 9, difficulty="hard", **requested)
    observed = GEN.observe_overrides(probe)

    generator_sha256 = hashlib.sha256(Path(GENERATOR_PATH).read_bytes()).hexdigest()
    ok = (
        canonical_passed == len(canon)
        and count == strict_passed == ties == disagreements == deterministic
        and observed == requested
        and not failures
    )
    return {
        "schema": "f7b828a70061-qualification-v1",
        "task_id": TASK,
        "generator_sha256": generator_sha256,
        "seed": seed,
        "per_band": per_band,
        "ok": ok,
        "canonical_shortcut_fits": {
            "passed": canonical_passed,
            "total": len(canon),
        },
        "generated": {
            "count": count,
            "strict_passed": strict_passed,
            "bbox_area_tie": ties,
            "rival_disagreed": disagreements,
            "deterministic_replay": deterministic,
            "profiles": dict(sorted(profiles.items())),
            "failures": failures,
        },
        "override_probe": {
            "requested": requested,
            "observed": observed,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=91)
    parser.add_argument("--per-band", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_qualification(seed=args.seed, per_band=args.per_band)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
