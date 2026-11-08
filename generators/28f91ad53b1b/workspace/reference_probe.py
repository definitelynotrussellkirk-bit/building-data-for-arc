"""Source-bound independent probe for generator 28f91ad53b1b.

The probe checks the selected generator against an independent per-seed BFS
implementation, dynamically exercises every declared rival, exhausts all small
axis boundaries, and checks every query rotation of the five-profile curriculum.
With ``--racket`` it also executes the canonical authority through the public
``arcpuzzles.Catalog.apply`` API.  It is review tooling, not a label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "28f91ad53b1b"
BANDS = ("easy", "medium", "hard")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_task() -> dict[str, Any]:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent from {path}")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical_task()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Implement the written rule without importing generator helpers."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be ARC colors 0..9")

    infinity = height * width + 1
    seeds = [
        (value, row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]

    maps: list[tuple[int, list[list[int]]]] = []
    for color, start_row, start_col in seeds:
        distance = [[infinity] * width for _ in range(height)]
        distance[start_row][start_col] = 0
        queue = deque([(start_row, start_col)])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and grid[nr][nc] != 5
                    and distance[nr][nc] == infinity
                ):
                    distance[nr][nc] = distance[row][col] + 1
                    queue.append((nr, nc))
        maps.append((color, distance))

    output = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                output[row][col] = 5
                continue
            candidates = [
                (distance[row][col], color)
                for color, distance in maps
                if distance[row][col] < infinity
            ]
            output[row][col] = min(candidates)[1] if candidates else 0
    return output


def _safe_call(rule, grid, expected) -> tuple[bool, str | None]:
    try:
        return rule(deepcopy(grid)) == expected, None
    except Exception as exc:  # diagnostic boundary: retain exact callable error
        return False, f"{type(exc).__name__}: {exc}"


def _counterexample(module) -> dict[str, Any]:
    generation = {
        "seed": 314159,
        "sample_index": 7,
        "difficulty": "medium",
        "overrides": {
            "grid_h": 8,
            "grid_w": 10,
            "n_seeds": 2,
            "texture": "tie_order",
        },
    }
    grid = module.generate(
        generation["seed"],
        generation["sample_index"],
        difficulty=generation["difficulty"],
        **generation["overrides"],
    )
    intended = independent_rule(grid)
    shortcut = module.CANONICAL_SHORTCUTS["row_major_tie_break"](deepcopy(grid))
    differences = [
        {
            "row": row,
            "col": col,
            "intended": intended[row][col],
            "row_major_tie_break": shortcut[row][col],
        }
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if intended[row][col] != shortcut[row][col]
    ]
    return {
        "generation": generation,
        "input_sha256": grid_sha256(grid),
        "input": grid,
        "intended_output": intended,
        "row_major_tie_break_output": shortcut,
        "differences": differences,
    }


def _canonical_report(module) -> dict[str, Any]:
    pairs = canonical_pairs()
    independent_matches = 0
    mirror_matches = 0
    validation_errors: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs):
        independent_matches += independent_rule(pair["input"]) == pair["output"]
        mirror_matches += module.rule_mirror(deepcopy(pair["input"])) == pair["output"]
        findings = module.self_check(deepcopy(pair["input"]))
        if findings:
            validation_errors.append({"pair": index, "findings": findings})

    shortcut_fit: dict[str, dict[str, Any]] = {}
    for name, rival in sorted(dict(getattr(module, "CANONICAL_SHORTCUTS", {})).items()):
        matches = 0
        errors: list[dict[str, Any]] = []
        for index, pair in enumerate(pairs):
            matched, error = _safe_call(rival, pair["input"], pair["output"])
            matches += matched
            if error:
                errors.append({"pair": index, "error": error})
        shortcut_fit[name] = {
            "matches": matches,
            "total": len(pairs),
            "fits_all": matches == len(pairs) and not errors,
            "errors": errors,
        }

    return {
        "pairs": len(pairs),
        "independent_matches": independent_matches,
        "generator_mirror_matches": mirror_matches,
        "validation_errors": validation_errors,
        "canonical_shortcuts": shortcut_fit,
    }


def _rotation_report(module, seeds_per_band: int) -> dict[str, Any]:
    if seeds_per_band < 1:
        raise ValueError("seeds_per_band must be positive")
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}))
    profile_counts: Counter[str] = Counter()
    rival_refutations: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    windows = 0
    rotations = 0

    for band_index, band in enumerate(BANDS):
        for offset in range(seeds_per_band):
            seed = 280000 + band_index * 10000 + offset
            for start in range(5):
                pairs = []
                for pair_offset in range(6):
                    sample_index = start + pair_offset
                    grid = module.generate(seed, sample_index, difficulty=band)
                    expected = independent_rule(grid)
                    if module.rule_mirror(deepcopy(grid)) != expected:
                        failures.append(
                            {
                                "kind": "python_mirror_mismatch",
                                "band": band,
                                "seed": seed,
                                "sample_index": sample_index,
                            }
                        )
                    profile_counts[module.observe_overrides(grid)["texture"]] += 1
                    unique_inputs.add(grid_sha256(grid))
                    pairs.append({"input": grid, "output": expected})

                windows += 1
                ordinary = module.lesson_identifiable(pairs[:5], pairs[5])
                if ordinary:
                    failures.append(
                        {
                            "kind": "ordinary_lesson",
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "reasons": ordinary,
                        }
                    )
                for name, rival in competitors.items():
                    if any(
                        rival(deepcopy(pair["input"])) != pair["output"]
                        for pair in pairs[:5]
                    ):
                        rival_refutations[name] += 1
                    else:
                        failures.append(
                            {
                                "kind": "rival_survives_ordinary_demos",
                                "rival": name,
                                "band": band,
                                "seed": seed,
                                "start": start,
                            }
                        )

                for query_index, query in enumerate(pairs):
                    rotations += 1
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    reasons = module.lesson_identifiable(demos, query)
                    if reasons:
                        failures.append(
                            {
                                "kind": "query_rotation",
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "query_texture": module.observe_overrides(query["input"])["texture"],
                                "reasons": reasons,
                            }
                        )

    return {
        "seeds_per_band": seeds_per_band,
        "bands": list(BANDS),
        "starts_per_seed": 5,
        "windows": windows,
        "rotations": rotations,
        "ambiguous": sum(item["kind"] in {"ordinary_lesson", "query_rotation"} for item in failures),
        "unique_inputs": len(unique_inputs),
        "profile_counts": dict(sorted(profile_counts.items())),
        "rival_refutations": dict(sorted(rival_refutations.items())),
        "failures": failures,
    }


def _override_report(module) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    cases = 0
    for band in BANDS:
        for grid_h in (8, 10):
            for grid_w in (10, 12):
                for n_seeds in (2, 5):
                    for texture in module.SCHEDULE_PROFILES:
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_seeds": n_seeds,
                            "texture": texture,
                        }
                        try:
                            grid = module.generate(
                                910000 + cases,
                                cases % 17,
                                difficulty=band,
                                **requested,
                            )
                            observed = module.observe_overrides(grid)
                            findings = module.self_check(grid, difficulty=band)
                            mirror_matches = module.rule_mirror(deepcopy(grid)) == independent_rule(grid)
                            if observed != requested or findings or not mirror_matches:
                                errors.append(
                                    {
                                        "band": band,
                                        "requested": requested,
                                        "observed": observed,
                                        "findings": findings,
                                        "mirror_matches": mirror_matches,
                                    }
                                )
                        except Exception as exc:
                            errors.append(
                                {
                                    "band": band,
                                    "requested": requested,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            )
                        cases += 1
    return {"cases": cases, "errors": errors}


def _racket_report(module, grids: Iterable[list[list[int]]]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog

    grids = list(grids)
    receipt = Catalog(ROOT).apply(TASK, grids, reference="canonical", timeout=300)
    results = receipt["results"]
    expected = [independent_rule(grid) for grid in grids]
    mismatches = [
        index
        for index, (row, wanted) in enumerate(zip(results, expected, strict=True))
        if row.get("error") is not None or row.get("output") != wanted
    ]
    return {
        "status": "passed" if not mismatches and receipt.get("rule_hash_matches_catalog") else "failed",
        "checked": len(grids),
        "mismatches": mismatches,
        "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
        "executed_rule_hash": receipt.get("executed_rule_hash"),
        "catalog_rule_hash": receipt.get("catalog_rule_hash"),
        "generator_sha256": receipt.get("generator_sha256"),
        "elapsed_seconds": receipt.get("elapsed_seconds"),
        "results": results,
    }


def audit(module, *, seeds_per_band: int = 10, use_racket: bool = False) -> dict[str, Any]:
    canonical = _canonical_report(module)
    rotation = _rotation_report(module, seeds_per_band)
    overrides = _override_report(module)
    counterexample = _counterexample(module)

    racket_inputs = [pair["input"] for pair in canonical_pairs()]
    racket_inputs.append(counterexample["input"])
    racket = (
        _racket_report(module, racket_inputs)
        if use_racket
        else {"status": "not_requested", "checked": 0}
    )
    if use_racket and racket.get("status") == "passed":
        counterexample["intended_output_racket"] = racket["results"][-1]["output"]

    canonical_ok = (
        canonical["independent_matches"] == canonical["pairs"]
        and canonical["generator_mirror_matches"] == canonical["pairs"]
        and not canonical["validation_errors"]
        and all(item["fits_all"] for item in canonical["canonical_shortcuts"].values())
    )
    counterexample_ok = bool(counterexample["differences"])
    passed = (
        canonical_ok
        and not rotation["failures"]
        and not overrides["errors"]
        and counterexample_ok
        and (not use_racket or racket.get("status") == "passed")
    )

    generator_path = Path(module.__file__).resolve()
    canonical_row = canonical_task()
    normalized_rule = " ".join(canonical_row["program_solution"].split())
    return {
        "schema": "28f91ad53b1b-reference-probe-v1",
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": sha256_bytes(generator_path.read_bytes()),
        "probe_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "declared_rule_hash": module.RULE_HASH,
        "canonical_rule_hash": sha256_bytes(normalized_rule.encode())[:12],
        "canonical": canonical,
        "rotation_probe": rotation,
        "overrides": overrides,
        "question_counterexample": counterexample,
        "racket": racket,
        "limits": [
            "Finite declared-rival checks do not prove unique induction against every conceivable rule.",
            "The rotation probe enumerates all five schedule starts for a bounded deterministic seed cohort.",
            "The independent Python implementation is supplementary; canonical Racket remains authoritative.",
        ],
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, help="alternate selected generator.py")
    parser.add_argument("--seeds-per-band", type=int, default=10)
    parser.add_argument("--racket", action="store_true", help="require public canonical Racket parity")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    module = load_generator(args.generator)
    report = audit(module, seeds_per_band=args.seeds_per_band, use_racket=args.racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "task_id": report["task_id"],
                "generator_version": report["generator_version"],
                "generator_sha256": report["generator_sha256"],
                "canonical": report["canonical"],
                "rotation_probe": {
                    key: report["rotation_probe"][key]
                    for key in ("windows", "rotations", "ambiguous", "unique_inputs")
                },
                "overrides": {
                    "cases": report["overrides"]["cases"],
                    "errors": len(report["overrides"]["errors"]),
                },
                "racket": {
                    key: report["racket"].get(key)
                    for key in ("status", "checked", "mismatches")
                    if key in report["racket"]
                },
                "passed": report["passed"],
            },
            indent=2,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
