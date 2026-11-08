from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

WORK = Path(__file__).resolve().parents[3]
GEN_PATH = WORK / "repo/generators/generic_window_transplant_gen1/generator.py"
OUT_PATH = Path(__file__).with_name("counterexample.json")

spec = importlib.util.spec_from_file_location("generic_window_transplant_gen1_audit", GEN_PATH)
assert spec and spec.loader
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body


def interior(grid: list[list[int]], b: tuple[int, int, int, int]) -> list[list[int]]:
    return [row[b[1] + 1 : b[3]] for row in grid[b[0] + 1 : b[2]]]


def interior_bg(sub: list[list[int]]) -> int:
    counts = Counter(v for row in sub for v in row)
    # Match the generator's stable first-value tie behavior.
    best = sub[0][0]
    for row in sub:
        for v in row:
            if counts[v] > counts[best]:
                best = v
    return best


def decos(grid: list[list[int]], b: tuple[int, int, int, int]) -> list[list[tuple[int, int]]]:
    sub = interior(grid, b)
    return G._mc_comps(sub, interior_bg(sub))


def windows(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    h, w = len(grid), len(grid[0])
    found = []
    for r in range(h - 4):
        for c in range(w - 4):
            b = G._window_at(grid, r, c)
            if b is not None:
                found.append(b)
    found = sorted(found)
    # The detector may report ring-like subwindows nested inside a true frame.
    # The scene's two framed windows are the maximal (non-contained) boxes.
    outer = []
    for b in found:
        if not any(
            other != b
            and other[0] <= b[0]
            and other[1] <= b[1]
            and other[2] >= b[2]
            and other[3] >= b[3]
            for other in found
        ):
            outer.append(b)
    return outer


def positional_top_donor_bottom_receiver(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: semantic roles are fixed by vertical position.

    It otherwise performs the intended transplantation. It matches the current
    generator because every constructed donor is above every receiver.
    """
    ws = windows(grid)
    if len(ws) != 2:
        raise ValueError(f"expected two windows, got {ws}")
    donor, receiver = ws[0], ws[1]
    dsub = interior(grid, donor)
    rsub = interior(grid, receiver)
    donor_decos = decos(grid, donor)
    receiver_decos = decos(grid, receiver)
    icon = donor_decos[0]

    # Infer the anchor color as a color occurring exactly once in every receiver
    # decoration. This is the true marker color on ordinary generated samples;
    # after vertical reflection it remains the icon's unique anchor color.
    candidate_colors = sorted({rsub[r][c] for comp in receiver_decos for r, c in comp})
    marker_color = next(
        color
        for color in candidate_colors
        if all(sum(rsub[r][c] == color for r, c in comp) == 1 for comp in receiver_decos)
    )
    anchor = next((r, c) for r, c in icon if dsub[r][c] == marker_color)

    out = [row[receiver[1] : receiver[3] + 1] for row in grid[receiver[0] : receiver[2] + 1]]
    out = [row[:] for row in out]
    for comp in receiver_decos:
        mr, mc = next((r, c) for r, c in comp if rsub[r][c] == marker_color)
        for pr, pc in icon:
            out[1 + mr + pr - anchor[0]][1 + mc + pc - anchor[1]] = dsub[pr][pc]
    return out


def role_order(grid: list[list[int]]) -> tuple[str, str]:
    ws = windows(grid)
    if len(ws) != 2:
        return ("invalid", "invalid")
    sizes = [max(map(len, decos(grid, b)), default=0) for b in ws]
    roles = tuple("donor" if size > 1 else "receiver" for size in sizes)
    return roles  # type: ignore[return-value]


def sha_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


sample_pairs = 0
positional_matches = 0
role_orders: Counter[tuple[str, str]] = Counter()
for band in ("easy", "medium", "hard"):
    for seed in range(100):
        task = G.generate_task(seed, difficulty=band)
        for split in ("train", "test"):
            for pair in task[split]:
                sample_pairs += 1
                role_orders[role_order(pair["input"])] += 1
                positional_matches += positional_top_donor_bottom_receiver(pair["input"]) == pair["output"]

seed = 0
band = "medium"
task = G.generate_task(seed, difficulty=band)
original = task["train"][0]
flipped_input = list(reversed([row[:] for row in original["input"]]))
python_true = G._apply(flipped_input)
positional = positional_top_donor_bottom_receiver(flipped_input)

bridge = RacketBridge()
bridge.define_grid("g", flipped_input)
racket_true = bridge.eval_text(_program_body(G.PROGRAM))

record = {
    "schema": "arcpuzzles-generic-audit-counterexample-v1",
    "task_id": G.TASK_ID,
    "version": G.VERSION,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "program_sha256": hashlib.sha256(G.PROGRAM.encode()).hexdigest(),
    "generated_sample_census": {
        "bands": ["easy", "medium", "hard"],
        "seed_range": [0, 99],
        "pairs": sample_pairs,
        "role_order_counts": {"/".join(k): v for k, v in sorted(role_orders.items())},
        "top_donor_bottom_receiver_rival_matches": positional_matches,
    },
    "construction": {
        "seed": seed,
        "difficulty": band,
        "split": "train",
        "pair_index": 0,
        "transform": "vertical reflection of a generated input; preserves stripe field, frames, icon copies, marker copies, and geometry while reversing role position",
        "original_input_sha256": sha_json(original["input"]),
        "original_output_sha256": sha_json(original["output"]),
        "original_positional_rival_matches": positional_top_donor_bottom_receiver(original["input"]) == original["output"],
        "reflected_role_order": list(role_order(flipped_input)),
        "detected_windows": [list(b) for b in windows(flipped_input)],
    },
    "input": flipped_input,
    "actual_racket_output": racket_true,
    "python_mirror_output": python_true,
    "positional_rival_output": positional,
    "checks": {
        "racket_matches_python_mirror": racket_true == python_true,
        "rival_differs": positional != racket_true,
        "input_sha256": sha_json(flipped_input),
        "actual_output_sha256": sha_json(racket_true),
        "rival_output_sha256": sha_json(positional),
    },
    "command": [
        "python3",
        "run_with_racket.py",
        "python3",
        "../checks/audit/generic_window_transplant_gen1/probe.py",
    ],
    "cwd": "WORK",
    "domain_status": "domain-preserving counterfactual under the documented two-window scene; the generator has no explicit self_check hook",
}
OUT_PATH.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "sample_pairs": sample_pairs,
    "positional_matches": positional_matches,
    "role_orders": {"/".join(k): v for k, v in role_orders.items()},
    "racket_matches_python": racket_true == python_true,
    "rival_differs": positional != racket_true,
    "counterexample": str(OUT_PATH),
}, indent=2))
