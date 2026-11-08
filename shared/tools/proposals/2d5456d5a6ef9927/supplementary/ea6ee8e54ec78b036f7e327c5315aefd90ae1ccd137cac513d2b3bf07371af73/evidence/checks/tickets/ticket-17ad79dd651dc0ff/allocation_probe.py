#!/usr/bin/env python3
"""Bounded allocation-quality probe for ticket-17ad79dd651dc0ff.

One deterministic probe: inspect the three IDs sampled from the ticket seed,
materialize two demonstration inputs plus four query inputs per task, execute the
pinned canonical Racket rule for every input, and retain source/pool/catalog,
validation, diversity, timing, and current-evidence metadata.  This is an
allocation experiment input, not a task approval or training admission.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import time
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import (
    convert_dict_literals, strip_line_comments, strip_rule_wrapper,
)
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TICKET_ID = "ticket-17ad79dd651dc0ff"
TICKET_SEED = "8796f740db2426f56785e613407c9b1d62684c0e41e14d7fbed1e262e25014c9"
EXPECTED_SAMPLE = ["f3076f3858b4", "8eb9146172f8", "5cff0d794bdf"]
EXPECTED_GENERATOR_HASHES = {
    "f3076f3858b4": "6638cf72bf2340e323543ceb8718680eee8000518551d9148bc129a2d36edff0",
    "8eb9146172f8": "84301bd12c17dbb0897847b4ddd15d66ee1e7fa0c74d4cafaa9f9a3480472d95",
    "5cff0d794bdf": "b6ba414e0be2f73cd50ba150644a5039c190c831aba2339dcb03026182249493",
}
DIFFICULTIES = ("easy", "medium", "hard", "easy", "medium", "hard")
ROOT = find_root(__file__)
WORK = ROOT.parent
HERE = Path(__file__).resolve().parent


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _grid_bytes(grid: list[list[int]]) -> bytes:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha_bytes(_grid_bytes(grid))


def _racket_literal(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is int:
        return str(value)
    raise TypeError(f"unsupported Racket literal: {value!r}")


def _canonical_program(task_id: str) -> tuple[str, int]:
    programs: list[str] = []
    row_count = 0
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            row_count += 1
            program = row.get("program_solution")
            if isinstance(program, str) and program.strip():
                programs.append(program)
    unique = list(dict.fromkeys(programs))
    if len(unique) != 1:
        raise RuntimeError(f"{task_id}: expected one exact canonical program, found {len(unique)}")
    return unique[0], row_count


def _head(body: str) -> str | None:
    text = body.lstrip()
    if not text.startswith("("):
        return None
    index = 1
    while index < len(text) and text[index].isspace():
        index += 1
    end = index
    while end < len(text) and text[end] not in " \t\r\n()[];":
        end += 1
    return text[index:end] or None


def _portable_wrap_rule(program: str) -> str:
    # The stripped review runtime omits the scripts parser imported by the
    # shared shorthand converter. These three pinned programs already use
    # full Racket binding syntax, so apply the remaining shared normalization
    # steps and the same callable/h-w wrapping contract.
    source = convert_dict_literals(strip_line_comments(program))
    body = strip_rule_wrapper(source)
    head = _head(body)
    if head in ("lambda", "λ"):
        return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"
    if head is None or head in {"pipe", "compose", "fork", "power"}:
        return body
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def _apply(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    callable_source = _portable_wrap_rule(program)
    literal = "'" + _racket_literal(normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({callable_source} {literal})"))

def _catalog_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with (ROOT / "catalog/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    return rows


def _audit_summary(task_id: str) -> dict[str, Any]:
    path = ROOT / f"generators/{task_id}/evidence/review_index.json"
    if not path.is_file():
        return {"path": None, "count": 0, "resolutions": {}, "records": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for audit in data.get("audits", []):
        text = " ".join(str(audit.get("text", "")).split())
        records.append({
            "return_id": audit.get("return_id"),
            "resolution": audit.get("resolution"),
            "verification_status": audit.get("verification_status"),
            "summary_excerpt": text[:800],
        })
    return {
        "path": str(path.relative_to(WORK)),
        "count": len(records),
        "resolutions": dict(Counter(r["resolution"] for r in records)),
        "records": records,
    }


def _task_seed(task_id: str) -> int:
    raw = hashlib.sha256(f"{TICKET_SEED}|{task_id}|allocation-probe".encode()).digest()
    return int.from_bytes(raw[:8], "big")


def main() -> None:
    manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text(encoding="utf-8"))
    all_ids = sorted(manifest["all_ids"])
    sampled = random.Random(int(TICKET_SEED, 16)).sample(all_ids, 3)
    if sampled != EXPECTED_SAMPLE:
        raise RuntimeError(f"sample drift: expected {EXPECTED_SAMPLE}, got {sampled}")

    catalog = _catalog_rows()
    normal_ids = manifest["main_draw_policy"]["normal_ids"]
    focus = manifest["main_draw_policy"]["evaluation_focus"]
    pool_summary = {
        "all_ids": len(manifest["all_ids"]),
        "main_ids": len(manifest["main_ids"]),
        "normal_ids": len(normal_ids),
        "evaluation_focus_probability": focus["probability"],
        "evaluation_anchor_count": len(focus["anchors"]),
        "evaluation_direct_anchor_count": sum(bool(a["main_ids"]) for a in focus["anchors"]),
        "evaluation_inspired_anchor_count": sum(not a["main_ids"] for a in focus["anchors"]),
        "normal_mix_weights": dict(Counter(str(catalog[tid]["mix_weight"]) for tid in normal_ids)),
        "normal_train_safety": dict(Counter(catalog[tid]["train_safety"] for tid in normal_ids)),
        "normal_review_status": dict(Counter(catalog[tid]["review_status"] for tid in normal_ids)),
        "ticket_type_weights": manifest["supplementary_ticket_policy"]["weights"],
        "ticket_weight_basis": manifest["supplementary_ticket_policy"]["weight_basis"],
    }

    report: dict[str, Any] = {
        "schema": "arcpuzzles-allocation-quality-probe-v1",
        "ticket_id": TICKET_ID,
        "ticket_seed": TICKET_SEED,
        "sampling_method": "random.Random(int(ticket_seed, 16)).sample(sorted(all_ids), 3)",
        "sampled_ids": sampled,
        "pool_summary": pool_summary,
        "probe_scope": {
            "records": 3,
            "pairs_per_record": 6,
            "demo_count": 2,
            "query_count": 4,
            "racket_labels_planned": 18,
            "claim_limit": "finite current-source probe; no approval, corpus census, or model-quality ranking",
        },
        "records": [],
    }

    started = time.perf_counter()
    bridge = RacketBridge(timeout=20.0, startup_timeout=30.0)
    try:
        report["racket_runtime_identity"] = bridge.runtime_identity
        for task_id in sampled:
            module, source_path, source_hash = load_selected_generator(task_id, root=ROOT)
            if source_hash != EXPECTED_GENERATOR_HASHES[task_id]:
                raise RuntimeError(f"{task_id}: source hash drift {source_hash}")
            program, canonical_rows = _canonical_program(task_id)
            base_seed = _task_seed(task_id)
            pairs = []
            racket_started = time.perf_counter()
            for index, difficulty in enumerate(DIFFICULTIES):
                grid = normalize_grid(module.generate(base_seed, index, difficulty=difficulty))
                errors = list(module.self_check(grid, difficulty=difficulty, meta=None))
                output = _apply(bridge, program, grid)
                observed = None
                if hasattr(module, "observe_overrides"):
                    try:
                        observed = module.observe_overrides(grid)
                    except Exception as error:  # evidence, not a hidden pass
                        observed = {"error": f"{type(error).__name__}: {error}"}
                pairs.append({
                    "role": "demo" if index < 2 else "query",
                    "sample_index": index,
                    "difficulty": difficulty,
                    "input": grid,
                    "output": output,
                    "input_sha256": _grid_hash(grid),
                    "output_sha256": _grid_hash(output),
                    "shape": [len(grid), len(grid[0])],
                    "self_check_errors": errors,
                    "observed_axes": observed,
                })
            racket_elapsed = time.perf_counter() - racket_started
            query_pairs = [p for p in pairs if p["role"] == "query"]
            root = ROOT / f"generators/{task_id}"
            tests = sorted(str(p.relative_to(WORK)) for p in root.rglob("test*.py"))
            parametric = root / "workspace/parametric/evidence/manifest.json"
            row = catalog[task_id]
            report["records"].append({
                "task_id": task_id,
                "source_path": str(source_path.relative_to(WORK)),
                "generator_sha256": source_hash,
                "rule_hash": manifest["generators"][task_id]["rule_hash"],
                "canonical_row_count": canonical_rows,
                "catalog": {
                    "sources": row["sources"],
                    "mix_weight": row["mix_weight"],
                    "health": row["health"],
                    "train_safety": row["train_safety"],
                    "review_status": row["review_status"],
                    "version": row["version"],
                    "summary": row["summary"],
                },
                "draw_membership": {
                    "all": task_id in manifest["all_ids"],
                    "main": task_id in manifest["main_ids"],
                    "normal": task_id in normal_ids,
                },
                "declared_axes": sorted(getattr(module, "AXES", {}).keys()),
                "task_test_paths": tests,
                "parametric_manifest_path": str(parametric.relative_to(WORK)) if parametric.is_file() else None,
                "audit_summary": _audit_summary(task_id),
                "generation": {
                    "seed": base_seed,
                    "pairs": pairs,
                    "self_check_passed": all(not p["self_check_errors"] for p in pairs),
                    "distinct_all_inputs": len({p["input_sha256"] for p in pairs}),
                    "distinct_query_inputs": len({p["input_sha256"] for p in query_pairs}),
                    "distinct_query_outputs": len({p["output_sha256"] for p in query_pairs}),
                    "four_distinct_queries_materialized": len({p["input_sha256"] for p in query_pairs}) == 4,
                    "racket_calls": len(pairs),
                    "racket_elapsed_seconds": round(racket_elapsed, 6),
                },
            })
    finally:
        bridge.close()
    report["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    report["racket_labels_completed"] = sum(r["generation"]["racket_calls"] for r in report["records"])
    report["all_generated_self_checks_passed"] = all(r["generation"]["self_check_passed"] for r in report["records"])
    report["all_records_materialized_four_distinct_queries"] = all(
        r["generation"]["four_distinct_queries_materialized"] for r in report["records"]
    )
    out = HERE / "probe.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "sampled_ids": sampled,
        "racket_labels_completed": report["racket_labels_completed"],
        "all_generated_self_checks_passed": report["all_generated_self_checks_passed"],
        "all_records_materialized_four_distinct_queries": report["all_records_materialized_four_distinct_queries"],
        "elapsed_seconds": report["elapsed_seconds"],
        "output": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
