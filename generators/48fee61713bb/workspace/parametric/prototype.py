#!/usr/bin/env python3
"""Proposed, task-local stack-side parameterization; every label executes Racket."""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "48fee61713bb"
STACK_SIDES = ("toward_main", "toward_small")
DEFAULT_STACK_SIDE = "toward_main"
MAX_DEMOS = 32
MAX_QUERIES = 32
DEFAULT_MAX_ATTEMPTS = 256
CANONICAL_RULE_HASH = "88f9214cd87f"
OLD_CONDITION = "(if main-at-end (append p s m) (append m s p))"
NEW_CONDITION = "(if (not main-at-end) (append p s m) (append m s p))"


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


independent_output = _module("block_stack_independent_oracle", HERE / "oracle.py").independent_output


def stable_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def generator():
    return _module("block_stack_canonical_generator", ROOT / "generators" / TASK_ID / "generator.py")


@lru_cache(maxsize=1)
def canonical_rows():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        return tuple(row for line in handle if (row := json.loads(line)).get("task_id") == TASK_ID)


@lru_cache(maxsize=2)
def rule_text(stack_side):
    _side(stack_side)
    programs = {row["program_solution"] for row in canonical_rows()}
    if len(programs) != 1:
        raise ValueError("exactly one canonical rule authority is required")
    canonical = next(iter(programs))
    short_hash = text_digest(" ".join(canonical.split()))[:12]
    if short_hash != CANONICAL_RULE_HASH:
        raise ValueError("canonical rule authority changed; review the prototype")
    if canonical.count(OLD_CONDITION) != 1:
        raise ValueError("canonical stack condition must occur exactly once")
    expected = canonical if stack_side == DEFAULT_STACK_SIDE else canonical.replace(OLD_CONDITION, NEW_CONDITION)
    materialized = (HERE / "rules" / (stack_side + ".rkt")).read_text(encoding="utf-8")
    if materialized != expected:
        raise ValueError("materialized rule differs from its declared canonical derivation")
    return materialized


def _side(value):
    if value not in STACK_SIDES:
        raise ValueError("stack_side must be toward_main or toward_small")
    return value


def _integer(name, value, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(name + " must be a literal integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def choose_setting(seed):
    _integer("seed", seed, 0, 2**63-1)
    bit = hashlib.sha256(("stack-side-v1:" + str(seed)).encode()).digest()[0] & 1
    return STACK_SIDES[bit]


def source_identity():
    sources = [
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "shared/data/canonical/puzzles.jsonl",
        HERE / "prototype.py", HERE / "oracle.py", HERE / "README.md",
        HERE / "rules/toward_main.rkt", HERE / "rules/toward_small.rkt",
        ROOT / "generators" / TASK_ID / "tests/test_parametric_block_stack.py",
    ]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}


class RuleEngine:
    """Own one actual Racket bridge; apply self-contained rules atomically."""
    def __init__(self):
        self.bridge = RacketBridge(timeout=10.0)
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *error):
        self.bridge.shutdown()
        return False

    def apply(self, grid, stack_side):
        _side(stack_side)
        errors = generator().self_check(grid)
        if errors:
            raise ValueError("input outside prototype domain: " + "; ".join(errors))
        source = rule_text(stack_side)
        # These source-bound rules are simple lambda bodies: no shorthand,
        # dictionary literals, or free h/w bindings need the broad compiler.
        callable_source = strip_rule_wrapper(strip_line_comments(source))
        if not callable_source.lstrip().startswith("(lambda"):
            raise ValueError("prototype only supports its exact lambda rules")
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        output = self.bridge.eval_text(f"({callable_source} {literal})")
        if (not isinstance(output, list) or not output or not output[0] or
                any(not isinstance(row, list) or len(row) != len(output[0]) for row in output) or
                any(isinstance(cell, bool) or not isinstance(cell, int) or not 0 <= cell <= 9
                    for row in output for cell in row)):
            raise ValueError("Racket returned an invalid output grid")
        self.executions.append({
            "call_index": len(self.executions), "stack_side": stack_side,
            "input_sha256": digest(grid), "output_sha256": digest(output),
            "program_sha256": text_digest(source),
        })
        return output


