from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-288cf9ede8106d4a"
TASK_ID = "1a259ef9a7e7"
PINNED_SOURCE_SHA256 = "acb89e929db3afcc6d50513399c8b5fa9254780d16d5724c8699243690800615"
PINNED_RULE_HASH = "091b7cbaf545"
PROBE_SEED_HEX = "caa7e24aeedb5df8eff5daa69135362a47d71f4a4bb99c6e8ed4cfbb830d732c"
ROOT = find_root(__file__)
OUT = Path(__file__).with_name("witness.json")


def rule_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return row["program_solution"]
    raise KeyError(TASK_ID)


def body(program: str) -> str:
    text = program.strip()
    assert text.startswith("(rule!") and text.endswith(")")
    return text[len("(rule!") : -1].strip()


def reversed_concat_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong shortcut: append mirror instead of prepending it."""
    strips = [row + list(reversed(row)) for row in grid]
    return list(reversed(strips)) + strips + list(reversed(strips))


def main() -> None:
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha256 == PINNED_SOURCE_SHA256
    assert source_path == ROOT / "generators" / TASK_ID / "generator.py"
    seed = int(PROBE_SEED_HEX[:16], 16)
    sample_index = int(PROBE_SEED_HEX[-8:], 16) % 7919
    grid = module.generate(seed, sample_index, difficulty="medium")
    assert not module.self_check(grid)
    expected = module.rule_mirror(grid)
    rival = reversed_concat_rival(grid)
    assert expected != rival

    program = rule_source()
    normalized_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    assert normalized_hash == PINNED_RULE_HASH
    with RacketBridge(max_calls_before_restart=32) as bridge:
        bridge.define_grid("g", grid)
        racket_output = bridge.eval_text(f"({body(program)} g)")
    assert racket_output == expected

    differences = [
        {"row": row, "col": col, "canonical": expected[row][col], "rival": rival[row][col]}
        for row in range(len(expected))
        for col in range(len(expected[0]))
        if expected[row][col] != rival[row][col]
    ]
    report = {
        "schema": "adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED_HEX,
        "source_path": str(source_path.relative_to(ROOT)),
        "source_sha256": source_sha256,
        "rule_hash": normalized_hash,
        "shortcut": "Build each horizontal strip as input-row + reversed-row instead of reversed-row + input-row.",
        "why_plausible": "Both candidates double width by mirroring and use the same vertical [flip, original, flip] stack; only horizontal placement differs.",
        "input": grid,
        "self_check_findings": module.self_check(grid),
        "observed_axes": module.observe_overrides(grid),
        "canonical_output": expected,
        "racket_matches_python_oracle": racket_output == expected,
        "rival_output": rival,
        "difference_count": len(differences),
        "first_differences": differences[:12],
        "verdict": "lawful witness refutes the shortcut",
        "scope_limit": "One pinned generated scene; this is not a full shortcut census or peer approval decision.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("ticket_id", "task_id", "difference_count", "verdict")}, indent=2))


if __name__ == "__main__":
    main()
