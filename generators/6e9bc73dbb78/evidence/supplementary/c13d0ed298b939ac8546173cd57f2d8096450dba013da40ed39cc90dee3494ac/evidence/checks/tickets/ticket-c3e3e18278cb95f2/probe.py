#!/usr/bin/env python3
"""One bounded lawful witness against the `fewest_cells` shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "6e9bc73dbb78"
TICKET_ID = "ticket-c3e3e18278cb95f2"
EXPECTED_SOURCE_SHA256 = "f197aeb193e415e700f86fc2fadca9d1f9561de22d85d937d27dbced052099fe"
EXPECTED_RULE_HASH = "9098234c66fa"
PROBE_SEED_HEX = "556707b493dab29e4bba0365c3278ee4e27dc1db76f5eb3f4609868729918960"


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _canonical_program(root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise RuntimeError(f"canonical program not found for {TASK_ID}")


def main() -> None:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha256}")
    if generator.RULE_HASH != EXPECTED_RULE_HASH:
        raise RuntimeError(f"rule hash drift: {generator.RULE_HASH}")

    seed = int(PROBE_SEED_HEX[:8], 16)
    overrides = {
        "grid_h": 10,
        "grid_w": 12,
        "n_repeat": 3,
        "size_profile": "target_larger_total",
        "color_order": "target_lower",
        "position_order": "target_last",
    }
    grid = generator.generate(seed, 5, difficulty="hard", **overrides)
    errors = generator.self_check(grid)
    facts = generator._scene_facts(grid)
    canonical_python = generator.rule_mirror(grid)
    shortcut = generator.SEMANTIC_RIVALS["fewest_cells"](grid)

    program = _canonical_program(root)
    application = f"({wrap_rule(program)} {_grid_literal(grid)})"
    with RacketBridge(timeout=30.0) as bridge:
        canonical_racket = bridge.eval_text(application)

    result = {
        "schema": "arcpuzzles-bounded-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "probe_seed": PROBE_SEED_HEX,
        "targeted_probe_count": 1,
        "shortcut": "fewest_cells",
        "overrides": overrides,
        "input": grid,
        "canonical_output": canonical_racket,
        "shortcut_output": shortcut,
        "facts": {
            "target_color": facts["target_color"],
            "repeat_color": facts["repeat_color"],
            "target_area": facts["target_area"],
            "repeat_total_area": facts["repeat_total_area"],
            "target_component_count": facts["counts"][facts["target_color"]],
            "repeat_component_count": facts["counts"][facts["repeat_color"]],
            "observed_overrides": generator.observe_overrides(grid),
        },
        "checks": {
            "self_check_pass": errors == [],
            "python_mirror_matches_racket": canonical_python == canonical_racket,
            "canonical_differs_from_shortcut": canonical_racket != shortcut,
            "shortcut_selected_repeat_color": all(
                (out == 4) == (cell == facts["repeat_color"])
                for in_row, out_row in zip(grid, shortcut)
                for cell, out in zip(in_row, out_row)
            ),
            "canonical_selected_unique_component_color": all(
                (out == 4) == (cell == facts["target_color"])
                for in_row, out_row in zip(grid, canonical_racket)
                for cell, out in zip(in_row, out_row)
            ),
        },
        "input_sha256": hashlib.sha256(
            json.dumps(grid, separators=(",", ":")).encode()
        ).hexdigest(),
        "outcome": (
            "lawful witness retained: the target has more total cells, so the "
            "fewest-cells shortcut recolors the repeated color while the Racket "
            "authority recolors the sole one-component color"
        ),
    }
    if not all(result["checks"].values()):
        raise AssertionError(json.dumps(result["checks"], sort_keys=True))
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "result": str(out), "checks": result["checks"]}, sort_keys=True))


if __name__ == "__main__":
    main()