def identify_query(demonstrations, query_input, *, engine):
    """Fit settings on demos ONLY; query answers and selected setting are absent."""
    rivals = []
    consistent = []
    predictions = {}
    for side in STACK_SIDES:
        mismatches = [index for index, pair in enumerate(demonstrations)
                      if engine.apply(pair["input"], side) != pair["output"]]
        if not mismatches:
            consistent.append(side)
        rivals.append({"stack_side": side, "fits_demonstrations": not mismatches,
                       "mismatching_demo_indices": mismatches})
    # Complete the demonstration fit before evaluating either query prediction.
    for rival in rivals:
        predicted = engine.apply(query_input, rival["stack_side"])
        predictions[rival["stack_side"]] = digest(predicted)
        rival["query_prediction_sha256"] = digest(predicted)
    possible = {predictions[side] for side in consistent}
    identified = len(possible) == 1
    return {
        "status": "identified_within_declared_rivals" if identified else "ambiguous_within_declared_rivals",
        "query_input_sha256": digest(query_input),
        "consistent_settings": consistent,
        "determined_output_sha256": next(iter(possible)) if identified else None,
        "query_answer_used_for_demo_fit": False,
        "rivals": rivals,
    }


def _checked_label(engine, grid, side, split, index):
    output = engine.apply(grid, side)
    if output != independent_output(grid, side):
        raise ValueError(f"independent component oracle disagrees at {split}[{index}]")
    evidence = dict(engine.executions[-1], split=split, index=index,
                    independent_component_oracle_match=True)
    evidence.pop("call_index")
    return {"input": copy.deepcopy(grid), "output": output}, evidence


def generate_episode(seed, *, stack_side=None, demos=3, queries=4,
                     max_attempts=DEFAULT_MAX_ATTEMPTS, engine=None):
    _integer("seed", seed, 0, 2**63-1)
    _integer("demos", demos, 1, MAX_DEMOS)
    _integer("queries", queries, 1, MAX_QUERIES)
    _integer("max_attempts", max_attempts, 1, 10000)
    selected = choose_setting(seed) if stack_side is None else _side(stack_side)
    inputs, indices, rejected, seen = [], [], [], set()
    for attempt in range(max_attempts):
        grid = generator().generate(seed, attempt)
        errors = generator().self_check(grid)
        key = digest(grid)
        if errors or key in seen:
            rejected.append({"sample_index": attempt, "reasons": errors or ["duplicate input"]})
            continue
        inputs.append(grid)
        indices.append(attempt)
        seen.add(key)
        if len(inputs) == demos + queries:
            break
    if len(inputs) != demos + queries:
        raise RuntimeError(f"sampling budget exhausted: accepted {len(inputs)} distinct inputs of {demos+queries} requested after {max_attempts} attempts")
    if engine is None:
        with RuleEngine() as active:
            return _episode(seed, selected, demos, queries, max_attempts, inputs, indices, rejected, active)
    return _episode(seed, selected, demos, queries, max_attempts, inputs, indices, rejected, engine)


def _episode(seed, side, demos, queries, max_attempts, inputs, indices, rejected, engine):
    train, test, checks, reports = [], [], [], []
    for index, grid in enumerate(inputs[:demos]):
        pair, check = _checked_label(engine, grid, side, "train", index)
        train.append(pair)
        checks.append(check)
    for index, grid in enumerate(inputs[demos:]):
        report = identify_query(train, grid, engine=engine)
        if report["status"] != "identified_within_declared_rivals" or report["consistent_settings"] != [side]:
            raise RuntimeError("demonstrations do not identify the fixed episode setting")
        pair, check = _checked_label(engine, grid, side, "test", index)
        if report["determined_output_sha256"] != digest(pair["output"]):
            raise ValueError("demonstration-derived prediction disagrees with Racket label")
        test.append(pair)
        checks.append(check)
        reports.append(dict(report, query_index=index))
    return {
        "schema": "block-stack-parametric-prototype-v1", "status": "proposed",
        "task_id": TASK_ID, "seed": seed, "stack_side": side,
        "demo_count": demos, "query_count": queries,
        "max_attempts": max_attempts, "accepted_sample_indices": indices,
        "rejected_draws": rejected, "train": train, "test": test,
        "program_solution": rule_text(side), "program_sha256": text_digest(rule_text(side)),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "source_sha256": source_identity(), "label_checks": checks,
        "query_identification": reports,
    }


