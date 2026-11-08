"""Scoped adversarial, causal and public-projection audit for 269e22fb."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _root() -> Path:
    return next(parent for parent in HERE.parents if (parent / "src/arcpuzzles/parametric_worker.py").is_file())


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def run(out: Path, seeds: int = 32):
    if type(seeds) is not int or not 1 <= seeds <= 256:
        raise ValueError("seeds must be in 1..256")
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir(); (out / "private").mkdir()
    root = _root(); sys.path[:0] = [str(root / "src"), str(root / "shared/runtime")]
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes

    adapter = _load(HERE / "adapter.py", "_crop_audit_adapter")
    rivals = _load(HERE / "rivals.py", "_crop_audit_rivals")
    values = adapter.PARAMETERS["pocket_policy"]
    report = {
        "schema": "269e22fb-adversarial-audit-v1",
        "status": "passed",
        "seed_count": seeds,
        "episodes": 0,
        "pair_instances": 0,
        "matched_input_checks": 0,
        "prefix_checks": 0,
        "public_turn_checks": 0,
        "distinct_inputs": 0,
        "python_rival_checks": 0,
        "racket_evaluations": 0,
        "teaching": [],
        "limits": "Finite authored rival bank and bounded seeds; no universal uniqueness, owner acceptance, or training admission.",
    }
    distinct = set()
    for seed in range(seeds):
        full = {value: adapter.generate(seed, {"pocket_policy": value}, 6, 4) for value in values}
        left = [pair["input"] for split in ("train", "test") for pair in full[values[0]][split]]
        right = [pair["input"] for split in ("train", "test") for pair in full[values[1]][split]]
        assert left == right
        report["matched_input_checks"] += 1
        distinct.update(_sha(json.dumps(grid, separators=(",", ":")).encode()) for grid in left)
        for demos in range(2, 7):
            for queries in range(1, 5):
                for value in values:
                    episode = adapter.generate(seed, {"pocket_policy": value}, demos, queries)
                    assert episode["train"] == full[value]["train"][:demos]
                    assert episode["test"] == full[value]["test"][:queries]
                    report["episodes"] += 1; report["pair_instances"] += demos + queries; report["prefix_checks"] += 1
                    for index in range(queries):
                        turn = adapter.public_turn(episode, index)
                        assert set(turn) == {"train", "test"}
                        assert turn["test"] == [{"input": episode["test"][index]["input"]}]
                        poisoned = deepcopy(episode)
                        poisoned["private"] = {"canary": "PRIVATE"}; poisoned["program_solution"] = "PRIVATE"
                        for j in range(len(poisoned["test"])):
                            poisoned["test"][j]["output"] = [[9]]
                        assert adapter.public_turn(poisoned, index) == turn
                        report["public_turn_checks"] += 1
        for value in values:
            episode = full[value]
            expected = [pair["output"] for pair in episode["train"][:2]]
            survivors = []
            for name in rivals.python_names():
                labels = [rivals.predict(pair["input"], name) for pair in episode["train"][:2]]
                report["python_rival_checks"] += 2
                if labels == expected:
                    survivors.append(name)
            assert survivors == [value], (seed, value, survivors)
            report["teaching"].append({"seed": seed, "settings": {"pocket_policy": value}, "survivors": survivors})
    report["distinct_inputs"] = len(distinct)

    programs = rivals.racket_programs()
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    executions = []
    try:
        for seed in (17, 43):
            episode = adapter.generate(seed, {"pocket_policy": "mark_enclosed"}, 2, 4)
            for name, program in programs.items():
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = apply(program, pair["input"])
                        expected = rivals.predict(pair["input"], name)
                        assert actual == expected, (seed, name, split, index)
                        report["racket_evaluations"] += 1
                        executions.append({
                            "seed": seed, "name": name, "split": split, "index": index,
                            "program_sha256": _sha(program.encode()),
                            "input_sha256": _sha(json.dumps(pair["input"], separators=(",", ":")).encode()),
                            "output_sha256": _sha(json.dumps(actual, separators=(",", ":")).encode()),
                        })
    finally:
        bridge.close()
    report["racket"] = identity

    payloads = {}; private = []
    for seed in (17, 43, 71, 97):
        for value in values:
            episode = adapter.generate(seed, {"pocket_policy": value}, 2, 4)
            for index in range(4):
                raw = public_challenge_bytes(adapter.public_turn(episode, index))
                key = _sha(raw)
                assert key not in payloads
                payloads[key] = raw
                private.append({
                    "id": key, "seed": seed, "settings": {"pocket_policy": value},
                    "source_query": episode["private"]["query_permutation"][index],
                    "answer_sha256": _sha(json.dumps(episode["test"][index]["output"], separators=(",", ":")).encode()),
                })
    for key, raw in sorted(payloads.items()):
        (out / "public" / f"{key}.json").write_bytes(raw)
    _dump(out / "private/queries.json", private)
    _dump(out / "private/racket-executions.json", executions)
    report["public_files"] = len(payloads)

    # Source-bound causal counterfactual: corrupt step A to the base pose, then
    # run the same step B pocket marker. Pick a reflected query so outputs differ.
    episode = adapter.generate(17, {"pocket_policy": "mark_enclosed"}, 2, 4)
    index = next(i for i, cert in enumerate(episode["private"]["certificates"][2:]) if cert["pose"] != 0)
    pair = episode["test"][index]
    correct_program = programs["mark_enclosed"]
    wrong_program = programs["wrong_base_mark"]
    apply, identity2, bridge = _real_evaluator(root / "shared/runtime")
    try:
        correct = apply(correct_program, pair["input"])
        wrong = apply(wrong_program, pair["input"])
    finally:
        bridge.close()
    assert correct == pair["output"] and wrong != correct
    diff = sum(a != b for ar, br in zip(correct, wrong) for a, b in zip(ar, br))
    causal = {
        "schema": "269e22fb-sequential-witness-v1",
        "status": "passed",
        "seed": 17,
        "query_index": index,
        "step_a": "infer the unique crop pose and render the full 20 by 20 completion",
        "intermediate": "the completed two-color canvas",
        "step_b": "mark background pockets unreachable from the completed boundary",
        "wrong_intermediate": "force the untransformed base emblem before the same pocket pass",
        "different_cells": diff,
        "correct_program_sha256": _sha(correct_program.encode()),
        "wrong_program_sha256": _sha(wrong_program.encode()),
        "input": pair["input"],
        "correct_output": correct,
        "wrong_output": wrong,
        "racket": identity2,
    }
    _dump(out / "causal.json", causal)
    report["causal_witness"] = "causal.json"
    report["source_sha256"] = {
        path.name: _sha(path.read_bytes())
        for path in HERE.iterdir() if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
    }
    _dump(out / "audit.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    result = run(args.out, args.seeds)
    print(json.dumps({key: result[key] for key in (
        "status", "episodes", "pair_instances", "distinct_inputs",
        "python_rival_checks", "racket_evaluations", "public_files"
    )}))


if __name__ == "__main__":
    main()
