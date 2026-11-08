#!/usr/bin/env python3
"""Bounded adversarial pass for the legend-selected sort prototype.

Surfaces: (1) parameter/Python/Racket parity across diverse seeds and (2)
public/private export separation, exact numeric types, and copy isolation.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / "89ab40aedfe4" / "workspace" / "parametric"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


prototype = load_module("adversarial_prototype_89ab40aedfe4", PARAMETRIC / "prototype.py")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode("utf-8"))


def racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("program is not one rule! form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("program body is not a lambda")
    return expression


def grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def application(source: str, grid: list[list[int]]) -> str:
    return f"({racket_callable(source)} {grid_literal(grid)})"


def all_exact_int_colors(value: Any) -> bool:
    if isinstance(value, dict):
        return all(all_exact_int_colors(item) for item in value.values())
    if isinstance(value, list):
        return all(all_exact_int_colors(item) for item in value)
    return type(value) is int and 0 <= value <= 9


def grid_values_exact(value: dict[str, Any]) -> bool:
    for pair in value["train"]:
        if not all_exact_int_colors(pair["input"]) or not all_exact_int_colors(pair["output"]):
            return False
    return all(all_exact_int_colors(pair["input"]) for pair in value["test"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "adversarial.json"))
    args = parser.parse_args()
    started = time.monotonic()

    seeds = [-1, 0, 1, 20261023, 2**31 - 1]
    programs = {mode: prototype.program_for(mode, root=ROOT) for mode in prototype.SELECTION_MODES}
    parity_rows: list[dict[str, Any]] = []
    export_rows: list[dict[str, Any]] = []
    retained_edge: dict[str, Any] | None = None

    bridge = RacketBridge(timeout=30, max_calls_before_restart=96)
    try:
        runtime_identity = bridge.runtime_identity
        for seed in seeds:
            episodes = {
                mode: prototype.build_episode(
                    seed,
                    selection_mode=mode,
                    demonstration_count=3,
                    query_count=4,
                    root=ROOT,
                )
                for mode in prototype.SELECTION_MODES
            }
            all_inputs = [pair["input"] for pair in episodes["all_slots"]["train"] + episodes["all_slots"]["test"]]
            other_inputs = [pair["input"] for pair in episodes["contains_key"]["train"] + episodes["contains_key"]["test"]]
            if all_inputs != other_inputs:
                raise SystemExit(f"settings changed sampler inputs at seed {seed}")

            for pair_index, grid in enumerate(all_inputs):
                outputs: dict[str, list[list[int]]] = {}
                for mode, source in programs.items():
                    python_output = prototype.apply_python(grid, mode)
                    racket_output = bridge.eval_text(application(source, grid))
                    if racket_output != python_output:
                        raise SystemExit(f"Racket/Python mismatch seed={seed} pair={pair_index} mode={mode}")
                    selected_episode = episodes[mode]
                    selected_pairs = selected_episode["train"] + selected_episode["test"]
                    if selected_pairs[pair_index]["output"] != racket_output:
                        raise SystemExit(f"episode label mismatch seed={seed} pair={pair_index} mode={mode}")
                    outputs[mode] = racket_output
                if outputs["all_slots"] == outputs["contains_key"]:
                    raise SystemExit(f"settings failed to disagree seed={seed} pair={pair_index}")
                parity_rows.append(
                    {
                        "seed": seed,
                        "pair_index": pair_index,
                        "input_sha256": grid_sha256(grid),
                        "output_sha256": {mode: grid_sha256(output) for mode, output in outputs.items()},
                    }
                )
                if retained_edge is None:
                    retained_edge = {
                        "seed": seed,
                        "pair_index": pair_index,
                        "input": grid,
                        "all_slots_output": outputs["all_slots"],
                        "contains_key_output": outputs["contains_key"],
                        "purpose": (
                            "The key names two required body rows; two candidates miss one required row and remain fixed, "
                            "while two equal-population selected candidates retain source order."
                        ),
                    }

            for mode, episode in episodes.items():
                public = prototype.public_challenge(episode)
                public_bytes = public_challenge_bytes(public)
                public_id = public_challenge_id(public)
                query_payloads = {
                    json.dumps(pair["input"], separators=(",", ":")) for pair in public["test"]
                }
                serialized = public_bytes.decode("utf-8")
                private_mutation = deepcopy(episode)
                private_mutation["seed"] = seed + 999999
                private_mutation["parameter"] = {"selection_mode": "hidden-mutated"}
                private_mutation["program"] = "hidden-mutated"
                private_mutation["status"] = "hidden-mutated"
                metadata_invariant = public_challenge_bytes(prototype.public_challenge(private_mutation)) == public_bytes
                query_label_mutation = deepcopy(episode)
                for pair in query_label_mutation["test"]:
                    pair["output"] = [[9]]
                query_labels_invariant = (
                    public_challenge_bytes(prototype.public_challenge(query_label_mutation)) == public_bytes
                    and public_challenge_id(prototype.public_challenge(query_label_mutation)) == public_id
                )

                clone = prototype.public_challenge(episode)
                before = episode["train"][0]["input"][0][0]
                clone["train"][0]["input"][0][0] = 0 if before else 1
                copy_isolated = episode["train"][0]["input"][0][0] == before

                bool_rejected = False
                bad = deepcopy(public)
                bad["test"][0]["input"][0][0] = True
                try:
                    public_challenge_bytes(bad)
                except ValueError:
                    bool_rejected = True

                checks = {
                    "hidden_fields_absent": all(token not in serialized for token in ("selection_mode", "program", "seed", "status")),
                    "test_outputs_absent": all(set(pair) == {"input"} for pair in public["test"]),
                    "train_labels_present": all(set(pair) == {"input", "output"} for pair in public["train"]),
                    "query_inputs_distinct": len(query_payloads) == 4,
                    "exact_integer_colors": grid_values_exact(public),
                    "private_metadata_does_not_change_public_bytes": metadata_invariant,
                    "private_query_answers_do_not_change_public_bytes_or_id": query_labels_invariant,
                    "public_projection_is_deep_copy": copy_isolated,
                    "bool_color_rejected": bool_rejected,
                }
                if not all(checks.values()):
                    raise SystemExit(f"export check failed seed={seed} mode={mode}: {checks}")
                export_rows.append({"seed": seed, "mode": mode, "public_id": public_id, "checks": checks})
    finally:
        bridge.shutdown()

    result = {
        "schema": "89ab40aedfe4-legend-selector-adversarial-v1",
        "status": "passed",
        "surfaces": [
            "parameter/Python/Racket parity across diverse signed and large seeds",
            "public/private export separation, exact numeric types, and copy isolation",
        ],
        "seeds": seeds,
        "counts": {
            "seeds": len(seeds),
            "unique_inputs": len(seeds) * 7,
            "racket_executions": len(parity_rows) * len(programs),
            "parity_rows": len(parity_rows),
            "export_cases": len(export_rows),
        },
        "program_sha256": {mode: sha256_bytes(source.encode("utf-8")) for mode, source in programs.items()},
        "runtime_identity": runtime_identity,
        "retained_edge_case": retained_edge,
        "parity": parity_rows,
        "exports": export_rows,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "limitations": [
            "The pass covers five deterministic seeds and the prototype sampler's fixed 12x17 six-slot domain, not all structurally valid grids.",
            "The export attack checks in-memory projection and canonical public bytes; it does not exercise network publication or catalog admission.",
            "No production generator, approval state, or canonical authority was changed by this prototype-only pass.",
        ],
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
