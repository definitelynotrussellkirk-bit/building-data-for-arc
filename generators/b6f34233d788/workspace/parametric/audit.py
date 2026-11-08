#!/usr/bin/env python3
"""Bounded native-family audit with optional protected-Racket replay.

The script is deliberately checkout-local and source-binding friendly.  It
checks all legal demo/query prefixes across a finite seed sweep, the declared
setting and shortcut survivor sets, setting-neutral inputs, deterministic
prefixes, private/public separation, a 30x30 stress query, and (by default)
protected-Racket parity for seeds 0 and 17.  It is authoring evidence only; it
never grants owner acceptance or training admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]

from reviewer_support import public_challenge_bytes


def _load(filename: str, tag: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(
        f"_native_audit_{tag}_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load("adapter.py", "adapter")
PROTOTYPE = _load("prototype.py", "prototype")
CONTRACT = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
PARAMETER = next(iter(CONTRACT["parameters"]))
SETTINGS = tuple(CONTRACT["parameters"][PARAMETER])
TASK_ID = HOME.parents[1].name


def _grid_key(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _assert_episode(episode: dict[str, Any], demos: int, queries: int) -> None:
    if type(episode) is not dict or len(episode.get("train", [])) != demos or len(episode.get("test", [])) != queries:
        raise AssertionError("wrong episode shape/counts")
    if set(episode) != {"train", "test", "program_solution"}:
        raise AssertionError(f"unexpected private episode fields: {sorted(episode)}")
    serial = []
    for pair in episode["train"] + episode["test"]:
        if set(pair) != {"input", "output"}:
            raise AssertionError("private pair must contain exactly input/output")
        serial.append(_grid_key(pair["input"]))
    if len(serial) != len(set(serial)):
        raise AssertionError("episode inputs are not distinct")


def _public_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    view = ADAPTER.public_turn(episode, query_index)
    if set(view) != {"train", "test"}:
        raise AssertionError("public view leaked or omitted a top-level field")
    if len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
        raise AssertionError("public view must expose one unanswered query")
    if any(set(pair) != {"input", "output"} for pair in view["train"]):
        raise AssertionError("public demonstrations malformed")
    return public_challenge_bytes(view)


def _protected_replay(seeds: Iterable[int]) -> tuple[int, dict[str, Any] | None]:
    seeds = tuple(dict.fromkeys(seeds))
    if not seeds:
        return 0, None
    if any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("racket seeds must be nonnegative exact integers")
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    evaluations = 0
    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            if identity.get("backend") != "racket" or identity.get("protected") is not True:
                raise AssertionError(f"unprotected evaluator: {identity}")
            for seed in seeds:
                shared_inputs = None
                for setting in SETTINGS:
                    settings = {PARAMETER: setting}
                    episode = ADAPTER.generate(seed, settings, 2, 4)
                    visible = _inputs(episode)
                    if shared_inputs is None:
                        shared_inputs = visible
                    elif visible != shared_inputs:
                        raise AssertionError("protected replay saw setting-dependent inputs")
                    program = ADAPTER.program(settings)
                    if episode["program_solution"] != program:
                        raise AssertionError("episode/program mismatch")
                    for pair in episode["train"] + episode["test"]:
                        actual = _grid(apply(program, deepcopy(pair["input"])))
                        evaluations += 1
                        if actual != _grid(pair["output"]):
                            raise AssertionError(
                                f"protected Racket disagrees: seed={seed} {PARAMETER}={setting}"
                            )
        finally:
            bridge.close()
    return evaluations, identity


def build_report(*, seeds: int = 8, racket_seeds: Iterable[int] = (0, 17)) -> dict[str, Any]:
    if type(seeds) is not int or not 1 <= seeds <= 128:
        raise ValueError("seeds must be an exact integer in 1..128")
    if len(SETTINGS) != 2:
        raise AssertionError("this bounded auditor expects exactly two declared settings")

    requests = prefix_checks = setting_neutral_checks = public_checks = 0
    deterministic_checks = causal_checks = stress_checks = 0
    rival_survivors: list[dict[str, Any]] = []
    distinct_inputs: set[str] = set()
    query_orders: set[tuple[str, ...]] = set()

    canonical_text = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    if ADAPTER.program({PARAMETER: SETTINGS[0]}) != canonical_text:
        raise AssertionError("declared default is not exact canonical source")
    if ADAPTER.program({PARAMETER: SETTINGS[1]}) == canonical_text:
        raise AssertionError("alternate program is not distinct")

    for seed in range(seeds):
        full = {
            setting: ADAPTER.generate(seed, {PARAMETER: setting}, 6, 4)
            for setting in SETTINGS
        }
        for episode in full.values():
            _assert_episode(episode, 6, 4)
        reference_inputs = _inputs(full[SETTINGS[0]])
        if _inputs(full[SETTINGS[1]]) != reference_inputs:
            raise AssertionError(f"setting-dependent inputs at seed {seed}")
        setting_neutral_checks += 1
        distinct_inputs.update(_grid_key(grid) for grid in reference_inputs)
        query_orders.add(tuple(_grid_key(pair["input"]) for pair in full[SETTINGS[0]]["test"]))

        again = ADAPTER.generate(seed, {PARAMETER: SETTINGS[0]}, 6, 4)
        if again != full[SETTINGS[0]] or again is full[SETTINGS[0]]:
            raise AssertionError("generation is not deterministic/fresh")
        mutated = deepcopy(again)
        mutated["train"][0]["input"][0][0] = (mutated["train"][0]["input"][0][0] + 1) % 10
        if ADAPTER.generate(seed, {PARAMETER: SETTINGS[0]}, 6, 4) != full[SETTINGS[0]]:
            raise AssertionError("returned episode aliases cached state")
        deterministic_checks += 1

        if not all(
            PROTOTYPE.transform(grid, SETTINGS[0]) != PROTOTYPE.transform(grid, SETTINGS[1])
            for grid in reference_inputs
        ):
            raise AssertionError(f"non-causal setting pair at seed {seed}")
        causal_checks += len(reference_inputs)

        stress = [pair["input"] for pair in full[SETTINGS[0]]["test"] if (len(pair["input"]), len(pair["input"][0])) == (30, 30)]
        if len(stress) != 1:
            raise AssertionError("query bank must contain exactly one 30x30 stress input")
        metrics = PROTOTYPE.input_metrics(stress[0])
        if metrics["foreground_cells"] < 60 or len(metrics["boundary_sides"]) < 2:
            raise AssertionError(f"weak 30x30 stress input: {metrics}")
        stress_checks += 1

        for demos in range(2, 7):
            for queries in range(1, 5):
                current_inputs = None
                for setting in SETTINGS:
                    settings = {PARAMETER: setting}
                    episode = ADAPTER.generate(seed, settings, demos, queries)
                    _assert_episode(episode, demos, queries)
                    if episode["program_solution"] != ADAPTER.program(settings):
                        raise AssertionError("program_solution not adapter-bound")
                    if episode["train"] != full[setting]["train"][:demos] or episode["test"] != full[setting]["test"][:queries]:
                        raise AssertionError("count-prefix instability")
                    prefix_checks += 1
                    visible_inputs = _inputs(episode)
                    if current_inputs is None:
                        current_inputs = visible_inputs
                    elif visible_inputs != current_inputs:
                        raise AssertionError("setting-dependent input prefix")
                    check = PROTOTYPE.teaching_check(episode["train"], setting)
                    if check.get("survivors") != [setting]:
                        rival_survivors.append({"seed": seed, "demos": demos, "queries": queries, "setting": setting, "kind": "declared", "survivors": check.get("survivors")})
                    for rival in check.get("rival_survivors", []):
                        rival_survivors.append({"seed": seed, "demos": demos, "queries": queries, "setting": setting, "kind": "shortcut", "rival": rival})
                    for query_index in range(queries):
                        raw = _public_bytes(episode, query_index)
                        hidden = deepcopy(episode)
                        hidden["program_solution"] = "PRIVATE SENTINEL"
                        hidden["settings"] = {"PRIVATE": "SENTINEL"}
                        for pair in hidden["test"]:
                            pair["output"] = [[9]]
                        for later in range(query_index + 1, len(hidden["test"])):
                            hidden["test"][later]["input"] = [[8]]
                        if _public_bytes(hidden, query_index) != raw:
                            raise AssertionError("public bytes depend on hidden fields")
                        public_checks += 1
                    one = ADAPTER.generate(seed, settings, demos, 1)
                    if _public_bytes(episode, 0) != _public_bytes(one, 0):
                        raise AssertionError("first turn depends on private query count")
                    requests += 1
                setting_neutral_checks += 1

    if rival_survivors:
        raise AssertionError(f"finite teaching audit found survivors: {rival_survivors[:3]}")
    evaluations, runtime_identity = _protected_replay(racket_seeds)

    source_names = ("adapter.py", "prototype.py", "promotion.json", "canonical.rkt", "audit.py")
    report = {
        "schema": "arcpuzzles-native-family-bounded-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "parameter": PARAMETER,
        "settings": list(SETTINGS),
        "finite_scope": {
            "seeds": list(range(seeds)),
            "demo_counts": list(range(2, 7)),
            "query_counts": list(range(1, 5)),
            "racket_seeds": list(dict.fromkeys(racket_seeds)),
            "declared_shortcuts": list(PROTOTYPE.RIVALS),
        },
        "episodes": requests,
        "prefix_checks": prefix_checks,
        "setting_neutral_input_checks": setting_neutral_checks,
        "determinism_and_copy_checks": deterministic_checks,
        "causal_output_disagreements": causal_checks,
        "public_projection_checks": public_checks,
        "stress_30x30_checks": stress_checks,
        "distinct_input_sha256": len(distinct_inputs),
        "distinct_query_orders": len(query_orders),
        "rival_survivors": rival_survivors,
        "racket_evaluations": evaluations,
        "racket": runtime_identity,
        "source_sha256": {
            name: hashlib.sha256((HOME / name).read_bytes()).hexdigest()
            for name in source_names
        },
        "owner_accepted": False,
        "training_admitted": False,
        "limitation": "Finite declared-setting/shortcut audit. It is authoring evidence, not universal identifiability, owner acceptance, measured learning gain, or training admission.",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new JSON report path")
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--racket-seeds", type=int, nargs="*", default=[0, 17])
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit(f"refusing to overwrite {args.out}")
    report = build_report(seeds=args.seeds, racket_seeds=args.racket_seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "task_id", "episodes", "distinct_input_sha256", "racket_evaluations")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
