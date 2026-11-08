"""Replay the current 01f1e6b34a5b transform-collision witness through protected Racket."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK_ID = "01f1e6b34a5b"
EXPECTED_SOURCE_SHA256 = "e4941959b42ae8ea13014eff9cf03b6d0e3bea94e92856cfe14069396abad52d"
SOURCE = REPO / f"generators/{TASK_ID}/generator.py"
LEGACY = REPO / (
    "generators/01f1e6b34a5b/counterexamples/"
    "review-6a3b9b07f56910e2-v0001/retained/checks/tickets/"
    "ticket-55191f7a25735c55"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    height = max(len(left), len(right))
    width = max(max(map(len, left), default=0), max(map(len, right), default=0))
    return sum(
        (left[r][c] if r < len(left) and c < len(left[r]) else None)
        != (right[r][c] if r < len(right) and c < len(right[r]) else None)
        for r in range(height)
        for c in range(width)
    )


def main() -> None:
    started = time.monotonic()
    sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src")]
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import normalize_grid

    current_sha = sha256(SOURCE)
    if current_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {current_sha}")

    witness = json.loads((LEGACY / "witness.json").read_text())
    pairs = witness["pairs"]
    if len(pairs) != 5 or [row["split"] for row in pairs] != ["train"] * 4 + ["test"]:
        raise RuntimeError("unexpected retained witness structure")

    canonical_source = (LEGACY / "canonical.rkt").read_text()
    rival_source = (LEGACY / "rival.rkt").read_text()
    bridge = RacketBridge(timeout=8.0, startup_timeout=20.0)
    replayed = []
    try:
        bridge.eval_text(f"(define replay_canonical {wrap_rule(canonical_source)})")
        bridge.eval_text(f"(define replay_rival {wrap_rule(rival_source)})")
        for index, row in enumerate(pairs):
            grid = normalize_grid(row["input"])
            bridge.define_grid("replay_input", grid)
            canonical = normalize_grid(bridge.eval_text("(replay_canonical replay_input)"))
            rival = normalize_grid(bridge.eval_text("(replay_rival replay_input)"))
            replayed.append(
                {
                    "split": row["split"],
                    "index": index,
                    "input": grid,
                    "canonical_output": canonical,
                    "rival_output": rival,
                    "outputs_equal": canonical == rival,
                    "changed_cells": changed_cells(canonical, rival),
                }
            )
    finally:
        bridge.shutdown()

    fits = all(row["outputs_equal"] for row in replayed[:4])
    disagrees = not replayed[4]["outputs_equal"]
    if not (fits and disagrees):
        raise RuntimeError("retained transform shortcut no longer reproduces")

    result = {
        "schema": "arcpuzzles-peer-adversarial-replay-v1",
        "task_id": TASK_ID,
        "status": "finding",
        "generator_sha256": current_sha,
        "canonical_program_sha256": hashlib.sha256(canonical_source.encode()).hexdigest(),
        "rival_program_sha256": hashlib.sha256(rival_source.encode()).hexdigest(),
        "rival": "Treat command code 4 as rotate-clockwise instead of flip-up/down.",
        "scope": "Four lawful constructed demonstrations and one lawful held-out query; protected Racket replay of both rules.",
        "rival_fits_every_demonstration": fits,
        "query_disagreement": disagrees,
        "query_changed_cells": replayed[4]["changed_cells"],
        "pairs": replayed,
        "recommendation": (
            "Repair the generator's asymmetry criterion and lesson selection so at least one visible "
            "demonstration separates rotate-clockwise from flip-up/down before a code-4 query."
        ),
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    (HERE / "replay.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "rival_fits_every_demonstration", "query_disagreement", "query_changed_cells", "elapsed_seconds")}, sort_keys=True))


if __name__ == "__main__":
    main()
