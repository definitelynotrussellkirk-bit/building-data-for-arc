"""Finite protected-Racket teaching audit for the rotation relay family.

The audit fits a declared finite set of rival programs on demonstrations only.
Queries are then used solely to detect a rival that survived the demonstrations
but changes a selected answer.  It is deliberately a bounded diagnostic, not a
claim of universal identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]


def _adjacent(name: str):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_148acacd84d9_audit_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = _adjacent("adapter")
RULES = _adjacent("rules")

SETTINGS = (
    {"post_rotation": "none"},
    {"post_rotation": "marker_relay"},
)
RIVAL_KINDS = (
    "skip_a",
    "skip_b",
    "wrong_order",
    "wrong_intermediate",
    "opposite_second_edge",
    "always_top",
    "always_left",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _demo_counts(value: int | Iterable[int]) -> tuple[int, ...]:
    values = (value,) if type(value) is int else tuple(value)
    if not values or any(type(item) is not int or item < 2 or item > 6 for item in values):
        raise ValueError("demos must be an integer or non-empty iterable of integers in 2..6")
    if len(set(values)) != len(values):
        raise ValueError("demo counts must be unique")
    return values


def _seeds(value: Iterable[int]) -> tuple[int, ...]:
    values = tuple(value)
    if not values or any(type(item) is not int or item < 0 or item > 2**63 - 1 for item in values):
        raise ValueError("seeds must be a non-empty iterable of exact integers in 0..2**63-1")
    if len(set(values)) != len(values):
        raise ValueError("seeds must be unique")
    return values


def _candidate_programs() -> tuple[tuple[str, str], ...]:
    return (
        ("declared_none", RULES.program(SETTINGS[0])),
        ("declared_marker_relay", RULES.program(SETTINGS[1])),
        *((kind, RULES.counterfactual_program(kind)) for kind in RIVAL_KINDS),
    )


def audit(
    out: Path | str,
    seeds: Iterable[int] = (0, 17),
    demos: int | Iterable[int] = (2, 3, 6),
    queries: int = 4,
) -> dict:
    """Run the finite teaching screen and atomically write a JSON report."""
    if type(queries) is not int or queries < 1 or queries > 4:
        raise ValueError("queries must be an exact integer in 1..4")
    seed_values = _seeds(seeds)
    demo_values = _demo_counts(demos)
    out_path = Path(out)

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import normalize_grid

    candidates = _candidate_programs()
    names = [name for name, _ in candidates]
    if len(names) != len(set(names)):
        raise ValueError("rival names must be unique")

    source_files = (
        TASK_HOME / "generator.py",
        HERE / "adapter.py",
        HERE / "prototype.py",
        HERE / "rules.py",
        HERE / "canonical.rkt",
        HERE / "promotion.json",
        Path(__file__),
    )
    report = {
        "schema": "148acacd84d9-protected-racket-teaching-audit-v1",
        "task_id": "148acacd84d9",
        "scope": (
            "Finite declared-rival screen. Programs are fit using demonstrations only; "
            "four queries detect harmful survivors. This is not a universal induction proof."
        ),
        "status": "running",
        "seeds": list(seed_values),
        "demo_counts": list(demo_values),
        "queries": queries,
        "candidate_programs": [
            {"rival": name, "program_sha256": _sha256_text(program), "characters": len(program)}
            for name, program in candidates
        ],
        "source_binding": [
            {
                "path": str(path.relative_to(TASK_HOME.parents[1])),
                "sha256": _sha256_bytes(path.read_bytes()),
            }
            for path in source_files
        ],
        "jobs": [],
        "claim_mismatches": [],
        "harmful_survivors": [],
        "errors": [],
        "racket_evaluations": 0,
        "failure_count": 0,
    }

    cache: dict[tuple[str, str], list[list[int]]] = {}
    with RacketBridge() as bridge:
        report["racket"] = bridge.runtime_identity
        if bridge.runtime_identity.get("backend") != "racket" or bridge.runtime_identity.get("protected") is not True:
            raise RuntimeError("self-audit requires the protected actual Racket runtime")

        def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
            grid_key = json.dumps(grid, separators=(",", ":"))
            key = (_sha256_text(program), grid_key)
            if key not in cache:
                report["racket_evaluations"] += 1
                cache[key] = normalize_grid(
                    bridge.eval_text(f"({wrap_rule(program)} {_grid_literal(grid)})")
                )
            return cache[key]

        for seed in seed_values:
            for demo_count in demo_values:
                for settings in SETTINGS:
                    episode = ADAPTER.generate(seed, settings, demos=demo_count, queries=queries)
                    pairs = episode["train"] + episode["test"]
                    selected_program = ADAPTER.program(settings)
                    selected_name = (
                        "declared_none"
                        if settings["post_rotation"] == "none"
                        else "declared_marker_relay"
                    )
                    selected_outputs = [execute(selected_program, pair["input"]) for pair in pairs]
                    mismatches = [
                        index
                        for index, (actual, pair) in enumerate(zip(selected_outputs, pairs))
                        if actual != pair["output"]
                    ]
                    if mismatches:
                        report["claim_mismatches"].append(
                            {"seed": seed, "demos": demo_count, "settings": settings, "pair_indices": mismatches}
                        )

                    rows = []
                    for name, program in candidates:
                        outputs = [execute(program, pair["input"]) for pair in pairs]
                        refuting = [
                            index
                            for index in range(demo_count)
                            if outputs[index] != selected_outputs[index]
                        ]
                        query_mismatches = [
                            index
                            for index in range(queries)
                            if outputs[demo_count + index] != selected_outputs[demo_count + index]
                        ]
                        if name == selected_name:
                            status = "selected"
                        elif refuting:
                            status = "refuted"
                        elif query_mismatches:
                            status = "harmful_survivor"
                            report["harmful_survivors"].append(
                                {
                                    "seed": seed,
                                    "demos": demo_count,
                                    "settings": settings,
                                    "rival": name,
                                    "query_indices": query_mismatches,
                                }
                            )
                        else:
                            status = "answer_equivalent"
                        rows.append(
                            {
                                "rival": name,
                                "status": status,
                                "program_sha256": _sha256_text(program),
                                "refuting_demo_indices": refuting,
                                "query_mismatch_indices": query_mismatches,
                                "query_count": queries,
                            }
                        )
                    report["jobs"].append(
                        {
                            "seed": seed,
                            "demos": demo_count,
                            "queries": queries,
                            "settings": settings,
                            "selected_program_sha256": _sha256_text(selected_program),
                            "rivals": rows,
                        }
                    )

    report["failure_count"] = (
        len(report["claim_mismatches"])
        + len(report["harmful_survivors"])
        + len(report["errors"])
    )
    report["status"] = "pass" if report["failure_count"] == 0 else "fail"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = out_path.with_suffix(out_path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    temporary.replace(out_path)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--demos", type=int, nargs="+", default=[2, 3, 6])
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    report = audit(args.out, seeds=args.seeds, demos=args.demos, queries=args.queries)
    print(json.dumps({
        "status": report["status"],
        "jobs": len(report["jobs"]),
        "racket_evaluations": report["racket_evaluations"],
        "failure_count": report["failure_count"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
