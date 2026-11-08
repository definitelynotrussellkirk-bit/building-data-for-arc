"""Bounded, source-bound self-audit for the mirror-then-ray-tail family.

Run from the repository root through the packet wrapper::

    python3 review.py run python3 \
      generators/8eeb98656c43/workspace/parametric/audit.py \
      --out generators/8eeb98656c43/workspace/parametric/evidence/current

The report is reviewer evidence, not owner acceptance.  It exercises every
setting and count boundary, matched inputs, query-prefix stability, a declared
causal counterfactual, and a small protected-Racket replay.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "8eeb98656c43"
MODES = ("canonical", "ray_tail")

for candidate in (ROOT / "src", ROOT / "shared" / "runtime"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _load(filename: str, stem: str):
    path = HOME / filename
    name = f"_{stem}_{_sha256(path.read_bytes())[:20]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _apply(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})")


def _source_inventory() -> dict[str, Any]:
    paths = [
        HOME / "README.md",
        HOME / "adapter.py",
        HOME / "audit.py",
        HOME / "canonical.rkt",
        HOME / "family.py",
        HOME / "promotion.json",
        HOME / "ray_tail.rkt",
        HOME / "wrong_intermediate.rkt",
        ROOT / f"generators/{TASK_ID}/generator.py",
        ROOT / f"generators/{TASK_ID}/tests/test_parametric.py",
    ]
    files = []
    for path in sorted(paths):
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"missing regular audit source: {path}")
        raw = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(raw),
                "sha256": _sha256(raw),
            }
        )
    return {"schema": "arcpuzzles-source-inventory-v1", "task_id": TASK_ID, "files": files}


def run_audit(
    seeds: Iterable[int],
    *,
    protected: bool = True,
    protected_seeds: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Exercise the finite family and return a machine-readable report."""
    adapter = _load("adapter.py", "audit_adapter")
    family = adapter.family
    seed_values = tuple(seeds)
    if any(type(seed) is not int or not 0 <= seed <= 2**63 - 1 for seed in seed_values):
        raise ValueError("seeds must be exact nonnegative 63-bit integers")

    failures: list[dict[str, Any]] = []
    labeled_pairs = 0
    counterfactual_separations = 0
    dimensions: set[tuple[int, int]] = set()
    run_lengths: set[int] = set()
    query_position_counts = {str(source): [0, 0, 0, 0] for source in range(6, 10)}

    for seed in seed_values:
        try:
            full_by_mode = {
                mode: adapter.generate(seed, {"followup": mode}, 6, 4)
                for mode in MODES
            }
            canonical_inputs = _inputs(full_by_mode["canonical"])
            if canonical_inputs != _inputs(full_by_mode["ray_tail"]):
                raise AssertionError("matched settings received different inputs")
            if len({_grid_key(grid) for grid in canonical_inputs}) != 10:
                raise AssertionError("the complete ten-scene episode contains duplicate inputs")

            order = full_by_mode["canonical"]["query_source_indices"]
            if sorted(order) != [6, 7, 8, 9]:
                raise AssertionError(f"query source indices are not a permutation: {order}")
            for position, source in enumerate(order):
                query_position_counts[str(source)][position] += 1

            for demos in range(2, 7):
                for queries in range(1, 5):
                    episodes = {
                        mode: adapter.generate(seed, {"followup": mode}, demos, queries)
                        for mode in MODES
                    }
                    if _inputs(episodes[MODES[0]]) != _inputs(episodes[MODES[1]]):
                        raise AssertionError(
                            f"matched-input failure at demos={demos}, queries={queries}"
                        )
                    for mode, episode in episodes.items():
                        labeled_pairs += len(episode["train"]) + len(episode["test"])
                        if episode["test"] != full_by_mode[mode]["test"][:queries]:
                            raise AssertionError(
                                f"query prefix changed at mode={mode}, demos={demos}, queries={queries}"
                            )
                        if episode["train"] != full_by_mode[mode]["train"][:demos]:
                            raise AssertionError(
                                f"demonstration prefix changed at mode={mode}, demos={demos}"
                            )
                        for pair in episode["train"] + episode["test"]:
                            if pair["output"] != family.solve(pair["input"], mode):
                                raise AssertionError(f"Python label mismatch for {mode}")

                        survivors = [
                            candidate
                            for candidate in MODES
                            if all(
                                family.solve(pair["input"], candidate) == pair["output"]
                                for pair in episode["train"]
                            )
                        ]
                        if survivors != [mode]:
                            raise AssertionError(
                                f"demonstrations do not identify {mode}: survivors={survivors}"
                            )

            for index in range(10):
                grid = family.scene(seed, index)
                dimensions.add((len(grid), len(grid[0])))
                run_lengths.add(family.ray_intermediate(grid)["run_length"])
                if family.solve(grid, "ray_tail") == family.solve_wrong_fixed_tail(grid):
                    raise AssertionError(f"counterfactual collapsed at scene index {index}")
                counterfactual_separations += 1
        except Exception as exc:
            failures.append(
                {
                    "kind": "python_sweep",
                    "seed": seed,
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )

    protected_report: dict[str, Any] = {
        "enabled": False,
        "seed_count": 0,
        "evaluations": 0,
        "counterfactual_evaluations": 0,
        "runtime": None,
        "failures": [],
    }
    if protected:
        chosen = tuple(seed_values[:2] if protected_seeds is None else protected_seeds)
        protected_report = _protected_racket(adapter, family, chosen)
        failures.extend(protected_report["failures"])

    max_shape = max(dimensions, default=(0, 0))
    return {
        "schema": "arcpuzzles-ray-tail-self-audit-v1",
        "task_id": TASK_ID,
        "seed_count": len(seed_values),
        "seeds": list(seed_values),
        "labeled_pairs": labeled_pairs,
        "counterfactual_separations": counterfactual_separations,
        "failures": failures,
        "coverage": {
            "settings": list(MODES),
            "demonstration_counts": [2, 3, 4, 5, 6],
            "query_counts": [1, 2, 3, 4],
            "dimensions": [list(item) for item in sorted(dimensions)],
            "max_shape": list(max_shape),
            "run_lengths": sorted(run_lengths),
            "query_position_counts": query_position_counts,
            "declared_counterfactual": "fixed_tail_length_1",
        },
        "protected_racket": protected_report,
        "scope": (
            "Finite deterministic reviewer self-audit over listed seeds and the declared "
            "counterfactual; not owner acceptance or a universal induction proof."
        ),
    }


def _protected_racket(adapter, family, seeds: tuple[int, ...]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    evaluations = 0
    counterfactual_evaluations = 0
    runtime = None
    try:
        with RacketBridge(max_calls_before_restart=96) as bridge:
            runtime = bridge.runtime_identity
            for seed in seeds:
                for index in range(10):
                    grid = family.scene(seed, index)
                    for mode in MODES:
                        observed = _apply(bridge, adapter.program({"followup": mode}), grid)
                        evaluations += 1
                        if observed != family.solve(grid, mode):
                            failures.append(
                                {
                                    "kind": "protected_label_mismatch",
                                    "seed": seed,
                                    "scene_index": index,
                                    "settings": {"followup": mode},
                                }
                            )
                    observed_wrong = _apply(bridge, adapter.counterfactual_program(), grid)
                    counterfactual_evaluations += 1
                    expected_wrong = family.solve_wrong_fixed_tail(grid)
                    if observed_wrong != expected_wrong:
                        failures.append(
                            {
                                "kind": "protected_counterfactual_mismatch",
                                "seed": seed,
                                "scene_index": index,
                            }
                        )
    except Exception as exc:
        failures.append(
            {
                "kind": "protected_runtime_error",
                "error": type(exc).__name__,
                "message": str(exc),
            }
        )
    return {
        "enabled": True,
        "seed_count": len(seeds),
        "seeds": list(seeds),
        "evaluations": evaluations,
        "counterfactual_evaluations": counterfactual_evaluations,
        "runtime": runtime,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="task-local evidence directory")
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--protected-seed-count", type=int, default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.seed_count <= 512:
        parser.error("--seed-count must be in 1..512")
    if not 1 <= args.protected_seed_count <= args.seed_count:
        parser.error("--protected-seed-count must be in 1..seed-count")

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    if not out.resolve().is_relative_to(HOME.resolve()):
        parser.error("--out must stay inside this task's parametric workspace")
    out.mkdir(parents=True, exist_ok=True)

    seeds = tuple(range(args.seed_count))
    report = run_audit(
        seeds,
        protected=True,
        protected_seeds=seeds[: args.protected_seed_count],
    )
    inventory = _source_inventory()
    (out / "self-audit.json").write_bytes(_json_bytes(report))
    (out / "source-inventory.json").write_bytes(_json_bytes(inventory))
    print(
        json.dumps(
            {
                "status": "passed" if not report["failures"] else "failed",
                "seed_count": report["seed_count"],
                "labeled_pairs": report["labeled_pairs"],
                "protected_evaluations": report["protected_racket"]["evaluations"],
                "counterfactual_separations": report["counterfactual_separations"],
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
