"""Protected-Racket authoring audit for the equivalence-policy family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(name: str, filename: str):
    path = HERE / filename
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("_arcp_84aeaf4792a8_audit_prototype", "prototype.py")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _grid_sha(grid: Any) -> str:
    return _sha(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode())


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def python_preflight(seeds: Iterable[int] = (0, 17), demos_set=(2, 3, 6)) -> dict[str, Any]:
    failures = []
    episodes = 0
    for seed in seeds:
        for demos in demos_set:
            baseline_inputs = None
            for policy in prototype.POLICIES:
                episode = prototype.generate(seed, {"equivalence_policy": policy}, demos, 4)
                inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                if baseline_inputs is None:
                    baseline_inputs = inputs
                elif inputs != baseline_inputs:
                    failures.append({"kind": "setting_dependent_inputs", "seed": seed, "demos": demos})
                certificate = prototype.lesson_certificate(episode)
                if certificate["declared_survivors"] != [policy]:
                    failures.append({"kind": "declared_setting_ambiguity", "seed": seed,
                                     "demos": demos, "policy": policy,
                                     "survivors": certificate["declared_survivors"]})
                if certificate["harmful_rival_survivors"]:
                    failures.append({"kind": "harmful_rival", "seed": seed,
                                     "demos": demos, "policy": policy,
                                     "survivors": certificate["harmful_rival_survivors"]})
                turns = prototype.public_query_turns(episode)
                if len(turns) != 4 or any(len(turn["test"]) != 1 for turn in turns):
                    failures.append({"kind": "public_projection", "seed": seed,
                                     "demos": demos, "policy": policy})
                episodes += 1
    return {
        "schema": "arcpuzzles-equivalence-policy-python-audit-v1",
        "status": "pass" if not failures else "fail",
        "episodes_checked": episodes,
        "seeds": list(seeds),
        "demo_counts": list(demos_set),
        "rivals": list(prototype.RIVAL_NAMES),
        "failures": failures,
        "scope": "Finite declared settings and named rivals; not universal uniqueness.",
    }


def run(output: Path, seeds: Iterable[int] = (0, 17)) -> dict[str, Any]:
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes, public_challenge_id

    output = Path(output)
    if output.exists():
        raise FileExistsError(f"choose a new output directory: {output}")
    preflight = python_preflight(seeds)
    if preflight["status"] != "pass":
        raise RuntimeError(json.dumps(preflight["failures"]))
    programs = {policy: prototype.program({"equivalence_policy": policy})
                for policy in prototype.POLICIES}
    apply, identity, bridge = _real_evaluator(RUNTIME)
    calls = []
    cache = {}
    episodes = []
    public_rows = []

    def execute(policy, grid):
        key = policy, json.dumps(grid, separators=(",", ":"))
        if key not in cache:
            output_grid = apply(programs[policy], grid)
            claimed = prototype.solve(grid, policy)
            if output_grid != claimed:
                raise RuntimeError(f"Python/Racket mismatch for {policy}")
            cache[key] = output_grid
            calls.append({"policy": policy, "input_sha256": _grid_sha(grid),
                          "output_sha256": _grid_sha(output_grid)})
        return deepcopy(cache[key])

    output.mkdir(parents=True)
    try:
        for seed in seeds:
            baseline = None
            for policy in prototype.POLICIES:
                episode = prototype.generate(seed, {"equivalence_policy": policy}, 3, 4)
                inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                if baseline is None:
                    baseline = inputs
                elif baseline != inputs:
                    raise RuntimeError("settings changed inputs")
                for pair in episode["train"] + episode["test"]:
                    pair["output"] = execute(policy, pair["input"])
                certificate = prototype.lesson_certificate(episode)
                if certificate["declared_survivors"] != [policy] or certificate["harmful_rival_survivors"]:
                    raise RuntimeError("teaching certificate failed after protected labels")
                episodes.append({**episode, "teaching_certificate": certificate,
                                 "training_admitted": False, "owner_acceptance": "pending"})
                for query_index, public in enumerate(prototype.public_query_turns(episode)):
                    raw = public_challenge_bytes(public)
                    identifier = public_challenge_id(public)
                    path = output / "public" / f"{identifier}.json"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
                    public_rows.append({"seed": seed, "policy": policy,
                                        "query_index": query_index,
                                        "public_id": identifier,
                                        "path": path.relative_to(output).as_posix()})
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-equivalence-policy-protected-audit-v1",
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "settings": list(prototype.POLICIES),
        "seeds": list(seeds),
        "episodes": len(episodes),
        "labels_checked": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
        "racket_evaluations": len(calls),
        "racket": identity,
        "python_preflight": preflight,
        "public_turns": public_rows,
        "training_admitted": False,
        "owner_acceptance": "pending",
        "scope": "Protected Racket parity plus finite named-rival audit.",
    }
    _write(output / "authoring.json", report)
    _write(output / "episodes.private.json", episodes)
    _write(output / "execution_calls.json", calls)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    args = parser.parse_args(argv)
    try:
        report = run(args.out, args.seeds or (0, 17))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": type(exc).__name__, "message": str(exc)}))
        return 1
    print(json.dumps({key: report[key] for key in
                      ("status", "episodes", "labels_checked", "racket_evaluations")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
