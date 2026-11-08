#!/usr/bin/env python3
"""Compare anchor-stamp generator sources with task-specific teaching metrics.

The probe intentionally uses only public generator entry points plus generic
pixel observations.  It is useful for future reviews because it can compare an
old draft and a candidate repair without importing private check-runner code.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "531e65dffc0a"
BANDS = (None, "easy", "medium", "hard")
AXIS_VALUES = {
    "grid_h": (10, 11, 12),
    "grid_w": (10, 11, 12),
    "n_anchors": (2, 3, 4),
    "proto_size": (3, 4, 5),
}
ANCHOR_CODES = {2, 3, 4, 5}


def _load_module(path: Path, label: str):
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_{label}_{abs(hash(path.resolve()))}", path
    )
    if not spec or not spec.loader:
        raise ValueError(f"could not load generator source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"canonical task {TASK_ID} not found in {path}")


def _normalize(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    if not cells:
        return ()
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate(shape: tuple[tuple[int, int], ...], turns: int) -> tuple[tuple[int, int], ...]:
    result = shape
    for _ in range(turns % 4):
        if not result:
            return ()
        height = max(row for row, _ in result) + 1
        result = _normalize({(col, height - 1 - row) for row, col in result})
    return result


def _observe(grid: list[list[int]]) -> dict[str, Any]:
    height = len(grid)
    width = len(grid[0]) if grid else 0
    anchors = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in ANCHOR_CODES
    ]
    proto_cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in ANCHOR_CODES | {0}
    }
    shape = _normalize(proto_cells)
    palette_size = len({value for row in grid for value in row})
    return {
        "grid_h": height,
        "grid_w": width,
        "n_anchors": len(anchors),
        "proto_size": len(proto_cells),
        "codes": tuple(value for _, _, value in anchors),
        "palette_size": palette_size,
        "profile": (height, width, palette_size),
        "rotation_signature_count": len({_rotate(shape, turns) for turns in range(4)}),
    }


def _canonical_profiles(record: dict[str, Any]) -> list[list[int]]:
    profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for split in ("train", "test")
        for pair in record[split]
    }
    return [list(profile) for profile in sorted(profiles)]


def _safe_generate(module, seed: int, sample_index: int, difficulty, overrides=None):
    overrides = overrides or {}
    try:
        return module.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **overrides,
        ), None
    except Exception as exc:  # probe records failures instead of aborting comparison
        return None, f"{type(exc).__name__}: {exc}"


def _summarize_source(
    module,
    *,
    canonical_pairs: list[dict[str, Any]],
    canonical_profiles: set[tuple[int, int, int]],
    samples_per_band: int,
    lesson_starts: int,
    seed_base: int,
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    generation_errors: list[str] = []
    self_check_passes = 0

    for band_index, band in enumerate(BANDS):
        for sample_index in range(samples_per_band):
            grid, error = _safe_generate(
                module,
                seed_base + 1000 * band_index,
                sample_index,
                band,
            )
            if error:
                generation_errors.append(f"band={band!r} sample={sample_index}: {error}")
                continue
            facts = _observe(grid)
            facts["band"] = band
            facts["sample_index"] = sample_index
            observations.append(facts)
            checker = getattr(module, "self_check", None)
            if checker is not None:
                try:
                    self_check_passes += int(checker(grid) == [])
                except Exception:
                    pass

    override_total = 0
    override_exact = 0
    override_failures: list[dict[str, Any]] = []
    for axis_index, (axis, values) in enumerate(AXIS_VALUES.items()):
        for value_index, value in enumerate(values):
            override_total += 1
            grid, error = _safe_generate(
                module,
                seed_base + 9000 + axis_index,
                value_index,
                None,
                {axis: value},
            )
            if error:
                override_failures.append({"axis": axis, "value": value, "error": error})
                continue
            observed = _observe(grid)[axis]
            if observed == value:
                override_exact += 1
            else:
                override_failures.append(
                    {"axis": axis, "value": value, "observed": observed}
                )

    lesson_total = 0
    lesson_passes = 0
    shortcut_lesson_total = 0
    shortcut_lesson_eliminated = 0
    cyclic_rotation_total = 0
    cyclic_rotation_passes = 0
    shortcut_map = getattr(module, "CANONICAL_SHORTCUTS", {})
    mirror = getattr(module, "rule_mirror", None)
    lesson_checker = getattr(module, "lesson_identifiable", None)
    examples_needed = int(getattr(module, "EXAMPLES_NEEDED", 3))

    if callable(mirror) and callable(lesson_checker):
        for band_index, band in enumerate(BANDS):
            for start in range(lesson_starts):
                demos = []
                failed = False
                for sample_index in range(start, start + examples_needed):
                    grid, error = _safe_generate(
                        module,
                        seed_base + 20000 + 1000 * band_index,
                        sample_index,
                        band,
                    )
                    if error:
                        failed = True
                        break
                    try:
                        demos.append({"input": grid, "output": mirror(grid)})
                    except Exception:
                        failed = True
                        break
                query_grid, query_error = _safe_generate(
                    module,
                    seed_base + 20000 + 1000 * band_index,
                    start + examples_needed,
                    band,
                )
                if failed or query_error:
                    continue
                query = {"input": query_grid, "output": mirror(query_grid)}
                lesson_total += 1
                try:
                    lesson_passes += int(lesson_checker(demos, query) == [])
                except Exception:
                    pass

                # A lesson can look identifiable only because the one
                # discriminating pair happened to be assigned to a demo.
                # Reuse the same four materialized pairs and rotate every one
                # through the query position; no additional generation or
                # authority calls are required.
                episode = [*demos, query]
                for query_index, rotated_query in enumerate(episode):
                    rotated_demos = [
                        pair
                        for pair_index, pair in enumerate(episode)
                        if pair_index != query_index
                    ]
                    cyclic_rotation_total += 1
                    try:
                        cyclic_rotation_passes += int(
                            lesson_checker(rotated_demos, rotated_query) == []
                        )
                    except Exception:
                        pass
                if shortcut_map:
                    shortcut_lesson_total += 1
                    if all(
                        any(shortcut(pair["input"]) != pair["output"] for pair in demos)
                        for shortcut in shortcut_map.values()
                    ):
                        shortcut_lesson_eliminated += 1

    canonical_shortcuts_fit = bool(shortcut_map)
    if shortcut_map and callable(mirror):
        for shortcut in shortcut_map.values():
            for pair in canonical_pairs:
                try:
                    if shortcut(pair["input"]) != pair["output"]:
                        canonical_shortcuts_fit = False
                except Exception:
                    canonical_shortcuts_fit = False
    elif not shortcut_map:
        canonical_shortcuts_fit = False

    count = len(observations)
    profile_counts = Counter(tuple(item["profile"]) for item in observations)
    return {
        "source_version": getattr(module, "VERSION", None),
        "generated_samples": count,
        "generation_errors": generation_errors,
        "self_check_fraction": self_check_passes / count if count else 0.0,
        "asymmetric_rotation_fraction": (
            sum(item["rotation_signature_count"] == 4 for item in observations) / count
            if count
            else 0.0
        ),
        "canonical_profile_fraction": (
            sum(tuple(item["profile"]) in canonical_profiles for item in observations) / count
            if count
            else 0.0
        ),
        "profile_counts": {
            "x".join(map(str, key)): value for key, value in sorted(profile_counts.items())
        },
        "anchor_count_counts": dict(
            sorted(Counter(item["n_anchors"] for item in observations).items())
        ),
        "prototype_size_counts": dict(
            sorted(Counter(item["proto_size"] for item in observations).items())
        ),
        "override_exact_fraction": override_exact / override_total if override_total else 0.0,
        "override_exact_count": override_exact,
        "override_case_count": override_total,
        "override_failures": override_failures,
        "lesson_identifiable_fraction": lesson_passes / lesson_total if lesson_total else 0.0,
        "lesson_identifiable_count": lesson_passes,
        "lesson_count": lesson_total,
        "cyclic_query_rotation_fraction": (
            cyclic_rotation_passes / cyclic_rotation_total
            if cyclic_rotation_total
            else 0.0
        ),
        "cyclic_query_rotation_pass_count": cyclic_rotation_passes,
        "cyclic_query_rotation_count": cyclic_rotation_total,
        "canonical_shortcut_names": sorted(shortcut_map),
        "canonical_shortcuts_fit_all_canonical": canonical_shortcuts_fit,
        "canonical_shortcuts_eliminated_fraction": (
            shortcut_lesson_eliminated / shortcut_lesson_total
            if shortcut_lesson_total
            else 0.0
        ),
        "canonical_shortcut_lesson_count": shortcut_lesson_total,
    }


def compare_sources(
    *,
    before_path: Path,
    after_path: Path,
    canonical_path: Path,
    samples_per_band: int = 12,
    lesson_starts: int = 12,
    seed_base: int = 6921,
) -> dict[str, Any]:
    record = _canonical_record(Path(canonical_path))
    canonical_pairs = [*record["train"], *record["test"]]
    profiles = _canonical_profiles(record)
    profile_set = {tuple(profile) for profile in profiles}
    before = _load_module(Path(before_path), "before")
    after = _load_module(Path(after_path), "after")
    return {
        "schema": "anchor_stamp_distribution_probe/1",
        "task_id": TASK_ID,
        "parameters": {
            "samples_per_band": samples_per_band,
            "lesson_starts": lesson_starts,
            "seed_base": seed_base,
            "bands": [band if band is not None else "default" for band in BANDS],
        },
        "canonical": {
            "pair_count": len(canonical_pairs),
            "profiles": profiles,
        },
        "before": _summarize_source(
            before,
            canonical_pairs=canonical_pairs,
            canonical_profiles=profile_set,
            samples_per_band=samples_per_band,
            lesson_starts=lesson_starts,
            seed_base=seed_base,
        ),
        "after": _summarize_source(
            after,
            canonical_pairs=canonical_pairs,
            canonical_profiles=profile_set,
            samples_per_band=samples_per_band,
            lesson_starts=lesson_starts,
            seed_base=seed_base,
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--samples-per-band", type=int, default=12)
    parser.add_argument("--lesson-starts", type=int, default=12)
    parser.add_argument("--seed-base", type=int, default=6921)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = compare_sources(
        before_path=args.before,
        after_path=args.after,
        canonical_path=args.canonical,
        samples_per_band=args.samples_per_band,
        lesson_starts=args.lesson_starts,
        seed_base=args.seed_base,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
