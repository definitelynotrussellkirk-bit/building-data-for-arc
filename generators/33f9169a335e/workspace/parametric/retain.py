"""Execute and retain two proposed prototypes; no approval/admission is implied.

Run through review.py run so the exact packet's protected Racket is selected.
The public folder contains only visible demonstrations and unanswered queries.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "33f9169a335e"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def write_public_batch(episodes, out):
    """Validate the entire batch before writing; reject duplicate visible bytes."""
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")
    payloads = {}
    for episode in episodes:
        body = public_challenge_bytes(episode)
        identity = _sha(body)
        if identity in payloads:
            raise ValueError("duplicate visible challenge")
        payloads[identity] = body
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for identity, body in sorted(payloads.items()):
        (out / (identity + ".json")).write_bytes(body)
        rows.append({"public_id": identity, "file": identity + ".json",
                     "bytes": len(body), "sha256": identity})
    return rows


def lesson_certificate(predictions, chosen):
    """Choose surviving settings ONLY from demonstration outputs.

    Query outputs are inspected only after that fixed survivor set is known.
    This certifies the declared finite family, not all imaginable programs.
    """
    if type(predictions) is not dict or chosen not in predictions:
        raise ValueError("chosen setting is absent")
    base = predictions[chosen]
    if (type(base) is not dict or type(base.get("train")) is not list
            or not base["train"] or type(base.get("test")) is not list or not base["test"]):
        raise ValueError("nonempty demonstration and query predictions required")
    for value in predictions.values():
        if (type(value) is not dict or type(value.get("train")) is not list
                or type(value.get("test")) is not list
                or len(value["train"]) != len(base["train"])
                or len(value["test"]) != len(base["test"])):
            raise ValueError("misaligned predictions")
    eliminated, survivors = {}, []
    for name, value in sorted(predictions.items()):
        mismatches = [i for i, (a, b) in enumerate(zip(value["train"], base["train"]))
                      if a != b]
        if mismatches:
            eliminated[name] = mismatches
        else:
            survivors.append(name)
    queries = []
    for index, answer in enumerate(base["test"]):
        disagreements = [name for name in survivors
                         if predictions[name]["test"][index] != answer]
        if disagreements:
            raise ValueError(f"ambiguous query {index}: {disagreements}")
        queries.append({"query_index": index, "identified": True,
                        "agreeing_survivors": list(survivors)})
    return {"selection_basis": "demonstrations_only", "chosen": chosen,
            "declared_settings": sorted(predictions), "survivors": survivors,
            "eliminated": eliminated, "queries": queries}


def _load(name):
    spec = importlib.util.spec_from_file_location("retained_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _execute(label, program, task, out):
    from arc_repl.isolated_verifier import verify_candidate
    receipt = verify_candidate(task, program, racket_path=os.environ.get("RACKET_PATH", ""))
    _json(out / "private/receipts" / (label + ".json"), receipt)
    if (receipt.get("status") != "pass" or receipt.get("backend") != "racket"
            or receipt.get("hidden_exact") is not True):
        raise RuntimeError(f"protected Racket failed for {label}: {receipt.get('error', receipt)}")
    return receipt


def _predictions(episode):
    return {split: [pair["output"] for pair in episode[split]] for split in ("train", "test")}


def _source_bindings():
    files = [HERE / name for name in ("ray_mode.py", "analogy.py", "retain.py")]
    files += list((HERE.parents[1] / "tests").glob("test_parametric_*.py"))
    files += [HERE.parents[1] / "generator.py",
              ROOT / "shared/runtime/reviewer_support.py",
              ROOT / "shared/runtime/arc_repl/isolated_verifier.py",
              ROOT / "shared/runtime/arc_repl/racket_bridge.py",
              ROOT / "shared/data/canonical/puzzles.jsonl",
              ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json"]
    return {path.relative_to(ROOT).as_posix(): _sha(path.read_bytes()) for path in sorted(files)}


def _u_edges():
    mixed = [[0, 1, 2, 3, 0, 0, 0], [0, 5, 0, 6, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0], [0, 0, 7, 8, 9, 0, 0],
             [0, 0, 1, 0, 2, 0, 0], [0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0]]
    small = [[0] * 5 for _ in range(5)]
    large = [[0] * 30 for _ in range(30)]
    for grid, shapes in [(small, [(2, 3, 6)]), (large, [(0, 1, 2), (27, 28, 7)])]:
        for top, gap, color in shapes:
            for r, c in [(top, gap-1), (top, gap), (top, gap+1),
                         (top+1, gap-1), (top+1, gap+1)]:
                grid[r][c] = color
    return [mixed, small, large]


def run_evidence(out, *, seed=20261023, demo_count=2, query_count=4):
    for name, value in (("seed", seed), ("demo_count", demo_count), ("query_count", query_count)):
        if type(value) is not int or (name != "seed" and not 1 <= value <= 8):
            raise ValueError(f"{name} must be an exact integer with counts in 1..8")
    ray, analogy = _load("ray_mode"), _load("analogy")
    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema": "33f9169a335e-proposed-parametric-evidence-v1",
              "status": "running", "task_id": TASK_ID, "training_admitted": False,
              "seed": seed, "demo_count": demo_count, "query_count": query_count,
              "episodes": [], "racket_calls": 0, "executed_pairs": 0,
              "limitations": [
                  "Proposed variants only; canonical generator/rule/approvals are unchanged.",
                  "Certificates cover exactly two declared parameter values per prototype.",
                  "The analogy specializes the Boolean complement reasoning in public evaluation "
                  "4c7dc4dd demonstration 2; identity and alternate palette are proposed extensions.",
                  "This does not solve the whole public task or its line-connection demonstration 1.",
                  "Layout is two stacked framed pairs; tested finite seeds do not establish universal correctness."]}
    _json(out / "report.json", report)
    retained = []
    try:
        report["source_sha256"] = _source_bindings()
        runtime = Path(os.environ["RACKET_PATH"]).resolve(strict=True)
        report["runtime"] = {"backend": "racket", "binary_sha256": _sha(runtime.read_bytes())}
        groups = [("u_projection", ray, ray.MODES, "mode", seed),
                  ("boolean_analogy", analogy, analogy.COLOR_ROLES, "role", seed + 101)]
        for family, module, values, argument, input_seed in groups:
            episodes = {}
            for value in values:
                episode = module.sample_episode(seed, **{argument: value}, input_seed=input_seed,
                                                demo_count=demo_count, query_count=query_count)
                all_pairs = episode["train"] + episode["test"]
                if len({json.dumps(pair["input"]) for pair in all_pairs}) != demo_count + query_count:
                    raise ValueError("episode contains duplicate inputs")
                label = family + "-" + value
                program = episode["program"]
                rule_path = out / "private/rules" / (label + ".rkt")
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(program)
                receipt = _execute(label, program,
                                   {"train": episode["train"], "test": episode["test"]}, out)
                report["racket_calls"] += 1
                report["executed_pairs"] += len(all_pairs)
                # Public labels come from the successful real runtime receipt.
                for split, outputs in (("train", receipt["train_outputs"]),
                                       ("test", receipt["test_outputs"])):
                    for pair, observed in zip(episode[split], outputs, strict=True):
                        pair["output"] = observed
                episode["label_backend"] = "protected_racket"
                episode["program_sha256"] = _sha(program.encode())
                episode["source_sha256"] = report["source_sha256"]
                episodes[value] = episode
            reference_inputs = [[p["input"] for p in next(iter(episodes.values()))[s]]
                                for s in ("train", "test")]
            for episode in episodes.values():
                if [[p["input"] for p in episode[s]] for s in ("train", "test")] != reference_inputs:
                    raise ValueError("parameter comparisons must use identical ordered inputs")
            predictions = {value: _predictions(ep) for value, ep in episodes.items()}
            for value, episode in episodes.items():
                certificate = lesson_certificate(predictions, value)
                episode["lesson_certificate"] = certificate
                identity = public_challenge_id(episode)
                private_path = "private/episodes/" + identity + ".json"
                _json(out / private_path, episode)
                report["episodes"].append({"family": family, "parameters": episode["parameters"],
                    "public_id": identity, "private_path": private_path,
                    "program_sha256": episode["program_sha256"], "certificate": certificate,
                    "input_seed": input_seed})
                retained.append(episode)
        # Default canonical parity uses all four supplied canonical examples.
        from reviewer_support import canonical_pairs
        canonical = canonical_pairs(TASK_ID, root=ROOT)
        _execute("canonical-default", ray.rule_source("endpoint"),
                 {"train": canonical[:3], "test": canonical[3:]}, out)
        report["racket_calls"] += 1
        report["executed_pairs"] += len(canonical)
        report["canonical_default"] = {"pairs": len(canonical), "status": "pass",
                                      "program_exact": ray.rule_source("endpoint") == ray.canonical_program()}
        edge_inputs = _u_edges()
        edge_evidence = []
        for mode in ray.MODES:
            pairs = [{"input": grid, "output": ray.python_transform(grid, mode)} for grid in edge_inputs]
            receipt = _execute("u-edges-" + mode, ray.rule_source(mode),
                               {"train": pairs[:1], "test": pairs[1:]}, out)
            edge_evidence.append({"mode": mode, "pairs": pairs})
            report["racket_calls"] += 1
            report["executed_pairs"] += len(pairs)
        _json(out / "private/u-edge-cases.json", edge_evidence)
        a, b = analogy.context_counterfactual(17, 5)
        context_evidence = {"input_identity": a, "input_complement": b, "roles": []}
        changed = [(r, c) for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]
        if not changed:
            raise AssertionError("source-context counterfactual did not change")
        for role in analogy.COLOR_ROLES:
            pairs = [{"input": g, "output": analogy.python_transform(g, role)} for g in (a, b)]
            if pairs[0]["output"] == pairs[1]["output"]:
                raise AssertionError("source context does not affect target answer")
            receipt = _execute("context-" + role, analogy.rule_source(role),
                               {"train": pairs[:1], "test": pairs[1:]}, out)
            context_evidence["roles"].append({"role": role,
                "outputs": receipt["train_outputs"] + receipt["test_outputs"]})
            report["racket_calls"] += 1
            report["executed_pairs"] += 2
        context_evidence["changed_input_cells"] = changed
        _json(out / "private/context-necessity.json", context_evidence)
        report["context_necessity"] = {"status": "pass", "changed_input_cells": len(changed),
            "witness_path": "private/context-necessity.json",
            "claim": "only first reference panel changes; second reference and target are held fixed"}
        report["public_files"] = write_public_batch(retained, out / "public")
        # The identity is tested against changes in private code, settings and labels.
        for episode in retained:
            hidden = copy.deepcopy(episode)
            hidden["seed"] = -999
            hidden["parameters"] = {"private_changed": True}
            hidden["program"] = "private_changed"
            for pair in hidden["test"]:
                pair["output"] = [[0]]
            if public_challenge_bytes(hidden) != public_challenge_bytes(episode):
                raise AssertionError("private information changed public bytes")
        report["public_projection"] = {"status": "pass", "private_invariance": True,
            "duplicate_visible_payloads": 0, "ordering": "public_sha256"}
        report["episodes"].sort(key=lambda row: row["public_id"])
        report["status"] = "pass"
    except Exception as error:
        report["status"] = "fail"
        report["error"] = repr(error)
        _json(out / "report.json", report)
        raise
    _json(out / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    report = run_evidence(args.out, seed=args.seed, demo_count=args.demos, query_count=args.queries)
    print(json.dumps({key: report[key] for key in ("status", "racket_calls", "executed_pairs")}))
    print(str(args.out / "report.json"))


if __name__ == "__main__":
    main()
