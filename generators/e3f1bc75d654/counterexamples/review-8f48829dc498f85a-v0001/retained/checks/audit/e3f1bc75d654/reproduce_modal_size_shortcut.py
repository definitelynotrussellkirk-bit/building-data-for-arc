#!/usr/bin/env python3
"""Reproduce an untracked modal-frame-size shortcut for e3f1bc75d654.

Run from WORK/repo with:
  python3 ../run_with_racket.py python3 ../checks/audit/e3f1bc75d654/reproduce_modal_size_shortcut.py
"""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "tools"))

import types
_scripts_pkg = types.ModuleType("scripts")
_scripts_pkg.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", _scripts_pkg)

from arc_repl.racket_bridge import RacketBridge
from generator_module_loader import load_module_from_path
from puzzle_generators.rule_wrap import wrap_rule


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(v) for v in row) + ")" for row in grid)
    return f"'({rows})"


def rule_application(source: str, grid: list[list[int]]) -> str:
    return f"({wrap_rule(source)} {_grid_literal(grid)})"

TASK_ID = "e3f1bc75d654"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
REPORT_PATH = Path(__file__).with_name("modal-size-shortcut-report.json")


def canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError("canonical row not found")


def modal_size_shortcut(gen, grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: keep the most frequent frame size, not the template's size."""
    analysis = gen._analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    counts = collections.Counter(frame["interior"] for frame in analysis["frames"])
    max_count = max(counts.values())
    modal_sizes = [shape for shape, count in counts.items() if count == max_count]
    if len(modal_sizes) != 1:
        raise ValueError(f"modal size is tied: {modal_sizes}")
    selected_size = modal_sizes[0]
    template = analysis["template"]
    out = [[0] * analysis["grid_w"] for _ in range(analysis["grid_h"])]
    for frame in analysis["frames"]:
        if frame["interior"] != selected_size:
            continue
        r0, c0, r1, c1 = frame["bbox"]
        gen.draw_frame(out, r0, c0, r1, c1, frame["color"])
        ih, iw = frame["interior"]
        for dr, dc in template["pattern"]:
            if 0 <= dr < ih and 0 <= dc < iw:
                out[r0 + 1 + dr][c0 + 1 + dc] = frame["color"]
    return out


def draw_frame(grid: list[list[int]], r0: int, c0: int, r1: int, c1: int, color: int) -> None:
    for c in range(c0, c1 + 1):
        grid[r0][c] = color
        grid[r1][c] = color
    for r in range(r0, r1 + 1):
        grid[r][c0] = color
        grid[r][c1] = color


def accepted_counterexample() -> list[list[int]]:
    """Two 5x5 template-size frames; three repeated 6x6 distractors."""
    grid = [[0] * 24 for _ in range(24)]
    # Patterned template and one receiver: interior 3x3, count 2.
    draw_frame(grid, 1, 1, 5, 5, 1)
    grid[2][2] = 1
    grid[3][3] = 1
    draw_frame(grid, 1, 9, 5, 13, 2)
    # Three mutually equal distractors: interior 4x4, modal count 3.
    draw_frame(grid, 9, 1, 14, 6, 3)
    draw_frame(grid, 9, 10, 14, 15, 4)
    draw_frame(grid, 17, 5, 22, 10, 5)
    return grid


def main() -> None:
    gen = load_module_from_path(f"audit_{TASK_ID}", GENERATOR_PATH)
    row = canonical_row()
    source_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()

    generated_records: list[dict] = []
    for band in ("easy", "medium", "hard"):
        for seed in range(100):
            sample_index = seed % 8
            grid = gen.generate(seed, sample_index, difficulty=band)
            analysis = gen._analyze_scene(grid)
            if analysis["errors"]:
                raise AssertionError(analysis["errors"])
            counts = collections.Counter(frame["interior"] for frame in analysis["frames"])
            modal = max(counts, key=counts.get)
            intended = gen.rule_mirror(grid)
            shortcut = modal_size_shortcut(gen, grid)
            generated_records.append({
                "difficulty": band,
                "seed": seed,
                "sample_index": sample_index,
                "size_counts": {str(k): v for k, v in sorted(counts.items())},
                "template_size": list(analysis["template"]["interior"]),
                "modal_size": list(modal),
                "matches_python_mirror": shortcut == intended,
            })

    counterexample = accepted_counterexample()
    grammar_errors = gen.self_check(counterexample)
    analysis = gen._analyze_scene(counterexample)
    intended_py = gen.rule_mirror(counterexample)
    shortcut_out = modal_size_shortcut(gen, counterexample)

    # Independent Racket checks on the counterexample and 12 generated scenes.
    bridge = RacketBridge(max_calls_before_restart=32)
    racket_generated_matches = 0
    racket_generated_total = 0
    try:
        intended_racket = bridge.eval_text(rule_application(row["program_solution"], counterexample))
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(4):
                grid = gen.generate(900 + band_index * 10 + seed, seed, difficulty=band)
                oracle = bridge.eval_text(rule_application(row["program_solution"], grid))
                racket_generated_total += 1
                racket_generated_matches += int(modal_size_shortcut(gen, grid) == oracle)
    finally:
        bridge.shutdown()

    report = {
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "generator_version": gen.VERSION,
        "shortcut": (
            "use the unique most frequent frame interior size as the kept size; "
            "copy the sole visible template pattern into those frames"
        ),
        "generated_probe": {
            "sample_count": len(generated_records),
            "python_mirror_matches": sum(r["matches_python_mirror"] for r in generated_records),
            "all_python_mirror_matches": all(r["matches_python_mirror"] for r in generated_records),
            "racket_sample_count": racket_generated_total,
            "racket_matches": racket_generated_matches,
            "sample_summaries": generated_records,
        },
        "accepted_counterexample": {
            "self_check_errors": grammar_errors,
            "size_counts": {
                str(k): v
                for k, v in sorted(collections.Counter(
                    frame["interior"] for frame in analysis["frames"]
                ).items())
            },
            "template_size": list(analysis["template"]["interior"]),
            "input": counterexample,
            "canonical_racket_output": intended_racket,
            "python_mirror_output": intended_py,
            "shortcut_output": shortcut_out,
            "racket_matches_python_mirror": intended_racket == intended_py,
            "shortcut_differs": shortcut_out != intended_racket,
        },
        "finding": (
            "The sampler always makes every distractor size distinct, so the template-size "
            "class is the unique modal size. The public self_check grammar does not require "
            "distractor sizes to be mutually distinct and accepts a scene where three repeated "
            "distractors outnumber two template-size frames. The canonical rule follows the "
            "patterned template there, while the modal-size shortcut fails."
        ),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = {
        "report": str(REPORT_PATH),
        "generator_sha256": source_hash,
        "generated_python_matches": f"{report['generated_probe']['python_mirror_matches']}/{len(generated_records)}",
        "generated_racket_matches": f"{racket_generated_matches}/{racket_generated_total}",
        "counterexample_self_check_errors": grammar_errors,
        "counterexample_shortcut_differs": shortcut_out != intended_racket,
    }
    print(json.dumps(summary, indent=2))

    if grammar_errors:
        raise SystemExit("counterexample was not accepted by self_check")
    if intended_racket != intended_py:
        raise SystemExit("canonical Racket output and Python mirror disagree")
    if shortcut_out == intended_racket:
        raise SystemExit("counterexample did not refute modal-size shortcut")
    if not all(r["matches_python_mirror"] for r in generated_records):
        raise SystemExit("shortcut did not fit every sampled generated scene")
    if racket_generated_matches != racket_generated_total:
        raise SystemExit("shortcut did not match sampled Racket labels")


if __name__ == "__main__":
    main()
