"""Independent replay probe for the 4a9e2bc51201 reflection curriculum.

This tool is supplementary evidence, not a label authority.  It uses a small
independent Python transcription of the published behavior, reads canonical
pairs through ``reviewer_support``, and discovers semantic declarations from the
selected generator instead of duplicating their names.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs, find_root

TASK = "4a9e2bc51201"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
DEFAULT_BANDS = ("easy", "medium", "hard")


def load_generator(path: str | Path | None = None):
    selected = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("audited_reflection_generator", selected)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, selected


def oracle(grid):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not dividers:
        return out
    divider = dividers[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5) or c == divider:
                continue
            mirror = 2 * divider - c
            if 0 <= mirror < w and out[r][mirror] == 0:
                out[r][mirror] = value
    return out


def _digest(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def _pair(grid):
    return {"input": grid, "output": oracle(grid)}


def run_audit(
    *, count: int = 100, bands: Iterable[str] = DEFAULT_BANDS,
    generator_path: str | Path | None = None,
) -> dict:
    if type(count) is not int or count < 1:
        raise ValueError("count must be a positive integer")
    selected_bands = tuple(bands)
    if not selected_bands or any(b not in DEFAULT_BANDS for b in selected_bands):
        raise ValueError(f"bands must be a nonempty subset of {DEFAULT_BANDS}")

    generator, source = load_generator(generator_path)
    canonical = canonical_pairs(TASK, root=ROOT)
    canonical_profiles = {_profile(pair["input"]) for pair in canonical}
    canonical_failures = []
    accepted = parity = 0
    for pair in canonical:
        findings = generator.self_check(deepcopy(pair["input"]))
        accepted += not findings
        parity += oracle(pair["input"]) == pair["output"]
        if findings or oracle(pair["input"]) != pair["output"]:
            canonical_failures.append({
                "variant": pair["variant"], "split": pair["split"],
                "pair_index": pair["pair_index"], "self_check": findings,
                "oracle_matches": oracle(pair["input"]) == pair["output"],
            })

    per_band = {}
    overall_pass = not canonical_failures
    for band in selected_bands:
        unique = set()
        shapes = set()
        profile_counts: Counter[str] = Counter()
        exact_hits = 0
        self_errors = nondeterministic = identity = 0
        witness_hits = Counter()
        rival_disagreements = Counter()
        lesson_windows = lesson_failures = 0

        for index in range(count):
            seed = 50_000 + index
            sample_index = index * 7 + 3
            grid = generator.generate(seed, sample_index, difficulty=band)
            replay = generator.generate(seed, sample_index, difficulty=band)
            nondeterministic += grid != replay
            findings = generator.self_check(deepcopy(grid))
            self_errors += bool(findings)
            intended = oracle(grid)
            identity += intended == grid
            unique.add(_digest(grid))
            observed = generator.observe_overrides(grid)
            shapes.add((observed["grid_h"], observed["grid_w"]))
            profile_counts[generator.schedule_profile(seed, sample_index, band)] += 1
            exact_hits += _profile(grid) in canonical_profiles
            for name, predicate in generator.SEMANTIC_WITNESSES.items():
                witness_hits[name] += bool(predicate(deepcopy(grid)))
            for name, rival in generator.SEMANTIC_RIVALS.items():
                rival_disagreements[name] += rival(deepcopy(grid)) != intended

        # Consecutive production-style windows.  The ordinary sampler makes
        # every example individually counterfactual-rich, but this catches a
        # future schedule change that accidentally leaves a query-changing rival.
        for start in range(12):
            seed = 90_000 + start
            demos = []
            for offset in range(generator.EXAMPLES_NEEDED):
                demos.append(_pair(generator.generate(
                    seed, start + offset, difficulty=band
                )))
            query_grid = generator.generate(
                seed, start + generator.EXAMPLES_NEEDED, difficulty=band
            )
            reasons = generator.lesson_identifiable(demos, _pair(query_grid))
            lesson_windows += 1
            lesson_failures += bool(reasons)

        row = {
            "samples": count,
            "self_check_errors": self_errors,
            "nondeterministic": nondeterministic,
            "identity_outputs": identity,
            "unique_inputs": len(unique),
            "distinct_shapes": len(shapes),
            "exact_canonical_profile_hits": exact_hits,
            "schedule_profiles": dict(sorted(profile_counts.items())),
            "witness_hits": {name: witness_hits[name]
                             for name in sorted(generator.SEMANTIC_WITNESSES)},
            "rival_disagreement_samples": {
                name: rival_disagreements[name]
                for name in sorted(generator.SEMANTIC_RIVALS)
            },
            "lesson_windows": lesson_windows,
            "lesson_failures": lesson_failures,
        }
        row_pass = (
            self_errors == nondeterministic == identity == lesson_failures == 0
            and len(unique) == count
            and exact_hits > 0
            and all(v > 0 for v in witness_hits.values())
            and all(v == count for v in rival_disagreements.values())
        )
        row["passed"] = row_pass
        overall_pass &= row_pass
        per_band[band] = row

    return {
        "schema": "4a9e2bc51201-reflection-audit-v1",
        "status": "pass" if overall_pass else "fail",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "sampling": {
            "count_per_band": count,
            "seed_formula": "50000 + index",
            "sample_index_formula": "index * 7 + 3",
            "lesson_windows_per_band": 12,
        },
        "canonical": {
            "pairs": len(canonical),
            "accepted": accepted,
            "oracle_matches": parity,
            "profiles": sorted(canonical_profiles),
            "failures": canonical_failures,
        },
        "per_band": per_band,
        "limits": (
            "Finite checks against the generator's declared rivals do not prove "
            "universal identifiability; the selected Racket program remains the authority."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100, help="samples per band")
    parser.add_argument("--bands", nargs="+", choices=DEFAULT_BANDS,
                        default=list(DEFAULT_BANDS))
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_audit(count=args.count, bands=args.bands,
                       generator_path=args.generator)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
