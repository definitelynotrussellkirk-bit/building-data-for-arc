from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "dfc4967f816f"
PINNED_SOURCE_SHA256 = "c3e1e264f25bd4839eec5d91889b22330b83b745bc7cf027246171abf817f452"
PROBE_SEED = "d9ca261de33d092625806d0132f4aac7a26327351e8bdbe6b7f656c38d9a20c5"


def execute(bridge, program, grid):
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("unexpected canonical wrapper")
    bridge.define_grid("g", grid)
    body = program[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    return bridge.eval_text(expression)


def main():
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != PINNED_SOURCE_SHA256:
        raise SystemExit("pinned generator source identity does not match")
    digest = bytes.fromhex(PROBE_SEED)
    seed = int.from_bytes(digest[:8], "big") % (2**31)
    sample_index = int.from_bytes(digest[8:16], "big") % 100_000
    foreground_color = 1 + digest[16] % 8
    grid = generator.generate(
        seed,
        sample_index,
        difficulty="medium",
        tile_cols=4,
        foreground_color=foreground_color,
    )
    canonical_programs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    canonical_programs.append(row["program_solution"])
    if not canonical_programs or len(set(canonical_programs)) != 1:
        raise SystemExit("canonical authority is not unique")
    program = canonical_programs[0]
    with RacketBridge(max_calls_before_restart=16) as bridge:
        racket_output = execute(bridge, program, grid)
    canonical_output = generator.rule_mirror(grid)
    rival_output = generator.SEMANTIC_RIVALS["top_row_only"](grid)
    report = {
        "schema": "arcpuzzles-supplementary-adversarial-witness-v1",
        "ticket_id": "ticket-4842252759ec5b4c",
        "task_id": TASK_ID,
        "status": "completed",
        "probe_seed": PROBE_SEED,
        "source": {
            "path": str(source_path),
            "sha256": source_sha256,
            "rule_hash": generator.RULE_HASH,
            "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
        "recipe": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": "medium",
            "overrides": {"tile_cols": 4, "foreground_color": foreground_color},
        },
        "shortcut": {
            "name": "top_row_only",
            "description": "classify each tile from horizontal symmetry of only its first row",
        },
        "input": grid,
        "self_check": generator.self_check(grid),
        "python_rule_mirror": canonical_output,
        "racket_output": racket_output,
        "shortcut_output": rival_output,
        "checks": {
            "lawful": generator.self_check(grid) == [],
            "racket_python_parity": racket_output == canonical_output,
            "shortcut_refuted": rival_output != canonical_output,
            "declared_witness_fires": generator.SEMANTIC_WITNESSES["deep_row_asymmetry"](grid),
        },
    }
    report["checks"]["all_passed"] = all(report["checks"].values())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["checks"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
