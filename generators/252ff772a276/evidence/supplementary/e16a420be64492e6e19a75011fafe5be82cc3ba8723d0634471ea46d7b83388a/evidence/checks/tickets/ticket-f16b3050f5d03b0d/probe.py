from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-f16b3050f5d03b0d"
TICKET_PROBE_SEED = "05a20835104fa4f916f1a280f01e112ffbf164087160b312463f2b4e198e7116"
TASK_ID = "252ff772a276"
EXPECTED_SOURCE_SHA256 = "72ff11fcc16b122fe5b4e955183272715ac091936be06530888d3bc9f69b72b1"
EXPECTED_RULE_HASH = "40bcdf750b85"

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
generator, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def execute_rule(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    bridge.define_grid("g", grid)
    body = program[len("(rule!") : -1].strip()
    return bridge.eval_text(body)


def normalize_grid(value: list[Any]) -> list[list[int]]:
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def crop_and_fill(grid: list[list[int]], frame: dict[str, Any]) -> list[list[int]]:
    crop = [
        list(grid[row][frame["c1"] : frame["c2"] + 1])
        for row in range(frame["r1"], frame["r2"] + 1)
    ]
    for row in range(1, len(crop) - 1):
        for col in range(1, len(crop[0]) - 1):
            if crop[row][col] == 0:
                crop[row][col] = 3
    return crop


def largest_area_rival(grid: list[list[int]]) -> tuple[list[list[int]], dict[str, Any]]:
    frames = generator._analysis(grid)["frames"]
    chosen = min(frames, key=lambda frame: (-frame["area"], frame["r1"], frame["c1"]))
    return crop_and_fill(grid, chosen), chosen


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int | None]]:
    height = max(len(left), len(right))
    width = max(
        max((len(row) for row in left), default=0),
        max((len(row) for row in right), default=0),
    )
    result: list[list[int | None]] = []
    for row in range(height):
        for col in range(width):
            lv = left[row][col] if row < len(left) and col < len(left[row]) else None
            rv = right[row][col] if row < len(right) and col < len(right[row]) else None
            if lv != rv:
                result.append([row, col, lv, rv])
    return result


def load_canonical() -> dict[str, Any]:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 1:
        raise RuntimeError(f"expected one canonical row, found {len(rows)}")
    return rows[0]


if source_sha256 != EXPECTED_SOURCE_SHA256:
    raise RuntimeError(f"source SHA mismatch: {source_sha256}")
if getattr(generator, "RULE_HASH", None) != EXPECTED_RULE_HASH:
    raise RuntimeError(f"rule hash mismatch: {getattr(generator, 'RULE_HASH', None)!r}")

canonical = load_canonical()
program = canonical["program_solution"]
program_sha256 = hashlib.sha256(program.encode("utf-8")).hexdigest()
canonical_checks = []

# Bind the witness selection to the ticket seed while forcing the lawful profile
# whose semantics are under test.
generation_seed = int(TICKET_PROBE_SEED[:8], 16)
sample_index = int(TICKET_PROBE_SEED[8:16], 16)
difficulty = "hard"
profile = "small_winner"

with RacketBridge() as bridge:
    public_pairs = [*canonical["train"]]
    test = canonical["test"]
    public_pairs.extend(test if isinstance(test, list) else [test])
    for index, pair in enumerate(public_pairs):
        grid = normalize_grid(pair["input"])
        expected = normalize_grid(pair["output"])
        intended = execute_rule(bridge, program, grid)
        mirror = generator.rule_mirror(grid)
        rival, rival_frame = largest_area_rival(grid)
        if intended != expected or mirror != intended:
            raise RuntimeError(f"canonical authority mismatch at pair {index}")
        canonical_checks.append({
            "pair_index": index,
            "rival_matches": rival == intended,
            "intended_frame": generator._analysis(grid)["chosen"],
            "rival_frame": rival_frame,
        })

    grid = generator.generate(
        generation_seed,
        sample_index,
        difficulty=difficulty,
        scene_profile=profile,
    )
    findings = generator.self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"scene_profile": profile}},
    )
    if findings:
        raise RuntimeError(f"generated witness failed self-check: {findings}")
    info = generator._analysis(grid)
    intended = execute_rule(bridge, program, grid)
    mirror = generator.rule_mirror(grid)
    rival, rival_frame = largest_area_rival(grid)

if info["scene_profile"] != profile:
    raise RuntimeError(f"expected {profile}, got {info['scene_profile']}")
if intended != mirror:
    raise RuntimeError("Python mirror disagrees with canonical Racket")
if not all(row["rival_matches"] for row in canonical_checks):
    raise RuntimeError("largest-area rival should fit all canonical pairs")
chosen = info["chosen"]
if not chosen["seed_count"] > rival_frame["seed_count"]:
    raise RuntimeError("witness does not give the intended frame more seeds")
if not chosen["area"] < rival_frame["area"]:
    raise RuntimeError("witness does not make the intended frame strictly smaller")
if rival == intended:
    raise RuntimeError("witness does not refute the largest-area shortcut")

frame_projection = lambda frame: {
    key: frame[key]
    for key in ("r1", "c1", "r2", "c2", "height", "width", "area", "seed_count", "seed_cells")
}
payload = {
    "schema": "arcpuzzles-ticket-adversarial-witness-v1",
    "ticket_id": TICKET_ID,
    "ticket_probe_seed": TICKET_PROBE_SEED,
    "task_id": TASK_ID,
    "status": "completed",
    "source_path": str(source.relative_to(ROOT)),
    "source_sha256": source_sha256,
    "rule_hash": generator.RULE_HASH,
    "canonical_program_sha256": program_sha256,
    "shortcut": (
        "Select the valid frame with largest rectangular area, breaking ties "
        "topmost then leftmost; crop it and apply the intended interior fill."
    ),
    "canonical_pair_count": len(canonical_checks),
    "canonical_all_fit_shortcut": all(row["rival_matches"] for row in canonical_checks),
    "canonical_checks": canonical_checks,
    "witness": {
        "generation_seed": generation_seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "scene_profile": info["scene_profile"],
        "self_check": findings,
        "frames": [frame_projection(frame) for frame in info["frames"]],
        "intended_frame": frame_projection(chosen),
        "shortcut_frame": frame_projection(rival_frame),
        "intended_has_more_seeds": chosen["seed_count"] > rival_frame["seed_count"],
        "intended_has_smaller_area": chosen["area"] < rival_frame["area"],
        "input": grid,
        "intended_output": intended,
        "shortcut_output": rival,
        "shortcut_refuted": rival != intended,
        "differing_cells": differing_cells(intended, rival),
    },
    "conclusion": (
        "A largest-area solver fits every canonical pair but fails this lawful "
        "small_winner example: the correct frame has more interior seeds while "
        "being strictly smaller than the shortcut's frame."
    ),
}
(HERE / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "ticket_id": TICKET_ID,
    "task_id": TASK_ID,
    "status": payload["status"],
    "source_sha256": source_sha256,
    "canonical_all_fit_shortcut": payload["canonical_all_fit_shortcut"],
    "scene_profile": payload["witness"]["scene_profile"],
    "intended_seed_count": chosen["seed_count"],
    "shortcut_seed_count": rival_frame["seed_count"],
    "intended_area": chosen["area"],
    "shortcut_area": rival_frame["area"],
    "shortcut_refuted": payload["witness"]["shortcut_refuted"],
    "difference_count": len(payload["witness"]["differing_cells"]),
}, indent=2, sort_keys=True))
