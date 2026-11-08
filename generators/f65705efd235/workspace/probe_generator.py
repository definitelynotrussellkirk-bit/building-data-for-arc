#!/usr/bin/env python3
"""High-volume deterministic probe for the f65705efd235 generator.

This is intentionally independent of the battery orchestration.  It gives a
future reviewer one fast command that catches the two historical defects this
review found: silent object under-delivery and loss of canonical two-cell-thick
rectangles.  It also checks every named semantic witness/rival and every
three-example schedule window.

Run from the repository root:

    PYTHONPATH=shared/runtime python3 generators/f65705efd235/workspace/probe_generator.py \
        --draws-per-band 2000 --json-out /tmp/f65705efd235-probe.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "f65705efd235"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = HERE.parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            raw = [*row.get("train", []), row.get("test")]
            pairs = []
            for pair in raw:
                pairs.append(
                    {
                        "input": [[int(value) for value in text] for text in pair["input"]],
                        "output": [[int(value) for value in text] for text in pair["output"]],
                    }
                )
            return pairs
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def run(draws_per_band: int) -> dict[str, Any]:
    errors: list[str] = []
    canonical = _canonical_pairs()
    for index, pair in enumerate(canonical):
        findings = GEN.self_check(pair["input"])
        if findings:
            errors.append(f"canonical[{index}] rejected: {findings}")
        if GEN.rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"canonical[{index}] Python mirror mismatch")

    witness_hits = Counter({name: 0 for name in GEN.SEMANTIC_WITNESSES})
    rival_refutations = Counter({name: 0 for name in GEN.SEMANTIC_RIVALS})
    profiles = Counter()
    counts = Counter()
    colors = Counter()
    thin_hits = overlap_hits = strict_hits = 0
    generated = 0

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(draws_per_band):
            seed = 10_000_019 * (band_index + 1) + index * 7919
            sample_index = index * 37 + band_index
            try:
                grid = GEN.generate(seed, sample_index, difficulty=band)
            except Exception as exc:  # noqa: BLE001 - report exact generator crash
                errors.append(
                    f"generate({band}, seed={seed}, sample_index={sample_index}) "
                    f"raised {type(exc).__name__}: {exc}"
                )
                continue
            generated += 1
            findings = GEN.self_check(grid)
            if findings:
                errors.append(f"generated invalid {band}/{index}: {findings}")
                continue
            observed = GEN.observe_overrides(grid)
            profiles[(band, *observed.values())] += 1
            counts[observed["n_rects"]] += 1
            analysis = GEN._analysis(grid)
            colors.update(analysis["colors"])
            expected = GEN.rule_mirror(grid)
            if not GEN.strict_canonical_like(grid):
                strict_hits += 1
            thin = any(
                rect["rect_h"] == 2 or rect["rect_w"] == 2
                for rect in analysis["rectangles"]
            )
            overlap = any(
                analysis["rectangles"][i]["border"]
                & analysis["rectangles"][j]["border"]
                for i in range(len(analysis["rectangles"]))
                for j in range(i + 1, len(analysis["rectangles"]))
            )
            thin_hits += int(thin)
            overlap_hits += int(overlap)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                witness_hits[name] += int(bool(predicate(grid)))
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                rival_refutations[name] += int(rival(grid) != expected)

    # Exact boundary cross: this is the old silent-under-delivery repro.
    for band in ("easy", "medium", "hard"):
        for height in (7, 24):
            for width in (7, 24):
                for n_rects in (2, 6):
                    wanted = {"grid_h": height, "grid_w": width, "n_rects": n_rects}
                    grid = GEN.generate(314159, 2718, difficulty=band, **wanted)
                    observed = GEN.observe_overrides(grid)
                    if observed != wanted:
                        errors.append(
                            f"override under-delivery {band} wanted={wanted} observed={observed}"
                        )

    # Every contiguous 3-demo window over two full cycles must kill all rivals.
    pairs = []
    for index in range(12):
        grid = GEN.generate(8080, index, difficulty="hard")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    for start in range(9):
        reasons = GEN.lesson_identifiable(
            pairs[start : start + GEN.EXAMPLES_NEEDED],
            pairs[start + GEN.EXAMPLES_NEEDED],
        )
        if reasons:
            errors.append(f"lesson window {start} unidentifiable: {reasons}")

    for name, hits in witness_hits.items():
        if hits == 0:
            errors.append(f"semantic witness never fired: {name}")
    for name, hits in rival_refutations.items():
        if hits == 0:
            errors.append(f"semantic rival never refuted: {name}")
    if generated and thin_hits != generated:
        errors.append(f"thin canonical subcase missing in {generated - thin_hits}/{generated} draws")
    if generated and overlap_hits != generated:
        errors.append(f"overlap-order witness missing in {generated - overlap_hits}/{generated} draws")

    return {
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "draws_requested": draws_per_band * 3,
        "draws_generated": generated,
        "canonical_pairs_checked": len(canonical),
        "strict_hits": strict_hits,
        "thin_hits": thin_hits,
        "overlap_hits": overlap_hits,
        "rectangle_count_histogram": dict(sorted(counts.items())),
        "color_histogram": dict(sorted(colors.items())),
        "profile_histogram": {
            repr(key): count for key, count in sorted(profiles.items(), key=lambda item: repr(item[0]))
        },
        "witness_hits": dict(sorted(witness_hits.items())),
        "rival_refutations": dict(sorted(rival_refutations.items())),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws-per-band", type=int, default=2000)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.draws_per_band <= 0:
        parser.error("--draws-per-band must be positive")
    result = run(args.draws_per_band)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
