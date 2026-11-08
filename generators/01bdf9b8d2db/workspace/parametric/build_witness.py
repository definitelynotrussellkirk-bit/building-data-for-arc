"""Build the source-bound protected-Racket sequential dependency witness."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
SETTINGS = {"finish": "mark_smallest_total"}
STEP_A = "Flood every 4-connected non-wall chamber with the color of its unique seed."
INTERMEDIATE = "The input-dependent histogram of flooded cell totals for each seed color."
STEP_B = "Select the least-total color (lowest color on a tie) and recolor all of its flooded cells to 9."
WHY = (
    "The input contains one seed per chamber, so seed frequency does not reveal chamber area; "
    "changing the flooded-area histogram can change which color Step B selects."
)


def _load_local(name, path):
    module_name = f"_01bdf9_witness_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


P = _load_local("prototype", HERE / "prototype.py")


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _program_key(settings):
    return json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _seed_counts(grid):
    colors = sorted({value for row in grid for value in row} - {0, 5})
    counts = {
        color: sum(value == color for row in grid for value in row)
        for color in colors
    }
    selected = min(colors, key=lambda color: (counts[color], color))
    return counts, selected


def build(qualification_path, output_path, seed=0, demonstration_index=0):
    qualification_path = Path(qualification_path)
    output_path = Path(output_path)
    qualification = json.loads(qualification_path.read_bytes())
    if qualification.get("schema") != "arcpuzzles-parametric-qualification-v1":
        raise ValueError("expected a native parametric qualification receipt")
    if qualification.get("status") != "qualified":
        raise ValueError("qualification must have status qualified")
    expected_hash = qualification.get("programs", {}).get(_program_key(SETTINGS))
    intended_program = P.program(SETTINGS)
    if hashlib.sha256(intended_program.encode()).hexdigest() != expected_hash:
        raise ValueError("qualified alternative program differs from current source")
    pair = P.generate(seed, SETTINGS, 2, 4)["train"][demonstration_index]
    counterfactual_program = P.counterfactual_program("seed_frequency")

    runtime = ROOT / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    saved = {
        key: value
        for key, value in sys.modules.items()
        if key.split(".")[0] in {"arc_repl", "puzzle_generators"}
    }
    for key in saved:
        del sys.modules[key]
    bridge = None
    try:
        bridge_module = importlib.import_module("arc_repl.racket_bridge")
        wrap_module = importlib.import_module("puzzle_generators.rule_wrap")
        bridge = bridge_module.RacketBridge()
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("witness requires protected Racket")
        literal = _literal(pair["input"])
        output = bridge.eval_text(
            f"({wrap_module.wrap_rule(intended_program)} {literal})"
        )
        counterfactual_output = bridge.eval_text(
            f"({wrap_module.wrap_rule(counterfactual_program)} {literal})"
        )
    finally:
        if bridge is not None:
            bridge.close()
        for key in list(sys.modules):
            if key.split(".")[0] in {"arc_repl", "puzzle_generators"}:
                del sys.modules[key]
        sys.modules.update(saved)
        sys.path.remove(str(runtime))

    if output != pair["output"]:
        raise ValueError("protected intended output differs from generated label")
    if counterfactual_output == output:
        raise ValueError("counterfactual did not change the final output")
    info = P.O.intermediate(pair["input"])
    seed_counts, wrong_selected = _seed_counts(pair["input"])
    differences = [
        [row, col]
        for row in range(len(output))
        for col in range(len(output[0]))
        if output[row][col] != counterfactual_output[row][col]
    ]
    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "runtime_identity": {
            key: identity[key]
            for key in (
                "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY,
        "cases": [{
            "ablation": "wrong_intermediate",
            "settings": deepcopy(SETTINGS),
            "input": pair["input"],
            "intermediate_value": {
                "filled_color_totals": info["filled_color_totals"],
                "correct_selected_color": info["selected_color"],
                "wrong_seed_counts": seed_counts,
                "wrong_selected_color": wrong_selected,
            },
            "output": output,
            "counterfactual_output": counterfactual_output,
            "program": intended_program,
            "counterfactual_program": counterfactual_program,
            "counterfactual_description": (
                "Count one-cell input seeds by color instead of the areas produced by the "
                "canonical flood, then apply the same recoloring step."
            ),
            "difference_cells": len(differences),
            "difference_coordinates": differences,
        }],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(witness, sort_keys=True, indent=2) + "\n")
    return witness


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demonstration-index", type=int, default=0)
    args = parser.parse_args(argv)
    witness = build(
        args.qualification, args.out, args.seed, args.demonstration_index
    )
    print(json.dumps({
        "status": "reviewer_replayed",
        "cases": len(witness["cases"]),
        "difference_cells": witness["cases"][0]["difference_cells"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
