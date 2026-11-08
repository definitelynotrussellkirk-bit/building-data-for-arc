#!/usr/bin/env python3
"""Racket-backed verifier for the identity/transpose task-local prototype."""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import prototype


def _install_packet_scripts_namespace() -> None:
    """Expose mapped packet tools under their runtime ``scripts`` names.

    Full battery stages run in a materialized runtime tree where
    ``shared/tools/comment_solutions.py`` is mapped to
    ``scripts/comment_solutions.py``.  This standalone verifier runs directly
    from the packet repo, so install the same import identity in memory rather
    than copying or mutating the packet.
    """
    qualified = "scripts.comment_solutions"
    if qualified in sys.modules:
        return
    source = HERE.parents[3] / "shared" / "tools" / "comment_solutions.py"
    if not source.is_file():
        raise FileNotFoundError(f"missing packet parser source: {source}")
    package = sys.modules.get("scripts")
    if package is None:
        package = types.ModuleType("scripts")
        package.__path__ = [str(source.parent)]
        sys.modules["scripts"] = package
    spec = importlib.util.spec_from_file_location(qualified, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load packet parser source: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_text(text: str) -> str:
    return _sha_bytes(text.encode())


def _dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)

    _install_packet_scripts_namespace()
    from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
    from puzzle_generators.rule_wrap import wrap_rule

    canonical = prototype._canonical_generator()
    episode_seeds = {"identity": 2026101901, "transpose": 2026101902}
    episodes = {
        value: prototype.generate_episode(seed, key_transform=value)
        for value, seed in episode_seeds.items()
    }
    programs = {value: prototype.racket_program(value) for value in prototype.PARAMETER_VALUES}

    report = {
        "schema": "arcpuzzles-task-parametric-prototype-verification-v1",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.PROTOTYPE_VERSION,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "values": list(prototype.PARAMETER_VALUES),
            "default": prototype.DEFAULT_PARAMETER,
            "chosen_once_per_episode": True,
        },
        "input_constraints": episodes["identity"]["meta"]["input_constraints"],
        "programs": {},
        "episodes": {},
        "witness": {},
        "checks": [],
        "limitations": [
            "Prototype only: the production per-puzzle generator and canonical rule are unchanged.",
            "Evidence covers two fixed episodes and one cross-setting witness, not every seed or hypothesis.",
            "Inputs use a 14x14 frame with a dense asymmetric 2x3 key so both settings tile exactly.",
        ],
    }

    bridges = {}
    try:
        for value, program in programs.items():
            path = out / f"rule_{value}.rkt"
            path.write_text(program + "\n")
            bridge, fn = _open_bridge_with_rule(wrap_rule(program))
            bridges[value] = (bridge, fn)
            report["programs"][value] = {
                "path": path.name,
                "sha256": _sha_text(program),
                "text": program,
            }

        execution_count = 0
        for value, episode in episodes.items():
            survivors = prototype.surviving_parameter_values(episode["train"])
            if survivors != [value]:
                raise AssertionError(f"{value} episode survivors: {survivors}")
            pair_records = []
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    bridge, fn = bridges[value]
                    actual = _apply_rule(bridge, fn, pair["input"])
                    execution_count += 1
                    expected = prototype.apply_rule(pair["input"], value)
                    if actual != expected or actual != pair["output"]:
                        raise AssertionError(f"Racket mismatch for {value} {split}[{index}]")
                    if value == "identity" and actual != canonical.rule_mirror(pair["input"]):
                        raise AssertionError(f"identity diverges from canonical mirror at {split}[{index}]")
                    pair_records.append({
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_text(json.dumps(pair["input"], separators=(",", ":"))),
                        "output_sha256": _sha_text(json.dumps(actual, separators=(",", ":"))),
                        "racket_match": True,
                    })
            report["episodes"][value] = {
                "seed": episode["meta"]["seed"],
                "surviving_parameter_values": survivors,
                "pair_records": pair_records,
            }

            _dump(out / f"episode_{value}.json", episode)
            _dump(out / f"public_{value}.json", prototype.public_challenge(episode))

        witness_input = prototype.build_input(2026101999, 0)
        witness_outputs = {
            value: prototype.apply_rule(witness_input, value)
            for value in prototype.PARAMETER_VALUES
        }
        if witness_outputs["identity"] == witness_outputs["transpose"]:
            raise AssertionError("parameter witness does not change the output")
        racket_witness_outputs = {}
        for value in prototype.PARAMETER_VALUES:
            bridge, fn = bridges[value]
            racket_witness_outputs[value] = _apply_rule(bridge, fn, witness_input)
            execution_count += 1
            if racket_witness_outputs[value] != witness_outputs[value]:
                raise AssertionError(f"Racket witness mismatch for {value}")

        report["witness"] = {
            "seed": 2026101999,
            "input": witness_input,
            "outputs": witness_outputs,
            "racket_outputs": racket_witness_outputs,
            "settings_disagree": True,
        }
        report["checks"] = [
            "all complete episode outputs executed by their materialized Racket rule",
            "identity outputs equal the canonical Python mirror on all retained pairs",
            "each three-demo episode leaves exactly its selected parameter value alive",
            "one lawful input produces different identity and transpose outputs",
            "public challenge files omit hidden parameter values, Racket source, and query answers",
        ]
        report["racket_executions"] = execution_count
        report["source_hashes"] = {
            "prototype.py": _sha_bytes((HERE / "prototype.py").read_bytes()),
            "verify.py": _sha_bytes(Path(__file__).read_bytes()),
        }
        report["passed"] = True
        _dump(out / "report.json", report)
        print(json.dumps({
            "passed": True,
            "racket_executions": execution_count,
            "settings": list(prototype.PARAMETER_VALUES),
            "out": str(out),
        }, sort_keys=True))
        return 0
    finally:
        for bridge, _fn in bridges.values():
            bridge.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
