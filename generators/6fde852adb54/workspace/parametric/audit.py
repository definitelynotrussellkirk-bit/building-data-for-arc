"""Replayable finite audit and sequential public exporter for 6fde852adb54.

The fast ``python_preflight`` checks determinism, setting-neutral inputs, finite
setting identification, named shortcut survival, privacy, and boundary
coverage.  The CLI additionally re-executes both declared programs in the
packet's live protected Racket runtime and writes source-bound evidence.

This is proposal evidence only.  It does not claim owner acceptance or training
admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_HOME = HERE.parents[1]


def _load(filename: str, name: str):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("prototype.py", "_audit_6fde852adb54_prototype")
rivals = _load("rivals.py", "_audit_6fde852adb54_rivals")


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validated_ints(values: Iterable[int], low: int, high: int, name: str) -> list[int]:
    if type(values) not in (list, tuple) or not values:
        raise ValueError(f"{name} must be a nonempty list or tuple")
    result = [_exact_int(value, low, high, name) for value in values]
    if len(result) != len(set(result)):
        raise ValueError(f"{name} values must be distinct")
    return result


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _grid_sha(grid: list[list[int]]) -> str:
    return _sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _source_inventory() -> list[dict[str, str]]:
    result = []
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.suffix in {".py", ".rkt", ".json", ".md"}:
            result.append(
                {
                    "path": path.relative_to(REPO).as_posix(),
                    "sha256": _sha_bytes(path.read_bytes()),
                }
            )
    test = TASK_HOME / "tests" / "test_parametric_landing_metric.py"
    result.append(
        {
            "path": test.relative_to(REPO).as_posix(),
            "sha256": _sha_bytes(test.read_bytes()),
        }
    )
    return result


def python_preflight(
    seeds: Iterable[int], *, demo_counts: Iterable[int] = (2, 3, 6)
) -> dict[str, Any]:
    """Run the finite audit without invoking Racket or writing files."""
    seeds = _validated_ints(seeds, 0, 2**63 - 1, "seed")
    demo_counts = _validated_ints(demo_counts, 2, 6, "demo_count")
    failures: list[dict[str, Any]] = []
    episodes_checked = 0
    setting_neutral = True
    public_private_invariant = True
    max_surface = {"seen": False, "obstacle_cells": 0, "components": 0}

    for seed in seeds:
        for demos in demo_counts:
            episodes = {
                metric: prototype.generate(
                    seed, {"landing_metric": metric}, demos, 4
                )
                for metric in prototype.METRICS
            }
            reference_inputs = _inputs(episodes[prototype.METRICS[0]])
            for metric, episode in episodes.items():
                episodes_checked += 1
                context = {"seed": seed, "demos": demos, "metric": metric}
                if episode != prototype.generate(
                    seed, {"landing_metric": metric}, demos, 4
                ):
                    failures.append({**context, "kind": "nondeterministic"})
                if _inputs(episode) != reference_inputs:
                    setting_neutral = False
                    failures.append({**context, "kind": "setting_dependent_inputs"})

                report = prototype.teaching_report(
                    episode["train"],
                    [pair["input"] for pair in episode["test"]],
                    metric,
                )
                if report["setting_survivors"] != [metric]:
                    failures.append(
                        {
                            **context,
                            "kind": "declared_setting_survivors",
                            "survivors": report["setting_survivors"],
                        }
                    )
                if demos >= 3 and report["harmful_survivors"]:
                    failures.append(
                        {
                            **context,
                            "kind": "harmful_shortcut_survived",
                            "survivors": report["harmful_survivors"],
                        }
                    )

                first = prototype.public_turn_bytes(episode, 0)
                contaminated = deepcopy(episode)
                contaminated["program_solution"] = "private mutation"
                contaminated["settings"] = {"private": True}
                contaminated["seed"] = -1
                for pair in contaminated["test"]:
                    pair["output"] = [[9]]
                contaminated["test"][1]["input"] = [[8]]
                if prototype.public_turn_bytes(contaminated, 0) != first:
                    public_private_invariant = False
                    failures.append({**context, "kind": "public_private_leak"})

                large = prototype.analyze(episode["test"][-1]["input"])
                max_surface = {
                    "seen": large["height"] == 30 and large["width"] == 30,
                    "obstacle_cells": len(large["obstacle_cells"]),
                    "components": len(large["obstacle_components"]),
                }
                if not (
                    max_surface["seen"]
                    and max_surface["obstacle_cells"] >= 35
                    and max_surface["components"] >= 8
                ):
                    failures.append(
                        {**context, "kind": "weak_30x30_surface", **max_surface}
                    )

    return {
        "schema": "arcpuzzles-landing-metric-python-audit-v1",
        "status": "pass" if not failures else "fail",
        "task_id": prototype.TASK_ID,
        "seeds": seeds,
        "demo_counts": demo_counts,
        "episodes_checked": episodes_checked,
        "setting_neutral_inputs": setting_neutral,
        "public_private_invariant": public_private_invariant,
        "tested_models": list(rivals.MODEL_NAMES),
        "max_surface": max_surface,
        "failures": failures,
        "scope": "Finite declared settings and named rivals; not universal uniqueness or training admission.",
    }


def run(output: Path, *, seeds: Iterable[int] = (0, 17)) -> dict[str, Any]:
    """Run protected-Racket evidence generation into a new directory."""
    from arcpuzzles.parametric_worker import _real_evaluator

    seeds = _validated_ints(seeds, 0, 2**63 - 1, "seed")
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"choose a new evidence directory: {output}")
    preflight = python_preflight(seeds)
    if preflight["status"] != "pass":
        raise ValueError("python preflight failed: " + json.dumps(preflight["failures"]))

    programs = {
        metric: prototype.program({"landing_metric": metric})
        for metric in prototype.METRICS
    }
    apply, identity, bridge = _real_evaluator(REPO / "shared" / "runtime")
    cache: dict[tuple[str, str], list[list[int]]] = {}
    calls: list[dict[str, Any]] = []

    def execute(metric: str, grid: list[list[int]]) -> list[list[int]]:
        serialized = json.dumps(grid, separators=(",", ":"))
        key = metric, serialized
        if key not in cache:
            result = apply(programs[metric], grid)
            claimed = prototype.predict(grid, metric)
            if result != claimed:
                raise ValueError(f"Python/Racket mismatch for {metric}")
            cache[key] = result
            calls.append(
                {
                    "metric": metric,
                    "input_sha256": _sha_bytes(serialized.encode()),
                    "output_sha256": _grid_sha(result),
                }
            )
        return deepcopy(cache[key])

    episodes: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    public_rows: list[dict[str, Any]] = []
    output.mkdir(parents=True)
    try:
        for seed in seeds:
            for metric in prototype.METRICS:
                episode = prototype.generate(
                    seed, {"landing_metric": metric}, 3, 4
                )
                for pair in episode["train"] + episode["test"]:
                    pair["output"] = execute(metric, pair["input"])

                survivors = []
                rejection = {}
                for candidate in prototype.METRICS:
                    mismatches = [
                        index
                        for index, pair in enumerate(episode["train"])
                        if execute(candidate, pair["input"]) != pair["output"]
                    ]
                    rejection[candidate] = mismatches
                    if not mismatches:
                        survivors.append(candidate)
                if survivors != [metric]:
                    raise ValueError(
                        f"protected Racket setting survivors for {metric}: {survivors}"
                    )

                finite = prototype.teaching_report(
                    episode["train"],
                    [pair["input"] for pair in episode["test"]],
                    metric,
                )
                if finite["harmful_survivors"]:
                    raise ValueError(
                        f"harmful named rival survived: {finite['harmful_survivors']}"
                    )
                certificate = {
                    "seed": seed,
                    "settings": {"landing_metric": metric},
                    "declared_program_survivors": survivors,
                    "rejected_by_demonstration": rejection,
                    "finite_rival_audit": finite,
                }
                certificates.append(certificate)

                private = deepcopy(episode)
                private["reference"] = "proposed_parametric"
                private["training_admitted"] = False
                private["teaching_certificate"] = certificate
                episodes.append(private)

                for query_index in range(4):
                    raw = prototype.public_turn_bytes(episode, query_index)
                    identifier = _sha_bytes(raw)
                    destination = output / "public_turns" / f"{identifier}.json"
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open("xb") as stream:
                        stream.write(raw)
                    public_rows.append(
                        {
                            "seed": seed,
                            "settings": {"landing_metric": metric},
                            "query_index": query_index,
                            "public_id": identifier,
                            "path": destination.relative_to(output).as_posix(),
                        }
                    )
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-landing-metric-protected-audit-v1",
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "training_admitted": False,
        "owner_acceptance": "pending",
        "python_preflight": preflight,
        "settings": list(prototype.METRICS),
        "seeds": seeds,
        "episodes": len(episodes),
        "labels_checked": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
        "racket_evaluations": len(calls),
        "racket": identity,
        "certificates": certificates,
        "public_turns": public_rows,
        "source_inventory": _source_inventory(),
        "scope": (
            "Protected-Racket parity for declared settings plus a finite named-rival audit. "
            "This is reviewer evidence, not owner acceptance or training admission."
        ),
    }
    _write_json(output / "authoring.json", report)
    _write_json(output / "episodes.private.json", episodes)
    _write_json(output / "execution_calls.json", calls)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    args = parser.parse_args(argv)
    try:
        report = run(args.out, seeds=args.seeds or [0, 17])
    except Exception as exc:
        print(json.dumps({"status": "error", "error": type(exc).__name__, "message": str(exc)}))
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": report["episodes"],
                "labels_checked": report["labels_checked"],
                "racket_evaluations": report["racket_evaluations"],
                "public_turns": len(report["public_turns"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
