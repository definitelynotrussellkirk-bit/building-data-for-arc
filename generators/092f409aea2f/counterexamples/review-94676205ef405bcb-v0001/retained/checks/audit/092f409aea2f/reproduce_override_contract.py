"""Reduce the 092f409aea2f override-domain failure to a few direct calls."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "092f409aea2f"
HERE = Path(__file__).resolve().parent


def try_generate(module, *, difficulty, overrides):
    call = {
        "seed": 0,
        "sample_index": 3,
        "difficulty": difficulty,
        "overrides": overrides,
    }
    try:
        grid = module.generate(0, 3, difficulty=difficulty, **overrides)
    except Exception as exc:  # Evidence records the public call boundary exactly.
        return {"call": call, "accepted": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {
        "call": call,
        "accepted": True,
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "self_check": module.self_check(grid, difficulty=difficulty),
    }


def main() -> None:
    root = find_root(Path.cwd())
    module, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    cases = [
        try_generate(module, difficulty="easy", overrides={"grid_h": 4}),
        try_generate(module, difficulty="easy", overrides={"grid_h": 18}),
        try_generate(module, difficulty="easy", overrides={"grid_w": 4}),
        try_generate(module, difficulty="easy", overrides={"grid_w": 18}),
        try_generate(module, difficulty="easy", overrides={"n_bridges": 1}),
        try_generate(module, difficulty="easy", overrides={"n_bridges": 8}),
        try_generate(module, difficulty="easy", overrides={"__override_contract_unknown_axis__": 123}),
    ]
    declared_cases = cases[:-1]
    assert any(not case["accepted"] for case in declared_cases)
    assert cases[-1]["accepted"], "unknown-key acceptance should reproduce"

    evidence = {
        "schema": "generator-override-contract-reproduction-v1",
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": getattr(module, "RULE_HASH", None),
        "declared_axes": module.AXES,
        "cases": cases,
        "documented_domain": "values are endpoints of the generator's own AXES valid ranges",
        "failure": (
            "Declared exact-control values are rejected inside difficulty-specific draw ranges, "
            "while an unrecognized override key is silently accepted."
        ),
        "full_battery": {
            "path": "checks/audit/092f409aea2f/override/checks/092f409aea2f_audit_override_results.json",
            "finding_count": 7085,
            "draws_total": 70110,
        },
        "command": [
            "python3", "review.py", "run", "python3",
            "../checks/audit/092f409aea2f/reproduce_override_contract.py",
        ],
        "cwd": "packet_root",
    }
    out = HERE / "override-contract-current.json"
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "REPRODUCED",
        "generator_sha256": source_sha256,
        "declared_rejections": sum(not case["accepted"] for case in declared_cases),
        "unknown_key_accepted": cases[-1]["accepted"],
        "evidence": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
