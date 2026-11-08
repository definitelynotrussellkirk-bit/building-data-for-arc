#!/usr/bin/env python3
"""Source-bound semantic audit for generator 058ae70e4bdb.

This probe is intentionally independent of the generator's region parser and
Python rule mirror.  It checks every declared exact profile, the actual rival
mappings, canonical-shortcut claims, and every hold-one-out rotation of
consecutive four-pair lessons.  The JSON result records the exact generator
bytes so future agents can tell whether evidence still applies.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "058ae70e4bdb"
TASK_DIR = Path(__file__).resolve().parents[1]
DEFAULT_GENERATOR = TASK_DIR / "generator.py"
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
BANDS = ("easy", "medium", "hard")
CANONICAL_PROFILES = {
    (9, 11, 5),
    (10, 12, 5),
    (9, 13, 5),
    (11, 11, 6),
    (10, 14, 5),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("audit_generator_058ae70e4bdb", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _regions(grid: list[list[int]]) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 8 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in DIR4:
                    rr, cc = row + drow, col + dcol
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 8
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            cells.sort()
            markers = tuple(
                (row, col, grid[row][col])
                for row, col in cells
                if grid[row][col] not in (0, 8)
            )
            colors = Counter(color for _, _, color in markers)
            result.append({"cells": tuple(cells), "markers": markers, "colors": colors})
    return result


def _oracle(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for region in _regions(grid):
        if len(region["colors"]) != 1:
            continue
        color = next(iter(region["colors"]))
        for row, col in region["cells"]:
            output[row][col] = color
    return output


def _frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _record_failure(failures: list[dict[str, Any]], kind: str, **details: Any) -> None:
    failures.append({"kind": kind, **details})


def audit(
    *,
    samples_per_profile: int = 20,
    schedule_starts: int = 30,
    generator_path: str | Path | None = None,
) -> dict[str, Any]:
    if samples_per_profile < 1 or schedule_starts < 1:
        raise ValueError("samples_per_profile and schedule_starts must be positive")
    source = Path(generator_path) if generator_path is not None else DEFAULT_GENERATOR
    source = source.resolve()
    generator = _load_generator(source)
    failures: list[dict[str, Any]] = []
    seen_inputs: set[tuple[tuple[int, ...], ...]] = set()
    profile_counts: Counter[str] = Counter()

    profiles = tuple(generator.SCENE_PROFILES)
    competitors = dict(generator.LESSON_COMPETITORS)
    shortcuts = dict(generator.CANONICAL_SHORTCUTS)

    # Universal typo probe: an exact override surface must not swallow unknown keys.
    try:
        generator.generate(1, 0, difficulty="easy", __deep_audit_unknown_axis__=1)
    except (TypeError, ValueError):
        unknown_override_rejected = True
    except Exception as exc:  # loud but still a rejection
        unknown_override_rejected = True
        _record_failure(
            failures,
            "unknown_override_wrong_exception",
            exception=f"{type(exc).__name__}: {exc}",
        )
    else:
        unknown_override_rejected = False
        _record_failure(failures, "unknown_override_accepted")

    draw_count = 0
    for band_index, band in enumerate(BANDS):
        for profile_index, profile in enumerate(profiles):
            for sample in range(samples_per_profile):
                seed = 2_000_000 + band_index * 100_000 + profile_index * 10_000 + sample
                sample_index = profile_index * 1000 + sample
                context = {
                    "band": band,
                    "profile": profile,
                    "seed": seed,
                    "sample_index": sample_index,
                }
                try:
                    grid = generator.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                except Exception as exc:
                    _record_failure(
                        failures,
                        "profile_generation_error",
                        **context,
                        exception=f"{type(exc).__name__}: {exc}",
                    )
                    continue
                draw_count += 1
                profile_counts[profile] += 1
                seen_inputs.add(_frozen(grid))

                checks: list[tuple[str, bool, Any]] = []
                try:
                    observed = generator.observe_overrides(grid)
                    checks.append(("override_observation", observed == {"scene_profile": profile}, observed))
                except Exception as exc:
                    checks.append(("override_observation", False, f"{type(exc).__name__}: {exc}"))
                try:
                    self_findings = generator.self_check(
                        grid, difficulty=band, meta={"scene_profile": profile}
                    )
                    checks.append(("self_check", self_findings == [], self_findings))
                except Exception as exc:
                    checks.append(("self_check", False, f"{type(exc).__name__}: {exc}"))
                try:
                    strict_findings = generator.strict_canonical_like(grid)
                    checks.append(("strict_canonical_like", strict_findings == [], strict_findings))
                except Exception as exc:
                    checks.append(("strict_canonical_like", False, f"{type(exc).__name__}: {exc}"))

                expected = _oracle(grid)
                checks.append(("nonidentity", expected != grid, None))
                try:
                    checks.append(("python_mirror", generator.rule_mirror(grid) == expected, None))
                except Exception as exc:
                    checks.append(("python_mirror", False, f"{type(exc).__name__}: {exc}"))
                try:
                    replay = generator.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    checks.append(("deterministic_replay", replay == grid, None))
                except Exception as exc:
                    checks.append(("deterministic_replay", False, f"{type(exc).__name__}: {exc}"))
                morphology = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                checks.append(("canonical_profile", morphology in CANONICAL_PROFILES, morphology))
                for witness_name, predicate in generator.PROFILE_WITNESSES[profile].items():
                    try:
                        checks.append((f"profile_witness:{witness_name}", bool(predicate(grid)), None))
                    except Exception as exc:
                        checks.append(
                            (
                                f"profile_witness:{witness_name}",
                                False,
                                f"{type(exc).__name__}: {exc}",
                            )
                        )
                for check_name, passed, detail in checks:
                    if not passed:
                        _record_failure(
                            failures,
                            "profile_check_failed",
                            **context,
                            check=check_name,
                            detail=detail,
                        )

    expected_draws = len(BANDS) * len(profiles) * samples_per_profile
    if draw_count != expected_draws:
        _record_failure(
            failures,
            "profile_draw_count",
            expected=expected_draws,
            actual=draw_count,
        )
    if len(seen_inputs) != draw_count:
        _record_failure(
            failures,
            "duplicate_profile_inputs",
            draws=draw_count,
            unique=len(seen_inputs),
        )

    # Verify canonical data and every shortcut claim against an independent oracle.
    canonical_pairs_checked = 0
    shortcut_claims_checked = 0
    try:
        from reviewer_support import canonical_pairs, find_root

        canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    except Exception as exc:
        canonical = []
        _record_failure(
            failures,
            "canonical_load_error",
            exception=f"{type(exc).__name__}: {exc}",
        )
    for pair_index, pair in enumerate(canonical):
        canonical_pairs_checked += 1
        expected = _oracle(pair["input"])
        if expected != pair["output"]:
            _record_failure(failures, "independent_oracle_disagrees_canonical", pair_index=pair_index)
        for name, shortcut in shortcuts.items():
            shortcut_claims_checked += 1
            try:
                actual = shortcut(deepcopy(pair["input"]))
            except Exception as exc:
                _record_failure(
                    failures,
                    "canonical_shortcut_error",
                    shortcut=name,
                    pair_index=pair_index,
                    exception=f"{type(exc).__name__}: {exc}",
                )
                continue
            if actual != pair["output"]:
                _record_failure(
                    failures,
                    "canonical_shortcut_claim_false",
                    shortcut=name,
                    pair_index=pair_index,
                )

    # Exhaust every cyclic start requested and every hold-one-out query rotation.
    rotations_checked = 0
    competitor_checks = 0
    for band_index, band in enumerate(BANDS):
        for start in range(schedule_starts):
            seed = 4_000_000 + band_index * 100_000 + start
            pairs: list[dict[str, list[list[int]]]] = []
            for offset in range(4):
                sample_index = start + offset
                grid = generator.generate(seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": _oracle(grid)})
            for held_out in range(4):
                rotations_checked += 1
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                query = pairs[held_out]
                survivors: list[str] = []
                for name, competitor in competitors.items():
                    competitor_checks += 1
                    try:
                        if all(competitor(deepcopy(pair["input"])) == pair["output"] for pair in demos):
                            survivors.append(name)
                    except Exception as exc:
                        _record_failure(
                            failures,
                            "lesson_competitor_error",
                            band=band,
                            start=start,
                            held_out=held_out,
                            competitor=name,
                            exception=f"{type(exc).__name__}: {exc}",
                        )
                if survivors:
                    _record_failure(
                        failures,
                        "lesson_rival_survived",
                        band=band,
                        start=start,
                        held_out=held_out,
                        survivors=survivors,
                    )
                try:
                    reasons = generator.lesson_identifiable(demos, query)
                except Exception as exc:
                    _record_failure(
                        failures,
                        "lesson_hook_error",
                        band=band,
                        start=start,
                        held_out=held_out,
                        exception=f"{type(exc).__name__}: {exc}",
                    )
                else:
                    if reasons:
                        _record_failure(
                            failures,
                            "lesson_hook_rejected",
                            band=band,
                            start=start,
                            held_out=held_out,
                            reasons=reasons,
                        )

    report: dict[str, Any] = {
        "schema": "058ae70e4bdb-deep-audit-v1",
        "task_id": TASK_ID,
        "status": "pass" if not failures else "fail",
        "generator_path": str(source),
        "generator_sha256": sha256_file(source),
        "audit_tool_sha256": sha256_file(Path(__file__).resolve()),
        "samples_per_profile": samples_per_profile,
        "schedule_starts": schedule_starts,
        "profiles": list(profiles),
        "profiles_checked": draw_count,
        "profile_counts": dict(sorted(profile_counts.items())),
        "unique_profile_inputs": len(seen_inputs),
        "unknown_override_rejected": unknown_override_rejected,
        "canonical_pairs_checked": canonical_pairs_checked,
        "canonical_shortcuts": sorted(shortcuts),
        "shortcut_claims_checked": shortcut_claims_checked,
        "competitors": sorted(competitors),
        "lesson_rotations_checked": rotations_checked,
        "competitor_checks": competitor_checks,
        "failures": failures,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples",
        "--samples-per-profile",
        dest="samples_per_profile",
        type=int,
        default=20,
        help="draws per exact profile per difficulty band (default: 20)",
    )
    parser.add_argument(
        "--schedule-starts",
        type=int,
        default=30,
        help="consecutive lesson start offsets per band (default: 30)",
    )
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = audit(
        samples_per_profile=args.samples_per_profile,
        schedule_starts=args.schedule_starts,
        generator_path=args.generator,
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(
        f"{report['status'].upper()} task={TASK_ID} "
        f"profiles={report['profiles_checked']} "
        f"rotations={report['lesson_rotations_checked']} "
        f"failures={len(report['failures'])} "
        f"generator_sha256={report['generator_sha256']}"
    )
    if report["failures"]:
        print(json.dumps(report["failures"][:5], indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
