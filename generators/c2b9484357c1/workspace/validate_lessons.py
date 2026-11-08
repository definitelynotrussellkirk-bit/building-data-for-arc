"""Fail-closed semantic gate for *emitted* ARC episode JSONL, not synthetic lessons.

Run after reference-verified generation and before stripping private query labels.
This checks the generator's lesson hook on every actual query, binds its source
hash, and checks named competitors separately when available. It does not grant
approval, prove an unknown rule, or replace Racket label verification.

Exit codes: 0 = every episode passed; 1 = semantic/provenance/grid failure;
2 = missing contracts, malformed JSON/envelopes, or infrastructure failure.
Only inspect and load trusted local generator implementations.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
from typing import Any


def _grid(value: Any) -> bool:
    return (isinstance(value, list) and 0 < len(value) <= 30
            and isinstance(value[0], list) and 0 < len(value[0]) <= 30
            and all(isinstance(row, list) and len(row) == len(value[0])
                    and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
                    for row in value))


def assess_episode(episode: dict, module: Any, expected_generator_sha256: str) -> dict:
    """Evaluate actual demos/queries without mutating their caller-owned grids."""
    result = {"status": "fail", "task_id": None, "seed": None, "findings": [],
              "queries_checked": 0, "declared_examples_needed": None}
    findings = result["findings"]
    if not isinstance(episode, dict):
        findings.append("episode must be an object")
        return result
    result.update(task_id=episode.get("task_id"), seed=episode.get("seed"),
                  declared_examples_needed=getattr(module, "EXAMPLES_NEEDED", None))
    expected_id = getattr(module, "GENERATOR_ID", getattr(module, "TASK_ID", None))
    if expected_id and episode.get("task_id") != expected_id:
        findings.append("episode task_id does not match the loaded generator")
    provenance = episode.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    if provenance.get("generator_sha256") != expected_generator_sha256:
        findings.append("missing or mismatched provenance.generator_sha256")
    expected_rule = getattr(module, "RULE_HASH", None)
    if expected_rule and provenance.get("rule_hash") != expected_rule:
        findings.append("missing or mismatched provenance.rule_hash")
    for split in ("train", "test"):
        pairs = episode.get(split)
        if not isinstance(pairs, list) or not pairs:
            findings.append(f"{split} must contain labeled pairs")
            continue
        for index, pair in enumerate(pairs):
            if (not isinstance(pair, dict) or not _grid(pair.get("input"))
                    or not _grid(pair.get("output"))):
                findings.append(f"{split}[{index}] has missing or invalid input/output grid")
    if findings:
        return result
    hook = getattr(module, "lesson_identifiable", None)
    if not callable(hook):
        result["status"] = "no_contract"
        findings.append("no callable lesson_identifiable contract; not a semantic pass")
        return result
    competitors = getattr(module, "LESSON_COMPETITORS", {})
    if not isinstance(competitors, dict):
        findings.append("LESSON_COMPETITORS must be a name-to-callable dictionary")
        return result
    for qi, query in enumerate(episode["test"]):
        demos_copy = deepcopy(episode["train"])
        query_copy = deepcopy(query)
        try:
            reasons = hook(demos_copy, query_copy)
            if not isinstance(reasons, list) or any(not isinstance(r, str) for r in reasons):
                findings.append(f"query {qi}: lesson_identifiable returned an invalid result")
            else:
                findings.extend(f"query {qi}: {r}" for r in reasons)
        except Exception as exc:
            findings.append(f"query {qi}: hook raised {type(exc).__name__}: {exc}")
        if demos_copy != episode["train"] or query_copy != query:
            findings.append(f"query {qi}: lesson_identifiable mutated its input")
        for name, rival in sorted(competitors.items()):
            try:
                fits = True
                for demo in episode["train"]:
                    copied = deepcopy(demo["input"])
                    predicted = rival(copied)
                    if copied != demo["input"]:
                        raise ValueError("competitor mutated its input")
                    if not _grid(predicted):
                        raise ValueError("competitor returned a malformed grid")
                    if predicted != demo["output"]:
                        fits = False
                        break
                if fits:
                    copied = deepcopy(query["input"])
                    predicted = rival(copied)
                    if copied != query["input"]:
                        raise ValueError("competitor mutated its query")
                    if not _grid(predicted):
                        raise ValueError("competitor returned a malformed query grid")
                    if predicted != query["output"]:
                        message = f"query {qi}: competitor {name!r} fits every demo but gives a different query answer"
                        if message not in findings:
                            findings.append(message)
            except Exception as exc:
                findings.append(f"query {qi}: competitor {name!r} raised {type(exc).__name__}: {exc}")
        result["queries_checked"] += 1
    result["status"] = "fail" if findings else "pass"
    return result


def load_generator(library: Path, task_id: str):
    """Load from this explicit library, never from a sibling/predecessor checkout."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", task_id):
        raise ValueError(f"invalid task ID: {task_id!r}")
    source = library / "generators" / task_id / "generator.py"
    if not source.is_file():
        raise FileNotFoundError(f"generator not found: {source}")
    library = library.resolve()
    runtime = library / "shared/runtime/puzzle_generators"
    sys.path.insert(0, str(runtime.parent))
    root_package = importlib.import_module("puzzle_generators")
    package = importlib.import_module("puzzle_generators.per_puzzle")
    for loaded, expected in (
        (root_package, runtime / "__init__.py"),
        (package, runtime / "per_puzzle/__init__.py"),
    ):
        if Path(getattr(loaded, "__file__", "")).resolve() != expected.resolve():
            raise ValueError("runtime package already loaded from another library")
    package.__path__.append(str(library / "generators"))
    name = f"puzzle_generators.per_puzzle.{task_id}.generator"
    # Do not silently reuse a same-named module loaded from another library.
    if name in sys.modules and Path(sys.modules[name].__file__).resolve() != source.resolve():
        raise ValueError(f"module {name} already loaded from another source")
    module = importlib.import_module(name)
    if Path(getattr(module, "__file__", "")).resolve() != source.resolve():
        raise ValueError(f"module {name} resolved outside the requested library")
    return module, hashlib.sha256(source.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True, help="Private labeled episode JSONL")
    parser.add_argument("--out", type=Path, required=True, help="New JSON receipt path")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"refusing to overwrite evidence: {args.out}")
    results, sources = [], {}
    try:
        for line_no, line in enumerate(args.episodes.read_text().splitlines(), 1):
            if not line.strip():
                continue
            item = json.loads(line)
            tid = item.get("task_id") if isinstance(item, dict) else None
            if not isinstance(tid, str):
                raise ValueError(f"line {line_no}: task_id missing")
            if tid not in sources:
                sources[tid] = load_generator(args.library.resolve(), tid)
            module, digest = sources[tid]
            result = assess_episode(item, module, digest)
            results.append({"line": line_no, **result})
        if not results:
            raise ValueError("empty episode file is not a passing dataset")
        status = ("fail" if any(r["status"] == "fail" for r in results) else
                  "no_contract" if any(r["status"] != "pass" for r in results) else "pass")
        exit_code = {"pass": 0, "fail": 1, "no_contract": 2}[status]
        report = {"schema": "arcpuzzles-emitted-lesson-gate-v1", "status": status,
                  "episode_file_sha256": hashlib.sha256(args.episodes.read_bytes()).hexdigest(),
                  "generator_sha256": {tid: digest for tid, (_, digest) in sources.items()},
                  "episodes": results, "exit_code": exit_code}
    except Exception as exc:
        exit_code = 2
        report = {"schema": "arcpuzzles-emitted-lesson-gate-v1", "status": "error",
                  "error": f"{type(exc).__name__}: {exc}", "episodes": results,
                  "exit_code": exit_code}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "episodes": len(results), "report": str(args.out)}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
