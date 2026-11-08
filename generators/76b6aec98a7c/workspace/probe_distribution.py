#!/usr/bin/env python3
"""Source-bound distribution and teaching probe for generator 76b6aec98a7c.

This is an authoring tool, not a label source.  It samples all difficulty bands,
re-extracts every public axis from returned grids, checks the Python review
oracle and declared rivals, rotates each query through consecutive four-pair
lessons, and can optionally compare a small sample with the selected Racket
authority through ``Catalog.apply``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "76b6aec98a7c"
BANDS = ("easy", "medium", "hard")
CANONICAL_PROFILES = {(10, 16, 7), (11, 17, 7), (11, 18, 7)}


def _load_generator(root: Path):
    candidates = (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError(f"no generator {TASK_ID} under {root}")
    spec = importlib.util.spec_from_file_location("rotation_mosaic_probe_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def _grid_digest(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def audit(
    *, root=None, per_band: int = 24, window_starts: int = 12,
    racket_samples: int = 0, seed: int = 907,
) -> dict[str, Any]:
    """Return a JSON-serializable sampler/semantic receipt.

    ``racket_samples=0`` keeps the probe fast and pure-Python.  A positive value
    executes that many sampled inputs with the selected repository authority.
    """
    if per_band < 1 or window_starts < 1 or racket_samples < 0:
        raise ValueError("per_band/window_starts must be positive; racket_samples nonnegative")
    root = Path(root).resolve() if root is not None else find_root(__file__)
    gen, generator_path = _load_generator(root)

    axis_values = {name: set() for name in gen.AXES}
    input_digests: set[str] = set()
    output_digests: set[str] = set()
    failures: list[dict[str, Any]] = []
    sampled_inputs = []
    rival_disagreements = {name: 0 for name in gen.SEMANTIC_RIVALS}
    exact_profile_hits = {band: 0 for band in BANDS}

    for band_index, band in enumerate(BANDS):
        band_seed = seed + 100_003 * band_index
        for sample_index in range(per_band):
            try:
                grid = gen.generate(band_seed, sample_index, difficulty=band)
                findings = gen.self_check(grid, difficulty=band)
                if findings:
                    failures.append({
                        "kind": "self_check", "band": band,
                        "sample_index": sample_index, "findings": findings,
                    })
                    continue
                observed = gen.observe_overrides(grid)
                for name in axis_values:
                    axis_values[name].add(observed[name])
                expected = gen.rule_mirror(grid)
                for name, rival in gen.SEMANTIC_RIVALS.items():
                    if rival(grid) != expected:
                        rival_disagreements[name] += 1
                input_digests.add(_grid_digest(grid))
                output_digests.add(_grid_digest(expected))
                sampled_inputs.append(grid)
                if _profile(grid) in CANONICAL_PROFILES:
                    exact_profile_hits[band] += 1
            except Exception as exc:  # retained with exact band/index
                failures.append({
                    "kind": "sample_exception", "band": band,
                    "sample_index": sample_index, "error": repr(exc),
                })

    canonical = canonical_pairs(TASK_ID, root=root)
    shortcut_fit = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        shortcut_fit[name] = all(rival(pair["input"]) == pair["output"] for pair in canonical)

    lesson_failures = []
    lesson_rotations_checked = 0
    for start in range(window_starts):
        pairs = []
        for index in range(start, start + 4):
            grid = gen.generate(seed + 700_001, index, difficulty="medium")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            findings = gen.lesson_identifiable(demos, query)
            lesson_rotations_checked += 1
            if findings:
                lesson_failures.append({
                    "start": start, "query_index": query_index,
                    "findings": findings,
                })

    racket = {
        "requested": racket_samples,
        "checked": 0,
        "mismatches": [],
        "rule_hash_matches_catalog": None,
    }
    if racket_samples:
        from arcpuzzles import Catalog

        chosen = sampled_inputs[:racket_samples]
        receipt = Catalog(root).apply(TASK_ID, chosen, timeout=180)
        racket["checked"] = len(chosen)
        racket["rule_hash_matches_catalog"] = receipt.get("rule_hash_matches_catalog")
        for index, (grid, result) in enumerate(zip(chosen, receipt.get("results", []))):
            expected = gen.rule_mirror(grid)
            if not result.get("valid_output") or result.get("output") != expected:
                racket["mismatches"].append({
                    "index": index,
                    "valid_output": result.get("valid_output"),
                    "error": result.get("error"),
                })

    axis_coverage = {
        name: sorted(values, key=lambda value: (str(type(value)), str(value)))
        for name, values in axis_values.items()
    }
    expected_axis_coverage = (
        axis_values.get("source_color") == {6, 7, 8, 9}
        and axis_values.get("layout") == {
            "frame_left", "frame_right", "frame_above", "frame_below"
        }
        and axis_values.get("motif_size") == {2, 3, 4}
        and axis_values.get("code_h") == {2, 3}
        and axis_values.get("code_w") == {2, 3}
    )
    rivals_refuted = all(count > 0 for count in rival_disagreements.values())
    profiles_present = all(exact_profile_hits[band] > 0 for band in BANDS)
    racket_ok = (
        racket_samples == 0
        or (
            racket["checked"] == min(racket_samples, len(sampled_inputs))
            and racket["rule_hash_matches_catalog"] is True
            and not racket["mismatches"]
        )
    )
    status = "pass" if (
        not failures and not lesson_failures and expected_axis_coverage
        and rivals_refuted and profiles_present and all(shortcut_fit.values())
        and racket_ok
    ) else "fail"

    return {
        "schema": "rotation-mosaic-distribution-probe-v1",
        "task_id": TASK_ID,
        "status": status,
        "source": {
            "generator_path": str(generator_path.relative_to(root)),
            "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
            "version": gen.VERSION,
            "rule_hash": gen.RULE_HASH,
        },
        "settings": {
            "per_band": per_band, "window_starts": window_starts,
            "seed": seed, "racket_samples": racket_samples,
        },
        "summary": {
            "sampled": len(sampled_inputs),
            "unique_inputs": len(input_digests),
            "unique_outputs": len(output_digests),
            "self_check_failures": sum(item["kind"] == "self_check" for item in failures),
            "sample_exceptions": sum(item["kind"] == "sample_exception" for item in failures),
            "lesson_rotations_checked": lesson_rotations_checked,
            "lesson_failures": len(lesson_failures),
        },
        "axis_coverage": axis_coverage,
        "exact_canonical_profile_hits": exact_profile_hits,
        "rival_disagreements": rival_disagreements,
        "canonical_shortcut_fit": shortcut_fit,
        "failures": failures,
        "lesson_failures": lesson_failures,
        "racket": racket,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--per-band", type=int, default=24)
    parser.add_argument("--window-starts", type=int, default=12)
    parser.add_argument("--racket-samples", type=int, default=0)
    parser.add_argument("--seed", type=int, default=907)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit(
        root=args.root, per_band=args.per_band,
        window_starts=args.window_starts,
        racket_samples=args.racket_samples, seed=args.seed,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
