"""Export source-bound native wall examples after protected Racket verification.

The machine report is written to an explicit file. Runtime and launcher output
remain ordinary logs and are never parsed as evidence JSON.
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
TASK_ID = HERE.parents[1].name
PROMOTION_PATH = HERE / "promotion.json"

sys.path.insert(0, str(REPO / "src"))
from arcpuzzles import Catalog
from arcpuzzles.parametric_promotion import settings_space
from arcpuzzles.parametric_worker import evaluate_contract


def _load(name: str):
    path = HERE / f"{name}.py"
    if path.is_symlink() or path.resolve() != path:
        raise ValueError("example sources must be regular same-checkout files")
    spec = importlib.util.spec_from_file_location(f"_walls_examples_{name}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_binding() -> dict[str, str]:
    """Bind local authoring sources, native executors, serializer and rule data."""
    sources = {HERE.parents[1] / "generator.py"}
    sources.update(path for path in HERE.rglob("*")
                   if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
                   and not any(part in {"evidence", "examples", "__pycache__"}
                               for part in path.relative_to(HERE).parts))
    sources.update(REPO / relative for relative in (
        "src/arcpuzzles/parametric_worker.py",
        "src/arcpuzzles/parametric_promotion.py",
        "src/arcpuzzles/catalog.py",
        "src/arcpuzzles/runtime.py",
        "shared/runtime/reviewer_support.py",
        "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/tools/comment_solutions.py",
    ))
    ledger = next((REPO / relative for relative in (
        "data/canonical/puzzles.jsonl", "shared/data/canonical/puzzles.jsonl"
    ) if (REPO / relative).is_file()), None)
    if ledger is None:
        raise ValueError("same-checkout canonical ledger is missing")
    sources.add(ledger)
    result = {}
    for path in sorted(sources):
        if path.is_symlink() or path.resolve() != path:
            raise ValueError("example source binding must not follow symlinks")
        result[path.relative_to(REPO).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _catalog_binding() -> dict[str, Any]:
    selected = Catalog(REPO).describe(TASK_ID)
    return {key: selected[key] for key in (
        "id", "kind", "rule_task_id", "rule_hash", "generator_sha256",
        "family", "parent_ids", "sources", "split", "version",
    ) if key in selected}


def _report_destination(path: str | Path | None, destination: Path) -> Path | None:
    if path is None:
        return None
    report = Path(path)
    if report.exists() or report.is_symlink():
        raise FileExistsError(report)
    if report.resolve().is_relative_to(destination.resolve()):
        raise ValueError("report must be outside the manifested export directory")
    if any(parent.is_symlink() for parent in report.absolute().parents):
        raise ValueError("report destination must not have symlink ancestors")
    return report


def _write_report(path: Path, body: bytes) -> None:
    """Publish complete report bytes without overwriting a concurrent report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".wall-report-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(body)
            handle.flush()
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_examples(
    out_dir: str | Path,
    *,
    seed: int = 0,
    demos: int = 3,
    queries: int = 4,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify both settings at one seed, retain native evidence, export turns.

    Adapter labels are claims until the existing native evaluator checks every
    pair through protected Racket and identifies the setting from demos alone.
    The exact native wrapper and the complete adapter episode are retained
    privately; the worker's historical reference marker grants no acceptance.
    """
    destination = Path(out_dir)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    report_file = _report_destination(report_path, destination)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    contract = json.loads(PROMOTION_PATH.read_bytes())
    for name, value in (("demos", demos), ("queries", queries)):
        lower, upper = contract["limits"][name]
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    jobs = [{"seed": seed, "settings": setting, "demos": demos, "queries": queries}
            for setting in settings_space(contract)]
    source_binding = _source_binding()
    catalog_binding = _catalog_binding()
    execution = evaluate_contract(REPO, TASK_ID, contract, jobs)
    identity = execution.get("racket", {})
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("native examples require actual protected Racket execution")
    if len(execution["episodes"]) != len(jobs) or len(execution["checks"]) != len(jobs):
        raise ValueError("native execution returned an incomplete job set")

    adapter, exporter = _load("adapter"), _load("export")
    episodes, programs = [], []
    for native, certificate, job in zip(execution["episodes"], execution["checks"], jobs, strict=True):
        generated = adapter.generate(seed, deepcopy(job["settings"]), demos, queries)
        if generated.get("program_solution") != native["program"]:
            raise ValueError("retained adapter program differs from native execution")
        for split in ("train", "test"):
            claims = [{"input": pair["input"], "output": pair["output"]} for pair in generated[split]]
            if exporter._json_bytes(claims) != exporter._json_bytes(native[split]):
                raise ValueError("retained adapter grids differ from protected native execution")
        if (native["settings"] != job["settings"] or native["seed"] != seed
                or native["program_sha256"] != hashlib.sha256(native["program"].encode()).hexdigest()
                or certificate["survivors"] != [job["settings"]]):
            raise ValueError("native source/program/certificate identity differs from the job")
        if {"native_wrapper", "export_provenance"} & set(generated):
            raise ValueError("adapter episode collides with reserved private export fields")
        retained = deepcopy(generated)
        retained["native_wrapper"] = deepcopy(native)
        retained["export_provenance"] = {
            "reference": "protected_racket_pending_acceptance",
            "demo_only_certificate": deepcopy(certificate),
            "native_acceptance": "owner_pending",
            "training_admitted": False,
        }
        episodes.append(retained)
        programs.append({"settings": deepcopy(job["settings"]),
                         "program_sha256": native["program_sha256"]})
    if _source_binding() != source_binding or _catalog_binding() != catalog_binding:
        raise ValueError("example source or catalog changed during protected execution")

    context = {
        "schema": "arcpuzzles-native-wall-example-context-v1",
        "native_execution": execution,
        "contract": contract,
        "jobs": jobs,
        "source_sha256": source_binding,
        "catalog": catalog_binding,
        "native_acceptance": "owner_pending",
        "training_admitted": False,
    }
    transport = exporter.write_batch(episodes, destination, private_context=context)
    # This guard also covers changes during transport. Remove only this newly
    # written completion marker on drift; retain the partial evidence for review.
    if _source_binding() != source_binding or _catalog_binding() != catalog_binding:
        Path(transport["manifest_path"]).unlink()
        raise ValueError("example sources changed before publication completed")
    report = {
        "schema": "arcpuzzles-native-wall-example-report-v1",
        "status": "passed",
        **transport,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": [job["settings"] for job in jobs],
        "counts": {"episodes": len(episodes), "demonstrations_per_episode": demos,
                   "queries_per_episode": queries, "demo_labels": len(episodes) * demos,
                   "query_labels": len(episodes) * queries, "actor_payloads": len(transport["turn_ids"]),
                   "controller_payloads": len(transport["controller_ids"])},
        "programs": programs,
        "racket": identity,
        "racket_evaluations": execution["racket_evaluations"],
        "native_execution_sha256": hashlib.sha256(exporter._json_bytes(execution)).hexdigest(),
        "native_execution_hash_scope": "Canonical UTF-8 JSON with sorted keys, compact separators and trailing LF.",
        "source_sha256": source_binding,
        "catalog": catalog_binding,
        "reference_labels_checked": True,
        "native_acceptance": "owner_pending",
        "training_admitted": False,
        "limits": [
            "This seed/count pair checks the declared settings; it is not universal identification.",
            "Extra rivals and adversarial geometry are separate audits.",
            "Only one turns/<id>.json file belongs in an actor turn; controller containers and reports stay private.",
            "The native worker reference marker is preserved as execution data, not owner acceptance.",
            "No turn controller, training loop, measured training gain or downstream admission is implemented.",
        ],
    }
    if report_file is not None:
        _write_report(report_file, exporter._json_bytes(report))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path, help="Fresh private JSON report outside --out")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    options = parser.parse_args(argv)
    report = build_examples(options.out, seed=options.seed, demos=options.demos,
                            queries=options.queries, report_path=options.report)
    print(f"Wrote {report['counts']['actor_payloads']} single-query payloads; report: {options.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
