"""Replayable production coverage for bee63e6e52bd's visible diagonal spouts.

Run from the outer packet directory (payload cwd is WORK/repo):
  WORK/.venv/bin/python review.py run ../.venv/bin/python \
    generators/bee63e6e52bd/workspace/spout_coverage.py \
    --seed 730000 --default-seed 100000 --default-count 160 \
    --baseline ../checks/coverage-review/baseline_geometry.json \
    --out ../checks/large-coverage/evidence

The 256 explicit large inputs and four canonical inputs execute in Racket.
Default draws use independent Python labels and geometry only. Actual grids
are retained as gzip JSONL; each report artifact records its restoration name,
compressed/uncompressed sizes and SHA-256 hashes. For example:
  gzip -dc large-cases.jsonl.gz > large-cases.jsonl
Existing output directories are refused, so failed attempts cannot be replaced.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import itertools
import json
import sys
import traceback
from collections import Counter
from pathlib import Path

TASK_ID = "bee63e6e52bd"
LARGE_PROFILES = ("21x21", "21x30", "30x21", "30x30")
SIDES = ("left", "right", "top", "bottom")
ARMS = ("canonical_2_2", "short_1_1", "asym_1_3", "asym_3_1")
BANDS = (None, "easy", "medium", "hard")
HERE = Path(__file__).resolve()
for candidate in (HERE.parent, *HERE.parents):
    for support in (candidate / "reviewer_support.py", candidate / "shared/runtime/reviewer_support.py"):
        if support.is_file():
            if str(support.parent) not in sys.path:
                sys.path.insert(0, str(support.parent))
            break
    else:
        continue
    break
else:
    raise ImportError("cannot locate portable reviewer_support.py")

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid) -> str:
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def load_local(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measure(grid, output, oracle) -> dict:
    """Infer ray positions from visible frame geometry, independently of generator code."""
    facts = oracle.shape_facts(grid)
    r0, c0, r1, c1 = facts["bbox"]
    h, w = facts["height"], facts["width"]
    before, after, side = facts["arm_before"], facts["arm_after"], facts["open_side"]
    if side in ("left", "right"):
        mouth = c0 - 1 if side == "left" else c1 + 1
        outward = -1 if side == "left" else 1
        anchors = ((r0 + before - 1, mouth), (r1 - after + 1, mouth))
        directions = ((-1, outward), (1, outward))
    else:
        mouth = r0 - 1 if side == "top" else r1 + 1
        outward = -1 if side == "top" else 1
        anchors = ((mouth, c0 + before - 1), (mouth, c1 - after + 1))
        directions = ((outward, -1), (outward, 1))
    ray_lengths, painted_lengths = [], []
    for (ar, ac), (dr, dc) in zip(anchors, directions):
        positions = [(ar + distance * dr, ac + distance * dc)
                     for distance in range(1, max(h, w) + 1)
                     if 0 <= ar + distance * dr < h and 0 <= ac + distance * dc < w]
        ray_lengths.append(len(positions))
        painted_lengths.append(sum(grid[r][c] == 0 and output[r][c] == 4 for r, c in positions))
    return {
        "shape": [h, w], "bbox": list(facts["bbox"]),
        "frame_shape": [r1 - r0 + 1, c1 - c0 + 1],
        "open_side": side, "arms": [before, after],
        "ray_lengths_beyond_tip_anchors": ray_lengths,
        "painted_post_anchor_ray_cells": painted_lengths,
        "interior_area": max(0, r1 - r0 - 1) * max(0, c1 - c0 - 1),
        "changed_cells": sum(a != b for row, other in zip(grid, output) for a, b in zip(row, other)),
    }


def aggregate(rows: list[dict]) -> dict:
    metrics = [row["metrics"] for row in rows]
    rays = [length for item in metrics for length in item["ray_lengths_beyond_tip_anchors"]]
    best_rays = [max(item["ray_lengths_beyond_tip_anchors"]) for item in metrics]
    return {
        "draws": len(rows), "passed": sum(not row["failures"] for row in rows),
        "changed_cells_min": min(item["changed_cells"] for item in metrics),
        "changed_cells_max": max(item["changed_cells"] for item in metrics),
        "single_ray_min": min(rays), "single_ray_max": max(rays),
        "best_of_two_rays_min": min(best_rays), "best_of_two_rays_max": max(best_rays),
        "zero_both_rays": sum(length == 0 for length in best_rays),
        "at_least_one_ray_ge3": sum(length >= 3 for length in best_rays),
        "both_rays_ge3": sum(min(item["ray_lengths_beyond_tip_anchors"]) >= 3 for item in metrics),
        "frame_min_dimension": min(min(item["frame_shape"]) for item in metrics),
        "frame_max_dimension": max(max(item["frame_shape"]) for item in metrics),
        "profiles": dict(sorted(Counter(f"{item['shape'][0]}x{item['shape'][1]}" for item in metrics).items())),
    }


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_rows(output: Path, name: str, rows: list[dict]) -> dict:
    raw = "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows).encode()
    packed = gzip.compress(raw, mtime=0)
    filename = name + ".gz"
    (output / filename).write_bytes(packed)
    return {"path": filename, "restore_as": name, "format": "gzip-compressed JSONL", "rows": len(rows),
            "sha256": digest(packed), "uncompressed_sha256": digest(raw),
            "bytes": len(packed), "uncompressed_bytes": len(raw),
            "restore_command": f"gzip -dc {filename} > {name}"}


def checked_pair(grid, expected, actual, generator, oracle, *, original_hash, overrides=None, large=False) -> tuple[dict, list[str]]:
    failures = []
    checks = {
        "self_check": generator.self_check(grid) == [],
        "input_not_mutated": grid_hash(grid) == original_hash,
        "output_shape": len(actual) == len(grid) and all(len(a) == len(b) for a, b in zip(actual, grid)),
        "matches_independent_python": actual == expected,
        "nonzero_input_pixels_preserved": all(value == actual[r][c] for r, row in enumerate(grid)
                                               for c, value in enumerate(row) if value != 0),
        "only_zero_to_yellow_changes": all(a == b or (a == 0 and b == 4)
                                          for row, other in zip(grid, actual) for a, b in zip(row, other)),
    }
    strict = generator.strict_canonical_like(grid)
    metrics = measure(grid, actual, oracle)
    checks["all_expected_ray_cells_painted"] = (
        metrics["ray_lengths_beyond_tip_anchors"] == metrics["painted_post_anchor_ray_cells"])
    if overrides is not None:
        observed = generator.observe_overrides(grid)
        checks["exact_observed_overrides"] = observed == overrides
    else:
        observed = None
    if large:
        checks.update(noncanonical_strict=bool(strict), frame_min_dimension_ge7=min(metrics["frame_shape"]) >= 7,
                      at_least_one_ray_ge3=max(metrics["ray_lengths_beyond_tip_anchors"]) >= 3)
    failures.extend(name for name, passed in checks.items() if not passed)
    return {"metrics": metrics, "checks": checks, "strict_classification": strict,
            "observed_overrides": observed, "failures": failures}, failures


def run(args) -> dict:
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    generator, generator_path, generator_hash = load_selected_generator(TASK_ID, root=ROOT)
    oracle_path = HERE.parent / "reference_probe.py"
    prototype_path = HERE.parent / "parametric/prototype.py"
    oracle = load_local(oracle_path, "bee_spout_coverage_oracle")
    prototype = load_local(prototype_path, "bee_spout_coverage_racket")
    program = prototype.program_source("full")
    program_hash = digest(program.encode())
    normalized_rule_hash = digest(" ".join(program.split()).encode())[:12]
    if normalized_rule_hash != generator.RULE_HASH:
        raise ValueError("selected generator's rule pin differs from executed canonical program")
    (output / "canonical-program.rkt").write_text(program, encoding="utf-8")
    source_paths = (HERE, generator_path, oracle_path, prototype_path, prototype.HERE / "canonical-full.rkt")
    sources = {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in source_paths}
    all_failures, large_rows, canonical_rows, default_rows = [], [], [], []
    with prototype.RacketRunner() as runner:
        for index, (profile, side, arms, band) in enumerate(itertools.product(LARGE_PROFILES, SIDES, ARMS, BANDS)):
            overrides = {"scene_profile": profile, "open_side": side, "arm_profile": arms,
                         "color": generator.COLORS[index % len(generator.COLORS)]}
            seed = args.seed + index
            grid = generator.generate(seed, index, difficulty=band, **overrides)
            original_hash = grid_hash(grid)
            expected = oracle.intended_output(grid)
            actual = runner.apply(program, [grid])[0]
            details, failures = checked_pair(grid, expected, actual, generator, oracle,
                                            original_hash=original_hash, overrides=overrides, large=True)
            row = {"case": index, "seed": seed, "sample_index": index, "difficulty": band,
                   "overrides": overrides, "label_backend": "Racket", "input": grid,
                   "racket_output": actual, "input_sha256": original_hash,
                   "independent_python_output_sha256": grid_hash(expected), **details}
            if failures:
                row["independent_python_output"] = expected
                all_failures.append({"kind": "large", "case": index, "failures": failures})
            large_rows.append(row)
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            grid = pair["input"]
            original_hash = grid_hash(grid)
            expected = oracle.intended_output(grid)
            actual = runner.apply(program, [grid])[0]
            details, failures = checked_pair(grid, expected, actual, generator, oracle, original_hash=original_hash)
            details["checks"]["matches_canonical_label"] = actual == pair["output"]
            if actual != pair["output"]:
                failures.append("matches_canonical_label")
            row = {**pair, "label_backend": "Racket", "racket_output": actual,
                   "input_sha256": original_hash, "independent_python_output_sha256": grid_hash(expected), **details}
            canonical_rows.append(row)
            if failures:
                all_failures.append({"kind": "canonical", "pair": len(canonical_rows) - 1, "failures": failures})
        runtime = runner.bridge.runtime_identity
        racket_executions = runner.grid_executions

    for band in BANDS:
        for index in range(args.default_count):
            seed = args.default_seed + index
            grid = generator.generate(seed, index, difficulty=band)
            original_hash = grid_hash(grid)
            expected = oracle.intended_output(grid)
            details, failures = checked_pair(grid, expected, expected, generator, oracle, original_hash=original_hash)
            # This census does not execute Racket. Do not label self-comparison
            # as independent runtime parity, even though checked_pair shares checks.
            details["checks"].pop("matches_independent_python")
            details["checks"]["strict_canonical_profile"] = generator.strict_canonical_like(grid) == []
            details["checks"]["visible_post_anchor_ray"] = max(details["metrics"]["ray_lengths_beyond_tip_anchors"]) >= 1
            for name in ("strict_canonical_profile", "visible_post_anchor_ray"):
                if not details["checks"][name]:
                    failures.append(name)
            row = {"seed": seed, "sample_index": index, "difficulty": band,
                   "label_backend": "independent Python mirror; geometry only, no Racket execution",
                   "input": grid, "python_output": expected, "input_sha256": original_hash, **details}
            default_rows.append(row)
            if failures:
                all_failures.append({"kind": "default_geometry", "difficulty": band, "sample_index": index, "failures": failures})

    if len(large_rows) != 256 or len(canonical_rows) != 4 or racket_executions != 260:
        all_failures.append({"kind": "coverage_count", "large": len(large_rows), "canonical": len(canonical_rows),
                             "racket": racket_executions})
    default_bands = {str(band): aggregate([row for row in default_rows if row["difficulty"] == band]) for band in BANDS}
    baseline_comparison = None
    if args.baseline is not None:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        if baseline.get("task_id") != TASK_ID:
            raise ValueError("baseline report belongs to a different task")
        baseline_bands = baseline["baseline_bands"]
        baseline_comparison = {
            "report_sha256": digest(args.baseline.read_bytes()),
            "generator_sha256": baseline["generator_sha256"], "generator_version": baseline["version"],
            "basis": "retained baseline geometry statistics, not rerun Racket labels",
            "baseline_coordinate_recipe": "seed=100000+index, sample_index=index, index=0..159 for each band",
            "same_seed_index_recipe": args.default_seed == 100000 and args.default_count == 160,
            "bands": {band: {"baseline_draws": baseline_bands[band]["draws"],
                              "baseline_zero_both_rays": baseline_bands[band]["zero_both_rays"],
                              "current_draws": default_bands[band]["draws"],
                              "current_zero_both_rays": default_bands[band]["zero_both_rays"]} for band in default_bands},
        }
    artifacts = [write_rows(output, "large-cases.jsonl", large_rows),
                 write_rows(output, "canonical-cases.jsonl", canonical_rows),
                 write_rows(output, "default-geometry-cases.jsonl", default_rows)]
    changed_sources = [name for name, recorded in sources.items() if digest((ROOT / name).read_bytes()) != recorded]
    if changed_sources:
        all_failures.append({"kind": "sources_changed_during_run", "paths": changed_sources})
    report = {
        "schema": "bee63e6e52bd-spout-coverage-v1", "task_id": TASK_ID,
        "status": "pass" if not all_failures else "fail", "generator_version": generator.VERSION,
        "generator_sha256": generator_hash, "source_sha256": sources,
        "program_sha256": program_hash, "normalized_rule_hash": normalized_rule_hash,
        "program_file": "canonical-program.rkt", "runtime_identity": runtime,
        "payload_argv": [sys.executable, *sys.argv], "payload_cwd": str(Path.cwd()),
        "seed_controls": {"large_seed_base": args.seed, "large_sample_index_start": 0,
                          "default_seed_base": args.default_seed, "default_count_per_band": args.default_count},
        "racket_grid_executions": racket_executions,
        "large": {"summary": aggregate(large_rows),
                  "per_profile": {profile: aggregate([row for row in large_rows if row["overrides"]["scene_profile"] == profile]) for profile in LARGE_PROFILES},
                  "per_band": {str(band): aggregate([row for row in large_rows if row["difficulty"] == band]) for band in BANDS},
                  "per_profile_band_counts": {profile: {str(band): sum(row["overrides"]["scene_profile"] == profile and row["difficulty"] == band for row in large_rows) for band in BANDS} for profile in LARGE_PROFILES}},
        "canonical": {"pairs": len(canonical_rows), "matches": sum(not row["failures"] for row in canonical_rows)},
        "default_geometry": {"label_backend": "independent Python mirror and geometry; no Racket execution",
                             "summary": aggregate(default_rows), "per_band": default_bands},
        "baseline_comparison": baseline_comparison, "artifacts": artifacts, "failures": all_failures,
        "limitations": ["One source-bound seed per large-profile/side/arm/band combination; not exhaustive over seeds or colors.",
                        "Large inputs require at least one three-step ray, not two such rays.",
                        f"The default census uses Python/geometry labels only; its {len(default_rows)} default draws are not counted as Racket executions.",
                        "The optional baseline comparison consumes retained statistics and does not reexecute the baseline source."],
    }
    write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=730000)
    parser.add_argument("--default-seed", type=int, default=100000)
    parser.add_argument("--default-count", type=int, default=160)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    if args.default_count < 1:
        parser.error("--default-count must be positive")
    if args.out.exists():
        parser.error("--out must be a new directory; existing evidence is never overwritten")
    try:
        report = run(args)
    except FileExistsError:
        # If another process creates --out after preflight, preserve that
        # directory too rather than placing our failure receipt inside it.
        raise
    except Exception as exc:
        if args.out.is_dir():
            write_json(args.out / "failed-attempt.json", {"status": "fail", "exception": str(exc),
                       "traceback": traceback.format_exc(), "payload_argv": [sys.executable, *sys.argv],
                       "tool_sha256": digest(HERE.read_bytes())})
        raise
    print(json.dumps({"status": report["status"], "racket_grid_executions": report["racket_grid_executions"],
                      "large": report["large"]["summary"], "canonical": report["canonical"],
                      "default_geometry": report["default_geometry"]["summary"],
                      "baseline_comparison": report["baseline_comparison"], "failures": report["failures"]}, indent=2))
    return int(report["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
