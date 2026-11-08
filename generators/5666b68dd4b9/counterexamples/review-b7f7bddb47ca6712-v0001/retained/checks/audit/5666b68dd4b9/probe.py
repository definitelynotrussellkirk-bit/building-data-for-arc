#!/usr/bin/env python3
"""Bounded, selector-blind rival probe; run from the packet's repo directory.

PYTHONPATH=shared/runtime python3 ../checks/audit/5666b68dd4b9/probe.py
Then obtain labels using the supported public command recorded in manifest.json.
No reference runner internals are imported.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "5666b68dd4b9"
OUT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def components(grid):
    """Independent same-colour 4-connected extraction, ignoring both controls and 8."""
    body = [row[:] for row in grid]
    body[0][0] = body[0][-1] = 0
    seen = set()
    result = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            color = body[r][c]
            if color in (0, 8) or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and body[nr][nc] == color:
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            r0, r1 = min(p[0] for p in cells), max(p[0] for p in cells)
            c0, c1 = min(p[1] for p in cells), max(p[1] for p in cells)
            crop = [[color if (rr, cc) in cells else 0 for cc in range(c0, c1 + 1)] for rr in range(r0, r1 + 1)]
            result.append({"color": color, "cells": sorted(cells), "size": len(cells),
                           "bbox": [r0, c0, r1, c1], "crop": crop,
                           "half_turn_asymmetric": crop != [row[::-1] for row in crop[::-1]]})
    return result


def rival(grid):
    """Ignore top-left selector; select largest component asymmetric under 180°."""
    candidates = [obj for obj in components(grid) if obj["half_turn_asymmetric"]]
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    if not candidates:
        return out
    chosen = max(candidates, key=lambda obj: (obj["size"], -obj["bbox"][0], -obj["bbox"][1]))
    crop = chosen["crop"]
    code = grid[0][-1]
    if code == 1:
        crop = [list(row) for row in zip(*crop[::-1])]
    elif code == 2:
        crop = [row[::-1] for row in crop[::-1]]
    elif code == 3:
        crop = [row[::-1] for row in crop]
    frame = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    r0, r1 = min(p[0] for p in frame), max(p[0] for p in frame)
    c0, c1 = min(p[1] for p in frame), max(p[1] for p in frame)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                out[r][c] = 8
    top = r0 + 1 + (r1 - r0 - 1 - len(crop)) // 2
    left = c0 + 1 + (c1 - c0 - 1 - len(crop[0])) // 2
    for r, row in enumerate(crop):
        for c, color in enumerate(row):
            rr, cc = top + r, left + c
            if color != 0 and 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = color
    return out


def main():
    root = find_root(Path.cwd())
    generator_path = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_generator", generator_path)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    canonical_records = [json.loads(line) for line in canonical_path(root).open()
                         if line.strip() and json.loads(line).get("task_id") == TASK_ID]
    assert len(canonical_records) == 1
    record = canonical_records[0]
    program = record["program_solution"]
    program_sha = hashlib.sha256(program.encode()).hexdigest()
    assert program_sha.startswith(generator.RULE_HASH)

    cases = []
    for seed in range(8):
        for sample_index in range(4):
            grid = generator.generate(seed, sample_index, difficulty="hard")
            cases.append({"kind": "generated", "seed": seed, "sample_index": sample_index,
                          "difficulty": "hard", "overrides": {}, "input": grid})
    for pair in canonical_pairs(TASK_ID, root=root):
        cases.append({"kind": "canonical", **pair})

    base_case = cases[1]
    mutant = [row[:] for row in base_case["input"]]
    large = [obj for obj in components(mutant) if obj["size"] == 8]
    assert len(large) == 1
    removed = large[0]["cells"][0]
    mutant[removed[0]][removed[1]] = 0
    cases.append({"kind": "counterexample", "seed": base_case["seed"],
                  "sample_index": base_case["sample_index"], "difficulty": "hard", "overrides": {},
                  "mutation": {"operation": "remove one corner from the eight-cell wrong-colour ring",
                               "cell": removed, "old_color": large[0]["color"], "new_color": 0},
                  "generator_emits_exact_input": False,
                  "domain": "Accepted by self_check and strict_canonical_like; satisfies all declared structural invariants. Outside the emitter image because _BIG_DISTRACTOR is always the intact eight-cell ring.",
                  "input": mutant})

    for index, case in enumerate(cases):
        grid = case["input"]
        case["apply_index"] = index
        case["input_sha256"] = digest(grid)
        case["self_check_errors"] = generator.self_check(grid)
        case["strict_canonical_like_errors"] = generator.strict_canonical_like(grid)
        case["observed_overrides"] = generator.observe_overrides(grid)
        case["rival_output"] = rival(grid)
        case["mirror_output"] = generator.rule_mirror(grid)
        case["rival_matches_mirror"] = case["rival_output"] == case["mirror_output"]
        case["components"] = components(grid)
    assert all(not case["self_check_errors"] and not case["strict_canonical_like_errors"] for case in cases)
    assert all(case["rival_matches_mirror"] for case in cases[:-1])
    assert not cases[-1]["rival_matches_mirror"]
    declared = {
        "CANONICAL_SHORTCUTS": {
            name: {"agreements": sum(fn(case["input"]) == case["output"] for case in cases if case["kind"] == "canonical"),
                   "denominator": sum(case["kind"] == "canonical" for case in cases)}
            for name, fn in generator.CANONICAL_SHORTCUTS.items()
        },
        "LESSON_COMPETITORS": list(generator.LESSON_COMPETITORS),
    }
    manifest = {
        "task_id": TASK_ID,
        "generator_path": f"repo/generators/{TASK_ID}/generator.py",
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "generator_version": generator.VERSION,
        "rule_sha256": program_sha,
        "rule_hash": generator.RULE_HASH,
        "canonical_record_sha256": digest(record),
        "rival": "largest_half_turn_asymmetric_component",
        "rival_description": "Erase both controls for component extraction; exclude colour 8 and every half-turn-symmetric component; choose the largest remaining component, breaking ties by row then column; transform using top-right code and center in the frame. The top-left selector value is never read.",
        "generated_sample_range": {"seeds": list(range(8)), "sample_indices": list(range(4)), "difficulty": "hard", "overrides": {}},
        "counts": {"generated": 32, "canonical": 4, "counterexamples": 1, "apply_grids": len(cases),
                   "unique_generated_inputs": len({case["input_sha256"] for case in cases if case["kind"] == "generated"})},
        "public_command": {"cwd": "packet_root", "effective_cwd": "repo",
                           "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                                    "--input", f"../checks/audit/{TASK_ID}/input.json", "--out", f"../checks/audit/{TASK_ID}/racket.json"]},
        "declared_rival_probe": declared,
        "cases": cases,
    }
    for name, value in (("input.json", [case["input"] for case in cases]), ("rival.json", [case["rival_output"] for case in cases]),
                        ("manifest.json", manifest), ("canonical_record.json", record)):
        (OUT / name).write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"task_id": TASK_ID, "generator_sha256": manifest["generator_sha256"],
                      "rule_sha256": program_sha, "counts": manifest["counts"],
                      "counterexample_apply_index": len(cases) - 1,
                      "all_self_checks_accepted": True, "all_strict_checks_accepted": True,
                      "rival_mirror_agreement": f"{len(cases) - 1}/{len(cases) - 1} unmodified cases",
                      "counterexample_disagrees": True}, indent=2))


if __name__ == "__main__":
    main()
