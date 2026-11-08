#!/usr/bin/env python3
"""Proposed episode-level fewest/most selection prototype for 97bcb3b9194e.

The canonical task finds separated filled rectangles, counts every non-blue
(non-0/non-1) mark inside each rectangle, selects the unique fewest-mark
rectangle, and returns its unchanged bounding-box crop. This isolated prototype
keeps those steps and varies one hidden episode-level parameter:
``selection_mode`` is ``fewest`` (the exact canonical rule) or ``most``.
It does not modify the selected production generator or canonical authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "97bcb3b9194e"
PROTOTYPE_VERSION = "selection-mode-v1"
SELECTION_MODES = ("fewest", "most")
CANONICAL_DEFAULT = "fewest"
N_TRAIN = 3
N_TEST = 1
DEFAULT_EVIDENCE_SEEDS = (0, 1, 2, 3)

PARAMETER_SPEC = {
    "selection_mode": {
        "allowed": list(SELECTION_MODES),
        "canonical_default": CANONICAL_DEFAULT,
        "chosen_once_per_episode": True,
        "meaning": {
            "fewest": "crop the rectangle with the smallest all-non-blue mark count",
            "most": "crop the rectangle with the largest all-non-blue mark count",
        },
        "input_constraints": [
            "2-7 separated filled rectangles on background 0",
            "every rectangle retains blue body color 1 and has one or more non-blue marks",
            "the fewest-mark rectangle is unique for the canonical setting",
            "one selection_mode labels all demonstrations and the query in an episode",
        ],
        "invariant_reasoning": [
            "find every nonzero rectangular object",
            "count all marks whose color is neither 0 nor 1",
            "choose a count extremum and preserve row-major tie behavior",
            "return the selected rectangle's unchanged bounding-box crop",
        ],
        "varied_reasoning": "whether the selected count extremum is minimum or maximum",
    }
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _validate_mode(selection_mode: str) -> None:
    if type(selection_mode) is not str or selection_mode not in SELECTION_MODES:
        raise ValueError(f"selection_mode must be one of {SELECTION_MODES}")


def _canonical_program(root: Path) -> str:
    programs: set[str | None] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row.get("program_solution"))
    if None in programs or len(programs) != 1:
        raise ValueError(f"canonical variants disagree or lack a rule for {TASK_ID}")
    return next(iter(programs))  # type: ignore[return-value]


def program_for(
    selection_mode: str = CANONICAL_DEFAULT,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact Racket rule for one bounded parameter setting."""
    _validate_mode(selection_mode)
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_program(resolved)
    if selection_mode == CANONICAL_DEFAULT:
        return canonical
    old = "(lambda (a b) (< (first a) (first b)))"
    new = "(lambda (a b) (> (first a) (first b)))"
    if canonical.count(old) != 1:
        raise ValueError("canonical rule drift: mark-count comparator changed")
    return canonical.replace(old, new, 1)


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose one hidden rule setting from the seed for the entire episode."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    return {"selection_mode": SELECTION_MODES[seed % len(SELECTION_MODES)]}


def _component_records(grid: list[list[int]]) -> list[dict[str, Any]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    h, w = len(grid), width
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            bbox = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
            if cells != bbox:
                raise ValueError("nonzero component is not a filled rectangle")
            records.append(
                {
                    "bbox": (r1, c1, r2, c2),
                    "marks": sum(grid[r][c] not in (0, 1) for r, c in cells),
                }
            )
    records.sort(key=lambda record: (record["bbox"][0], record["bbox"][1]))
    if len(records) < 2:
        raise ValueError("expected at least two rectangles")
    return records


def apply_python(grid: list[list[int]], selection_mode: str) -> list[list[int]]:
    """Independent Python mirror used only to cross-check Racket execution."""
    _validate_mode(selection_mode)
    records = _component_records(grid)
    selector = min if selection_mode == "fewest" else max
    selected = selector(records, key=lambda record: record["marks"])
    r1, c1, r2, c2 = selected["bbox"]
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _racket_outputs(program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    body = strip_rule_wrapper(program)
    bridge = RacketBridge(max_calls_before_restart=128, timeout=30.0)
    try:
        outputs = []
        for grid in grids:
            bridge.define_grid("g", grid)
            outputs.append(bridge.eval_text(f"({body} g)"))
        return outputs
    finally:
        bridge.shutdown()


def _public_episode(grids, selected_outputs) -> dict[str, Any]:
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(
                grids[:N_TRAIN], selected_outputs[:N_TRAIN], strict=True
            )
        ],
        # Hidden parameter, Racket source, and query answer are omitted.
        "test": [{"input": grid} for grid in grids[N_TRAIN:]],
    }


