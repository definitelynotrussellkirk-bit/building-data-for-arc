"""Independent task-local oracle and diagnostics for 9000d0ea6484."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from itertools import permutations
from pathlib import Path

TASK_ID = "9000d0ea6484"
STARTS = (0, 5, 10, 15)
INTENDED_ORDER = (2, 3, 0, 1)
MANDATORY_SIGNATURES = frozenset({
    frozenset(),
    frozenset({0}), frozenset({1}), frozenset({2}), frozenset({3}),
    frozenset({0, 1}), frozenset({0, 2}), frozenset({0, 3}),
    frozenset({1, 2}), frozenset({1, 3}), frozenset({2, 3}),
})


def load_generator(path: str | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or Path(__file__).resolve().parents[1] / "generator.py")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_priority(grid, order=INTENDED_ORDER):
    return [
        [
            next((grid[r][STARTS[section] + c] for section in order
                  if grid[r][STARTS[section] + c] != 0), 0)
            for c in range(4)
        ]
        for r in range(4)
    ]


def signatures(grid):
    return [
        frozenset(section for section in range(4)
                  if grid[r][STARTS[section] + c] != 0)
        for r in range(4)
        for c in range(4)
    ]


def section_colors(grid):
    colors = []
    for start in STARTS:
        seen = {grid[r][start + c] for r in range(4) for c in range(4)
                if grid[r][start + c] != 0}
        if len(seen) != 1:
            raise ValueError(f"section at {start} has colors {sorted(seen)}")
        colors.append(next(iter(seen)))
    return tuple(colors)


def observed(grid):
    sigs = signatures(grid)
    extras = sigs.copy()
    for required in MANDATORY_SIGNATURES:
        extras.remove(required)
    return {
        "sec0_color": section_colors(grid)[0],
        "sec1_color": section_colors(grid)[1],
        "sec2_color": section_colors(grid)[2],
        "sec3_color": section_colors(grid)[3],
        "extra_overlap_count": sum(len(sig) >= 2 for sig in extras),
    }


def valid_priority_orders(grid, output):
    return [order for order in permutations(range(4)) if apply_priority(grid, order) == output]


def fixed_canonical_color_priority(grid):
    """Canonical shortcut: choose by colors 9 > 4 > 8 > 5, not section."""
    rank = {9: 0, 4: 1, 8: 2, 5: 3}
    out = []
    for r in range(4):
        row = []
        for c in range(4):
            vals = [grid[r][start + c] for start in STARTS if grid[r][start + c] != 0]
            row.append(min(vals, key=lambda value: (rank.get(value, 100 + value), value)) if vals else 0)
        out.append(row)
    return out


def canonical_pairs():
    """Load normalized canonical authoring pairs in source or portable layouts."""
    try:
        from reviewer_support import canonical_pairs as read_pairs, find_root

        return read_pairs(TASK_ID, root=find_root(__file__))
    except (ImportError, FileNotFoundError, KeyError):
        root = Path(__file__).resolve()
        for parent in root.parents:
            candidate = parent / "shared" / "data" / "canonical" / "puzzles.jsonl"
            if candidate.exists():
                for line in candidate.read_text().splitlines():
                    row = json.loads(line)
                    if row.get("task_id") == TASK_ID:
                        return list(row["train"]) + list(row["test"])
        raise FileNotFoundError(f"canonical task {TASK_ID} was not found")


def audit_generator(module, *, per_band: int = 100) -> dict:
    """Run an independent, Racket-free structural and shortcut census."""
    if per_band < 1:
        raise ValueError("per_band must be positive")
    errors: list[str] = []
    per_band_rows: dict[str, dict] = {}
    unique_inputs: set[str] = set()

    for band_index, band in enumerate(("easy", "medium", "hard")):
        order_failures = 0
        roundtrip_failures = 0
        self_check_failures = 0
        rival_survivors = {name: 0 for name in module.SEMANTIC_RIVALS}
        overlap_counts: list[int] = []
        for sample in range(per_band):
            seed = 10_000 * (band_index + 1) + sample
            sample_index = sample * 7 + band_index
            grid = module.generate(seed, sample_index, difficulty=band)
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            unique_inputs.add(digest)
            if module.self_check(grid, difficulty=band):
                self_check_failures += 1
            expected = apply_priority(grid)
            if valid_priority_orders(grid, expected) != [INTENDED_ORDER]:
                order_failures += 1
            try:
                if module.observe_overrides(grid) != observed(grid):
                    roundtrip_failures += 1
            except Exception:
                roundtrip_failures += 1
            overlap_counts.append(observed(grid)["extra_overlap_count"])
            for name, rival in module.SEMANTIC_RIVALS.items():
                rival_survivors[name] += int(rival(grid) == expected)

        row = {
            "draws": per_band,
            "self_check_failures": self_check_failures,
            "non_unique_priority_orders": order_failures,
            "override_roundtrip_failures": roundtrip_failures,
            "extra_overlap_min": min(overlap_counts),
            "extra_overlap_max": max(overlap_counts),
            "rival_answer_agreements": rival_survivors,
        }
        per_band_rows[band] = row
        for key in ("self_check_failures", "non_unique_priority_orders", "override_roundtrip_failures"):
            if row[key]:
                errors.append(f"{band}: {key}={row[key]}")

    canonical = canonical_pairs()
    canonical_mismatches = [
        index for index, pair in enumerate(canonical)
        if apply_priority(pair["input"]) != pair["output"]
    ]
    canonical_rejections = [
        index for index, pair in enumerate(canonical)
        if module.self_check(pair["input"])
    ]
    if canonical_mismatches:
        errors.append(f"canonical oracle mismatches: {canonical_mismatches}")
    if canonical_rejections:
        errors.append(f"canonical self_check rejections: {canonical_rejections}")

    source = Path(module.__file__)
    return {
        "schema": "9000d0ea6484-independent-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "per_band_requested": per_band,
        "draws_total": per_band * 3,
        "unique_inputs": len(unique_inputs),
        "canonical_pairs": len(canonical),
        "canonical_oracle_mismatches": canonical_mismatches,
        "canonical_self_check_rejections": canonical_rejections,
        "per_band": per_band_rows,
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", help="generator.py to inspect")
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    module = load_generator(args.generator)
    report = audit_generator(module, per_band=args.per_band)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    print(raw, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
