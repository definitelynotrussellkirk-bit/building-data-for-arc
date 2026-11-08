"""One bounded adversarial witness for ticket-b9b6caf3ff828e0e."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from reviewer_support import normalize_grid  # noqa: E402
from puzzle_generators.rule_wrap import strip_rule_wrapper  # noqa: E402

TASK_ID = "3108da8bf9e8"
EXPECTED_GENERATOR_SHA256 = "4c5d75752ec9c0899595a62b17076b1ed5e5240b3069e2d55b413477469730d3"
EXPECTED_RULE_HASH = "05977542b8d5"
TICKET_SEED = "640533f08ab0abb1dd248abff837a0531ec3446b9d5140b9f7ae22e1e379b020"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def load_generator():
    digest = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    if digest != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(f"generator identity mismatch: {digest}")
    spec = importlib.util.spec_from_file_location("ticket_3108da8bf9e8", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def canonical_program() -> str:
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            code = row["program_solution"]
            normalized = " ".join(code.split())
            digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
            if digest != EXPECTED_RULE_HASH:
                raise RuntimeError(f"rule identity mismatch: {digest}")
            return code
    raise RuntimeError("canonical task row not found")


def execute(program: str, grid, bridge: RacketBridge):
    function = strip_rule_wrapper(program)
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def original_row_groups_shortcut(gen, grid):
    """Wrong rule: keep original macro-row membership, rank whole rows by sum."""
    blocks = gen._extract_blocks(grid)
    groups = []
    for start in (0, 3, 6):
        group = sorted(blocks[start : start + 3], key=gen._block_count)
        groups.append(group)
    groups.sort(key=lambda group: sum(gen._block_count(block) for block in group), reverse=True)
    flattened = [block for group in groups for block in group]
    return gen._place_blocks(flattened, gen.ROW_MAJOR_BLOCKS)


def counts(gen, grid):
    return gen._block_one_counts(grid)


def main() -> int:
    gen, generator_sha = load_generator()
    program = canonical_program()
    seed = int(TICKET_SEED[:16], 16)
    base_index = int(TICKET_SEED[16:24], 16) % 10_000
    witness = None
    for offset in range(32):
        sample_index = base_index + offset
        grid = gen.generate(seed, sample_index, difficulty="hard")
        if gen.self_check(grid) != []:
            raise RuntimeError("generated input failed self_check")
        official_mirror = gen.rule_mirror(copy.deepcopy(grid))
        shortcut = original_row_groups_shortcut(gen, copy.deepcopy(grid))
        if shortcut != official_mirror:
            witness = (sample_index, grid, official_mirror, shortcut)
            break
    if witness is None:
        raise RuntimeError("bounded 32-index search found no distinguishing witness")

    sample_index, grid, official_mirror, shortcut = witness
    with RacketBridge() as bridge:
        official_racket = execute(program, grid, bridge)
    if official_racket != official_mirror:
        raise RuntimeError("Python mirror disagrees with canonical Racket")

    mismatch = [
        [r, c]
        for r in range(11)
        for c in range(11)
        if official_racket[r][c] != shortcut[r][c]
    ]
    result = {
        "schema": "supplementary-adversarial-witness-v1",
        "ticket_id": "ticket-b9b6caf3ff828e0e",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "normalized_rule_hash": EXPECTED_RULE_HASH,
        "probe": {"seed": seed, "sample_index": sample_index, "difficulty": "hard"},
        "shortcut": {
            "name": "sort_within_original_macro_rows_then_rank_rows_by_total_one_count",
            "description": (
                "Preserve each original macro-row as a group, sort its three blocks by one-count, "
                "then place whole groups top-to-bottom by total one-count."
            ),
        },
        "lawful_input": gen.self_check(grid) == [],
        "python_mirror_matches_racket": official_mirror == official_racket,
        "input_count_order": counts(gen, grid),
        "official_count_order": counts(gen, official_racket),
        "shortcut_count_order": counts(gen, shortcut),
        "mismatch_cell_count": len(mismatch),
        "mismatch_cells": mismatch,
        "input": grid,
        "authoritative_output": official_racket,
        "shortcut_output": shortcut,
        "bounded_result": "shortcut_refuted_by_one_lawful_witness",
        "scope": "One generated hard-band witness selected within 32 deterministic indices; not a census.",
    }
    out = HERE.with_name("witness.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "ticket_id", "task_id", "probe", "lawful_input", "python_mirror_matches_racket",
        "input_count_order", "official_count_order", "shortcut_count_order",
        "mismatch_cell_count", "bounded_result", "scope")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
