#!/usr/bin/env python3
"""Source-bound reproducer for eed263bf30fc's override contract."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "eed263bf30fc"


def call(gen, *, difficulty, overrides):
    try:
        grid = gen.generate(314159, 0, difficulty=difficulty, **overrides)
    except Exception as exc:  # evidence records the public failure mode
        return {"accepted": False, "exception": f"{type(exc).__name__}: {exc}"}
    return {
        "accepted": True,
        "shape": [len(grid), len(grid[0])],
        "realized_panel_n": (len(grid) - 1) // 2,
        "self_check": gen.self_check(grid, difficulty=difficulty),
    }


def main() -> None:
    root = Path.cwd().resolve()
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    report = {
        "task_id": TASK_ID,
        "source": str(source.relative_to(root)),
        "generator_sha256": source_sha256,
        "declared_panel_n_valid": gen.AXES["panel_n"]["valid"],
        "cases": {
            "easy_panel_n_8": call(gen, difficulty="easy", overrides={"panel_n": 8}),
            "medium_panel_n_8": call(gen, difficulty="medium", overrides={"panel_n": 8}),
            "hard_panel_n_8": call(gen, difficulty="hard", overrides={"panel_n": 8}),
            "unknown_axis": call(gen, difficulty="medium", overrides={"__override_contract_unknown_axis__": 7}),
        },
        "finding": (
            "panel_n=8 is declared valid but is ignored in easy, rejected in medium, "
            "and accepted only in hard; an unknown override key is silently accepted."
        ),
    }
    out = Path("../checks/audit/eed263bf30fc/override_contract.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
