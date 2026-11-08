from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

gen, _SOURCE_PATH, _LOADED_SHA256 = load_selected_generator(
    "a02bd9f85082", root=REPO
)

TICKET_ID = "ticket-57bc5e1804947842"
PROBE_SEED = "1efb5816bc80d694376989e022049967e06c0edf43a6fc1b6471744a86d9e831"
EXPECTED_SOURCE_SHA256 = "0024cd60bc116abe69355c14fc0b5bcc4d51e03ca77c19b1bd55afd10ce024d8"
SOURCE = REPO / "generators/a02bd9f85082/generator.py"
OUT = WORK / "checks/tickets" / TICKET_ID / "result.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def earlier_turn_wins(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: at overlap cells, the earliest turn wins."""
    analysis = gen._analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for col, color in enumerate(facts["legend"]):
        output[0][col] = color
    pivot = facts["pivot"]
    output[pivot[0]][pivot[1]] = 5
    # Reverse application means turn 0 is painted last and therefore wins.
    for turn in (3, 2, 1, 0):
        color = facts["legend"][turn]
        for row, col in facts["source"]:
            delta = (row - pivot[0], col - pivot[1])
            drow, dcol = gen._turn_cell(delta, turn)
            output[pivot[0] + drow][pivot[1] + dcol] = color
    return output


def main() -> None:
    actual_sha = sha256(SOURCE)
    if actual_sha != EXPECTED_SOURCE_SHA256 or _LOADED_SHA256 != EXPECTED_SOURCE_SHA256:
        raise SystemExit(
            f"source hash mismatch: file={actual_sha} loaded={_LOADED_SHA256}"
        )

    numeric_seed = int(PROBE_SEED[:16], 16) % (2**31)
    witness = None
    attempts = 0
    for family in ("linked", "generalized"):
        for sample_index in range(64):
            attempts += 1
            grid = gen.generate(
                numeric_seed,
                sample_index,
                difficulty="hard",
                scene_family=family,
            )
            facts = gen._analyze(grid)["facts"]
            if not facts["overlap_count"]:
                continue
            official = gen.rule_mirror(grid)
            rival = earlier_turn_wins(grid)
            differences = [
                [row, col, official[row][col], rival[row][col]]
                for row in range(len(grid))
                for col in range(len(grid[0]))
                if official[row][col] != rival[row][col]
            ]
            if differences:
                witness = {
                    "scene_family": family,
                    "sample_index": sample_index,
                    "input": grid,
                    "official_output": official,
                    "earlier_turn_wins_output": rival,
                    "differing_cells": differences,
                    "facts": {
                        "overlap_count": facts["overlap_count"],
                        "source_size": facts["source_size"],
                        "legend": list(facts["legend"]),
                        "pivot": list(facts["pivot"]),
                        "visible_turns": list(facts["visible_turns"]),
                    },
                    "self_check": gen.self_check(grid),
                }
                break
        if witness is not None:
            break

    result = {
        "ticket_id": TICKET_ID,
        "task_id": gen.TASK_ID,
        "source_sha256": actual_sha,
        "rule_hash": gen.RULE_HASH,
        "probe_seed": PROBE_SEED,
        "numeric_seed": numeric_seed,
        "shortcut": "earlier quarter-turn wins at overlap cells",
        "attempts": attempts,
        "status": "completed" if witness is not None else "unknown",
        "witness": witness,
        "conclusion": (
            "A lawful overlap scene refutes the first-turn-wins shortcut."
            if witness is not None
            else "No refuting overlap witness was found in the bounded search."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "attempts": attempts,
        "differing_cells": 0 if witness is None else len(witness["differing_cells"]),
        "output": str(OUT),
    }, sort_keys=True))
    if witness is None:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
