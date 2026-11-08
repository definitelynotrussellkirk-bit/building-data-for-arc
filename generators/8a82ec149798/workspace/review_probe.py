"""Source-bound Racket differential probe for generator 8a82ec149798.

Run from a review packet through ``run_with_racket.py``.  The probe derives
all labels with the canonical Racket program, compares the diagnostic Python
mirror only after that, checks the five-example teaching curriculum, and
retains the first concrete counterexample to every declared shortcut rival.
It is review evidence, not an alternate label authority or admission gate.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any


TASK_ID = "8a82ec149798"
BANDS = ("easy", "medium", "hard")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_generator(repo_root: Path):
    runtime = repo_root / "shared/runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    path = repo_root / f"generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location(f"review_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _load_canonical(repo_root: Path) -> tuple[dict[str, Any], Path]:
    path = repo_root / "shared/data/canonical/puzzles.jsonl"
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row, path
    raise RuntimeError(f"canonical task {TASK_ID} is missing from {path}")


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _different_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col, left[row][col], right[row][col]]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def run_probe(
    repo_root: Path,
    *,
    seed: int = 20260928,
    count_per_band: int = 20,
    lesson_windows_per_band: int = 4,
) -> dict[str, Any]:
    """Run a deterministic source-bound review census and return JSON data."""
    if count_per_band < 5:
        raise ValueError("count_per_band must be at least 5")
    if lesson_windows_per_band < 1:
        raise ValueError("lesson_windows_per_band must be positive")

    repo_root = repo_root.resolve()
    generator, generator_path = _load_generator(repo_root)
    canonical, canonical_path = _load_canonical(repo_root)

    runtime = repo_root / "shared/runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    # rule_wrap imports the packet's shared/tools directory by its staged
    # runtime name, ``scripts``.  Direct packet execution has no physical
    # scripts/ directory, so expose the same package boundary without copying
    # or mutating repository files.
    if "scripts" not in sys.modules:
        scripts_package = types.ModuleType("scripts")
        scripts_package.__path__ = [str(repo_root / "shared/tools")]
        sys.modules["scripts"] = scripts_package
    from puzzle_generators import runner

    bridge, function_name = runner._open_bridge_with_rule(
        runner.wrap_rule(canonical["program_solution"])
    )
    failures: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    band_rows: dict[str, Any] = {}
    lesson_rows: dict[str, Any] = {}
    first_rival_witness: dict[str, Any] = {}
    witness_counts: Counter[str] = Counter()
    rival_disagreements: Counter[str] = Counter()
    racket_calls = 0

    def apply_racket(name: str, grid: list[list[int]]) -> list[list[int]] | None:
        nonlocal racket_calls
        before = copy.deepcopy(grid)
        try:
            result = runner._apply_rule(bridge, function_name, grid)
            racket_calls += 1
        except Exception as exc:  # evidence should retain exact failure context
            failures.append(
                {
                    "name": name,
                    "kind": "racket_exception",
                    "error": f"{type(exc).__name__}: {exc}",
                    "input": before,
                }
            )
            return None
        if grid != before:
            failures.append({"name": name, "kind": "racket_mutated_input"})
        if not runner.is_well_formed(result):
            failures.append(
                {"name": name, "kind": "malformed_racket_output", "output": result}
            )
            return None
        return result

    try:
        for split in ("train", "test"):
            for index, pair in enumerate(canonical.get(split, [])):
                name = f"canonical:{split}:{index}"
                grid = copy.deepcopy(pair["input"])
                reasons = generator.self_check(grid)
                strict_reasons = generator.strict_canonical_like(grid)
                output = apply_racket(name, grid)
                row = {
                    "name": name,
                    "self_check": reasons,
                    "strict_canonical_like": strict_reasons,
                    "label_match": output == pair["output"],
                    "mirror_match": output is not None
                    and generator.rule_mirror(grid) == output,
                }
                canonical_rows.append(row)
                if reasons or strict_reasons or not row["label_match"] or not row["mirror_match"]:
                    failures.append({"name": name, "kind": "canonical_contract", **row})

        for band in BANDS:
            profiles: Counter[str] = Counter()
            modes: Counter[str] = Counter()
            axes: Counter[str] = Counter()
            color_counts: Counter[str] = Counter()
            shapes: Counter[str] = Counter()
            unique_inputs: set[str] = set()
            band_failures_before = len(failures)

            for index in range(count_per_band):
                case_seed = seed + index
                sample_index = index
                name = f"generated:{band}:{case_seed}:{sample_index}"
                try:
                    grid = generator.generate(
                        case_seed, sample_index, difficulty=band
                    )
                    repeat = generator.generate(
                        case_seed, sample_index, difficulty=band
                    )
                except Exception as exc:
                    failures.append(
                        {
                            "name": name,
                            "kind": "generation_exception",
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                if grid != repeat:
                    failures.append({"name": name, "kind": "nondeterministic_generation"})
                reasons = generator.self_check(grid)
                if reasons:
                    failures.append(
                        {"name": name, "kind": "self_check", "reasons": reasons}
                    )
                    continue
                output = apply_racket(name, grid)
                if output is None:
                    continue
                mirror = generator.rule_mirror(copy.deepcopy(grid))
                if mirror != output:
                    failures.append(
                        {
                            "name": name,
                            "kind": "python_mirror_mismatch",
                            "input": grid,
                            "racket_output": output,
                            "mirror_output": mirror,
                        }
                    )
                observed = generator.observe_overrides(grid)
                profile = generator.schedule_profile(case_seed, sample_index, band)
                profiles[profile] += 1
                modes[str(observed["distractor_mode"])] += 1
                axes[str(observed["axis_profile"])] += 1
                color_counts[str(observed["n_source_colors"])] += 1
                shapes[f"{observed['grid_h']}x{observed['grid_w']}"] += 1
                unique_inputs.add(_grid_key(grid))

                for witness_name, witness in generator.SEMANTIC_WITNESSES.items():
                    if not witness(grid):
                        continue
                    witness_counts[witness_name] += 1
                    for rival_name in generator.WITNESS_RIVALS[witness_name]:
                        rival_output = generator.SEMANTIC_RIVALS[rival_name](
                            copy.deepcopy(grid)
                        )
                        if rival_output == output:
                            continue
                        rival_disagreements[rival_name] += 1
                        first_rival_witness.setdefault(
                            rival_name,
                            {
                                "witness": witness_name,
                                "band": band,
                                "seed": case_seed,
                                "sample_index": sample_index,
                                "input": grid,
                                "racket_output": output,
                                "rival_output": rival_output,
                                "different_cells": _different_cells(output, rival_output),
                            },
                        )

            fixed_seed_profiles = {
                generator.schedule_profile(seed, index, band) for index in range(5)
            }
            if fixed_seed_profiles != set(generator.SCHEDULE_PROFILES):
                failures.append(
                    {
                        "name": f"schedule:{band}",
                        "kind": "incomplete_five_slot_schedule",
                        "observed": sorted(fixed_seed_profiles),
                    }
                )
            band_rows[band] = {
                "draws": count_per_band,
                "new_failures": len(failures) - band_failures_before,
                "unique_inputs": len(unique_inputs),
                "profiles": dict(sorted(profiles.items())),
                "distractor_modes": dict(sorted(modes.items())),
                "axis_profiles": dict(sorted(axes.items())),
                "source_color_counts": dict(sorted(color_counts.items())),
                "shapes": dict(sorted(shapes.items())),
                "five_slot_schedule_complete": fixed_seed_profiles
                == set(generator.SCHEDULE_PROFILES),
            }

        for band in BANDS:
            clean = 0
            examples: list[dict[str, Any]] = []
            for window in range(lesson_windows_per_band):
                lesson_seed = seed + 100_000 + window
                grids = [
                    generator.generate(lesson_seed, index, difficulty=band)
                    for index in range(generator.EXAMPLES_NEEDED + 1)
                ]
                pairs = []
                for index, grid in enumerate(grids):
                    output = apply_racket(f"lesson:{band}:{window}:{index}", grid)
                    if output is None:
                        break
                    pairs.append({"input": grid, "output": output})
                if len(pairs) != generator.EXAMPLES_NEEDED + 1:
                    continue
                reasons = generator.lesson_identifiable(pairs[:-1], pairs[-1])
                examples.append({"window": window, "reasons": reasons})
                if reasons:
                    failures.append(
                        {
                            "name": f"lesson:{band}:{window}",
                            "kind": "lesson_not_identifiable",
                            "reasons": reasons,
                        }
                    )
                else:
                    clean += 1
            lesson_rows[band] = {
                "checked": lesson_windows_per_band,
                "identifiable": clean,
                "examples": examples,
            }

        difficulty_collisions = 0
        for index in range(min(count_per_band, 20)):
            grids = [
                generator.generate(seed + index, index, difficulty=band)
                for band in BANDS
            ]
            if len({_grid_key(grid) for grid in grids}) != len(BANDS):
                difficulty_collisions += 1
        if difficulty_collisions:
            failures.append(
                {
                    "name": "difficulty-separation",
                    "kind": "band_collision",
                    "count": difficulty_collisions,
                }
            )

        rejection_cases = {
            "unknown_key": {"typo_axis": 3},
            "invalid_height": {"grid_h": 5},
            "invalid_color_count": {"n_source_colors": 3},
            "invalid_axis_profile": {"axis_profile": "almost_center"},
        }
        rejected: dict[str, str] = {}
        for name, kwargs in rejection_cases.items():
            try:
                generator.generate(seed, 0, **kwargs)
            except (TypeError, ValueError) as exc:
                rejected[name] = f"{type(exc).__name__}: {exc}"
            else:
                failures.append(
                    {"name": f"override:{name}", "kind": "expected_rejection_missing"}
                )

        missing_rivals = sorted(
            set(generator.SEMANTIC_RIVALS) - set(first_rival_witness)
        )
        if missing_rivals:
            failures.append(
                {
                    "name": "semantic-rivals",
                    "kind": "missing_counterexample",
                    "rivals": missing_rivals,
                }
            )
    finally:
        bridge.shutdown()

    return {
        "schema": "mirror-source-bound-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": _sha(generator_path.read_bytes()),
        "canonical_ledger_sha256": _sha(canonical_path.read_bytes()),
        "canonical_program_sha256": _sha(canonical["program_solution"].encode()),
        "label_authority": "canonical Racket program via puzzle_generators.runner",
        "runtime_identity": getattr(bridge, "runtime_identity", None),
        "seed": seed,
        "count_per_band": count_per_band,
        "lesson_windows_per_band": lesson_windows_per_band,
        "racket_calls": racket_calls,
        "canonical": canonical_rows,
        "bands": band_rows,
        "lessons": lesson_rows,
        "difficulty_band_collisions": difficulty_collisions,
        "expected_rejections": rejected,
        "witness_counts": dict(sorted(witness_counts.items())),
        "rival_disagreements": dict(sorted(rival_disagreements.items())),
        "first_rival_witness": first_rival_witness,
        "failure_count": len(failures),
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--seed", type=int, default=20260928)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--lesson-windows", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()

    report = run_probe(
        args.repo_root,
        seed=args.seed,
        count_per_band=args.count,
        lesson_windows_per_band=args.lesson_windows,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "task_id": report["task_id"],
                "passed": report["passed"],
                "failure_count": report["failure_count"],
                "racket_calls": report["racket_calls"],
                "rival_disagreements": report["rival_disagreements"],
                "out": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return int(args.require_clean and not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
