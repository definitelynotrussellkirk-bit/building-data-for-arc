#!/usr/bin/env python3
"""Independent ambiguity census for task 75b8cb3d5e9b.

The probe does not trust the generator's private analyzer.  It reparses the
three panels, enumerates all eight D4 explanations, and counts distinct query
answers.  Future reviews can use it before and after edits:

    PYTHONPATH=shared/runtime:. python3 \
      generators/75b8cb3d5e9b/workspace/transform_ambiguity_probe.py \
      --draws-per-band 500 --out generators/75b8cb3d5e9b/evidence/final_ambiguity.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence


BANDS: tuple[str | None, ...] = (None, "easy", "medium", "hard")


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _transform(grid: Sequence[Sequence[int]], code: int) -> list[list[int]]:
    src = [list(row) for row in grid]
    if code == 0:
        return [row[:] for row in src]
    if code == 1:
        return [list(row) for row in zip(*src[::-1])]
    if code == 2:
        return [row[::-1] for row in src[::-1]]
    if code == 3:
        return [list(row) for row in zip(*src)][::-1]
    if code == 4:
        return [row[::-1] for row in src]
    if code == 5:
        return _transform(_transform(src, 4), 1)
    if code == 6:
        return _transform(_transform(src, 4), 2)
    if code == 7:
        return _transform(_transform(src, 4), 3)
    raise ValueError(f"D4 code must be 0..7, got {code!r}")


def _crop(panel: Sequence[Sequence[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        raise ValueError("panel contains no motif")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[c0 : c1 + 1]) for row in panel[r0 : r1 + 1]]


def _parse(grid: Sequence[Sequence[int]]) -> tuple[list[list[int]], ...]:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("ragged grid")
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 2:
        raise ValueError(f"expected two full color-9 dividers, got {dividers}")
    cuts = (
        (0, dividers[0]),
        (dividers[0] + 1, dividers[1]),
        (dividers[1] + 1, w),
    )
    panels = [
        [[grid[r][c] for c in range(left, right)] for r in range(h)]
        for left, right in cuts
    ]
    return tuple(_crop(panel) for panel in panels)


def independent_facts(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Return transform ambiguity facts derived only from the pixel grid."""
    source, target, query = _parse(grid)
    candidates = [code for code in range(8) if _transform(source, code) == target]
    fitting_outputs = {_freeze(_transform(query, code)) for code in candidates}
    query_orbit = {_freeze(_transform(query, code)) for code in range(8)}
    return {
        "candidate_codes": candidates,
        "transform_candidate_count": len(candidates),
        "distinct_fitting_output_count": len(fitting_outputs),
        "query_orbit_size": len(query_orbit),
    }


def _module_sha256(module: Any) -> str | None:
    filename = getattr(module, "__file__", None)
    if not filename:
        return None
    path = Path(filename)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def audit_generator(module: Any, *, draws_per_band: int = 500, seed_base: int = 100_000) -> dict[str, Any]:
    if draws_per_band <= 0:
        raise ValueError("draws_per_band must be positive")

    total = 0
    ambiguous = 0
    non_discriminative = 0
    self_check_failures = 0
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    transforms: Counter[str] = Counter()
    profiles: Counter[str] = Counter()
    violations: list[dict[str, Any]] = []
    by_band: dict[str, dict[str, int]] = {}

    for band_index, band in enumerate(BANDS):
        label = "default" if band is None else band
        band_counts = {
            "draw_count": 0,
            "ambiguous_draw_count": 0,
            "non_discriminative_query_count": 0,
            "self_check_failure_count": 0,
        }
        for index in range(draws_per_band):
            seed = seed_base + band_index * draws_per_band + index
            sample_index = index * 17 + band_index * 5
            grid = module.generate(seed, sample_index, difficulty=band)
            total += 1
            band_counts["draw_count"] += 1
            unique_inputs.add(_freeze(grid))
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            profiles["x".join(map(str, profile))] += 1

            errors = list(module.self_check(grid))
            if errors:
                self_check_failures += 1
                band_counts["self_check_failure_count"] += 1

            facts = independent_facts(grid)
            if facts["distinct_fitting_output_count"] != 1:
                ambiguous += 1
                band_counts["ambiguous_draw_count"] += 1
            if facts["query_orbit_size"] != 8:
                non_discriminative += 1
                band_counts["non_discriminative_query_count"] += 1

            observed = module.observe_overrides(grid)
            transforms[str(observed.get("transform"))] += 1

            if errors or facts["distinct_fitting_output_count"] != 1 or facts["query_orbit_size"] != 8:
                if len(violations) < 20:
                    violations.append(
                        {
                            "band": label,
                            "seed": seed,
                            "sample_index": sample_index,
                            "self_check_errors": errors,
                            "facts": facts,
                            "grid": grid,
                        }
                    )
        by_band[label] = band_counts

    return {
        "schema": "transform-ambiguity-probe-v1",
        "task_id": getattr(module, "TASK_ID", None),
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "generator_sha256": _module_sha256(module),
        "draws_per_band": draws_per_band,
        "seed_base": seed_base,
        "draw_count": total,
        "unique_input_count": len(unique_inputs),
        "ambiguous_draw_count": ambiguous,
        "non_discriminative_query_count": non_discriminative,
        "self_check_failure_count": self_check_failures,
        "transform_counts": dict(sorted(transforms.items())),
        "profile_counts": dict(sorted(profiles.items())),
        "by_band": by_band,
        "violation_samples": violations,
        "limits": (
            "Finite generated-draw census. It proves neither universal D4 induction "
            "nor correctness outside the generator's declared domain."
        ),
    }


def _load_sibling_generator() -> Any:
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("reviewed_transform_generator", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=500)
    parser.add_argument("--seed-base", type=int, default=100_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = audit_generator(
        _load_sibling_generator(),
        draws_per_band=args.draws_per_band,
        seed_base=args.seed_base,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if not (
        report["ambiguous_draw_count"]
        or report["non_discriminative_query_count"]
        or report["self_check_failure_count"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
