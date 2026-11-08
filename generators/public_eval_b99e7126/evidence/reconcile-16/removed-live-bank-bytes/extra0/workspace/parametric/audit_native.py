"""Reusable finite-rival, protected-Racket, public-view, and causal audit.

Everything written by this tool is reviewer-private except an individually chosen
``public/<content-id>.json`` turn.  It never registers, qualifies, accepts, or
admits the family to training.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
HOME = BASE.parents[1]
TASK = HOME.name


def _load(name):
    key = f"_{TASK}_audit_{name}_{hashlib.sha256(str(BASE).encode()).hexdigest()[:12]}"
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
            path.suffix in (".py", ".rkt")
            or path.name in ("promotion.json", "public-parent.json")
        )
    }


def _settings():
    parameters = json.loads((BASE / "promotion.json").read_text())["parameters"]
    keys = sorted(parameters)
    return [dict(zip(keys, values)) for values in itertools.product(*(parameters[k] for k in keys))]


def validate_public_view(view, identifier=None):
    """Check one visible turn for strict fields, grids, and content identity."""
    from reviewer_support import public_challenge_id

    family = _load("family")
    if type(view) is not dict or set(view) != {"train", "test"}:
        raise ValueError("public fields must be exactly train/test")
    if type(view["train"]) is not list or not 2 <= len(view["train"]) <= 6:
        raise ValueError("public train must have 2..6 demonstrations")
    if type(view["test"]) is not list or len(view["test"]) != 1:
        raise ValueError("exactly one visible query is required")
    inputs = []
    for split in ("train", "test"):
        for pair in view[split]:
            expected = {"input", "output"} if split == "train" else {"input"}
            if type(pair) is not dict or set(pair) != expected:
                raise ValueError("public pair keys expose hidden data or omit a grid")
            for grid in pair.values():
                family.checked_grid(grid)
            inputs.append(_digest(pair["input"]))
    if len(set(inputs)) != len(inputs):
        raise ValueError("duplicate visible input")
    actual = public_challenge_id(view)
    if identifier is not None and identifier != actual:
        raise ValueError("public filename/content identity mismatch")
    return actual


def run_audit(out, *, seeds, racket_seeds):
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes, public_challenge_id

    out = Path(out)
    if out.exists():
        raise FileExistsError("choose a fresh audit directory")
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be nonempty and unique")
    if any(type(seed) is not int or not 0 <= seed < 2**63 for seed in list(seeds) + list(racket_seeds)):
        raise ValueError("seeds must be nonnegative exact 63-bit integers")

    adapter = _load("adapter")
    rivals = _load("rivals")
    source = _sources()
    findings = []
    equivalent_survivors = []
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
        "equivalent_survivors": equivalent_survivors,
        "source_sha256": source,
        "seeds": list(seeds),
        "racket_seeds": list(racket_seeds),
        "demo_counts": [2, 3, 6],
        "limits": (
            "Finite named semantic rivals and sampled seeds only; this is not a universal "
            "uniqueness, learning-benefit, owner-acceptance, or training-admission claim."
        ),
    }

    bridge = None
    try:
        if racket_seeds:
            apply, runtime, bridge = _real_evaluator(_root() / "shared/runtime")
        matched = {}
        for setting in _settings():
            selected = next(iter(setting.values()))
            for seed in seeds:
                for demos in (2, 3, 6):
                    episode = adapter.generate(seed, setting, demos, 4)
                    report["episodes"] += 1
                    pairs = episode["train"] + episode["private_query_bank"]
                    report["pair_claims"] += len(pairs)
                    grids = [pair["input"] for pair in pairs]
                    if len({_digest(grid) for grid in grids}) != len(grids):
                        findings.append({"kind": "duplicate_input", "seed": seed, "demos": demos})
                    key = (seed, demos)
                    if key in matched and matched[key] != grids:
                        findings.append({"kind": "unmatched_settings", "seed": seed, "demos": demos})
                    matched[key] = grids
                    if not any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                               for pair in episode["private_query_bank"]):
                        findings.append({"kind": "missing_30x30", "seed": seed})

                    candidates = set(rivals.predict(episode["train"][0]["input"], selected))
                    for pair in episode["train"]:
                        predictions = rivals.predict(pair["input"], selected)
                        report["rival_checks"] += len(candidates)
                        candidates = {name for name in candidates if predictions[name] == pair["output"]}
                    if selected not in candidates:
                        findings.append({"kind": "selected_rule_rejected", "seed": seed,
                                         "settings": setting, "demos": demos})
                    for name in sorted(candidates - {selected}):
                        changed = [
                            index
                            for index, pair in enumerate(episode["private_query_bank"])
                            if rivals.predict(pair["input"], selected)[name] != pair["output"]
                        ]
                        if changed:
                            findings.append({"kind": "harmful_survivor", "rival": name,
                                             "seed": seed, "settings": setting,
                                             "demos": demos, "queries": changed})
                        else:
                            equivalent_survivors.append({"rival": name, "seed": seed,
                                                         "settings": setting, "demos": demos})

                    if seed in racket_seeds:
                        for pair in pairs:
                            token = (_digest(episode["program_solution"]), _digest(pair["input"]))
                            if token not in cache:
                                cache[token] = apply(episode["program_solution"], pair["input"])
                                report["racket_evaluations"] += 1
                            if cache[token] != pair["output"]:
                                findings.append({"kind": "racket_parity", "seed": seed,
                                                 "settings": setting})

                    if demos == 2 and (seed in (17, 43) or seed == seeds[0]):
                        presentation_seed = seed ^ 0x9E3779B9
                        order = adapter.presentation_order(presentation_seed)
                        short = adapter.generate(seed, setting, 2, 1)
                        view_ids = []
                        for turn, source_index in enumerate(order):
                            view = adapter.public_view(episode, turn, presentation_seed)
                            validate_public_view(view)
                            if adapter.public_view(short, turn, presentation_seed) != view:
                                findings.append({"kind": "first_turn_prefix", "seed": seed,
                                                 "settings": setting, "turn": turn})
                            poisoned = copy.deepcopy(episode)
                            poisoned.update(seed="secret", settings={"secret": True},
                                            program_solution="secret")
                            for index, pair in enumerate(poisoned["private_query_bank"]):
                                pair["output"] = [[9]]
                                if index != source_index:
                                    pair["input"] = [[8]]
                            if adapter.public_view(poisoned, turn, presentation_seed) != view:
                                findings.append({"kind": "private_leak", "seed": seed,
                                                 "settings": setting, "turn": turn})
                            payload = public_challenge_bytes(view)
                            identifier = public_challenge_id(view)
                            if identifier in exports:
                                findings.append({"kind": "duplicate_public_payload", "id": identifier})
                            exports[identifier] = payload
                            view_ids.append(identifier)
                            report["public_turns"] += 1
                        private_index.append({
                            "settings": setting,
                            "seed": seed,
                            "presentation_seed": presentation_seed,
                            "source_indices": order,
                            "view_ids": view_ids,
                            "answers": [episode["private_query_bank"][index]["output"] for index in order],
                        })
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
    receipt = json.loads(preflight.read_text())
    if (receipt.get("task_id") != TASK or receipt.get("status") != "passed"
            or receipt.get("owner_accepted") is not False):
        raise ValueError("expected this task authoring preflight, not approval")
    root = _root()
    for row in receipt["source_binding"]["files"]:
        if hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("source changed since preflight: " + row["path"])
    execution_path = preflight.with_name("execution.json")
    if hashlib.sha256(execution_path.read_bytes()).hexdigest() != receipt["evidence_sha256"]["execution.json"]:
        raise ValueError("preflight execution evidence changed")

    adapter = _load("adapter")
    execution = json.loads(execution_path.read_text())
    episode = next(ep for ep in execution["episodes"] if ep["settings"] == adapter.causal_settings())
    pair = next(pair for pair in episode["test"]
                if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
    apply, runtime, bridge = _real_evaluator(root / "shared/runtime")
    try:
        actual = apply(episode["program_solution"], pair["input"])
        wrong = apply(adapter.counterfactual_program(), pair["input"])
        if actual != pair["output"] or actual == wrong:
            raise ValueError("causal output mismatch or counterfactual has no effect")
    finally:
        bridge.close()

    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": receipt["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        **adapter.CAUSAL_DESCRIPTIONS,
        "cases": [{
            "input": pair["input"],
            "settings": episode["settings"],
            "intermediate_value": adapter.causal_intermediate(pair["input"]),
            "program": episode["program_solution"],
            "output": actual,
            "counterfactual_program": adapter.counterfactual_program(),
            "counterfactual_output": wrong,
            "ablation": "wrong_intermediate",
        }],
    }
    raw = (json.dumps(witness, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    validate_sequential_witness(
        {"sequential_dependency": {**adapter.CAUSAL_DESCRIPTIONS,
                                    "witness_path": "witness.json"}},
        receipt,
        lambda _: raw,
    )
    replay = replay_witness(root, witness)
    replay.update(status="reviewer_replayed", owner_accepted=False,
                  caller_scope="Reviewer authoring replay, not owner acceptance")
    changed = sum(a != b for row_a, row_b in zip(actual, wrong)
                  for a, b in zip(row_a, row_b))
    out.mkdir(parents=True)
    (out / "witness.json").write_bytes(raw)
    _write(out / "replay.json", replay)
    summary = {
        "status": "reviewer_replayed",
        "evaluations": replay.get("evaluations", 2),
        "changed_cells": changed,
        "racket": runtime,
        "owner_accepted": False,
    }
    _write(out / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 17, 43])
    parser.add_argument("--racket-seeds", type=int, nargs="*", default=[0, 17, 43])
    parser.add_argument("--causal-preflight", type=Path)
    args = parser.parse_args()
    report = (build_causal(args.causal_preflight, args.out)
              if args.causal_preflight else
              run_audit(args.out, seeds=args.seeds, racket_seeds=args.racket_seeds))
    printable = {key: value for key, value in report.items()
                 if key not in ("source_sha256", "racket", "findings", "equivalent_survivors")}
    print(json.dumps(printable, sort_keys=True))
    return 0 if report["status"] in ("passed", "reviewer_replayed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
