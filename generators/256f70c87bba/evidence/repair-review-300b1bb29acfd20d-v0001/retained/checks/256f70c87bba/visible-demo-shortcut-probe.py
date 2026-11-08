#!/usr/bin/env python3
"""Bounded visible-demo shortcut probe for 256f70c87bba."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_path, load_selected_generator

TASK = "256f70c87bba"
EXPECTED_SOURCE = "27a1b85f4d4a59b63f015b41b78c2bb124fcd5e478e463cf6c0508602dd720e1"


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def blank(h, w):
    return [[0 for _ in range(w)] for _ in range(h)]


def render(module, analysis, turns_for_component, *, retain_one_marker=False):
    out = blank(analysis["h"], analysis["w"])
    for r, c in analysis["pivots"]:
        out[r][c] = 8
    for component in analysis["components"]:
        turns = turns_for_component(component, analysis) % 4
        for r, c in module._rotate_cells_cw(component["cells"], analysis["pivots"][component["owner"]], turns):
            out[r][c] = component["color"]
    if retain_one_marker:
        for (pr, pc), cue in zip(analysis["pivots"], analysis["cues"]):
            if cue == 1:
                out[pr][pc - 1] = 1
    return out


def rivals(module, grid):
    analysis = module._analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"])
    first_cue = analysis["cues"][0]
    first_turns = first_cue if first_cue in (1, 2, 3) else 0
    return {
        "one_global_first_pivot_command": render(
            module, analysis, lambda _component, _analysis: first_turns
        ),
        "component_color_is_command": render(
            module, analysis,
            lambda component, _analysis: component["color"] if component["color"] in (1, 2, 3) else 0,
        ),
        "all_nonzero_cues_rotate_modulo_four": render(
            module, analysis,
            lambda component, current: current["cues"][component["owner"]] % 4,
        ),
        "retain_command_one_marker": render(
            module, analysis,
            lambda component, current: (
                current["cues"][component["owner"]]
                if current["cues"][component["owner"]] in (1, 2, 3)
                else 0
            ),
            retain_one_marker=True,
        ),
    }


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: visible-demo-shortcut-probe.py OUTPUT.json")
    output = Path(sys.argv[1])
    if output.exists():
        raise FileExistsError(output)
    module, source_path, source_hash = load_selected_generator(TASK)
    if source_hash != EXPECTED_SOURCE:
        raise ValueError(f"peer source changed: {source_hash}")
    sources = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(Path.cwd()).read_text().splitlines())
        if row.get("task_id") == TASK
    }
    if len(sources) != 1:
        raise ValueError("expected one canonical program")
    program = sources.pop()

    runtime = Path.cwd() / "shared/runtime"
    sys.path[:0] = [str(runtime)]
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    wrapped = wrap_rule(program)
    identity = bridge.runtime_identity
    rows = []
    findings = []
    racket_evaluations = 0
    try:
        for seed in range(24):
            grids = [module.generate(seed, index, difficulty="medium") for index in range(5)]
            labels = []
            for grid in grids:
                racket_evaluations += 1
                label = bridge.eval_text(f"({wrapped} {literal(grid)})")
                if label != module._expected_output(grid):
                    raise ValueError("Python mirror differs from protected Racket")
                labels.append(label)
            demos = [{"input": deepcopy(grid), "output": deepcopy(label)}
                     for grid, label in zip(grids[:4], labels[:4])]
            query = {"input": deepcopy(grids[4]), "output": deepcopy(labels[4])}
            hook = module.lesson_identifiable(demos, query)
            if hook:
                raise ValueError(f"seed {seed}: lesson hook rejected generated lesson: {hook}")

            names = sorted(rivals(module, grids[0]))
            result = {}
            for name in names:
                rival_outputs = [rivals(module, grid)[name] for grid in grids]
                demo_matches = [got == want for got, want in zip(rival_outputs[:4], labels[:4])]
                survives = all(demo_matches)
                query_disagrees = rival_outputs[4] != labels[4]
                result[name] = {
                    "demo_matches": demo_matches,
                    "survives_demos": survives,
                    "query_disagrees": query_disagrees,
                }
                if survives and query_disagrees:
                    findings.append({
                        "seed": seed,
                        "rival": name,
                        "query_input": grids[4],
                        "canonical_output": labels[4],
                        "rival_output": rival_outputs[4],
                    })
            rows.append({"seed": seed, "lesson_identifiable": True, "rivals": result})
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-peer-visible-demo-shortcut-probe-v1",
        "task_id": TASK,
        "source_path": source_path.relative_to(Path.cwd()).as_posix(),
        "source_sha256": source_hash,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "racket": {"backend": identity.get("backend"), "protected": identity.get("protected")},
        "seeds": 24,
        "lessons": 24,
        "demonstrations_per_lesson": 4,
        "queries_per_lesson": 1,
        "rivals": [
            "one_global_first_pivot_command",
            "component_color_is_command",
            "all_nonzero_cues_rotate_modulo_four",
            "retain_command_one_marker",
        ],
        "racket_evaluations": racket_evaluations,
        "findings": findings,
        "status": "finding" if findings else "bounded_no_finding",
        "rows": rows,
        "limits": (
            "Finite medium-band sample and four authored shortcuts only; no universal uniqueness "
            "claim and no peer source modification."
        ),
    }
    output.write_bytes(raw(report))
    print(json.dumps({
        "status": report["status"],
        "lessons": report["lessons"],
        "rivals": len(report["rivals"]),
        "racket_evaluations": racket_evaluations,
        "findings": len(findings),
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
