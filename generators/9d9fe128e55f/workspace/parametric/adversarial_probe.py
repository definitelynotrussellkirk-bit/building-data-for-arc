#!/usr/bin/env python3
"""Bounded adversarial and protected-Racket probe for 9d9fe128e55f.

The probe is intentionally task-local so later reviewers can replay the exact
reasoning attacks without reconstructing an ad-hoc command.  Python checks hunt
for teaching shortcuts across seeds/counts/settings; the protected section also
re-executes canonical, base-generator, and parametric labels in Racket.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9d9fe128e55f"
HOME = Path(__file__).resolve().parent
ROOT = find_root(__file__)
DEFAULT_SEEDS = (0, 1, 5, 17, 31, 97)
DEFAULT_DEMO_COUNTS = (2, 3, 6)


def _load_local(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HOME / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {HOME / filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load_local("parametric_9d9_probe_prototype", "prototype.py")
adapter = _load_local("parametric_9d9_probe_adapter", "adapter.py")


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _record_failure(
    failures: list[dict[str, Any]],
    *,
    seed: int,
    demos: int,
    mode: str,
    check: str,
    detail: Any,
) -> None:
    failures.append(
        {
            "seed": seed,
            "demos": demos,
            "mode": mode,
            "check": check,
            "detail": detail,
        }
    )


def run_python_probe(
    *,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    demo_counts: Iterable[int] = DEFAULT_DEMO_COUNTS,
) -> dict[str, Any]:
    """Attack the smallest promised lesson without invoking Racket."""
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    bad_cases: list[dict[str, Any]] = []
    rivals: set[str] = set()
    case_count = 0
    matched_input_checks = 0
    max_rows = max_cols = 0

    for seed in seeds:
        for demos in demo_counts:
            episodes = {
                mode: adapter.generate(
                    seed,
                    {"rank_policy": mode},
                    demos=demos,
                    queries=4,
                )
                for mode in prototype.MODES
            }
            left_inputs = [
                pair["input"]
                for pair in episodes[prototype.MODES[0]]["train"]
                + episodes[prototype.MODES[0]]["test"]
            ]
            right_inputs = [
                pair["input"]
                for pair in episodes[prototype.MODES[1]]["train"]
                + episodes[prototype.MODES[1]]["test"]
            ]
            matched_input_checks += 1
            if left_inputs != right_inputs:
                _record_failure(
                    bad_cases,
                    seed=seed,
                    demos=demos,
                    mode="both",
                    check="matched_inputs",
                    detail="settings changed the generated inputs",
                )

            if not any(
                left_pair["output"] != right_pair["output"]
                for left_pair, right_pair in zip(
                    episodes[prototype.MODES[0]]["train"]
                    + episodes[prototype.MODES[0]]["test"],
                    episodes[prototype.MODES[1]]["train"]
                    + episodes[prototype.MODES[1]]["test"],
                )
            ):
                _record_failure(
                    bad_cases,
                    seed=seed,
                    demos=demos,
                    mode="both",
                    check="semantic_branch",
                    detail="settings never changed a label",
                )

            for mode, episode in episodes.items():
                case_count += 1
                pairs = episode["train"] + episode["test"]
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    _record_failure(
                        bad_cases,
                        seed=seed,
                        demos=demos,
                        mode=mode,
                        check="counts",
                        detail={
                            "train": len(episode["train"]),
                            "test": len(episode["test"]),
                        },
                    )
                encoded = [_grid_key(pair["input"]) for pair in pairs]
                if len(encoded) != len(set(encoded)):
                    _record_failure(
                        bad_cases,
                        seed=seed,
                        demos=demos,
                        mode=mode,
                        check="duplicate_inputs",
                        detail="episode contains duplicate visible inputs",
                    )
                for pair_index, pair in enumerate(pairs):
                    rows, cols = len(pair["input"]), len(pair["input"][0])
                    max_rows, max_cols = max(max_rows, rows), max(max_cols, cols)
                    expected = prototype.python_mirror(pair["input"], mode)
                    if pair["output"] != expected:
                        _record_failure(
                            bad_cases,
                            seed=seed,
                            demos=demos,
                            mode=mode,
                            check="python_label",
                            detail=pair_index,
                        )

                standard = prototype.adversarial_survivors(episode["train"], mode)
                if standard:
                    _record_failure(
                        bad_cases,
                        seed=seed,
                        demos=demos,
                        mode=mode,
                        check="standard_rivals",
                        detail=standard,
                    )
                extended = prototype.extended_rival_results(
                    episode["train"], episode["test"], mode
                )
                rivals.update(row["name"] for row in extended)
                query_changing_survivors = [
                    row
                    for row in extended
                    if row["fits_demos"] and row["query_disagreements"]
                ]
                if query_changing_survivors:
                    _record_failure(
                        bad_cases,
                        seed=seed,
                        demos=demos,
                        mode=mode,
                        check="query_changing_rivals",
                        detail=query_changing_survivors,
                    )

    return {
        "schema": "arcpuzzles-parametric-adversarial-probe-v1",
        "task_id": TASK_ID,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "case_count": case_count,
        "matched_input_checks": matched_input_checks,
        "max_grid": [max_rows, max_cols],
        "rivals": sorted(rivals),
        "bad_cases": bad_cases,
    }


def _run_rule(program: str, grid: list[list[int]], bridge) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    bridge.define_grid("g", grid)
    return bridge.eval_text(f"({wrap_rule(program)} g)")


def run_protected_probe(*, seed: int = 17, demos: int = 3) -> dict[str, Any]:
    """Replay representative canonical/base/parametric labels in protected Racket."""
    from arc_repl.racket_bridge import RacketBridge

    canonical_program = prototype.canonical_source()
    ledger_rows = []
    ledger_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            ledger_rows.append(row)
    if len(ledger_rows) != 1:
        raise AssertionError(f"expected one canonical row, found {len(ledger_rows)}")
    if ledger_rows[0].get("program_solution") != canonical_program:
        raise AssertionError("task-local canonical.rkt differs from selected ledger source")

    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    canonical_checks = 0
    base_checks = 0
    parametric_checks = 0
    base_cases: list[dict[str, Any]] = []

    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            actual = _run_rule(canonical_program, pair["input"], bridge)
            if actual != pair["output"]:
                raise AssertionError(
                    "canonical Racket mismatch at "
                    f"{pair['split']}[{pair['pair_index']}]"
                )
            canonical_checks += 1

        ordinary = [(11, index, {}) for index in range(4)]
        boundaries = [
            (
                101,
                0,
                {
                    "grid_h": 8,
                    "left_w": 7,
                    "right_w": 1,
                    "n_blobs": 3,
                    "palette_order": "descending",
                    "distractor": True,
                },
            ),
            (
                102,
                2,
                {
                    "grid_h": 18,
                    "left_w": 16,
                    "right_w": 3,
                    "n_blobs": 4,
                    "palette_order": "mixed",
                    "distractor": True,
                },
            ),
        ]
        for case_seed, sample_index, overrides in ordinary + boundaries:
            grid = generator.generate(case_seed, sample_index, **overrides)
            errors = generator.self_check(grid, meta={"overrides": overrides})
            if errors:
                raise AssertionError(f"base self_check failed: {errors}")
            observed = generator.observe_overrides(grid)
            for name, value in overrides.items():
                if observed.get(name) != value:
                    raise AssertionError(
                        f"base override {name}={value!r} realized as {observed.get(name)!r}"
                    )
            expected = generator.rule_mirror(grid)
            actual = _run_rule(canonical_program, grid, bridge)
            if actual != expected:
                raise AssertionError(
                    f"base Racket mismatch for sample_index={sample_index}, overrides={overrides}"
                )
            base_checks += 1
            base_cases.append(
                {
                    "seed": case_seed,
                    "sample_index": sample_index,
                    "overrides": overrides,
                    "shape": [len(grid), len(grid[0])],
                }
            )

        for mode in prototype.MODES:
            episode = adapter.generate(
                seed,
                {"rank_policy": mode},
                demos=demos,
                queries=4,
            )
            program = adapter.program({"rank_policy": mode})
            for pair_index, pair in enumerate(episode["train"] + episode["test"]):
                actual = _run_rule(program, pair["input"], bridge)
                if actual != pair["output"]:
                    raise AssertionError(
                        f"parametric Racket mismatch for {mode} pair {pair_index}"
                    )
                parametric_checks += 1

    return {
        "canonical_source_sha256": hashlib.sha256(
            canonical_program.encode("utf-8")
        ).hexdigest(),
        "base_source": str(source_path.relative_to(ROOT)),
        "base_source_sha256": source_sha256,
        "canonical_racket_labels": canonical_checks,
        "base_racket_labels": base_checks,
        "parametric_racket_labels": parametric_checks,
        "parametric_seed": seed,
        "parametric_demos": demos,
        "base_cases": base_cases,
    }


def build_report(*, include_racket: bool = True) -> dict[str, Any]:
    report = run_python_probe()
    if report["bad_cases"]:
        raise AssertionError(f"adversarial probe found failures: {report['bad_cases']}")
    report["protected_racket"] = run_protected_probe() if include_racket else None
    return report


def _parse_int_csv(value: str) -> tuple[int, ...]:
    try:
        result = tuple(int(item) for item in value.split(",") if item != "")
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected comma-separated integers") from error
    if not result:
        raise argparse.ArgumentTypeError("at least one integer is required")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seeds", type=_parse_int_csv, default=DEFAULT_SEEDS)
    parser.add_argument(
        "--demo-counts", type=_parse_int_csv, default=DEFAULT_DEMO_COUNTS
    )
    parser.add_argument("--skip-racket", action="store_true")
    args = parser.parse_args(argv)

    report = run_python_probe(seeds=args.seeds, demo_counts=args.demo_counts)
    if not args.skip_racket:
        report["protected_racket"] = run_protected_probe()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if report["bad_cases"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
