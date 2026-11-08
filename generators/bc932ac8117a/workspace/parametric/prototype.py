"""Proposed task-local parametric extension for ``bc932ac8117a``.

This does not alter production generation or the selected canonical authority.
It materializes one bounded rule parameter once per complete episode:

``hole_selection = all_holes`` (canonical/default)
    Carve every enclosed region from the solid twin.

``hole_selection = largest_hole`` (proposed alternative)
    Carve only the largest enclosed region.  Prototype inputs always contain
    at least two unequal holes, so every demonstration distinguishes the two
    settings.

All saved labels are produced by the included Racket bridge.  ``python_apply``
is only an independent parity oracle used by focused tests.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
ROOT = HERE.parents[3]
TASK_ID = "bc932ac8117a"
PARAMETER_NAME = "hole_selection"
ALLOWED_VALUES = ("all_holes", "largest_hole")
DEFAULT_VALUE = "all_holes"
PROTOTYPE_SEEDS = {"all_holes": 1701, "largest_hole": 1702}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def canonical_program() -> str:
    """Return the selected canonical Racket program verbatim."""
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(f"canonical task not found: {TASK_ID}")


_LARGEST_HELPER = """(define (largest-region regions) (let loop ((best (first regions)) (remaining (rest regions))) (if (empty? remaining) best (let ((candidate (first remaining))) (loop (if (> (length candidate) (length best)) candidate best) (rest remaining))))))"""
_CANONICAL_FLATTEN = """(apply append (map (lambda (region) (map (lambda (p) (list (+ r0 (first p)) (+ c0 (second p)))) region)) regions))"""
_LARGEST_FLATTEN = """(if (empty? regions) (list) (apply append (map (lambda (region) (map (lambda (p) (list (+ r0 (first p)) (+ c0 (second p)))) region)) (list (largest-region regions)))))"""


def program_for(policy: str) -> str:
    """Materialize the exact Racket program for one bounded setting."""
    if policy not in ALLOWED_VALUES:
        raise ValueError(f"unsupported {PARAMETER_NAME}: {policy!r}")
    program = canonical_program()
    if policy == DEFAULT_VALUE:
        return program
    insertion_point = "(define (nx-hole-cells cells)"
    if program.count(insertion_point) != 1 or program.count(_CANONICAL_FLATTEN) != 1:
        raise RuntimeError("canonical program shape changed; refusing a silent rewrite")
    program = program.replace(
        insertion_point,
        f"{_LARGEST_HELPER} {insertion_point}",
        1,
    )
    return program.replace(_CANONICAL_FLATTEN, _LARGEST_FLATTEN, 1)


def _draw_frame(grid: list[list[int]], top: int, left: int, size: int, color: int) -> None:
    bottom, right = top + size - 1, left + size - 1
    for col in range(left, right + 1):
        grid[top][col] = color
        grid[bottom][col] = color
    for row in range(top, bottom + 1):
        grid[row][left] = color
        grid[row][right] = color


def _pattern(diagonal: str) -> set[tuple[int, int]]:
    # The 5x5 interior staircase splits the enclosed background into regions of
    # sizes one and four.  That unequal pair is the parameter witness.
    cells = {(1, 1), (2, 1), (2, 2), (3, 2)}
    if diagonal == "anti":
        return {(row, 4 - col) for row, col in cells}
    if diagonal != "main":
        raise ValueError(diagonal)
    return cells


def make_input(seed: int, sample_index: int) -> list[list[int]]:
    """Build a deterministic lawful input with two unequal enclosed holes."""
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed and nonnegative sample_index must be literal integers")
    rng = random.Random((seed * 1_000_003 + sample_index * 9_176 + 41) & ((1 << 64) - 1))
    size = 5
    height = rng.randint(5, 9)
    width = rng.randint(12, 18)
    gap = rng.randint(1, width - 2 * size)
    span = 2 * size + gap
    start_col = rng.randint(0, width - span)
    pair_top = rng.randint(0, height - size)
    left_col = start_col
    right_col = start_col + size + gap
    hollow_side = "left" if sample_index % 2 == 0 else "right"
    hollow_left, solid_left = (
        (left_col, right_col) if hollow_side == "left" else (right_col, left_col)
    )
    palettes = ((2, 3), (4, 6), (1, 8), (5, 9))
    hollow_color, solid_color = palettes[(seed + sample_index) % len(palettes)]
    if (seed + sample_index) % 3 == 0:
        hollow_color, solid_color = solid_color, hollow_color
    diagonal = "main" if (seed + sample_index) % 2 == 0 else "anti"

    grid = [[0 for _ in range(width)] for _ in range(height)]
    _draw_frame(grid, pair_top, hollow_left, size, hollow_color)
    for row, col in _pattern(diagonal):
        grid[pair_top + row][hollow_left + col] = hollow_color
    for row in range(pair_top, pair_top + size):
        for col in range(solid_left, solid_left + size):
            grid[row][col] = solid_color
    return grid


def _analysis_helpers():
    workspace = TASK_HOME / "workspace"
    if str(workspace) not in sys.path:
        sys.path.insert(0, str(workspace))
    from hole_transfer_probe import analyze
    return analyze


def python_apply(grid: list[list[int]], policy: str) -> list[list[int]]:
    """Independent mirror for parity tests; never label authority."""
    if policy not in ALLOWED_VALUES:
        raise ValueError(policy)
    analyze = _analysis_helpers()
    _hollow, solid, holes = analyze(grid)
    selected = holes if policy == "all_holes" else [max(holes, key=len)]
    row0, col0, _, _ = solid["bbox"]
    output = deepcopy(grid)
    for region in selected:
        for row, col in region:
            output[row0 + row][col0 + col] = 0
    return output


def run_program(program: str, grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Execute one exact Racket program over a batch; no Python fallback."""
    materialized = list(grids)
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parametric-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "request.json").write_text(
            json.dumps({"program": program, "grids": materialized}),
            encoding="utf-8",
        )
        worker = r'''import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", worker], stage, timeout=180)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(
                "Racket worker failed: " + result.get("stderr", "") + result.get("stdout", "")
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(materialized):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def build_episode(seed: int, policy: str | None = None) -> dict[str, Any]:
    """Choose one hidden setting once, then label a complete episode in Racket."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    chosen = ALLOWED_VALUES[seed % len(ALLOWED_VALUES)] if policy is None else policy
    program = program_for(chosen)
    inputs = [make_input(seed, index) for index in range(3)]
    outputs = run_program(program, inputs)
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, outputs)]
    return {
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "seed": seed,
            PARAMETER_NAME: chosen,
            "rule_sha256": _sha256_text(program),
            "label_authority": "executed_racket",
        },
        "train": pairs[:2],
        "test": pairs[2:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden parameter and query answers from a challenge view."""
    return {
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "seed": episode["meta"]["seed"],
        },
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def materialize(out_dir: Path = HERE) -> dict[str, Any]:
    """Write exact rules, complete episodes, public views, and hash evidence."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = out_dir / "rules"
    episodes = out_dir / "episodes"
    challenges = out_dir / "challenges"
    rules.mkdir(exist_ok=True)
    episodes.mkdir(exist_ok=True)
    challenges.mkdir(exist_ok=True)

    settings: dict[str, Any] = {}
    for policy in ALLOWED_VALUES:
        program = program_for(policy)
        rule_rel = Path("rules") / f"{policy}.rkt"
        episode_rel = Path("episodes") / f"{policy}.json"
        challenge_rel = Path("challenges") / f"{policy}.json"
        rule_bytes = (program + "\n").encode("utf-8")
        (out_dir / rule_rel).write_bytes(rule_bytes)
        episode = build_episode(PROTOTYPE_SEEDS[policy], policy=policy)
        (out_dir / episode_rel).write_text(
            json.dumps(episode, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (out_dir / challenge_rel).write_text(
            json.dumps(public_challenge(episode), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        rival = next(value for value in ALLOWED_VALUES if value != policy)
        demo_inputs = [pair["input"] for pair in episode["train"]]
        query_inputs = [pair["input"] for pair in episode["test"]]
        rival_demo_outputs = run_program(program_for(rival), demo_inputs)
        rival_query_outputs = run_program(program_for(rival), query_inputs)
        demo_disagreements = [
            sum(a != b for row_a, row_b in zip(pair["output"], rival_output)
                for a, b in zip(row_a, row_b))
            for pair, rival_output in zip(episode["train"], rival_demo_outputs)
        ]
        query_disagreements = [
            sum(a != b for row_a, row_b in zip(pair["output"], rival_output)
                for a, b in zip(row_a, row_b))
            for pair, rival_output in zip(episode["test"], rival_query_outputs)
        ]
        if not all(value > 0 for value in demo_disagreements + query_disagreements):
            raise AssertionError(f"parameter rival survived for {policy}")
        settings[policy] = {
            "seed": PROTOTYPE_SEEDS[policy],
            "rule_path": rule_rel.as_posix(),
            "rule_sha256": _sha256_bytes(rule_bytes),
            "program_sha256_without_trailing_newline": _sha256_text(program),
            "racket_program": program,
            "episode_path": episode_rel.as_posix(),
            "challenge_path": challenge_rel.as_posix(),
            "label_authority": "executed_racket",
            "rival": rival,
            "demo_cell_disagreements_vs_rival": demo_disagreements,
            "query_cell_disagreements_vs_rival": query_disagreements,
        }

    source_path = Path(__file__).resolve()
    evidence = {
        "schema": "bc932ac8117a_parametric_prototype/1",
        "status": "proposed_prototype",
        "production_integration": False,
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_VALUES),
            "default": DEFAULT_VALUE,
            "chosen_once_per_episode": True,
            "input_constraints": [
                "one hollow 5x5 twin and one same-size solid twin",
                "at least two enclosed hole regions of unequal area",
                "two demonstrations, each distinguishing both settings",
            ],
        },
        "prototype_source": source_path.relative_to(ROOT).as_posix(),
        "prototype_source_sha256": _sha256_bytes(source_path.read_bytes()),
        "settings": settings,
        "limitations": [
            "not wired into the production generator or approval catalog",
            "bounded evidence covers two fixed episodes and focused tests, not all seeds",
            "largest-hole ties are intentionally outside the prototype input domain",
            "canonical all_holes remains the only selected/approved behavior",
        ],
    }
    (out_dir / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("materialize", "show"), nargs="?", default="materialize")
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args(argv)
    evidence = materialize(args.out) if args.command == "materialize" else json.loads(
        (args.out / "evidence.json").read_text(encoding="utf-8")
    )
    print(json.dumps({
        "status": evidence["status"],
        "parameter": evidence["parameter"],
        "settings": {
            name: {
                "rule_sha256": value["rule_sha256"],
                "demo_cell_disagreements_vs_rival": value["demo_cell_disagreements_vs_rival"],
                "query_cell_disagreements_vs_rival": value["query_cell_disagreements_vs_rival"],
            }
            for name, value in evidence["settings"].items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
