"""Private generation worker, copied into a self-contained execution tree."""
from __future__ import annotations

import copy
import contextlib
from copy import deepcopy
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import sys


def canonical_bundle(runner, task_id: str, module):
    """Execute the same selected authority whose hash controls approval."""
    from scripts.canonical_profile_gate import canonical_rule_source

    rule_task_id = runner._resolve_rule_task_id(task_id, module, kind="per_puzzle")
    source = canonical_rule_source(rule_task_id)
    return runner.GeneratorBundle(
        task_id=task_id,
        rule_task_id=rule_task_id,
        rule_source=source,
        rule_callable_text=runner.wrap_rule(source),
        rule_file="data/canonical/puzzles.jsonl",
        generator_module=module,
        allow_identity_output=bool(getattr(module, "ALLOW_IDENTITY_OUTPUT", False)),
        kind="per_puzzle",
    )


def _lesson_rivals(module, episode):
    """Score named pure grid rules; only demo survivors need query checks."""
    from reviewer_support import normalize_grid

    declarations, rivals, errors = [], {}, []
    for attribute in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        if not hasattr(module, attribute):
            continue
        declarations.append(attribute)
        raw = getattr(module, attribute)
        if not isinstance(raw, dict):
            errors.append(f"{attribute}: expected dict of named callables")
            continue
        for name, fn in raw.items():
            if not isinstance(name, str) or not callable(fn):
                errors.append(f"{attribute}:{name!r}: expected string name and callable")
            else:
                rivals[f"{attribute}:{name}"] = fn

    def predict(fn, pair):
        predictions = []
        for _ in range(2):
            grid = deepcopy(pair["input"])
            output = fn(grid)
            if grid != pair["input"]:
                raise ValueError("rival mutated its input")
            predictions.append(normalize_grid(output))
        if predictions[0] != predictions[1]:
            raise ValueError("rival returned inconsistent predictions")
        return predictions[0]

    results = {}
    query_reasons = [[] for _ in episode["test"]]
    for name, fn in sorted(rivals.items()):
        try:
            if not all(predict(fn, pair) == pair["output"] for pair in episode["train"]):
                results[name] = "refuted"
                continue
            disagreements = [index for index, query in enumerate(episode["test"])
                             if predict(fn, query) != query["output"]]
            results[name] = "ambiguous" if disagreements else "survived_all"
            for index in disagreements:
                query_reasons[index].append(f"{name} fits every demo but disagrees with query")
        except Exception as exc:
            results[name] = "error"
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    return declarations, results, errors, query_reasons


