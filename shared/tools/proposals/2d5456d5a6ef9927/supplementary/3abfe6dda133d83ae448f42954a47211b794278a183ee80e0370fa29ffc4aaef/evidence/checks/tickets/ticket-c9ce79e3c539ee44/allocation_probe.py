#!/usr/bin/env python3
"""One bounded, ticket-seeded allocation-quality probe.

The probe samples exactly three packet records, builds seven distinct lawful
inputs per record when possible, and executes the selected canonical Racket rule
once per record. It records facts only; the human allocation estimate lives in
proposal.md beside the JSON output.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time
from typing import Any

TICKET_ID = "ticket-c9ce79e3c539ee44"
TICKET_SEED = "ed204f09b0359ea28175e9017cfa12740e7d7c7ec1a265c4d089a618b913dc86"
SAMPLE_COUNT = 3
PAIR_COUNT = 7
DEMO_COUNT = 3
QUERY_COUNT = 4
SEMANTIC_NAMES = {
    "strict_canonical_like",
    "SEMANTIC_WITNESSES",
    "SEMANTIC_RIVALS",
    "WITNESS_RIVALS",
    "LESSON_COMPETITORS",
    "lesson_identifiable",
}


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def value_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def load_jsonl_by_id(path: Path, key: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[row[key]] = row
    return rows


def declared_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            result.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.add(node.name)
    return result


def tier_for(task_id: str, priority: dict[str, Any]) -> str | None:
    for tier, task_ids in priority.get("tiers", {}).items():
        if task_id in task_ids:
            return tier
    if task_id in priority.get("related_generators", {}):
        return "related_generators"
    return None


def evidence_summary(task_dir: Path, root: Path) -> dict[str, Any]:
    review_path = task_dir / "evidence/review_index.json"
    associated_path = task_dir / "evidence/associated_notes.jsonl"
    notes_path = task_dir / "notes.md"
    review: dict[str, Any] = {}
    if review_path.is_file():
        data = json.loads(review_path.read_text(encoding="utf-8"))
        audits = data.get("audits", []) if isinstance(data, dict) else []
        decisions = data.get("decisions", []) if isinstance(data, dict) else []
        review = {
            "path": review_path.relative_to(root).as_posix(),
            "sha256": sha256_path(review_path),
            "audit_count": len(audits) if isinstance(audits, list) else None,
            "decision_count": len(decisions) if isinstance(decisions, list) else None,
            "audit_resolutions": dict(Counter(
                row.get("resolution", "") for row in audits if isinstance(row, dict)
            )),
            "audit_verification_statuses": dict(Counter(
                row.get("verification_status", "") for row in audits if isinstance(row, dict)
            )),
        }
    categories: Counter[str] = Counter()
    associated_count = 0
    if associated_path.is_file():
        for line in associated_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            associated_count += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                categories["<invalid-json>"] += 1
            else:
                categories[str(row.get("category", ""))] += 1
    note_claims: list[str] = []
    if notes_path.is_file():
        for line in notes_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if re.search(r"(?:\d[\d,]*/\d[\d,]*|ambigu|racket|census|shortcut|blank row|grammar|repair)", stripped, re.I):
                note_claims.append(stripped[:280])
            if len(note_claims) == 12:
                break
    counterexamples = sorted(
        path.relative_to(root).as_posix()
        for path in (task_dir / "counterexamples").rglob("*")
        if path.is_file()
    ) if (task_dir / "counterexamples").is_dir() else []
    tests = sorted(
        path.relative_to(root).as_posix()
        for path in (task_dir / "tests").glob("test*.py")
        if path.is_file()
    ) if (task_dir / "tests").is_dir() else []
    return {
        "review_index": review or None,
        "associated_note_count": associated_count,
        "associated_note_categories": dict(categories),
        "notes_path": notes_path.relative_to(root).as_posix() if notes_path.is_file() else None,
        "notes_sha256": sha256_path(notes_path) if notes_path.is_file() else None,
        "selected_note_claims": note_claims,
        "counterexample_files": counterexamples,
        "test_files": tests,
        "parametric_workspace_present": (task_dir / "workspace/parametric").is_dir(),
    }


def canonical_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[row["task_id"]] = row
    return rows


def generate_inputs(module: Any, ticket_seed: str, task_id: str, normalize_grid: Any) -> dict[str, Any]:
    base_seed = int(hashlib.sha256(f"{ticket_seed}:{task_id}".encode("utf-8")).hexdigest()[:16], 16)
    difficulties = ("easy", "medium", "hard")
    grids: list[list[list[int]]] = []
    seen: set[str] = set()
    duplicate_rejections = 0
    grammar_rejections: list[dict[str, Any]] = []
    generation_errors: list[dict[str, str]] = []
    attempts = 0
    for sample_index in range(64):
        if len(grids) >= PAIR_COUNT:
            break
        attempts += 1
        difficulty = difficulties[sample_index % len(difficulties)]
        try:
            raw = module.generate(base_seed, sample_index, difficulty=difficulty)
            grid = normalize_grid(raw)
        except Exception as exc:
            generation_errors.append({
                "sample_index": str(sample_index),
                "difficulty": difficulty,
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue
        errors = list(module.self_check(grid, difficulty=difficulty))
        if errors:
            grammar_rejections.append({
                "sample_index": sample_index,
                "difficulty": difficulty,
                "errors": errors,
            })
            continue
        key = value_sha256(grid)
        if key in seen:
            duplicate_rejections += 1
            continue
        seen.add(key)
        grids.append(grid)
    return {
        "base_seed": base_seed,
        "attempts": attempts,
        "accepted_count": len(grids),
        "duplicate_rejections": duplicate_rejections,
        "grammar_rejections": grammar_rejections,
        "generation_errors": generation_errors,
        "input_hashes": [value_sha256(grid) for grid in grids],
        "grids": grids,
    }


def execute_racket(program: str, grids: list[list[list[int]]], ArcExecutor: Any, normalize_grid: Any) -> dict[str, Any]:
    started = time.monotonic()
    if not grids:
        return {"status": "not_run", "reason": "no accepted inputs"}
    task = {"train": [], "test": [{"input": grid} for grid in grids]}
    outputs: list[list[list[int]]] = []
    applications: list[dict[str, Any]] = []
    try:
        with ArcExecutor(task, use_racket=True) as executor:
            runtime = executor.runtime_identity
            rule_response = executor.step(program)
            if "ERROR" in rule_response:
                raise RuntimeError(f"rule rejected: {rule_response}")
            for index in range(len(grids)):
                command = f"(apply! {index})"
                response = executor.step(command)
                if "ERROR" in response:
                    raise RuntimeError(f"apply {index} failed: {response}")
                refs = executor.state_summary["applied_results"].get(index, [])
                if len(refs) != 1:
                    raise RuntimeError(f"apply {index} produced {len(refs)} result references")
                result = executor._results[refs[0]]
                output = normalize_grid(getattr(result, "data", None))
                outputs.append(output)
                applications.append({
                    "test_index": index,
                    "command": command,
                    "result_ref": refs[0],
                    "output_sha256": value_sha256(output),
                })
        return {
            "status": "pass",
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "runtime": runtime,
            "rule_response": rule_response,
            "applications": applications,
            "outputs": outputs,
        }
    except Exception as exc:
        return {
            "status": "error",
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "error": f"{type(exc).__name__}: {exc}",
            "outputs": outputs,
            "applications": applications,
        }


def semantic_checks(module: Any, grids: list[list[list[int]]], outputs: list[list[list[int]]]) -> dict[str, Any]:
    names = sorted(name for name in SEMANTIC_NAMES if hasattr(module, name))
    result: dict[str, Any] = {
        "declared_contract_names": names,
        "four_query_check_available": callable(getattr(module, "lesson_identifiable", None)),
        "four_query_results": [],
    }
    strict = getattr(module, "strict_canonical_like", None)
    if callable(strict):
        strict_results = []
        for grid in grids:
            try:
                value = strict(grid)
                strict_results.append(value if isinstance(value, (bool, str, int, float, list, dict, type(None))) else repr(value))
            except Exception as exc:
                strict_results.append(f"{type(exc).__name__}: {exc}")
        result["strict_canonical_like_results"] = strict_results
    checker = getattr(module, "lesson_identifiable", None)
    if callable(checker) and len(grids) >= PAIR_COUNT and len(outputs) >= PAIR_COUNT:
        pairs = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
        demos = pairs[:DEMO_COUNT]
        for query_index, query in enumerate(pairs[DEMO_COUNT:], start=DEMO_COUNT):
            try:
                errors = checker(demos, query)
                result["four_query_results"].append({
                    "query_pair_index": query_index,
                    "errors": list(errors) if isinstance(errors, (list, tuple)) else [f"unexpected result: {errors!r}"],
                })
            except Exception as exc:
                result["four_query_results"].append({
                    "query_pair_index": query_index,
                    "errors": [f"{type(exc).__name__}: {exc}"],
                })
    result["four_query_all_identifiable"] = (
        len(result["four_query_results"]) == QUERY_COUNT
        and all(not row["errors"] for row in result["four_query_results"])
    )
    for attr in ("SEMANTIC_WITNESSES", "SEMANTIC_RIVALS", "WITNESS_RIVALS", "LESSON_COMPETITORS"):
        value = getattr(module, attr, None)
        if isinstance(value, dict):
            result[attr.lower() + "_keys"] = sorted(map(str, value))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True, help="WORK directory")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", default=TICKET_SEED)
    args = parser.parse_args()

    root = args.root.resolve()
    repo = (root / "repo").resolve()
    runtime = repo / "shared/runtime"
    sys.path.insert(0, str(runtime))
    from reviewer_support import canonical_path, load_selected_generator, normalize_grid
    from arc_repl.executor import ArcExecutor

    manifest_path = root / "PACKET-MANIFEST.json"
    catalog_path = repo / "catalog/puzzles.jsonl"
    weights_path = repo / "shared/data/derived/generator_weights.json"
    authority_path = repo / "catalog/authority_files.json"
    draw_path = repo / "src/arcpuzzles/review_full_draw.py"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    catalog = load_jsonl_by_id(catalog_path, "id")
    weights = json.loads(weights_path.read_text(encoding="utf-8"))
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    canonical_ledger_path = Path(canonical_path(repo))
    canonical = canonical_rows(canonical_ledger_path)

    population = sorted(manifest["generators"])
    sampled = random.Random(int(args.seed, 16)).sample(population, min(SAMPLE_COUNT, len(population)))
    observations: list[dict[str, Any]] = []
    for task_id in sampled:
        task_dir = repo / "generators" / task_id
        source = task_dir / "generator.py"
        packet_entry = manifest["generators"][task_id]
        catalog_entry = catalog[task_id]
        names = declared_names(source)
        module, selected_path, selected_sha = load_selected_generator(task_id, root=repo)
        generated = generate_inputs(module, args.seed, task_id, normalize_grid)
        row = canonical[task_id]
        program = row["program_solution"]
        racket = execute_racket(program, generated["grids"], ArcExecutor, normalize_grid)
        outputs = racket.pop("outputs", [])
        semantic = semantic_checks(module, generated["grids"], outputs)
        generated.pop("grids", None)
        authority_matches = [
            {"path": path, "task_id": mapped}
            for path, mapped in authority.items()
            if mapped == task_id
        ]
        observations.append({
            "task_id": task_id,
            "source": {
                "path": source.relative_to(root).as_posix(),
                "sha256": sha256_path(source),
                "selected_path": selected_path.relative_to(repo).as_posix(),
                "selected_sha256": selected_sha,
                "packet_sha256": packet_entry["generator_sha256"],
                "source_hashes_match": sha256_path(source) == selected_sha == packet_entry["generator_sha256"],
                "declared_names": sorted(names),
            },
            "allocation": {
                "approved": packet_entry.get("approved"),
                "main_pool": task_id in manifest.get("main_ids", []),
                "normal_draw_pool": task_id in manifest["main_draw_policy"].get("normal_ids", []),
                "parametric_priority_tier": tier_for(task_id, manifest["parametric_priority"]),
                "catalog_sources": catalog_entry.get("sources", []),
                "catalog_review_status": catalog_entry.get("review_status", ""),
                "catalog_train_safety": catalog_entry.get("train_safety"),
                "catalog_mix_weight": catalog_entry.get("mix_weight"),
                "derived_sampling_weight": weights.get(task_id),
            },
            "canonical_authority": {
                "ledger_path": canonical_ledger_path.relative_to(repo).as_posix(),
                "program_sha256": sha256_bytes(program.encode("utf-8")),
                "solution_language": row.get("solution_language"),
                "authority_file_mappings": authority_matches,
                "rule_hash": packet_entry.get("rule_hash"),
            },
            "evidence": evidence_summary(task_dir, root),
            "generation_and_dedup": generated,
            "racket_smoke": racket,
            "teaching": semantic,
        })

    policy = manifest["main_draw_policy"]
    focus = policy["evaluation_focus"]
    sources = [source for obs in observations for source in obs["allocation"]["catalog_sources"]]
    report = {
        "schema": "arcpuzzles-bounded-allocation-quality-probe-v1",
        "ticket_id": TICKET_ID,
        "seed": args.seed,
        "sampler": "random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.generators), 3)",
        "population_size": len(population),
        "sample_size": len(sampled),
        "sampled_ids": sampled,
        "probe_contract": {
            "records": SAMPLE_COUNT,
            "accepted_inputs_target_per_record": PAIR_COUNT,
            "demonstrations": DEMO_COUNT,
            "queries": QUERY_COUNT,
            "racket_processes": len(observations),
            "no_peer_battery": True,
            "no_large_census": True,
        },
        "source_files": {
            "manifest": {"path": manifest_path.relative_to(root).as_posix(), "sha256": sha256_path(manifest_path)},
            "draw_policy": {"path": draw_path.relative_to(root).as_posix(), "sha256": sha256_path(draw_path)},
            "catalog": {"path": catalog_path.relative_to(root).as_posix(), "sha256": sha256_path(catalog_path)},
            "weights": {"path": weights_path.relative_to(root).as_posix(), "sha256": sha256_path(weights_path)},
            "authority_map": {"path": authority_path.relative_to(root).as_posix(), "sha256": sha256_path(authority_path)},
            "canonical_ledger": {"path": canonical_ledger_path.relative_to(root).as_posix(), "sha256": sha256_path(canonical_ledger_path)},
        },
        "draw_context": {
            "main_ids": len(manifest["main_ids"]),
            "normal_ids": len(policy["normal_ids"]),
            "evaluation_focus_probability": focus["probability"],
            "evaluation_focus_anchor_count": len(focus["anchors"]),
            "parametric_priority_counts": manifest["parametric_priority"]["counts"],
        },
        "source_specific_coverage": {
            "sampled_sources": sorted(set(sources)),
            "arc_gen_sampled": any("arc-gen" in source.lower() for source in sources),
            "re_arc_sampled": any("re-arc" in source.lower() or "re_arc" in source.lower() for source in sources),
            "conclusion": "No ARC-GEN or RE-ARC record was selected; this sample supports no source-specific quality conclusion for either corpus. Provenance is recorded but never treated as a quality guarantee.",
        },
        "observations": observations,
        "coverage_limits": [
            "Three ticket-seeded records are a bounded spot sample, not a corpus-wide rate estimate.",
            "A seven-input canonical Racket smoke proves executability and bounded dedup cost, not a parametric variant or unique program identification.",
            "Four-query identifiability is reported only when the selected generator exports a source-bound lesson_identifiable checker.",
            "Catalog review state and provenance are evidence fields, not automatic quality scores.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "sampled_ids": sampled,
        "out": str(args.out),
        "sha256": sha256_path(args.out),
        "racket_statuses": {obs["task_id"]: obs["racket_smoke"]["status"] for obs in observations},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
