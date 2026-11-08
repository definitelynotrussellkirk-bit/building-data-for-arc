"""Export source-bound examples labeled by this task's protected native worker.

The native worker fits declared programs to demonstrations only, executes every
selected query label, and checks the canonical default's exact source. These
examples remain owner-pending and do not grant acceptance or training admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "8de1c257a9c7"
PROMOTION_PATH = HERE / "promotion.json"

for source in (REPO / "src", REPO / "shared/runtime"):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from arcpuzzles.parametric_promotion import settings_space
from arcpuzzles.parametric_worker import evaluate_contract


def _adjacent_module(name: str):
    """Compile the exact task-local bytes without generic module-name reuse."""
    path = HERE / f"{name}.py"
    if not path.is_file() or path.resolve() != path:
        raise ValueError(f"missing regular task-local {name} source")
    source = path.read_bytes()
    module_name = f"_{TASK_ID}_{name}_{hashlib.sha256(source).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def _source_binding() -> dict[str, str]:
    """Bind task sources and the native execution/serialization helper closure.

    Protected Racket's binary, prelude, bridge boot script, and candidate-symbol
    policy additionally carry their live runtime identity in private metadata.
    The program hash binds the exact selected rule, independently of catalog
    display fields. This inventory is evidence, not an acceptance record.
    """
    sources = {HERE.parents[1] / "generator.py"}
    excluded = {"evidence", "examples", "__pycache__"}
    for path in HERE.rglob("*"):
        if (path.is_file() and path.suffix in {".py", ".rkt", ".json"}
                and not excluded.intersection(path.relative_to(HERE).parts)):
            sources.add(path)
    sources.update(REPO / relative for relative in (
        "src/arcpuzzles/__init__.py",
        "src/arcpuzzles/catalog.py",
        "src/arcpuzzles/parametric_worker.py",
        "src/arcpuzzles/parametric_promotion.py",
        "src/arcpuzzles/parametric_priority.py",
        "src/arcpuzzles/runtime.py",
        "src/arcpuzzles/receipt_input.py",
        "shared/runtime/reviewer_support.py",
        "shared/runtime/puzzle_generators/__init__.py",
        "shared/runtime/puzzle_generators/base.py",
        "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/runtime/arc_repl/__init__.py",
        "shared/runtime/arc_repl/parser.py",
        "shared/runtime/arc_repl/security.py",
        "shared/runtime/arc_repl/racket_bridge.py",
        "shared/tools/comment_solutions.py",
    ))
    for path in sources:
        if not path.is_file() or path.resolve() != path:
            raise ValueError(f"source must be a regular same-checkout file: {path}")
    return {path.relative_to(REPO).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(sources)}


def _raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _same(left: Any, right: Any) -> bool:
    """JSON comparison keeps bool/int and other scalar types distinct."""
    return _raw(left) == _raw(right)


def _request_count(contract: dict[str, Any], name: str, value: Any) -> int:
    limits = contract.get("limits", {}).get(name)
    supported = {"demos": (2, 6), "queries": (1, 4)}
    if (type(limits) is not list or len(limits) != 2
            or any(type(bound) is not int for bound in limits)
            or not supported[name][0] <= limits[0] <= limits[1] <= supported[name][1]):
        raise ValueError(f"invalid native {name} limits")
    if type(value) is not int or not limits[0] <= value <= limits[1]:
        raise ValueError(f"{name} must be an exact integer in {limits[0]}..{limits[1]}")
    return value


def _claims(generated: dict[str, Any], split: str) -> list[dict[str, Any]]:
    pairs = generated.get(split)
    if type(pairs) is not list or any(type(pair) is not dict for pair in pairs):
        raise ValueError(f"adapter replay omitted {split} pairs")
    try:
        return [{"input": pair["input"], "output": pair["output"]} for pair in pairs]
    except KeyError as error:
        raise ValueError("adapter replay omitted input/output labels") from error


def build_examples(
    out_dir: str | Path, *, seed: int = 0, demos: int = 3, queries: int = 4
) -> dict[str, Any]:
    """Execute every declared setting with matched seed and independent counts.

    Label authority is the live native ``evaluate_contract`` invocation. A pure
    adapter replay preserves its complete private metadata; exact program and
    input/output agreement with that invocation is required before publication.
    """
    destination = Path(out_dir)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    contract = json.loads(PROMOTION_PATH.read_bytes())
    if type(contract) is not dict:
        raise ValueError("promotion contract must be an object")
    demos = _request_count(contract, "demos", demos)
    queries = _request_count(contract, "queries", queries)
    jobs = [{"seed": seed, "settings": setting, "demos": demos, "queries": queries}
            for setting in settings_space(contract)]
    source_binding = _source_binding()
    execution = evaluate_contract(REPO, TASK_ID, contract, deepcopy(jobs))
    identity = execution.get("racket", {})
    if (type(identity) is not dict or identity.get("backend") != "racket"
            or identity.get("protected") is not True):
        raise ValueError("example export requires live protected Racket execution")
    if _source_binding() != source_binding:
        raise ValueError("example generation source changed during protected execution")
    checked, certificates = execution.get("episodes"), execution.get("checks")
    if (type(checked) is not list or type(certificates) is not list
            or len(checked) != len(jobs) or len(certificates) != len(jobs)):
        raise ValueError("native execution must return every requested episode and certificate")
    evaluations = execution.get("racket_evaluations")
    expected_evaluations = len(jobs) * (len(jobs) * demos + queries)
    if type(evaluations) is not int or evaluations != expected_evaluations:
        raise ValueError("native execution evaluation count does not match the declared job set")

    adapter = _adjacent_module("adapter")
    episodes = []
    for job, episode, certificate in zip(jobs, checked, certificates, strict=True):
        if type(episode) is not dict or type(certificate) is not dict:
            raise ValueError("native episodes and certificates must be objects")
        if (episode.get("task_id") != TASK_ID
                or not _same(episode.get("seed"), job["seed"])
                or not _same(episode.get("settings"), job["settings"])
                or not _same(certificate.get("seed"), job["seed"])
                or not _same(certificate.get("settings"), job["settings"])
                or not _same(certificate.get("survivors"), [job["settings"]])
                or not _same(certificate.get("counts"), {"demos": demos, "queries": queries})
                or not _same(certificate.get("label_count"), demos + queries)):
            raise ValueError("native episode or demonstration-only certificate does not match its request")
        exact_program = adapter.program(deepcopy(job["settings"]))
        if (type(exact_program) is not str or not exact_program.strip()
                or episode.get("program") != exact_program
                or episode.get("program_sha256") != hashlib.sha256(exact_program.encode()).hexdigest()):
            raise ValueError("native episode must retain its exact task-local Racket program")
        authored = adapter.generate(seed, deepcopy(job["settings"]), demos, queries)
        if type(authored) is not dict or authored.get("program_solution") != exact_program:
            raise ValueError("adapter replay changed its exact selected program")
        for split, count in (("train", demos), ("test", queries)):
            claimed = _claims(authored, split)
            if len(claimed) != count or not _same(claimed, episode.get(split)):
                raise ValueError("adapter replay differs from protected native inputs or labels")
        episodes.append({
            **episode,
            "reference": "protected_racket_pending_acceptance",
            "private": {
                "adapter_episode": authored,
                "racket": identity,
                "demo_only_certificate": certificate,
                "native_acceptance": "owner_pending",
                "training_admitted": False,
                "source_sha256": source_binding,
                "certificate_scope": "Declared settings only; additional rivals require their separate audit.",
            },
        })
    if _source_binding() != source_binding:
        raise ValueError("example generation source changed during metadata replay")
    exported = _adjacent_module("export").write_batch(
        episodes, destination, source_sha256=source_binding,
    )
    return {
        **exported,
        "task_id": TASK_ID,
        "settings": [job["settings"] for job in jobs],
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "racket": identity,
        "racket_evaluations": evaluations,
        "source_sha256": source_binding,
        "native_acceptance": "owner_pending",
        "training_admitted": False,
    }


def _write_report(path: Path, payload: bytes) -> None:
    """Publish a complete report without replacing an existing file or symlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}-", dir=path.parent) as staged:
        staged.write(payload)
        staged.flush()
        os.fsync(staged.fileno())
        os.link(staged.name, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--report", type=Path, help="new JSON report path outside the export directory")
    args = parser.parse_args(argv)
    if args.report is not None:
        if args.report.exists() or args.report.is_symlink():
            raise FileExistsError(args.report)
        if args.report.resolve().is_relative_to(args.out.resolve()):
            raise ValueError("report path must be outside the manifested export directory")
    report = build_examples(args.out, seed=args.seed, demos=args.demos, queries=args.queries)
    payload = _raw(report)
    if args.report is not None:
        _write_report(args.report, payload)
    sys.stdout.write(payload.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
