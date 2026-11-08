#!/usr/bin/env python3
"""Source-bound probe for the 083ba0fc4534 consensus generator.

This is intentionally Racket-free and cheap.  It checks the generator's public
validator, an independent Python statement of the cell law, declared rivals,
canonical-shortcut claims, profiles, branches, and exact observable axes.  Use
the retained Racket battery and lesson census for authority-backed acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "083ba0fc4534"
BANDS = ("easy", "medium", "hard")
REQUIRED_BRANCHES = ("ab", "ax", "bx", "abc", "conflict")


def _load_generator(repo_root: Path):
    path = repo_root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_sha256(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return _sha256_bytes(payload)


def _panels(grid):
    height = len(grid)
    width = len(grid[0])
    if (width - 2) % 3:
        raise ValueError(f"width {width} is not three equal panels plus dividers")
    panel_w = (width - 2) // 3
    divider_2 = 2 * panel_w + 1
    bases = (0, panel_w + 1, divider_2 + 1)
    return [
        [[grid[row][base + col] for col in range(panel_w)] for row in range(height)]
        for base in bases
    ]


def _independent_output(grid):
    left, middle, right = _panels(grid)
    output = []
    for row in range(len(left)):
        out_row = []
        for col in range(len(left[0])):
            a, b, x = left[row][col], middle[row][col], right[row][col]
            if a != 0 and (a == b or a == x):
                out_row.append(a)
            elif b != 0 and b == x:
                out_row.append(b)
            else:
                out_row.append(0)
        output.append(out_row)
    return output


def _branches(grid) -> Counter[str]:
    left, middle, right = _panels(grid)
    counts: Counter[str] = Counter()
    for row in range(len(left)):
        for col in range(len(left[0])):
            a, b, x = left[row][col], middle[row][col], right[row][col]
            nonzero = [value for value in (a, b, x) if value != 0]
            if a != 0 and a == b == x:
                name = "abc"
            elif a != 0 and a == b and x != a:
                name = "ab"
            elif a != 0 and a == x and b != a:
                name = "ax"
            elif b != 0 and b == x and a != b:
                name = "bx"
            elif not nonzero:
                name = "empty"
            elif len(nonzero) >= 2 and len(set(nonzero)) == len(nonzero):
                name = "conflict"
            elif len(nonzero) == 1:
                name = "lone"
            else:
                name = "other"
            counts[name] += 1
    return counts


def build_report(*, per_band: int, seed_base: int) -> dict[str, Any]:
    if per_band < 1:
        raise ValueError("--per-band must be positive")
    repo_root = find_root(__file__)
    generator, generator_path = _load_generator(repo_root)

    self_check_failures: list[dict[str, Any]] = []
    mirror_mismatches: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    profile_counts: Counter[str] = Counter()
    branch_firings: Counter[str] = Counter()
    branch_minima = {name: None for name in REQUIRED_BRANCHES}
    rival_refutations: Counter[str] = Counter()
    axis_support: dict[str, dict[str, set[int]]] = {
        band: {name: set() for name in generator.AXES} for band in BANDS
    }

    for band_index, band in enumerate(BANDS):
        for offset in range(per_band):
            seed = seed_base + band_index * 100_000 + offset
            sample_index = offset
            grid = generator.generate(seed, sample_index, difficulty=band)
            grid_hash = _grid_sha256(grid)
            unique_inputs.add(grid_hash)

            errors = generator.self_check(grid, difficulty=band)
            if errors:
                self_check_failures.append(
                    {
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": list(errors),
                        "input_sha256": grid_hash,
                    }
                )

            independent = _independent_output(grid)
            if generator.rule_mirror(grid) != independent:
                mirror_mismatches.append(
                    {
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "input_sha256": grid_hash,
                    }
                )

            palette = {value for row in grid for value in row}
            profile = f"{len(grid)}x{len(grid[0])}/colors={len(palette)}"
            profile_counts[profile] += 1

            counts = _branches(grid)
            for name in REQUIRED_BRANCHES:
                if counts[name] > 0:
                    branch_firings[name] += 1
                current = branch_minima[name]
                branch_minima[name] = counts[name] if current is None else min(current, counts[name])

            observed = generator.observe_overrides(grid)
            for name, value in observed.items():
                if isinstance(value, int):
                    axis_support[band][name].add(value)

            for name, rival in generator.LESSON_COMPETITORS.items():
                if rival(grid) != independent:
                    rival_refutations[name] += 1

    canonical = canonical_pairs(TASK_ID, root=repo_root, labeled_only=True)
    shortcut_fit = {
        name: all(shortcut(pair["input"]) == pair["output"] for pair in canonical)
        for name, shortcut in generator.CANONICAL_SHORTCUTS.items()
    }

    samples = per_band * len(BANDS)
    return {
        "schema": "consensus-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": _sha256_bytes(generator_path.read_bytes()),
        "rule_hash": generator.RULE_HASH,
        "sampler": {
            "bands": list(BANDS),
            "per_band": per_band,
            "seed_base": seed_base,
            "seed_formula": "seed_base + band_index*100000 + offset; sample_index=offset",
        },
        "samples": samples,
        "unique_inputs": len(unique_inputs),
        "self_check_failures": self_check_failures,
        "mirror_mismatches": mirror_mismatches,
        "canonical_pairs": len(canonical),
        "canonical_shortcuts_fit_all_canonical": shortcut_fit,
        "rival_refutations": {
            name: rival_refutations[name] for name in sorted(generator.LESSON_COMPETITORS)
        },
        "required_branch_firings": {
            name: branch_firings[name] for name in REQUIRED_BRANCHES
        },
        "required_branch_minima": branch_minima,
        "profile_counts": dict(sorted(profile_counts.items())),
        "axis_support": {
            band: {name: sorted(values) for name, values in axes.items()}
            for band, axes in axis_support.items()
        },
        "limits": [
            "Python-only diagnostic; authoritative labels require the retained Racket checks.",
            "Finite declared-rival coverage is not a proof against undeclared hypotheses.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=10_000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(per_band=args.per_band, seed_base=args.seed_base)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": report["task_id"],
        "samples": report["samples"],
        "unique_inputs": report["unique_inputs"],
        "self_check_failures": len(report["self_check_failures"]),
        "mirror_mismatches": len(report["mirror_mismatches"]),
        "out": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
