"""Source-bound research export and fail-closed validation of actual JSONL lessons.

This task-local prototype uses the library's existing canonical Racket runner,
not Python-generated labels. The audit/export paths can be reused for another
per-puzzle generator with RULE_HASH, SEMANTIC_RIVALS and lesson_identifiable.
The census path deliberately measures this task's two-panel Boolean branches.

Run via the packet's run_with_racket.py, or set RACKET_PATH to a real runtime.
Use --help for exact commands. No shared exporter behavior or approval is changed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

DEFAULT_TASK = "27080597d778"
DEFAULT_LIBRARY = Path(__file__).resolve().parents[3]
SCHEMA = "arcpuzzles-actual-lesson-gate-v1"


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule_digest(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def load_subject(library: Path, task_id: str, source: Path | None = None):
    library = library.resolve()
    if not task_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in task_id):
        raise ValueError("invalid task ID")
    source = (source or library / "generators" / task_id / "generator.py").resolve()
    sys.path.insert(0, str(library / "shared/runtime"))
    sys.path.insert(0, str(library / "src"))
    # The packaged public runtime maps shared/tools to the legacy scripts/
    # namespace. Reuse those exact modules for the runner's syntax normalizer
    # without copying a runtime or relying on the process working directory.
    tools = str(library / "shared/tools")
    scripts = sys.modules.get("scripts")
    if scripts is None:
        scripts = ModuleType("scripts")
        scripts.__path__ = [tools]
        sys.modules["scripts"] = scripts
    elif tools not in getattr(scripts, "__path__", ()):
        raise ValueError("scripts namespace belongs to another runtime; use a fresh process")
    spec = importlib.util.spec_from_file_location("lesson_subject_" + sha_file(source)[:16], source)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "TASK_ID", None) != task_id:
        raise ValueError("generator TASK_ID mismatch")
    rule_task = getattr(module, "RULE_TASK_ID", task_id)
    with (library / "shared/data/canonical/puzzles.jsonl").open() as handle:
        rows = [row for line in handle if (row := json.loads(line)).get("task_id") == rule_task]
    if len(rows) != 1 or not isinstance(rows[0].get("program_solution"), str):
        raise ValueError("missing or ambiguous canonical authority")
    return module, rows[0]


@contextmanager
def reference_for(program: str):
    from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule, wrap_rule
    bridge, name = _open_bridge_with_rule(wrap_rule(program))
    try:
        yield lambda grid: _apply_rule(bridge, name, grid)
    finally:
        bridge.shutdown()


def _integer_grid(grid) -> bool:
    return (isinstance(grid, list) and bool(grid) and isinstance(grid[0], list)
            and 0 < len(grid) <= 30 and 0 < len(grid[0]) <= 30
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(v) is int and 0 <= v <= 9 for v in row) for row in grid))


def audit_episode(episode, module, reference, *, rule_hash: str) -> dict[str, Any]:
    """Audit ALL final queries and labels; a missing contract is an error.

    `reference` is injected for unit tests. CLI callers always supply a persistent
    canonical Racket function. Rival survival is independently checked even when
    a task's lesson hook incorrectly returns an empty error list.
    """
    result: dict[str, Any] = {"passed": False, "errors": [], "queries": [], "reference_pairs_checked": 0}
    errors = result["errors"]
    hook = getattr(module, "lesson_identifiable", None)
    rivals = getattr(module, "SEMANTIC_RIVALS", None)
    if (not callable(hook) or not isinstance(rivals, dict) or not rivals
            or not all(isinstance(k, str) and callable(v) for k, v in rivals.items())
            or not callable(getattr(module, "self_check", None))):
        errors.append("missing/invalid semantic contract: self_check, lesson_identifiable and nonempty SEMANTIC_RIVALS required")
        return result
    if not callable(reference):
        errors.append("canonical reference executor is required")
        return result
    if not isinstance(episode, dict):
        errors.append("episode must be an object")
        return result
    if episode.get("task_id") != getattr(module, "TASK_ID", None):
        errors.append("episode task_id does not match source")
    if episode.get("rule_task_id") != getattr(module, "RULE_TASK_ID", module.TASK_ID):
        errors.append("episode rule_task_id does not match source")
    if getattr(module, "RULE_HASH", None) != rule_hash or episode.get("executed_rule_hash") != rule_hash:
        errors.append("rule hash mismatch or missing rule pin")
    program = episode.get("program")
    if not isinstance(program, str) or rule_digest(program) != rule_hash:
        errors.append("private program is missing or differs from canonical rule")
    provenance = episode.get("provenance")
    source_file = getattr(module, "__file__", None)
    if (not isinstance(provenance, dict) or not source_file
            or provenance.get("generator_sha256") != sha_file(Path(source_file))):
        errors.append("generator source hash missing or stale")
    train, queries = episode.get("train"), episode.get("test")
    if not isinstance(train, list) or not train or not isinstance(queries, list) or not queries:
        errors.append("nonempty train and test lists are required")
        return result
    indices = episode.get("sample_indices")
    if indices is not None and (not isinstance(indices, list) or len(indices) != len(train) + len(queries)
                                or any(type(i) is not int or i < 0 for i in indices)
                                or len(set(indices)) != len(indices)):
        errors.append("sample_indices do not match the materialized pair ordering")
    valid: dict[tuple[str, int], bool] = {}
    seen = set()
    for split, pairs in (("train", train), ("test", queries)):
        for index, pair in enumerate(pairs):
            name = f"{split}[{index}]"
            good = isinstance(pair, dict) and _integer_grid(pair.get("input")) and _integer_grid(pair.get("output"))
            valid[split, index] = good
            if not good:
                errors.append(f"{name}: missing/malformed integer input or output grid")
                continue
            digest = json.dumps(pair["input"], separators=(",", ":"))
            if digest in seen:
                errors.append(f"{name}: duplicate input leaks a demonstrated/query answer")
            seen.add(digest)
            try:
                candidate = deepcopy(pair["input"])
                findings = module.self_check(candidate)
                if not isinstance(findings, list) or findings:
                    errors.append(f"{name}: input grammar rejected: {findings}")
                    valid[split, index] = False
                if candidate != pair["input"]:
                    errors.append(f"{name}: self_check mutated input")
                    valid[split, index] = False
                if not valid[split, index]:
                    continue
                candidate = deepcopy(pair["input"])
                official = reference(candidate)
                result["reference_pairs_checked"] += 1
                if candidate != pair["input"]:
                    errors.append(f"{name}: reference executor mutated input")
                if not _integer_grid(official) or official != pair["output"]:
                    errors.append(f"{name}: stored output differs from canonical Racket")
            except Exception as exc:
                errors.append(f"{name}: reference/grammar failure: {type(exc).__name__}: {exc}")
    demos_valid = all(valid["train", i] for i in range(len(train)))
    # Rival errors are failures of the declared contract, NOT evidence that a
    # rival was eliminated. Keep inputs isolated from every task-supplied hook.
    survivors = {}
    if demos_valid:
        for name, solver in rivals.items():
            try:
                predictions = []
                for demo in train:
                    grid = deepcopy(demo["input"])
                    predicted = solver(grid)
                    if not _integer_grid(predicted):
                        raise ValueError("rival returned an invalid integer grid")
                    predictions.append(predicted)
                    if grid != demo["input"]:
                        raise ValueError("rival mutated input")
                if all(pred == demo["output"] for pred, demo in zip(predictions, train)):
                    survivors[name] = solver
            except Exception as exc:
                errors.append(f"rival {name}: {type(exc).__name__}: {exc}")
    for index, query in enumerate(queries):
        entry = {"index": index, "passed": False, "errors": [], "conflicting_rivals": []}
        if not demos_valid or not valid["test", index]:
            entry["errors"].append("cannot evaluate malformed demonstration/query")
        else:
            try:
                demos_copy, query_copy = deepcopy(train), deepcopy(query)
                findings = hook(demos_copy, query_copy)
                if demos_copy != train or query_copy != query:
                    entry["errors"].append("lesson hook mutated its arguments")
                if not isinstance(findings, list) or any(not isinstance(e, str) for e in findings):
                    entry["errors"].append("lesson hook returned an invalid contract value")
                else:
                    entry["errors"].extend(findings)
                for name, solver in survivors.items():
                    grid = deepcopy(query["input"])
                    predicted = solver(grid)
                    if not _integer_grid(predicted):
                        raise ValueError(f"rival {name} returned an invalid integer grid")
                    if grid != query["input"]:
                        raise ValueError(f"rival {name} mutated query input")
                    if predicted != query["output"]:
                        entry["conflicting_rivals"].append(name)
                        entry["errors"].append(f"rival {name} fits every demo but contradicts query {index}")
            except Exception as exc:
                entry["errors"].append(f"semantic contract failed: {type(exc).__name__}: {exc}")
        entry["passed"] = not entry["errors"]
        result["queries"].append(entry)
    result["passed"] = not errors and all(q["passed"] for q in result["queries"])
    return result


def shuffle_demos(episode: dict[str, Any]) -> dict[str, Any]:
    from puzzle_generators.base import stable_rng
    result = deepcopy(episode)
    permutation = list(range(len(result["train"])))
    stable_rng(result["seed"], f"{result['task_id']}:final-demo-order", SCHEMA).shuffle(permutation)
    result["train"] = [result["train"][i] for i in permutation]
    indices = result.get("sample_indices")
    if isinstance(indices, list):
        result["sample_indices"] = [indices[i] for i in permutation] + indices[len(permutation):]
    result["lesson_gate"] = {"schema": SCHEMA, "demo_permutation": permutation}
    return result


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])} for p in episode["train"]],
            "test": [{"input": deepcopy(p["input"])} for p in episode["test"]]}


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_jsonl(path: Path, rows) -> None:
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def source_receipt(module, row: dict, library: Path) -> dict[str, str]:
    return {"task_id": module.TASK_ID, "generator_sha256": sha_file(Path(module.__file__)),
            "canonical_rule_hash": rule_digest(row["program_solution"]),
            "canonical_file_sha256": sha_file(library / "shared/data/canonical/puzzles.jsonl"),
            "gate_sha256": sha_file(Path(__file__))}


def _audit_file(args, module, row, reference):
    results = []
    with args.episodes.open() as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                result = audit_episode(json.loads(line), module, reference, rule_hash=rule_digest(row["program_solution"]))
            except Exception as exc:
                result = {"passed": False, "errors": [f"{type(exc).__name__}: {exc}"], "queries": []}
            results.append({"line": number, **result})
    report = {"schema": SCHEMA, "source": source_receipt(module, row, args.library),
              "input_sha256": sha_file(args.episodes), "episodes": results,
              "passed": bool(results) and all(r["passed"] for r in results)}
    if not results:
        report["errors"] = ["input JSONL contained no episodes"]
    _write_json(args.report, report)
    return report


def _build(args, module, row, reference):
    from arcpuzzles import Catalog
    if args.out.exists():
        raise FileExistsError(args.out)
    source = source_receipt(module, row, args.library)
    catalog = Catalog(args.library)
    episodes = catalog.generate(args.task_id, count=args.count, seed=args.seed,
                                n_train=getattr(module, "EXAMPLES_NEEDED", 4), n_test=args.queries,
                                difficulty=args.difficulty, allow_unapproved=args.allow_unapproved,
                                timeout=args.timeout)
    episodes = [shuffle_demos(episode) for episode in episodes]
    results = [audit_episode(episode, module, reference, rule_hash=source["canonical_rule_hash"]) for episode in episodes]
    report = {"schema": SCHEMA, "source": source, "episodes": results,
              "passed": bool(results) and all(r["passed"] for r in results),
              "scope": "research examples; no approval or measured model-training improvement"}
    if not report["passed"]:
        # Keep failures and the actual materialized lessons; no challenge file
        # is emitted and there is no success manifest to mistake for admission.
        args.out.mkdir(parents=True)
        _write_json(args.out / "rejections.json", report)
        _write_jsonl(args.out / "episodes.rejected.private.jsonl", episodes)
        return report
    if source != source_receipt(module, row, args.library):
        raise ValueError("source changed during export")
    args.out.mkdir(parents=True)
    _write_jsonl(args.out / "episodes.private.jsonl", episodes)
    _write_jsonl(args.out / "challenges.jsonl", [public_challenge(e) for e in episodes])
    _write_jsonl(args.out / "labels.private.jsonl", [{"test": [{"output": p["output"]} for p in e["test"]]} for e in episodes])
    _write_json(args.out / "validation.json", report)
    files = ["episodes.private.jsonl", "challenges.jsonl", "labels.private.jsonl", "validation.json"]
    _write_json(args.out / "manifest.json", {"schema": SCHEMA, "passed": True, "source": source,
                "episodes": len(episodes), "queries": sum(len(e["test"]) for e in episodes),
                "files": {name: sha_file(args.out / name) for name in files},
                "admission": "research_only; inherited approval metadata unchanged"})
    return report


def _profile(grid) -> str:
    overlap = sum(bool(r[c]) and bool(r[c + 5]) for r in grid for c in range(4))
    gap = sum(not r[c] and not r[c + 5] for r in grid for c in range(4))
    if overlap and gap:
        return "balanced" if overlap == gap else "mixed"
    return "overlap" if overlap else "gap" if gap else "complement"


def _census(args, module, row, reference):
    if args.task_id != DEFAULT_TASK:
        raise ValueError("the Boolean-panel census is task-specific; audit/build support other declared contracts")
    contract, _ = load_subject(args.library, args.task_id)
    failures, total_failures = [], 0
    counts = {}
    canonical = []
    for split in ("train", "test"):
        for index, pair in enumerate(row[split]):
            official = reference(deepcopy(pair["input"]))
            record = {"split": split, "index": index, "reference_matches_label": official == pair["output"],
                      "self_check_errors": module.self_check(deepcopy(pair["input"]))}
            canonical.append(record)
    for band in ("easy", "medium", "hard"):
        count = Counter()
        for seed in range(args.seeds):
            for index in range(args.indices):
                count["attempted"] += 1
                try:
                    grid = module.generate(seed, index, difficulty=band)
                    original = deepcopy(grid)
                    official = reference(grid)
                    if grid != original:
                        raise ValueError("reference mutated input")
                    count["reference_pairs_checked"] += 1
                    count["profile:" + _profile(grid)] += 1
                    count["self_check_accepted"] += not module.self_check(grid)
                    count["strict_canonical_anchor"] += not contract.strict_canonical_like(grid)
                    if contract.audit_output(grid) != official:
                        raise ValueError("audit mirror differs from canonical Racket")
                    count["audit_mirror_matches"] += 1
                    for name, solver in contract.SEMANTIC_RIVALS.items():
                        count["rival_correct:" + name] += solver(grid) == official
                except Exception as exc:
                    total_failures += 1
                    if len(failures) < 12:
                        failures.append({"band": band, "seed": seed, "sample_index": index,
                                         "error": f"{type(exc).__name__}: {exc}"})
        counts[band] = dict(count)
    report = {"schema": "arcpuzzles-panel-census-v1", "source": source_receipt(module, row, args.library),
              "rival_contract_sha256": sha_file(Path(contract.__file__)), "seeds": args.seeds,
              "indices_per_seed": args.indices, "bands": counts, "canonical": canonical,
              "failures": failures, "total_failures": total_failures,
              "passed": total_failures == 0 and all(p["reference_matches_label"] for p in canonical),
              "scope": "execution/mirror parity; branch and self-check deficiencies are reported, not hidden in passed"}
    _write_json(args.report, report)
    return report


def positive(value: str) -> int:
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--task-id", default=DEFAULT_TASK)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="validate all final queries in private generated JSONL")
    audit.add_argument("--episodes", type=Path, required=True)
    audit.add_argument("--report", type=Path, required=True)
    build = sub.add_parser("build", help="generate, shuffle, independently verify, then split public/private rows")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--count", type=positive, default=8)
    build.add_argument("--queries", type=positive, default=2)
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    build.add_argument("--timeout", type=positive, default=600)
    build.add_argument("--allow-unapproved", action="store_true")
    census = sub.add_parser("census", help="Racket-backed paired-panel distribution/rival census")
    census.add_argument("--generator", type=Path, help="optional frozen generator to compare against current contracts")
    census.add_argument("--seeds", type=positive, default=32)
    census.add_argument("--indices", type=positive, default=16)
    census.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    args.library = args.library.resolve()
    try:
        module, row = load_subject(args.library, args.task_id, getattr(args, "generator", None))
        with reference_for(row["program_solution"]) as reference:
            action = {"audit": _audit_file, "build": _build, "census": _census}[args.command]
            report = action(args, module, row, reference)
        print(json.dumps({"passed": report["passed"], "command": args.command,
                          "output": str(getattr(args, "report", getattr(args, "out", "")))}, sort_keys=True))
        return 0 if report["passed"] else 1
    except Exception as exc:
        print(json.dumps({"passed": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
