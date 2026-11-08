#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    matches = [row for row in rows if row.get("task_id") == task_id]
    assert len(matches) == 1
    return matches[0]


def full_height_nines(grid: list[list[int]]) -> list[int]:
    return [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]


def split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    cuts = full_height_nines(grid)
    starts = [0] + [c + 1 for c in cuts]
    ends = cuts + [len(grid[0])]
    return [[row[a:b] for row in grid] for a, b in zip(starts, ends) if a < b]


def occupied(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    }


def connected_component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
    return count


def normalized(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def first_component(panel: list[list[int]]) -> set[tuple[int, int]]:
    cells = occupied(panel)
    if not cells:
        return set()
    start = min(cells)
    comp = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if nxt in cells and nxt not in comp:
                comp.add(nxt)
                stack.append(nxt)
    return comp


def first_component_rival(grid: list[list[int]]) -> list[list[int]]:
    panels = split_panels(grid)
    source = normalized(first_component(panels[0]))
    return [[8 if normalized(first_component(panel)) == source else 0 for panel in panels[1:]]]


def e5_probe() -> dict[str, Any]:
    task = "e5ec1ac39df5"
    module, source_hash = load_generator(task)
    row = canonical(task)
    pairs = [*row["train"], row["test"]]
    errors = [module.self_check(pair["input"]) for pair in pairs]
    assert errors[0] == []
    assert errors[1]
    assert errors[2]

    uniform_centered = 0
    sampled = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(1, 101):
            grid = module.generate(seed, seed, difficulty=difficulty)
            assert module.self_check(grid) == []
            wr = module._wall_rows(grid)
            wc = module._wall_cols(grid)
            room_hs = [b - a - 1 for a, b in zip(wr, wr[1:])]
            room_ws = [b - a - 1 for a, b in zip(wc, wc[1:])]
            centered = True
            for ra, rb in zip(wr, wr[1:]):
                for ca, cb in zip(wc, wc[1:]):
                    seeds = [
                        (r, c)
                        for r in range(ra + 1, rb)
                        for c in range(ca + 1, cb)
                        if grid[r][c] == 2
                    ]
                    if seeds:
                        center = (
                            ra + 1 + (rb - ra - 1) // 2,
                            ca + 1 + (cb - ca - 1) // 2,
                        )
                        centered &= seeds == [center]
            sampled += 1
            uniform_centered += int(
                len(set(room_hs)) == 1 and len(set(room_ws)) == 1 and centered
            )
    assert uniform_centered == sampled == 300

    racket = json.loads((ROOT / "checks" / "audit" / task / "racket.json").read_text())
    rival_outputs = [
        [[0 for _ in result["input"][0]] for _ in result["input"]]
        for result in racket["results"]
    ]
    assert all(rival != result["output"] for rival, result in zip(rival_outputs, racket["results"]))
    report = {
        "schema": "arcpuzzles-audit-finding-v1",
        "task_id": task,
        "generator_sha256": source_hash,
        "executed_rule_hash": racket["executed_rule_hash"],
        "finding_type": "canonical-coverage-and-teaching-domain",
        "canonical_self_check": [
            {"pair_index": index, "errors": pair_errors}
            for index, pair_errors in enumerate(errors)
        ],
        "sample_probe": {
            "difficulties": ["easy", "medium", "hard"],
            "seeds_and_sample_indices": "1..100, sample_index=seed",
            "draws": sampled,
            "uniform_rooms_and_centered_seeds": uniform_centered,
        },
        "shortcut": (
            "Only solve uniform rectangular lattices with centered seeds; return blank "
            "for one-row, nonuniform, or off-center-seed layouts."
        ),
        "inputs_are_canonical": True,
        "inputs_pass_self_check": [not bool(item) for item in errors[1:]],
        "racket_outputs": [result["output"] for result in racket["results"]],
        "rival_outputs": rival_outputs,
        "apply_command": racket["command"],
        "apply_cwd": racket["cwd"],
        "note": (
            "The first audited input is the second canonical train pair (1x3 rooms); "
            "the second is the canonical test pair (nonuniform rooms/off-center seed)."
        ),
    }
    path = ROOT / "checks" / "audit" / task / "finding.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def panel_probe() -> dict[str, Any]:
    task = "5ca7ad03e520"
    module, source_hash = load_generator(task)
    input_grid = json.loads((ROOT / "checks" / "audit" / task / "input.json").read_text())
    validator_errors = module.self_check(input_grid)
    assert validator_errors == []
    racket = json.loads((ROOT / "checks" / "audit" / task / "racket.json").read_text())
    actual = racket["results"][0]["output"]
    rival = first_component_rival(input_grid)
    assert actual == [[0, 8, 0]]
    assert rival == [[8, 8, 0]]

    connected_draws = 0
    total_draws = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(1, 101):
            grid = module.generate(seed, seed, difficulty=difficulty)
            panels = split_panels(grid)
            total_draws += 1
            if all(connected_component_count(occupied(panel)) == 1 for panel in panels):
                connected_draws += 1
    assert connected_draws == total_draws == 300

    override_rows = []
    for seed in range(1, 21):
        grid = module.generate(seed, seed, difficulty="hard", n_panels=7)
        realized = len(split_panels(grid))
        errs = module.self_check(grid)
        override_rows.append(
            {"seed": seed, "requested_n_panels": 7, "realized_n_panels": realized, "self_check": errs}
        )
    assert all(row["realized_n_panels"] == 6 and row["self_check"] == [] for row in override_rows)

    report = {
        "schema": "arcpuzzles-audit-finding-v1",
        "task_id": task,
        "generator_sha256": source_hash,
        "executed_rule_hash": racket["executed_rule_hash"],
        "finding_type": "semantic-shortcut-and-override-contract",
        "input": input_grid,
        "input_passes_self_check": True,
        "documented_domain": {
            "panel_h": 3,
            "n_panels": 4,
            "motif_sizes": [1, 2],
        },
        "racket_output": actual,
        "rival_output": rival,
        "shortcut": (
            "Compare only the first 4-connected occupied component in each panel. "
            "This is equivalent on every generated panel because all sampled motifs are connected, "
            "but fails on an accepted disconnected source motif."
        ),
        "sample_probe": {
            "difficulties": ["easy", "medium", "hard"],
            "seeds_and_sample_indices": "1..100, sample_index=seed",
            "draws": total_draws,
            "all_panels_connected": connected_draws,
        },
        "override_probe": {
            "difficulty": "hard",
            "seeds_and_sample_indices": "1..20, sample_index=seed",
            "rows": override_rows,
            "summary": "20/20 requests for n_panels=7 silently returned 6 self-check-clean panels.",
        },
        "apply_command": racket["command"],
        "apply_cwd": racket["cwd"],
    }
    path = ROOT / "checks" / "audit" / task / "finding.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    e5 = e5_probe()
    panels = panel_probe()
    print(json.dumps({
        "e5ec1ac39df5": {
            "canonical_rejections": sum(bool(x["errors"]) for x in e5["canonical_self_check"]),
            "sampled_uniform_centered": e5["sample_probe"]["uniform_rooms_and_centered_seeds"],
        },
        "5ca7ad03e520": {
            "accepted_counterexample": panels["input_passes_self_check"],
            "racket_output": panels["racket_output"],
            "rival_output": panels["rival_output"],
            "connected_draws": panels["sample_probe"]["all_panels_connected"],
            "override_rows": len(panels["override_probe"]["rows"]),
        },
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
