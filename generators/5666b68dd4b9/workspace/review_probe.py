#!/usr/bin/env python3
"""Replayable semantic probe for keyed-frame generator ``5666b68dd4b9``.

This tool is intentionally generator-local.  It builds one four-code lesson,
checks every declared competitor, finds an emitted selector/code shortcut
counterexample, and can optionally execute the protected canonical Racket rule
when ``RACKET_PATH`` points to an activated runtime.

Examples (from the repository root)::

    PYTHONPATH=shared/runtime python3 generators/5666b68dd4b9/workspace/review_probe.py
    RACKET_PATH=/path/to/racket PYTHONPATH=shared/runtime \
      python3 generators/5666b68dd4b9/workspace/review_probe.py \
      --racket --out /tmp/5666b68dd4b9_probe.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any


TASK_ID = "5666b68dd4b9"
HERE = Path(__file__).resolve()
GENERATOR_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
GENERATOR_PATH = GENERATOR_DIR / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME_PATH = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_canonical_rule() -> str:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
                return source
    raise RuntimeError(f"canonical row {TASK_ID} not found in {CANONICAL_PATH}")


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in grid
    )
    return f"'({rows})"


def _install_source_tools_namespace() -> None:
    """Expose ``shared/tools`` under the runtime's expected ``scripts`` name.

    Exported review runtimes already place these files in a top-level
    ``scripts`` package.  The source repository stores the same modules under
    ``shared/tools``.  Installing a tiny namespace alias keeps ``wrap_rule`` on
    its canonical parser path in both layouts instead of copying its parser.
    """
    if "scripts" in sys.modules:
        return
    package = types.ModuleType("scripts")
    package.__path__ = [str(REPO_ROOT / "shared" / "tools")]
    package.__package__ = "scripts"
    sys.modules["scripts"] = package


def _apply_racket(grid: list[list[int]]) -> tuple[list[list[int]], dict[str, Any]]:
    _install_source_tools_namespace()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    source = _load_canonical_rule()
    expression = f"({wrap_rule(source)} {_grid_literal(grid)})"
    bridge = RacketBridge(timeout=15.0)
    try:
        output = bridge.eval_text(expression)
        identity = bridge.runtime_identity
    finally:
        bridge.shutdown()
    if not (
        isinstance(output, list)
        and output
        and all(isinstance(row, list) for row in output)
    ):
        raise RuntimeError(f"Racket returned a non-grid value: {output!r}")
    return output, identity


def _find_selector_lookup_counterexample(gen, *, seed: int, start: int,
                                          difficulty: str | None) -> tuple[int, list[list[int]]]:
    rival = gen.SEMANTIC_RIVALS["selector_color_lookup"]
    for offset in range(32):
        sample_index = start + offset
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        if rival(grid) != gen.rule_mirror(grid):
            return sample_index, grid
    raise RuntimeError(
        f"no selector_color_lookup counterexample found for seed={seed}, start={start}"
    )


def build_report(*, seed: int = 0, start: int = 0, difficulty: str | None = "hard",
                 use_racket: bool = False) -> dict[str, Any]:
    """Build a JSON-serializable lesson and shortcut audit report."""
    gen = _load_generator()
    lesson_grids = [
        gen.generate(seed, start + offset, difficulty=difficulty)
        for offset in range(gen.EXAMPLES_NEEDED + 1)
    ]
    lesson_pairs = [
        {"input": grid, "output": gen.rule_mirror(grid)}
        for grid in lesson_grids
    ]
    demos = lesson_pairs[:gen.EXAMPLES_NEEDED]
    query = lesson_pairs[gen.EXAMPLES_NEEDED]

    competitor_refutations = {
        name: [
            index
            for index, pair in enumerate(demos)
            if rival(pair["input"]) != pair["output"]
        ]
        for name, rival in gen.LESSON_COMPETITORS.items()
    }
    witness_hits = {
        name: [
            index
            for index, pair in enumerate(demos)
            if witness(pair["input"])
        ]
        for name, witness in gen.SEMANTIC_WITNESSES.items()
    }

    counter_index, counter_grid = _find_selector_lookup_counterexample(
        gen, seed=seed, start=start, difficulty=difficulty
    )
    intended = gen.rule_mirror(counter_grid)
    shortcut = gen.SEMANTIC_RIVALS["selector_color_lookup"](counter_grid)
    counterexample: dict[str, Any] = {
        "seed": seed,
        "sample_index": counter_index,
        "difficulty": difficulty,
        "selector": counter_grid[0][0],
        "transform_code": counter_grid[0][-1],
        "shortcut": (
            "infer transform from selector colour (6->clockwise, 7->180, "
            "9->flip-left-right) and ignore the top-right code"
        ),
        "input": counter_grid,
        "intended_output": intended,
        "shortcut_output": shortcut,
        "shortcut_disagrees": shortcut != intended,
        "generator_emits": True,
        "self_check_errors": gen.self_check(counter_grid),
        "observed_axes": gen.observe_overrides(counter_grid),
    }

    racket_receipt: dict[str, Any] | None = None
    if use_racket:
        racket_output, runtime_identity = _apply_racket(counter_grid)
        counterexample["racket_output"] = racket_output
        counterexample["racket_matches_rule_mirror"] = racket_output == intended
        racket_receipt = {
            "matches_rule_mirror": racket_output == intended,
            "runtime_identity": runtime_identity,
        }

    return {
        "schema": "keyed-frame-review-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "seed": seed,
        "start_sample_index": start,
        "difficulty": difficulty,
        "lesson": {
            "demo_sample_indices": list(range(start, start + gen.EXAMPLES_NEEDED)),
            "query_sample_index": start + gen.EXAMPLES_NEEDED,
            "codes": [pair["input"][0][-1] for pair in demos],
            "selectors": [pair["input"][0][0] for pair in demos],
            "layouts": [gen.observe_overrides(pair["input"])["distractor_layout"] for pair in demos],
            "identifiable_errors": gen.lesson_identifiable(demos, query),
            "competitor_refutations": competitor_refutations,
            "witness_hits": witness_hits,
            "demos": demos,
            "query": query,
        },
        "shortcut_counterexample": counterexample,
        "racket_receipt": racket_receipt,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--start", type=int, default=0, help="first demo sample_index")
    parser.add_argument(
        "--difficulty",
        choices=("easy", "medium", "hard", "none"),
        default="hard",
    )
    parser.add_argument("--racket", action="store_true", help="execute canonical protected Racket rule")
    parser.add_argument("--out", type=Path, help="write JSON here instead of stdout only")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    difficulty = None if args.difficulty == "none" else args.difficulty
    report = build_report(
        seed=args.seed,
        start=args.start,
        difficulty=difficulty,
        use_racket=args.racket,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
        print(args.out)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
