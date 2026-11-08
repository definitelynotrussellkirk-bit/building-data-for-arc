"""Findings-only audit of the omitted four-header reflection in b88894a36787."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "b88894a36787"
OUT = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


def save(name: str, value) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def assumed_missing_position(grid):
    """Shortcut induced by sampler geometry, not the intended color relation."""
    h, w = len(grid), len(grid[0])
    header = [(c, color) for c, color in enumerate(grid[0]) if color]
    dots = [(r, c, grid[r][c]) for r in range(1, h) for c in range(w) if grid[r][c]]
    guessed = None
    if len(dots) < len(header):
        sides = {c for _, c, _ in dots}
        if len(sides) == 2:
            guessed = len(header) // 2
        elif sides == {0}:
            guessed = len(header) - 1
        elif sides == {w - 1}:
            guessed = 0
    entries = []
    for i, (header_col, color) in enumerate(header):
        dot = next((item for item in dots if item[2] == color), None)
        target_row, target_col = (dot[0], dot[1]) if dot else (0, None)
        vertical_end = h - 1 if i == guessed else target_row
        entries.append((header_col, color, target_row, target_col, vertical_end))
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            for hc, color, tr, tc, ve in entries:
                vertical = c == hc and r <= ve
                horizontal = tc is not None and r == tr and min(hc, tc) <= c <= max(hc, tc)
                if vertical or horizontal:
                    out[r][c] = color
                    break
    return out


def observe(grid):
    header = [(c, value) for c, value in enumerate(grid[0]) if value]
    dots = [(r, c, grid[r][c]) for r in range(1, len(grid)) for c in range(len(grid[0])) if grid[r][c]]
    present = {value for _, _, value in dots}
    return {
        "header": header,
        "dots": dots,
        "missing_indices": [i for i, (_c, color) in enumerate(header) if color not in present],
    }


def prepare() -> None:
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    canonical_fits = sum(assumed_missing_position(pair["input"]) == pair["output"] for pair in canonical)
    base = GEN.generate(0, 0, grid_h=11, grid_w=11, n_markers=4)
    reflected = [row[::-1] for row in base]
    if GEN.self_check(reflected):
        raise AssertionError(f"reflected legal input rejected: {GEN.self_check(reflected)}")

    generated_cases = []
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17, 101):
            for index in range(8):
                grid = GEN.generate(seed, index, difficulty=difficulty, n_markers=4)
                generated_cases.append({
                    "difficulty": difficulty,
                    "seed": seed,
                    "sample_index": index,
                    "observed": observe(grid),
                    "rival_matches_python_diagnostic": assumed_missing_position(grid) == GEN._prediction(grid),
                })
    summary = {
        "task_id": TASK,
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA,
        "rule_hash": GEN.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_rival_fits": canonical_fits,
        "generated_cases": len(generated_cases),
        "generated_rival_python_matches": sum(item["rival_matches_python_diagnostic"] for item in generated_cases),
        "base_recipe": {"seed": 0, "sample_index": 0, "difficulty": None,
                        "overrides": {"grid_h": 11, "grid_w": 11, "n_markers": 4}},
        "transformation": "reverse every input row (horizontal reflection)",
        "reflected_self_check": GEN.self_check(reflected),
        "reflected_observed": observe(reflected),
        "source_reasoning": (
            "phase 0 always omits n//2; phase 2 omits only a boundary; phases 1 and 3 omit none. "
            "For n=4, interior missing index 1 is unreachable although its horizontal reflection is lawful."
        ),
    }
    save("prepared.json", {"summary": summary, "generated_cases": generated_cases})
    save("input.json", reflected)
    save("base_input.json", base)
    print(json.dumps(summary, indent=2))


def verify() -> None:
    prepared = json.loads((OUT / "prepared.json").read_text())
    receipt = json.loads((OUT / "racket.json").read_text())
    grid = json.loads((OUT / "input.json").read_text())
    base = json.loads((OUT / "base_input.json").read_text())
    if prepared["summary"]["generator_sha256"] != SOURCE_SHA:
        raise AssertionError("generator changed since prepare")
    result = receipt["results"][0]
    if result["input"] != grid:
        raise AssertionError("authority receipt input mismatch")
    rival = assumed_missing_position(grid)
    differences = [
        [r, c, result["output"][r][c], rival[r][c]]
        for r in range(len(grid)) for c in range(len(grid[0]))
        if result["output"][r][c] != rival[r][c]
    ]
    if not differences:
        raise AssertionError("shortcut unexpectedly agrees on reflected witness")
    if result["output"] != GEN._prediction(grid):
        raise AssertionError("Racket authority differs from diagnostic mirror")
    evidence = {
        "task_id": TASK,
        "generator_sha256": SOURCE_SHA,
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "rule_hash": GEN.RULE_HASH,
        "rule_callable_sha256": receipt.get("rule_text_sha256"),
        "authority_command": receipt.get("command"),
        "authority_cwd": receipt.get("cwd"),
        "recipe": prepared["summary"]["base_recipe"],
        "transformation": prepared["summary"]["transformation"],
        "input": grid,
        "actual_racket_output": result["output"],
        "rival_name": "assumed_missing_position",
        "rival_output": rival,
        "self_check": GEN.self_check(grid),
        "documented_domain": True,
        "sampler_reachable": False,
        "unreachability": prepared["summary"]["source_reasoning"],
        "observed": observe(grid),
        "differing_cells": differences,
        "generated_support_probe": {
            "cases": prepared["summary"]["generated_cases"],
            "rival_python_matches": prepared["summary"]["generated_rival_python_matches"],
            "canonical_pairs": prepared["summary"]["canonical_pairs"],
            "canonical_rival_fits": prepared["summary"]["canonical_rival_fits"],
        },
        "base_input_sha256": hashlib.sha256(json.dumps(base, separators=(",", ":")).encode()).hexdigest(),
    }
    save("counterexample.json", evidence)
    print(json.dumps({
        "generator_sha256": SOURCE_SHA,
        "self_check": evidence["self_check"],
        "observed": evidence["observed"],
        "difference_cells": len(differences),
        "generated_support_probe": evidence["generated_support_probe"],
    }, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify}[sys.argv[1]]()
