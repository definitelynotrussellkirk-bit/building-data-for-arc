"""Finite-rival, protected-Racket, public-view, and causal audit runner.

The reports are author-private evidence. This tool never registers, qualifies,
accepts, or admits the family to training.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
HOME = BASE.parents[1]
TASK = HOME.name


def _load(name):
    key = f"_p380_audit_{name}_{hashlib.sha256(str(BASE).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(key, BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _root():
    from reviewer_support import find_root

    return find_root(__file__)


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _sources():
    root = _root()
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(HOME.rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and (
            path.suffix in (".py", ".rkt", ".md")
            or path.name in ("promotion.json", "public-parent.json")
        )
    }


def _settings():
    return [{"stack_order": "source_rows"}, {"stack_order": "difference_desc"}]


def run_audit(out, *, seeds, racket_seeds):
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes, public_challenge_id

    out = Path(out)
    if out.exists():
        raise FileExistsError("choose a fresh audit directory")
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be nonempty and unique")
    if any(type(seed) is not int or seed < 0 for seed in list(seeds) + list(racket_seeds)):
        raise ValueError("seeds must be nonnegative exact integers")

    adapter = _load("adapter")
    family = adapter.family
    source = _sources()
    findings = []
    exports = {}
    private_index = []
    cache = {}
    runtime = None
    report = {
        "task_id": TASK,
        "status": "running",
        "episodes": 0,
        "pair_claims": 0,
        "racket_evaluations": 0,
        "rival_checks": 0,
        "public_turns": 0,
        "findings": findings,
        "source_sha256": source,
        "seeds": list(seeds),
        "racket_seeds": list(racket_seeds),
        "demo_counts": [2, 3, 6],
        "rivals": list(family.RIVALS),
        "limits": (
            "Finite named rivals and sampled seeds only; no universal uniqueness, "
            "learning-benefit, owner-acceptance, or training-admission claim."
        ),
    }

    bridge = None
    try:
        if racket_seeds:
            apply, runtime, bridge = _real_evaluator(_root() / "shared/runtime")
        matched = {}
        for setting in _settings():
            selected = setting["stack_order"]
            for seed in seeds:
                for demos in (2, 3, 6):
                    episode = adapter.generate(seed, setting, demos, 4)
                    report["episodes"] += 1
                    pairs = episode["train"] + episode["test"]
                    report["pair_claims"] += len(pairs)
                    grids = [pair["input"] for pair in pairs]
                    if len({_digest(grid) for grid in grids}) != len(grids):
                        findings.append({"kind": "duplicate_input", "seed": seed, "demos": demos})
                    key = (seed, demos)
                    if key in matched and matched[key] != grids:
                        findings.append({"kind": "unmatched_settings", "seed": seed, "demos": demos})
                    matched[key] = grids
                    if not any(
                        len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                        for pair in episode["private_query_bank"]
                    ):
                        findings.append({"kind": "missing_30x30", "seed": seed})

                    candidates = set(family.RIVALS)
                    for pair in episode["train"]:
                        report["rival_checks"] += len(candidates)
                        candidates = {
                            name
                            for name in candidates
                            if family.render(pair["input"], name) == pair["output"]
                        }
                    for name in sorted(candidates - {selected}):
                        for query_index, pair in enumerate(episode["test"]):
                            if family.render(pair["input"], name) != pair["output"]:
                                findings.append(
                                    {
                                        "kind": "harmful_survivor",
                                        "rival": name,
                                        "seed": seed,
                                        "settings": setting,
                                        "demos": demos,
                                        "query": query_index,
                                    }
                                )
                                break

                    if seed in racket_seeds:
                        for pair in pairs:
                            token = (_digest(episode["program_solution"]), _digest(pair["input"]))
                            if token not in cache:
                                cache[token] = apply(episode["program_solution"], pair["input"])
                                report["racket_evaluations"] += 1
                            if cache[token] != pair["output"]:
                                findings.append(
                                    {
                                        "kind": "racket_parity",
                                        "seed": seed,
                                        "settings": setting,
                                    }
                                )

                    if demos == 2 and (seed in (17, 43) or seed == seeds[0]):
                        order = adapter.presentation_order(seed ^ 0x9E3779B9)
                        short = adapter.generate(seed, setting, 2, 1)
                        view_ids = []
                        for source_index in order:
                            view = adapter.public_view(episode, source_index)
                            if adapter.public_view(short, source_index) != view:
                                findings.append({"kind": "first_turn_prefix", "seed": seed})
                            poisoned = copy.deepcopy(episode)
                            poisoned.update(
                                seed="secret",
                                settings={"secret": True},
                                program_solution="secret",
                            )
                            for index, pair in enumerate(poisoned["private_query_bank"]):
                                pair["output"] = [[9]]
                                if index != source_index:
                                    pair["input"] = [[8]]
                            if adapter.public_view(poisoned, source_index) != view:
                                findings.append({"kind": "private_leak", "seed": seed})
                            payload = public_challenge_bytes(view)
                            identifier = public_challenge_id(view)
                            if identifier in exports:
                                findings.append({"kind": "duplicate_public_payload", "id": identifier})
                            exports[identifier] = payload
                            view_ids.append(identifier)
                            report["public_turns"] += 1
                        private_index.append(
                            {
                                "settings": setting,
                                "seed": seed,
                                "source_indices": order,
                                "view_ids": view_ids,
                                "answers": [
                                    episode["private_query_bank"][index]["output"] for index in order
                                ],
                            }
                        )
        report["first_query_indices"] = sorted(
            {adapter.presentation_order(seed)[0] for seed in range(64)}
        )
        if report["first_query_indices"] != [0, 1, 2, 3]:
            findings.append({"kind": "presentation_not_varied"})
        if _sources() != source:
            raise ValueError("source changed during audit")
    finally:
        if bridge is not None:
            bridge.close()

    report["status"] = "passed" if not findings else "failed"
    report["racket"] = runtime
    out.mkdir(parents=True)
    (out / "public").mkdir()
    for identifier, payload in sorted(exports.items()):
        (out / "public" / f"{identifier}.json").write_bytes(payload)
    _write(out / "private/index.json", {"controller_only": True, "episodes": private_index})
    _write(out / "report.json", report)
    return report


def build_causal(preflight, out):
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness

    preflight = Path(preflight)
    out = Path(out)
    if out.exists():
        raise FileExistsError("choose a fresh causal directory")
    qualification = json.loads(preflight.read_text())
    if (
        qualification["task_id"] != TASK
        or qualification["status"] != "passed"
        or qualification.get("owner_accepted") is not False
    ):
        raise ValueError("expected this task authoring preflight, not approval")
    root = _root()
    for row in qualification["source_binding"]["files"]:
        if hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("source changed since preflight: " + row["path"])
    execution_path = preflight.with_name("execution.json")
    if (
        hashlib.sha256(execution_path.read_bytes()).hexdigest()
        != qualification["evidence_sha256"]["execution.json"]
    ):
        raise ValueError("preflight execution evidence changed")

    adapter = _load("adapter")
    execution = json.loads(execution_path.read_text())
    episode = next(
        row for row in execution["episodes"] if row["settings"] == adapter.causal_settings()
    )
    apply, runtime, bridge = _real_evaluator(root / "shared/runtime")
    selected = None
    try:
        for split in ("test", "train"):
            for pair in reversed(episode[split]):
                actual = apply(episode["program_solution"], pair["input"])
                wrong = apply(adapter.counterfactual_program(), pair["input"])
                if actual == pair["output"] and actual != wrong:
                    selected = (pair, actual, wrong)
                    break
            if selected is not None:
                break
    finally:
        bridge.close()
    if selected is None:
        raise ValueError("no qualified pair exposes the wrong ranking intermediate")
    pair, actual, wrong = selected
    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        **adapter.CAUSAL_DESCRIPTIONS,
        "cases": [
            {
                "input": pair["input"],
                "settings": episode["settings"],
                "intermediate_value": adapter.causal_intermediate(pair["input"]),
                "program": episode["program_solution"],
                "output": actual,
                "counterfactual_program": adapter.counterfactual_program(),
                "counterfactual_output": wrong,
                "ablation": "wrong_intermediate",
            }
        ],
    }
    raw = (json.dumps(witness, sort_keys=True, indent=2) + "\n").encode()
    validate_sequential_witness(
        {
            "sequential_dependency": {
                **adapter.CAUSAL_DESCRIPTIONS,
                "witness_path": "witness.json",
            }
        },
        qualification,
        lambda _path: raw,
    )
    replay = replay_witness(root, witness)
    replay.update(
        status="reviewer_replayed",
        owner_accepted=False,
        caller_scope="Reviewer authoring replay, not owner acceptance",
    )
    out.mkdir(parents=True)
    (out / "witness.json").write_bytes(raw)
    _write(out / "replay.json", replay)
    return {
        "status": "reviewer_replayed",
        "evaluations": 4,
        "changed_cells": sum(
            a != b for row_a, row_b in zip(actual, wrong) for a, b in zip(row_a, row_b)
        ),
        "racket": runtime,
        "owner_accepted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 17, 43])
    parser.add_argument("--racket-seeds", type=int, nargs="*", default=[0, 17, 43])
    parser.add_argument("--causal-preflight", type=Path)
    args = parser.parse_args()
    report = (
        build_causal(args.causal_preflight, args.out)
        if args.causal_preflight
        else run_audit(args.out, seeds=args.seeds, racket_seeds=args.racket_seeds)
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in ("source_sha256", "racket")},
            sort_keys=True,
        )
    )
    return 0 if report["status"] in ("passed", "reviewer_replayed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
