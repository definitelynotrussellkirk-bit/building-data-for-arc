#!/usr/bin/env python3
"""Protected-Racket finite-rival audit for the native ebe910be6876 family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


SCHEMA = "ebe910be6876-largest-cluster-self-audit-v1"


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_verify_ebe910be6876_" + hashlib.sha256(
        str(path).encode() + path.read_bytes()
    ).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seeds must be exact integers in 0..2**63-1")
    return seed


def _remove_generated_directory(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        if not path.is_dir():
            raise ValueError(f"generated output path is not a directory: {path}")
        shutil.rmtree(path)


def materialize_public_batch(records: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    """Precompute, validate, sort, then physically emit all visible files.

    No challenge file is opened until every visible payload and identifier has
    been computed and duplicate-checked.  Physical creation happens in public-ID
    order inside a staging directory, which is atomically renamed afterward.
    """
    if type(records) is not list or not records:
        raise ValueError("public records must be a nonempty list")
    planned: list[tuple[str, bytes, dict[str, Any]]] = []
    seen_ids: set[str] = set()
    seen_payloads: set[bytes] = set()
    for record in records:
        if not isinstance(record, dict) or "public" not in record:
            raise ValueError("each public record must contain a visible challenge")
        payload = public_challenge_bytes(record["public"])
        identifier = public_challenge_id(record["public"])
        if hashlib.sha256(payload).hexdigest() != identifier:
            raise AssertionError("public helper ID differs from exact visible bytes")
        if identifier in seen_ids or payload in seen_payloads:
            raise ValueError(f"duplicate visible challenge in retained batch: {identifier}")
        seen_ids.add(identifier)
        seen_payloads.add(payload)
        metadata = {key: deepcopy(value) for key, value in record.items() if key != "public"}
        planned.append((identifier, payload, metadata))

    planned.sort(key=lambda item: item[0])
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    public_dir = output / "public"
    stage = output / ".public-stage"
    _remove_generated_directory(stage)
    stage.mkdir()
    write_order: list[str] = []
    try:
        for identifier, payload, _metadata in planned:
            target = stage / f"challenge-{identifier}.json"
            target.write_bytes(payload)
            write_order.append(identifier)
        _remove_generated_directory(public_dir)
        os.replace(stage, public_dir)
    except BaseException:
        _remove_generated_directory(stage)
        raise

    expected_order = [identifier for identifier, _payload, _metadata in planned]
    if write_order != expected_order:
        raise AssertionError("physical public writes were not in public-ID order")
    return {
        "schema": "ebe910be6876-visible-public-batch-v1",
        "files": [
            {
                "public_id": identifier,
                "path": f"public/challenge-{identifier}.json",
                "sha256": hashlib.sha256(payload).hexdigest(),
                **metadata,
            }
            for identifier, payload, metadata in planned
        ],
        "write_order": write_order,
        "precomputed_before_writes": True,
        "duplicate_visible_challenges": 0,
    }


def build_report(output: Path, *, seeds=(0, 17)) -> dict[str, Any]:
    """Execute both family programs and all declared rivals on visible lessons."""
    proto = _load_prototype()
    normalized_seeds = tuple(_validate_seed(seed) for seed in seeds)
    if not normalized_seeds or len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("seeds must be a nonempty distinct sequence")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)

    programs = {
        "expand_only": proto.program({"finish": "expand_only"}),
        "mark_largest_cluster": proto.program({"finish": "mark_largest_cluster"}),
        **proto.rival_programs(),
    }
    wrapped = {name: wrap_rule(source) for name, source in programs.items()}
    cache: dict[tuple[str, str], list[list[int]]] = {}
    evaluations = 0
    jobs = []
    public_records: list[dict[str, Any]] = []
    harmful = []
    python_racket_exact = True
    public_masked = True
    first_turn_prefix_stable = True

    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity

        def execute(name: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            key = name, _json_key(grid)
            if key not in cache:
                cache[key] = bridge.eval_text(
                    f"({wrapped[name]} {_literal(grid)})"
                )
                evaluations += 1
            return deepcopy(cache[key])

        for seed in normalized_seeds:
            sampled = proto.sample_inputs(seed, demos=2, queries=4)
            one = proto.generate(
                seed, {"finish": "mark_largest_cluster"}, 2, 1
            )
            many = proto.generate(
                seed, {"finish": "mark_largest_cluster"}, 2, 4
            )
            first_turn_prefix_stable &= (
                proto.public_turn(one, 0) == proto.public_turn(many, 0)
            )

            for finish in proto.FINISHES:
                settings = {"finish": finish}
                episode = proto.generate(seed, settings, 2, 4)
                pairs = episode["train"] + episode["test"]
                for pair in pairs:
                    python_racket_exact &= (
                        execute(finish, pair["input"]) == pair["output"]
                    )
                for rival in proto.RIVAL_NAMES:
                    for pair in pairs:
                        python_racket_exact &= (
                            execute(rival, pair["input"])
                            == proto.rival_solve(pair["input"], rival)
                        )

                survivors = []
                demo_mismatches = {}
                query_disagreements = {}
                for name in programs:
                    mismatch_count = sum(
                        execute(name, pair["input"]) != pair["output"]
                        for pair in episode["train"]
                    )
                    demo_mismatches[name] = mismatch_count
                    if mismatch_count == 0:
                        survivors.append(name)
                    query_disagreements[name] = sum(
                        execute(name, pair["input"]) != pair["output"]
                        for pair in episode["test"]
                    )
                    if (
                        name != finish
                        and mismatch_count == 0
                        and query_disagreements[name] > 0
                    ):
                        harmful.append(
                            {
                                "seed": seed,
                                "finish": finish,
                                "candidate": name,
                                "query_disagreements": query_disagreements[name],
                            }
                        )

                turns = [proto.public_turn(episode, index) for index in range(4)]
                for query_index, turn in enumerate(turns):
                    public_records.append(
                        {
                            "seed": seed,
                            "settings": deepcopy(settings),
                            "query_index": query_index,
                            "public": turn,
                        }
                    )
                    public_masked &= set(turn) == {"train", "test"}
                    public_masked &= len(turn["test"]) == 1
                    public_masked &= set(turn["test"][0]) == {"input"}
                    public_masked &= all(
                        set(pair) == {"input", "output"}
                        for pair in turn["train"]
                    )
                    serialized = json.dumps(turn, sort_keys=True)
                    public_masked &= "program_solution" not in serialized
                    public_masked &= "settings" not in serialized

                jobs.append(
                    {
                        "seed": seed,
                        "settings": settings,
                        "counts": {"demos": 2, "queries": 4},
                        "survivors": survivors,
                        "demo_mismatches": demo_mismatches,
                        "query_disagreements": query_disagreements,
                        "input_shapes": [
                            [len(pair["input"]), len(pair["input"][0])]
                            for pair in pairs
                        ],
                        "output_shapes": [
                            [len(pair["output"]), len(pair["output"][0])]
                            for pair in pairs
                        ],
                    }
                )
    finally:
        bridge.close()

    public_export = materialize_public_batch(public_records, output)

    report = {
        "schema": SCHEMA,
        "task_id": proto.TASK_ID,
        "seeds": list(normalized_seeds),
        "settings": [dict(row) for row in proto.SETTINGS],
        "declared_rivals": list(proto.RIVAL_NAMES),
        "jobs": jobs,
        "harmful_survivors": harmful,
        "all_python_racket_exact": bool(python_racket_exact),
        "all_public_turns_masked": bool(public_masked),
        "first_turn_prefix_stable": bool(first_turn_prefix_stable),
        "public_export": public_export,
        "racket": {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "racket_evaluations": evaluations,
        "program_sha256": {
            name: hashlib.sha256(source.encode()).hexdigest()
            for name, source in programs.items()
        },
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(HERE.iterdir())
            if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
        },
        "limits": [
            "Finite audit of four declared rivals, two demonstrations, four queries, and the listed seeds.",
            "No finite rival set proves unique human or model induction.",
        ],
    }
    if harmful:
        raise AssertionError({"harmful_survivors": harmful})
    if not python_racket_exact:
        raise AssertionError("Python and protected-Racket labels differ")
    if not public_masked or not first_turn_prefix_stable:
        raise AssertionError("public projection or prefix stability failed")
    path = output / "self-audit.json"
    path.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    args = parser.parse_args(argv)
    seeds = tuple(args.seeds) if args.seeds else (0, 17)
    report = build_report(args.out, seeds=seeds)
    print(
        json.dumps(
            {
                "schema": report["schema"],
                "jobs": len(report["jobs"]),
                "racket_evaluations": report["racket_evaluations"],
                "harmful_survivors": len(report["harmful_survivors"]),
                "protected": report["racket"].get("protected"),
                "report": str(args.out / "self-audit.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