def materialize_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Generate and Racket-label one complete parameter-consistent episode."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(difficulty) is not str or difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=resolved)
    mode = choose_parameters(seed)["selection_mode"]
    rival_mode = "most" if mode == "fewest" else "fewest"
    sample_start = (seed * 104729 + 17) % 10_000
    grids = [
        generator.generate(seed, sample_start + index, difficulty=difficulty)
        for index in range(N_TRAIN + N_TEST)
    ]

    programs = {value: program_for(value, root=resolved) for value in SELECTION_MODES}
    outputs = {value: _racket_outputs(programs[value], grids) for value in SELECTION_MODES}
    for value in SELECTION_MODES:
        mirrors = [apply_python(grid, value) for grid in grids]
        if outputs[value] != mirrors:
            raise AssertionError(f"Racket output disagrees with {value!r} Python mirror")

    differences = [
        outputs["fewest"][index] != outputs["most"][index]
        for index in range(len(grids))
    ]
    demo_differences = [index for index, differs in enumerate(differences[:N_TRAIN]) if differs]
    query_differences = [index for index, differs in enumerate(differences[N_TRAIN:]) if differs]
    if demo_differences != list(range(N_TRAIN)) or query_differences != [0]:
        raise AssertionError("episode failed to distinguish both parameter settings")

    selected = outputs[mode]
    rival = outputs[rival_mode]
    prototype_path = Path(__file__).resolve()
    ledger_path = canonical_path(resolved)
    return {
        "schema": "arc-parametric-prototype-evidence-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "sample_start": sample_start,
        "parameter": {
            "selection_mode": mode,
            "allowed": list(SELECTION_MODES),
            "canonical_default": CANONICAL_DEFAULT,
        },
        "parameter_spec": PARAMETER_SPEC,
        "rival_setting": rival_mode,
        "demonstration_difference_indices": demo_differences,
        "query_difference_indices": query_differences,
        "racket_verified": True,
        "programs": {
            value: {"text": text, "sha256": _sha256_text(text)}
            for value, text in programs.items()
        },
        "sources": {
            "prototype_path": str(prototype_path),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha,
            "canonical_path": str(ledger_path),
            "canonical_sha256": _sha256_file(ledger_path),
        },
        "public": _public_episode(grids, selected),
        "private": {
            "train": [
                {
                    "input": grids[index],
                    "output": selected[index],
                    "rival_output": rival[index],
                    "settings_disagree": differences[index],
                }
                for index in range(N_TRAIN)
            ],
            "test": [
                {
                    "input": grids[index],
                    "output": selected[index],
                    "rival_output": rival[index],
                    "settings_disagree": differences[index],
                }
                for index in range(N_TRAIN, N_TRAIN + N_TEST)
            ],
        },
        "limitations": [
            "prototype only; production remains bound to the canonical fewest-mark rule",
            "bounded evidence for retained seeds and generated episodes, not all seeds or hypotheses",
            "the alternative maximum may be tied; canonical stable sort/row-major behavior is preserved",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_EVIDENCE_SEEDS))
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    root = find_root(__file__)
    out_dir = args.out_dir.resolve()
    if out_dir.exists():
        raise FileExistsError(f"choose a new evidence directory: {out_dir}")
    records = []
    observed = set()
    programs_written = False
    for seed in args.seeds:
        evidence = materialize_episode(seed, difficulty=args.difficulty, root=root)
        mode = evidence["parameter"]["selection_mode"]
        observed.add(mode)

        public_path = out_dir / "public" / f"seed-{seed}.json"
        private_path = out_dir / "private" / f"seed-{seed}.json"
        _write_json(public_path, evidence["public"])
        private_document = dict(evidence)
        private_document.pop("public")
        _write_json(private_path, private_document)

        if not programs_written:
            for value, record in evidence["programs"].items():
                rule_path = out_dir / "private" / "rules" / f"selection-{value}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(record["text"] + "\n", encoding="utf-8")
            programs_written = True

        records.append(
            {
                "seed": seed,
                "selection_mode": mode,
                "sample_start": evidence["sample_start"],
                "demonstration_difference_indices": evidence[
                    "demonstration_difference_indices"
                ],
                "query_difference_indices": evidence["query_difference_indices"],
                "public_path": str(public_path),
                "public_sha256": _sha256_file(public_path),
                "private_path": str(private_path),
                "private_sha256": _sha256_file(private_path),
                "program_hashes": {
                    value: record["sha256"]
                    for value, record in evidence["programs"].items()
                },
            }
        )

    if observed != set(SELECTION_MODES):
        raise RuntimeError(
            f"retained seeds must cover both settings; observed {sorted(observed)}"
        )
    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "prototype_status": "proposed",
        "parameter_spec": PARAMETER_SPEC,
        "command": " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv]),
        "episodes": records,
    }
    _write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
