"""Bounded protected-Racket teaching audit for the native parametric family.

The audit verifies intended labels, count/prefix stability, matched inputs across
settings, exact 30x30 stress, the finite alternate setting, four executable
selector rivals, and two Python-only structural rivals. It is intentionally
bounded and grants neither owner acceptance nor training admission.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback

TASK_ID = "01bdf9b8d2db"
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]


def _load_local(name, path):
    module_name = f"_01bdf9_audit_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


P = _load_local("prototype", HERE / "prototype.py")
R = _load_local("rivals", HERE / "rivals.py")


def _raw(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _source_hashes():
    return {
        path.relative_to(ROOT).as_posix(): _sha_file(path)
        for path in sorted(HERE.iterdir())
        if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
    }


@contextmanager
def _runtime():
    before = list(sys.path)
    sys.path[:0] = [str(ROOT / "shared" / "runtime")]
    saved = {
        key: value
        for key, value in sys.modules.items()
        if key.split(".")[0] in {"arc_repl", "puzzle_generators"}
    }
    for key in saved:
        del sys.modules[key]
    try:
        bridge_module = importlib.import_module("arc_repl.racket_bridge")
        wrap_module = importlib.import_module("puzzle_generators.rule_wrap")
        bridge = bridge_module.RacketBridge()
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires the live protected Racket backend")
        yield bridge, wrap_module.wrap_rule, identity
    finally:
        try:
            bridge.close()
        except UnboundLocalError:
            pass
        for key in list(sys.modules):
            if key.split(".")[0] in {"arc_repl", "puzzle_generators"}:
                del sys.modules[key]
        sys.modules.update(saved)
        sys.path[:] = before


def _public_turn_bytes(episode, index):
    return _raw(P.public_turn(episode, index))


def audit(output, seeds=(0, 17, 97), demo_counts=(2, 3, 6)):
    seeds = tuple(dict.fromkeys(seeds))
    demo_counts = tuple(dict.fromkeys(demo_counts))
    if not seeds or any(type(seed) is not int or not 0 <= seed < 2**63 for seed in seeds):
        raise ValueError("seeds must be distinct exact nonnegative 63-bit integers")
    if not demo_counts or any(count not in (2, 3, 4, 5, 6) for count in demo_counts):
        raise ValueError("demo counts must be drawn from 2..6")
    before = _source_hashes()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    failures = []
    jobs = []
    witnesses = {}
    cache = {}
    evaluations = 0
    cache_hits = 0
    executable_rivals = R.program_sources()
    program_sources = {
        "fill_all": P.program({"finish": "fill_all"}),
        "mark_smallest_total": P.program({"finish": "mark_smallest_total"}),
        **executable_rivals,
    }
    with _runtime() as (bridge, wrap_rule, identity):
        wrapped = {}

        def execute(source, grid):
            nonlocal evaluations, cache_hits
            key = (_sha_bytes(source.encode("utf-8")), _sha_bytes(_raw(grid)))
            if key in cache:
                cache_hits += 1
                return deepcopy(cache[key])
            if source not in wrapped:
                wrapped[source] = wrap_rule(source)
            evaluations += 1
            value = bridge.eval_text(f"({wrapped[source]} {_literal(grid)})")
            cache[key] = value
            return deepcopy(value)

        for seed in seeds:
            shared_inputs = {}
            for demos in demo_counts:
                for settings in P.SETTINGS:
                    finish = settings["finish"]
                    episode = P.generate(seed, deepcopy(settings), demos, 4)
                    row = {
                        "seed": seed,
                        "settings": deepcopy(settings),
                        "demos": demos,
                        "queries": 4,
                        "status": "passed",
                        "racket_refutations": {},
                        "python_refutations": {},
                    }
                    try:
                        inputs = [
                            pair["input"]
                            for pair in episode["train"] + episode["test"]
                        ]
                        key = (seed, demos)
                        if key in shared_inputs and shared_inputs[key] != inputs:
                            raise AssertionError("inputs differ across settings")
                        shared_inputs[key] = deepcopy(inputs)
                        short = P.generate(seed, deepcopy(settings), demos, 1)
                        extended = P.generate(seed, deepcopy(settings), 6, 4)
                        if (
                            _public_turn_bytes(short, 0) != _public_turn_bytes(episode, 0)
                            or extended["train"][:demos] != episode["train"]
                            or extended["test"] != episode["test"]
                        ):
                            raise AssertionError("count independence or first-turn stability failed")
                        if len({ _sha_bytes(_raw(grid)) for grid in inputs }) != len(inputs):
                            raise AssertionError("episode inputs are not distinct")
                        if demos == 6 and finish == "mark_smallest_total":
                            stress = episode["test"][3]["input"]
                            if (len(stress), len(stress[0])) != (30, 30):
                                raise AssertionError("fourth query is not exact 30x30")
                        intended = program_sources[finish]
                        for split in ("train", "test"):
                            for index, pair in enumerate(episode[split]):
                                actual = execute(intended, pair["input"])
                                if actual != pair["output"]:
                                    raise AssertionError(
                                        f"intended label mismatch at {split}/{index}"
                                    )
                        candidates = {
                            "alternate_setting": program_sources[
                                "mark_smallest_total" if finish == "fill_all" else "fill_all"
                            ],
                            **executable_rivals,
                        }
                        for name, source in candidates.items():
                            refuted = [
                                index
                                for index, pair in enumerate(episode["train"])
                                if execute(source, pair["input"]) != pair["output"]
                            ]
                            row["racket_refutations"][name] = refuted
                            if not refuted:
                                mismatches = [
                                    index
                                    for index, pair in enumerate(episode["test"])
                                    if execute(source, pair["input"]) != pair["output"]
                                ]
                                if mismatches:
                                    failures.append({
                                        "kind": "teaching_ambiguity",
                                        "seed": seed,
                                        "settings": settings,
                                        "demos": demos,
                                        "candidate": name,
                                        "query_mismatches": mismatches,
                                    })
                                    row["status"] = "failed"
                            elif name not in witnesses:
                                first = refuted[0]
                                pair = episode["train"][first]
                                witnesses[name] = {
                                    "seed": seed,
                                    "settings": deepcopy(settings),
                                    "demos": demos,
                                    "demonstration_index": first,
                                    "input": pair["input"],
                                    "intended_output": pair["output"],
                                    "rival_output": execute(source, pair["input"]),
                                    "intended_program_sha256": _sha_bytes(intended.encode()),
                                    "rival_program_sha256": _sha_bytes(source.encode()),
                                }
                        for name in R.python_outputs(episode["train"][0]["input"]):
                            refuted = [
                                index
                                for index, pair in enumerate(episode["train"])
                                if R.python_outputs(pair["input"])[name] != pair["output"]
                            ]
                            row["python_refutations"][name] = refuted
                            if not refuted:
                                mismatches = [
                                    index
                                    for index, pair in enumerate(episode["test"])
                                    if R.python_outputs(pair["input"])[name] != pair["output"]
                                ]
                                if mismatches:
                                    failures.append({
                                        "kind": "python_teaching_ambiguity",
                                        "seed": seed,
                                        "settings": settings,
                                        "demos": demos,
                                        "candidate": name,
                                        "query_mismatches": mismatches,
                                    })
                                    row["status"] = "failed"
                    except Exception as exc:
                        failures.append({
                            "kind": "job_failed",
                            "seed": seed,
                            "settings": settings,
                            "demos": demos,
                            "error": f"{type(exc).__name__}: {exc}",
                            "traceback": traceback.format_exc(),
                        })
                        row["status"] = "failed"
                    jobs.append(row)
    after = _source_hashes()
    if after != before:
        failures.append({"kind": "source_changed_during_audit"})
    report = {
        "schema": "01bdf9b8d2db-parametric-teaching-audit-v1",
        "task_id": TASK_ID,
        "status": "failed" if failures else "passed",
        "source_hashes": before,
        "settings": list(P.SETTINGS),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": 4,
        "counts": {
            "jobs": len(jobs),
            "passed_jobs": sum(row["status"] == "passed" for row in jobs),
            "racket_evaluations": evaluations,
            "racket_cache_hits": cache_hits,
            "distinct_executed_programs": len({_sha_bytes(v.encode()) for v in program_sources.values()}),
            "racket_rivals": 1 + len(executable_rivals),
            "python_rivals": 2,
        },
        "racket": {
            key: identity[key]
            for key in (
                "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "jobs": jobs,
        "failures": failures,
        "program_sha256": {
            name: _sha_bytes(source.encode("utf-8"))
            for name, source in program_sources.items()
        },
        "limits": (
            "Three seeds, demo counts 2/3/6, four queries, two declared settings, "
            "four executable selector rivals and two Python structural rivals only; "
            "no universal identifiability, owner acceptance or training admission."
        ),
        "training_admitted": False,
    }
    witness_report = {
        "schema": "01bdf9b8d2db-parametric-rival-witnesses-v1",
        "task_id": TASK_ID,
        "source_hashes": before,
        "racket": report["racket"],
        "witnesses": witnesses,
        "limits": report["limits"],
        "training_admitted": False,
    }
    (output / "self-audit.json").write_bytes(_raw(report) + b"\n")
    (output / "rival-witnesses.json").write_bytes(_raw(witness_report) + b"\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--demos", type=int, action="append")
    args = parser.parse_args(argv)
    report = audit(
        args.out,
        seeds=(0, 17, 97) if args.seed is None else args.seed,
        demo_counts=(2, 3, 6) if args.demos is None else args.demos,
    )
    print(json.dumps({
        "status": report["status"],
        "counts": report["counts"],
        "failures": report["failures"],
    }, sort_keys=True))
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