def lesson_check(module, episode: dict, request: dict) -> dict:
    """Declared hook/rival evidence on materialized pairs, not universal identifiability."""
    policy = request.get("demonstration_policy", {"automatic": False, "declared_minimum": None})
    reasons = []
    minimum = policy["declared_minimum"]
    if minimum is not None and len(episode["train"]) < minimum:
        reasons.append(f"below declared minimum: {len(episode['train'])} < {minimum}")
    hook = getattr(module, "lesson_identifiable", None)
    declared = hasattr(module, "lesson_identifiable")
    rival_declarations, rival_results, rival_errors, rival_findings = ([], {}, [], [])
    if any(hasattr(module, attr) for attr in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")):
        rival_declarations, rival_results, rival_errors, rival_findings = _lesson_rivals(module, episode)
    reasons.extend(rival_errors)
    queries = []
    if declared or rival_declarations:
        for index, query in enumerate(episode["test"]):
            demos, checked_query = deepcopy(episode["train"]), deepcopy(query)
            try:
                findings = hook(demos, checked_query) if declared else []
                if (not isinstance(findings, list) or any(not isinstance(item, str) for item in findings)):
                    raise ValueError("lesson_identifiable must return a list of reason strings")
                if demos != episode["train"] or checked_query != query:
                    raise ValueError("lesson_identifiable mutated its lesson")
            except Exception as exc:
                findings = [f"{type(exc).__name__}: {exc}"]
            if rival_findings:
                findings = findings + rival_findings[index]
            queries.append({"query_index": index, "reasons": findings})
            reasons.extend(f"query {index}: {item}" for item in findings)
    verdict = {"status": ("diagnostic_unsupported" if reasons else
                           "passed_declared_rivals" if rival_results and not declared else
                           "passed_declared_hook" if declared else "not_declared"),
               "hook_declared": declared, "queries": queries, "reasons": reasons,
               "rival_declarations": rival_declarations, "rivals": rival_results,
               "contract": ("hook_and_rivals" if declared and rival_results else
                            "rivals_only" if rival_results else
                            "hook_only" if declared else "none"),
               "scope": "declared checks on materialized demos and each labeled query"}
    if reasons and policy["automatic"]:
        raise ValueError("Automatic lesson unsupported: " + json.dumps(verdict))
    return verdict


def _apply(root: Path, request: dict, runner, is_well_formed) -> None:
    """Apply the selected reference rule to caller-supplied grids; one bridge, per-input errors."""
    task_id = request["task_id"]
    if request["reference"] == "archival":
        bundle = runner._load_bundle(task_id)
    else:
        module = importlib.import_module(request["runtime_generator"].replace("/", ".")[:-3])
        bundle = canonical_bundle(runner, task_id, module)
    results = []
    bridge = None
    try:
        for index, grid in enumerate(request["inputs"]):
            try:
                if bridge is None:
                    bridge, name = runner._open_bridge_with_rule(bundle.rule_callable_text)
                output = runner._apply_rule(bridge, name, grid)
                valid = is_well_formed(output)
                results.append({"index": index, "output": output if valid else None, "valid_output": valid,
                                "error": None if valid else "rule returned a value that is not a rectangular 0-9 grid"})
            except Exception as exc:
                results.append({"index": index, "output": None, "valid_output": False,
                                "error": f"{type(exc).__name__}: {exc}"[:2000]})
                # A timeout can kill/respawn the Racket child without its named
                # rule. Define the rule again on a fresh bridge for the next input.
                if bridge is not None:
                    with contextlib.suppress(Exception):
                        bridge.shutdown()
                    bridge = None
    finally:
        if bridge is not None:
            bridge.shutdown()
    if request.get("check_generator_domain"):
        # Run after authority application and on a copy: validator rejection,
        # mutation or exceptions must never suppress the authoritative result.
        module = bundle.generator_module if hasattr(bundle, "generator_module") else module
        checker = getattr(module, "self_check", None)
        for grid, result in zip(request["inputs"], results):
            domain = {"status": "not_declared", "errors": []}
            if callable(checker):
                try:
                    errors = checker(copy.deepcopy(grid))
                    if not isinstance(errors, (list, tuple)) or any(not isinstance(e, str) for e in errors):
                        raise TypeError("self_check must return list[str]")
                    domain = {"status": "invalid" if errors else "valid", "errors": list(errors)}
                except Exception as exc:
                    domain = {"status": "error", "errors": [f"{type(exc).__name__}: {exc}"[:2000]]}
            result["generator_domain"] = domain
    (root / "applied.json").write_text(json.dumps({
        "rule_task_id": bundle.rule_task_id, "rule_file": bundle.rule_file,
        "executed_rule_hash": hashlib.sha256(" ".join(bundle.rule_source.split()).encode()).hexdigest()[:12],
        "rule_text_sha256": hashlib.sha256(bundle.rule_callable_text.encode()).hexdigest(),
        "results": results}) + "\n")


def main() -> None:
    from puzzle_generators import runner
    from puzzle_generators.helpers.grid import is_well_formed

    root = Path(__file__).resolve().parent
    request = json.loads((root / "request.json").read_text())
    if request.get("mode") == "imports":
        imported, errors = 0, []
        for name in request["modules"]:
            try:
                importlib.import_module(name)
                imported += 1
            except Exception as exc:
                errors.append(f"{name}: {type(exc).__name__}: {exc}")
        (root / "imports.json").write_text(json.dumps({"imported": imported, "errors": errors}) + "\n")
        return
    if request.get("mode") == "apply":
        _apply(root, request, runner, is_well_formed)
        return
    if request.get("mode") == "legacy_compare":
        bundle = runner._load_bundle(request["task_id"])
        task = runner.run_one(request["task_id"], request["seed"], 0, bundle=bundle,
                              n_train=request["n_train"], n_test=request["n_test"],
                              difficulty=request["difficulty"])
        if any(len(task[split]) < request["n_" + split] for split in ("train", "test")):
            raise ValueError("Legacy generator produced fewer than requested pairs")
        result = {"train": task["train"][:request["n_train"]],
                  "test": task["test"][:request["n_test"]],
                  "rule_hash": hashlib.sha256(" ".join(bundle.rule_source.split()).encode()).hexdigest()[:12],
                  "rule_file": bundle.rule_file}
        (root / "legacy_result.json").write_text(json.dumps(result) + "\n")
        return
    tid, kind = request["task_id"], request["kind"]
    module_name = request["runtime_generator"].replace("/", ".")[:-3]
    module = importlib.import_module(module_name)
    episodes = []
    partial = (root / "episodes.partial.jsonl").open("a")
    shared = {"bundle": None, "bridge": None, "name": None}

    def keep(episode):
        # Each completed episode survives a later timeout or crash of this batch.
        episode["lesson_check"] = lesson_check(module, episode, request)
        episodes.append(episode)
        partial.write(json.dumps(episode) + "\n")
        partial.flush()
        os.fsync(partial.fileno())

    def rule_bridge():
        # One bridge per batch: the per-puzzle reference rule is the same for every
        # episode, and Racket startup costs ~2 s against ~1 ms per application.
        if shared["bridge"] is None:
            shared["bridge"], shared["name"] = runner._open_bridge_with_rule(shared["bundle"].rule_callable_text)
        return shared["bridge"], shared["name"]

    def drop_rule_bridge():
        # A failed or timed-out call may respawn the child without the rule
        # defined; never reuse a bridge after any application error.
        bridge, shared["bridge"] = shared["bridge"], None
        if bridge is not None:
            with contextlib.suppress(Exception):
                bridge.shutdown()

    try:
        _generate_episodes(request, module, runner, is_well_formed, keep, shared, rule_bridge, drop_rule_bridge)
    finally:
        drop_rule_bridge()
        partial.close()
    (root / "episodes.json").write_text(json.dumps(episodes) + "\n")


def _generate_episodes(request, module, runner, is_well_formed, keep, shared, rule_bridge, drop_rule_bridge):
    tid, kind = request["task_id"], request["kind"]
    for index in range(request.get("start_index", 0), request["count"]):
        seed = request["seed"] + index
        if kind == "generic":
            task = module.generate_task(seed, difficulty=request["difficulty"] or "medium")
            checker = getattr(module, "self_check_task", None)
            if callable(checker):
                checked = deepcopy(task)
                findings = checker(checked)
                if findings or checked != task:
                    raise ValueError(f"{tid}: generic self-check failed or mutated its task: {findings}")
            program = task.get("program") or getattr(module, "PROGRAM", None)
            if not isinstance(program, str) or not program.strip():
                raise ValueError(f"{tid}: no Racket program supplied by generic generator")
            # Some native generators emit an expression evaluated with `g`
            # bound, rather than the REPL's rule! form. Preserve those bytes
            # and explicitly record the equivalent executable rule form.
            emitted_program = program
            if not program.lstrip().startswith("(rule!"):
                program = f"(rule! {program}\n)"
                task["emitted_program"] = emitted_program
                task["program_normalization"] = "expression_to_rule"
            task["program"] = program
            bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(program))
            try:
                seen = set()
                for split in ("train", "test"):
                    if not task.get(split):
                        raise ValueError(f"{tid}: missing {split} pairs")
                    for pair in task[split]:
                        if not is_well_formed(pair.get("input")):
                            raise ValueError(f"{tid}: malformed input")
                        actual = runner._apply_rule(bridge, name, pair["input"])
                        if not is_well_formed(actual) or actual != pair.get("output"):
                            raise ValueError(f"{tid}: generated output disagrees with Racket program")
                        reason = runner._validate_pair(pair["input"], actual,
                                                       allow_identity_output=bool(getattr(module, "ALLOW_IDENTITY_OUTPUT", False)))
                        if reason:
                            raise ValueError(f"{tid}: generated pair failed {reason}")
                        digest = runner._content_hash({"input": pair["input"], "output": actual})
                        if digest in seen:
                            raise ValueError(f"{tid}: duplicate pair")
                        seen.add(digest)
                        pair["output"] = actual
                for split in ("train", "test"):
                    count = request["n_" + split]
                    if len(task[split]) < count:
                        raise ValueError(f"{tid}: native generator produced fewer than requested {split} pairs")
                    task[split] = task[split][:count]
                task.update({"task_id": tid, "seed": seed, "sample_index": request.get("sample_index", 0),
                             "generator_version": getattr(module, "VERSION", "?"), "rejections": [],
                             "executed_rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]})
                task["episode_index"] = index
                keep(task)
            finally:
                bridge.shutdown()
            continue

        # Archival execution is an explicit research choice, never a fallback
        # after canonical failure. The parent labels it unapproved.
        if shared["bundle"] is None:
            shared["bundle"] = (runner._load_bundle(tid) if request.get("reference") == "archival"
                                else canonical_bundle(runner, tid, module))
        bundle = shared["bundle"]
        wanted = request["n_train"] + request["n_test"]
        pairs, rejections, seen, accepted_indices = [], [], set(), []
        first_index = request.get("sample_index", 0)
        for sample_index in range(first_index, first_index + wanted * 5):
            try:
                generated = module.generate(seed=seed, sample_index=sample_index,
                                            difficulty=request["difficulty"], **request.get("overrides", {}))
                grid = generated.get("input") if isinstance(generated, dict) else generated
                if not is_well_formed(grid):
                    raise ValueError("malformed generated input")
                self_check = getattr(module, "self_check", None)
                if callable(self_check):
                    checked = deepcopy(grid)
                    signature = inspect.signature(self_check)
                    supports_difficulty = "difficulty" in signature.parameters or any(
                        p.kind == inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values())
                    kwargs = {"difficulty": request["difficulty"]} if supports_difficulty else {}
                    findings = self_check(checked, **kwargs)
                    if findings:
                        raise ValueError(f"self_check: {findings}")
                    if checked != grid:
                        raise ValueError("self_check mutated its input")
                bridge, name = rule_bridge()
                try:
                    output = runner._apply_rule(bridge, name, grid)
                except Exception:
                    drop_rule_bridge()
                    raise
                reason = runner._validate_pair(grid, output, allow_identity_output=bundle.allow_identity_output)
                if reason:
                    raise ValueError(reason)
                pair = {"input": grid, "output": output}
                digest = runner._content_hash(pair)
                if digest in seen:
                    raise ValueError("duplicate pair")
                seen.add(digest)
                pairs.append(pair)
                accepted_indices.append(sample_index)
            except Exception as exc:
                rejection = {"seed": seed, "sample_index": sample_index,
                             "error": type(exc).__name__, "reason": str(exc)}
                rejections.append(rejection)
                print(json.dumps({"rejection": rejection}), file=sys.stderr)
            if len(pairs) == wanted:
                break
        if len(pairs) != wanted:
            raise RuntimeError(f"{tid}: only {len(pairs)}/{wanted} pairs; {len(rejections)} recorded rejections")
        keep({"task_id": tid, "seed": seed, "episode_index": index,
              "generator_version": getattr(module, "VERSION", ""),
              "sample_index": first_index, "sample_indices": accepted_indices,
              "sampling": runner._sampling_metadata(pairs, accepted_indices, n_train=request['n_train'],
                                                     requested_start=first_index, rejections=rejections),
              "rule_task_id": bundle.rule_task_id, "rule_file": bundle.rule_file,
              "train": pairs[:request["n_train"]], "test": pairs[request["n_train"]:],
              "program": bundle.rule_source,
              "executed_rule_hash": hashlib.sha256(" ".join(bundle.rule_source.split()).encode()).hexdigest()[:12],
              "rule_source": bundle.rule_file, "rejections": rejections})


if __name__ == "__main__":
    with contextlib.redirect_stdout(sys.stderr):
        main()