def public_payload(episode):
    """Construct exactly the visible payload, ignoring private metadata."""
    return {
        "train": [{"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
                  for pair in episode["train"]],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_id(episode):
    return digest(public_payload(episode))


def write_public_challenge(destination, episode):
    """Export only visible content; hash exactly the bytes in the file."""
    visible = public_payload(episode)
    name = hashlib.sha256(stable_bytes(visible)).hexdigest()
    path = Path(destination) / "public" / (name + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = stable_bytes(visible)
    if path.exists() and path.read_bytes() != payload:
        raise ValueError("visible-content hash collision or existing file corruption")
    path.write_bytes(payload)
    return path


def _validate_episode(episode, *, engine):
    """Re-execute every label without writing any output."""
    side = _side(episode["stack_side"])
    if episode["source_sha256"] != source_identity():
        raise ValueError("source identity changed; regenerate the episode")
    if episode["program_solution"] != rule_text(side) or episode["program_sha256"] != text_digest(rule_text(side)):
        raise ValueError("episode rule provenance disagrees with materialized Racket")
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            actual = engine.apply(pair["input"], side)
            if actual != pair["output"] or actual != independent_output(pair["input"], side):
                raise ValueError(f"label mismatch at {split}[{index}]")


def _write_validated_episode(destination, episode):
    """Write one episode after a caller has completed label validation."""
    side = _side(episode["stack_side"])
    public_path = write_public_challenge(destination, episode)
    private_path = Path(destination) / "private/episodes" / public_path.name
    private_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_text(json.dumps(episode, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    rule_path = Path(destination) / "private/rules" / (text_digest(rule_text(side)) + ".rkt")
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    rule_path.write_text(rule_text(side), encoding="utf-8")
    return {"public_path": str(public_path), "private_path": str(private_path), "rule_path": str(rule_path)}


def write_episodes(destination, episodes, *, engine=None):
    """Validate a batch, reject visible duplicates, then write by public ID."""
    projected = []
    seen = {}
    for episode in episodes:
        payload = stable_bytes(public_payload(episode))
        identifier = hashlib.sha256(payload).hexdigest()
        previous = seen.get(identifier)
        if previous is not None:
            if previous == payload:
                raise ValueError("duplicate visible payload in episode batch")
            raise ValueError("visible-content hash collision in episode batch")
        seen[identifier] = payload
        projected.append((identifier, episode))
    projected.sort(key=lambda item: item[0])
    if engine is None:
        with RuleEngine() as active:
            return write_episodes(destination, [episode for _, episode in projected], engine=active)
    for _, episode in projected:
        _validate_episode(episode, engine=engine)
    written = []
    for identifier, episode in projected:
        saved = _write_validated_episode(destination, episode)
        written.append(dict(saved, public_id=identifier))
    return written


def write_episode(destination, episode, *, engine=None):
    """Re-execute every label before public and separate private writes."""
    saved = write_episodes(destination, [episode], engine=engine)[0]
    return {key: saved[key] for key in ("public_path", "private_path", "rule_path")}


def _reflect_short_axis(output):
    return [list(reversed(row)) for row in output] if len(output) == 7 else list(reversed(output))


def retain_evidence(destination, *, seed, sides, demos, queries, max_attempts):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with RuleEngine() as engine:
        episodes = []
        for side in sides:
            episode = generate_episode(seed, stack_side=side, demos=demos, queries=queries,
                                       max_attempts=max_attempts, engine=engine)
            episodes.append(episode)
        written = write_episodes(destination, episodes, engine=engine)
        paths_by_public_id = {saved["public_id"]: saved for saved in written}
        canonical_checks = []
        for row in canonical_rows():
            for split in ("train", "test"):
                for index, pair in enumerate(row[split]):
                    for side in STACK_SIDES:
                        actual = engine.apply(pair["input"], side)
                        expected = pair["output"] if side == "toward_main" else _reflect_short_axis(pair["output"])
                        if actual != expected or actual != independent_output(pair["input"], side):
                            raise ValueError("canonical parity failure")
                        canonical_checks.append(dict(engine.executions[-1], source=row["source"],
                                                     split=split, index=index, passed=True))
        generated_checks = []
        for probe_seed in (0, 17, 41, 2026):
            for sample_index in range(4):
                grid = generator().generate(probe_seed, sample_index)
                main = engine.apply(grid, "toward_main")
                if main != generator().rule_mirror(grid) or main != independent_output(grid, "toward_main"):
                    raise ValueError("generated canonical parity failure")
                generated_checks.append(dict(engine.executions[-1], seed=probe_seed,
                                             sample_index=sample_index, passed=True))
                other = engine.apply(grid, "toward_small")
                if other != _reflect_short_axis(main) or other != independent_output(grid, "toward_small"):
                    raise ValueError("generated alternate parity failure")
                generated_checks.append(dict(engine.executions[-1], seed=probe_seed,
                                             sample_index=sample_index, passed=True))
        witness_input = canonical_rows()[0]["train"][0]["input"]
        witness = {"input": witness_input, "outputs": {side: engine.apply(witness_input, side) for side in STACK_SIDES}}
        if witness["outputs"]["toward_main"] == witness["outputs"]["toward_small"]:
            raise ValueError("parameter witness does not change behavior")
        witness["input_sha256"] = digest(witness_input)
        witness["program_sha256"] = {side: text_digest(rule_text(side)) for side in STACK_SIDES}
        (destination / "private/parameter-witness.json").write_text(json.dumps(witness, indent=2) + "\n")
        report = {
            "schema": "block-stack-parametric-evidence-v1", "status": "proposed",
            "parameter": {"name": "stack_side", "values": list(STACK_SIDES), "canonical_default": DEFAULT_STACK_SIDE,
                          "auto_choice": "SHA-256 of stack-side-v1:seed, low bit of first byte, once per episode"},
            "seed": seed, "demo_count": demos, "query_count": queries,
            "source_sha256": source_identity(),
            "rule_sha256": {side: text_digest(rule_text(side)) for side in STACK_SIDES},
            "canonical_normalized_rule_hash": CANONICAL_RULE_HASH,
            "public_write_order": [saved["public_id"] for saved in written],
            "episodes": [{"stack_side": episode["stack_side"], "public_id": public_id(episode),
                          "paths": {key: str(Path(value).relative_to(destination))
                                    for key, value in paths_by_public_id[public_id(episode)].items()
                                    if key != "public_id"},
                          "accepted_sample_indices": episode["accepted_sample_indices"],
                          "rejected_draws": episode["rejected_draws"],
                          "distinct_input_count": len({digest(pair["input"]) for pair in episode["train"] + episode["test"]}),
                          "label_count": len(episode["label_checks"]),
                          "query_identification": episode["query_identification"]}
                         for episode in episodes],
            "canonical_checks": canonical_checks, "generated_checks": generated_checks,
            "label_counts": {"canonical_occurrences_both_settings": len(canonical_checks),
                             "generated_parity_both_settings": len(generated_checks),
                             "episode_labels": sum(len(episode["label_checks"]) for episode in episodes),
                             "writer_label_rechecks": sum(len(episode["label_checks"]) for episode in episodes),
                             "parameter_witness_labels": 2},
            "racket_execution_count": len(engine.executions),
            "limits": [
                "Proposed task-local extension; no production API, approval, or training admission change.",
                "Exactly 30x30 inputs from the unchanged canonical generator's finite ring-pattern bank.",
                "Allowed counts are 1..32 demos and 1..32 queries; defaults are 3 and 4.",
                "Sampling is bounded and fails explicitly rather than cloning or shortening the requested episode.",
                "Identification is only against the two declared stack-side settings; no completeness claim.",
                "The blue marker is retained in lawful inputs but is not a causal input to the executed placement condition.",
                "Canonical Racket comments are preserved verbatim even where they inaccurately describe marker causality.",
                "Evidence covers the recorded seeds and inputs, not every scene or possible episode.",
            ],
        }
        (destination / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        (destination / "private/racket-executions.json").write_text(json.dumps(engine.executions, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--stack-side", choices=("auto", "both") + STACK_SIDES, default="auto")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--out", type=Path, default=Path("../checks/parametric"))
    args = parser.parse_args()
    sides = STACK_SIDES if args.stack_side == "both" else (
        choose_setting(args.seed) if args.stack_side == "auto" else args.stack_side,)
    report = retain_evidence(args.out, seed=args.seed, sides=sides, demos=args.demos,
                             queries=args.queries, max_attempts=args.max_attempts)
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "demos_each": args.demos, "queries_each": args.queries,
                      "racket_executions": report["racket_execution_count"],
                      "summary": str(args.out / "summary.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
