#!/usr/bin/env python3
"""Source-bound reconciliation checks for the two retained 97b3f59b5cc4 returns.

The current generator intentionally supersedes both older audited sources.  This
helper proves that the current bytes still retain the useful parts of both
returns: truthful exact controls and a lesson that distinguishes components
which share a color but have opposite border fates.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Iterable, Sequence

from reviewer_support import canonical_pairs, find_root


TASK_ID = "97b3f59b5cc4"
PRIOR_RETURNS = (
    {
        "return_id": "review-abe8247bc7f3032c:v0001",
        "retained_improvement": (
            "accept canonical component structure and teach repeated-color "
            "components with opposite border fates"
        ),
    },
    {
        "return_id": "review-30f42b66093700f5:v0001",
        "retained_improvement": (
            "replace ignored or falsely bounded controls with four exact, "
            "auditable axes and reject retired controls"
        ),
    },
)
RETIRED_CONTROLS = ("palette_size", "n_distinct_colors")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_generator(root: Path) -> tuple[ModuleType, Path, str]:
    source = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"reconcile_generator_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source, _sha256(source)


def _failure(**fields: object) -> dict[str, object]:
    return dict(fields)


def _check_canonical(generator: ModuleType, root: Path) -> dict[str, object]:
    pairs = canonical_pairs(TASK_ID, root=root)
    failures: list[dict[str, object]] = []
    for pair in pairs:
        grid = pair["input"]
        errors = list(generator.self_check(grid))
        strict_errors = list(generator.strict_canonical_like(grid))
        predicted = generator.rule_mirror(grid)
        if errors or strict_errors or predicted != pair["output"]:
            failures.append(
                _failure(
                    variant=pair["variant"],
                    split=pair["split"],
                    pair_index=pair["pair_index"],
                    self_check=errors,
                    strict_canonical_like=strict_errors,
                    output_matches=predicted == pair["output"],
                )
            )
    return {"pairs": len(pairs), "failures": failures}


def _check_exact_controls(
    generator: ModuleType,
    *,
    sample_indexes: Sequence[int],
    difficulties: Sequence[str | None],
) -> dict[str, object]:
    failures: list[dict[str, object]] = []
    cases = 0
    for difficulty in difficulties:
        for sample_index in sample_indexes:
            for grid_h in range(5, 13):
                for grid_w in range(7, 15):
                    for n_border in range(1, 5):
                        for n_interior in range(1, 5):
                            expected = {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "n_border": n_border,
                                "n_interior": n_interior,
                            }
                            cases += 1
                            try:
                                first = generator.generate(
                                    23097,
                                    sample_index,
                                    difficulty=difficulty,
                                    **expected,
                                )
                                second = generator.generate(
                                    23097,
                                    sample_index,
                                    difficulty=difficulty,
                                    **expected,
                                )
                                observed = generator.observe_overrides(first)
                                errors = list(
                                    generator.self_check(
                                        first, difficulty=difficulty
                                    )
                                )
                                if first != second or observed != expected or errors:
                                    failures.append(
                                        _failure(
                                            difficulty=difficulty,
                                            sample_index=sample_index,
                                            requested=expected,
                                            observed=observed,
                                            deterministic=first == second,
                                            self_check=errors,
                                        )
                                    )
                            except Exception as exc:  # evidence must retain crashes
                                failures.append(
                                    _failure(
                                        difficulty=difficulty,
                                        sample_index=sample_index,
                                        requested=expected,
                                        exception=f"{type(exc).__name__}: {exc}",
                                    )
                                )
    return {"cases": cases, "failures": failures}


def _check_retired_controls(generator: ModuleType) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for name in RETIRED_CONTROLS:
        try:
            generator.generate(0, 0, **{name: 3})
        except ValueError as exc:
            results.append(
                {
                    "control": name,
                    "rejected": "unknown override" in str(exc),
                    "error": str(exc),
                }
            )
        except Exception as exc:  # wrong failure class is still evidence
            results.append(
                {
                    "control": name,
                    "rejected": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            results.append({"control": name, "rejected": False, "error": None})
    return {
        "controls": results,
        "all_rejected": all(row["rejected"] for row in results),
    }


def _check_teaching_windows(
    generator: ModuleType,
    *,
    seeds: Sequence[int],
    difficulties: Sequence[str | None],
    sample_count: int,
) -> dict[str, object]:
    if sample_count < 3:
        raise ValueError("ordinary_sample_count must be at least 3")
    failures: list[dict[str, object]] = []
    windows = 0
    samples = 0
    for seed in seeds:
        for difficulty in difficulties:
            grids = [
                generator.generate(seed, index, difficulty=difficulty)
                for index in range(sample_count)
            ]
            samples += len(grids)
            for start in range(sample_count - 2):
                window = grids[start : start + 3]
                windows += 1
                shared_fates = any(
                    generator._has_shared_color_opposite_fates(grid)
                    for grid in window
                )
                refutes_global_color = any(
                    generator._keep_border_colors_globally(grid)
                    != generator.rule_mirror(grid)
                    for grid in window
                )
                valid = all(
                    generator.self_check(grid, difficulty=difficulty) == []
                    for grid in window
                )
                if not (shared_fates and refutes_global_color and valid):
                    failures.append(
                        _failure(
                            seed=seed,
                            difficulty=difficulty,
                            start_index=start,
                            shared_color_opposite_fates=shared_fates,
                            refutes_global_color=refutes_global_color,
                            all_self_check=valid,
                        )
                    )
    return {
        "samples": samples,
        "windows": windows,
        "window_size": 3,
        "failures": failures,
    }


def _check_counterexample(
    generator: ModuleType,
    root: Path,
    generator_sha256: str,
) -> dict[str, object]:
    path = (
        root
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "shared-color-opposite-fates.json"
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    origin = record["origin"]
    regenerated = generator.generate(
        origin["seed"],
        origin["sample_index"],
        difficulty=origin.get("difficulty"),
        **origin.get("overrides", {}),
    )
    intended = generator.rule_mirror(regenerated)
    rival = generator._keep_border_colors_globally(regenerated)
    return {
        "path": str(path.relative_to(root)),
        "generator_sha256": record.get("generator_sha256"),
        "current_generator_sha256": generator_sha256,
        "source_bound": record.get("generator_sha256") == generator_sha256,
        "replayed_exactly": (
            regenerated == record.get("input")
            and intended == record.get("intended_output")
        ),
        "self_check": generator.self_check(regenerated),
        "shared_color_opposite_fates": generator._has_shared_color_opposite_fates(
            regenerated
        ),
        "rival_differs": rival != intended and rival == record.get("rival", {}).get("output"),
    }


def build_report(
    root: Path,
    *,
    exact_sample_indexes: Sequence[int] = (0, 1, 2, 3),
    exact_difficulties: Sequence[str | None] = (None, "easy", "medium", "hard"),
    ordinary_seeds: Sequence[int] = tuple(range(10)),
    ordinary_difficulties: Sequence[str | None] = (
        None,
        "easy",
        "medium",
        "hard",
    ),
    ordinary_sample_count: int = 12,
) -> dict[str, object]:
    """Build a finite, source-bound reconciliation report for the current task."""
    root = Path(root).resolve()
    generator, source, generator_sha256 = _load_generator(root)
    canonical = _check_canonical(generator, root)
    exact_controls = _check_exact_controls(
        generator,
        sample_indexes=tuple(exact_sample_indexes),
        difficulties=tuple(exact_difficulties),
    )
    retired_controls = _check_retired_controls(generator)
    teaching_windows = _check_teaching_windows(
        generator,
        seeds=tuple(ordinary_seeds),
        difficulties=tuple(ordinary_difficulties),
        sample_count=ordinary_sample_count,
    )
    counterexample = _check_counterexample(generator, root, generator_sha256)
    checks_passed = (
        not canonical["failures"]
        and not exact_controls["failures"]
        and bool(retired_controls["all_rejected"])
        and not teaching_windows["failures"]
        and bool(counterexample["source_bound"])
        and bool(counterexample["replayed_exactly"])
        and not counterexample["self_check"]
        and bool(counterexample["shared_color_opposite_fates"])
        and bool(counterexample["rival_differs"])
    )
    return {
        "schema": "arcpuzzles-conflict-reconciliation-v1",
        "status": (
            "reconciled_current_source" if checks_passed else "conflict_detected"
        ),
        "checks_passed": checks_passed,
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": generator_sha256,
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "decision": (
            "retain the current merged generator unchanged; add executable "
            "regression evidence that both useful prior-return improvements remain"
        ),
        "prior_returns": [dict(row) for row in PRIOR_RETURNS],
        "canonical": canonical,
        "exact_controls": exact_controls,
        "retired_controls": retired_controls,
        "teaching_windows": teaching_windows,
        "retained_counterexample": counterexample,
        "scope": {
            "finite": True,
            "training_approved": False,
            "variant_approved": False,
            "note": (
                "This manifest proves only the enumerated canonical, exact-axis, "
                "ordinary-window, and retained-counterexample checks."
            ),
        },
    }


def _parse_csv_ints(value: str) -> tuple[int, ...]:
    return tuple(int(piece) for piece in value.split(",") if piece.strip())


def _parse_difficulties(value: str) -> tuple[str | None, ...]:
    result: list[str | None] = []
    for piece in value.split(","):
        piece = piece.strip()
        if not piece:
            continue
        result.append(None if piece.lower() in {"none", "null"} else piece)
    return tuple(result)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--exact-sample-indexes", default="0,1,2,3")
    parser.add_argument("--exact-difficulties", default="none,easy,medium,hard")
    parser.add_argument("--ordinary-seeds", default=",".join(map(str, range(10))))
    parser.add_argument("--ordinary-difficulties", default="none,easy,medium,hard")
    parser.add_argument("--ordinary-sample-count", type=int, default=12)
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = (args.root or find_root(__file__)).resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    if out.exists():
        parser.error(f"refusing to overwrite existing output: {out}")
    report = build_report(
        root,
        exact_sample_indexes=_parse_csv_ints(args.exact_sample_indexes),
        exact_difficulties=_parse_difficulties(args.exact_difficulties),
        ordinary_seeds=_parse_csv_ints(args.ordinary_seeds),
        ordinary_difficulties=_parse_difficulties(args.ordinary_difficulties),
        ordinary_sample_count=args.ordinary_sample_count,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "status": report["status"]}, sort_keys=True))
    return 0 if report["status"] == "reconciled_current_source" else 1


if __name__ == "__main__":
    raise SystemExit(main())
