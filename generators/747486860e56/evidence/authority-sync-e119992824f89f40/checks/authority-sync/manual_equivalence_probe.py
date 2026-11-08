#!/usr/bin/env python3
"""Finite semantic probe for legacy selected Racket copies versus canonical authority."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.builtins import Grid, _unwrap
from arc_repl.executor import ArcExecutor
from arc_repl.racket_bridge import racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = "747486860e56"
ROOT = find_root(__file__)
AUTHORITY_FILES = (
    "shared/data/base/solutions/training/902510d5__747486860e56.json",
    "shared/data/base/solutions/augmented/902510d5__50f50ce3a1e3.json",
)


def sha(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def canonical_source() -> str:
    values = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    values.add(row["program_solution"])
    if len(values) != 1:
        raise RuntimeError(f"expected one canonical source, got {len(values)}")
    return values.pop()


def load_generator():
    path = ROOT / f"generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location("authority_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_executor(source: str) -> ArcExecutor:
    executor = ArcExecutor({"train": [], "test": []}, use_racket=True)
    result = executor.step(source)
    if result.startswith("ERROR:"):
        executor.close()
        raise RuntimeError(result)
    return executor


def run_rule(executor: ArcExecutor, grid):
    return normalize_grid(_unwrap(executor._apply_rule(Grid(normalize_grid(grid)))))


def case_rows(generator):
    rows = []
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        rows.append({"kind": "canonical", "id": f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}", "input": pair["input"]})
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            for index in range(6):
                rows.append({
                    "kind": "generated_default",
                    "id": f"{band}-seed{seed}-index{index}",
                    "input": generator.generate(seed, index, difficulty=band),
                })
    for band in ("easy", "medium", "hard"):
        for index in range(3):
            for corner in generator.CORNERS:
                for count in range(3, 9):
                    side = max(7, count)
                    rows.append({
                        "kind": "generated_override",
                        "id": f"{band}-index{index}-{corner}-k{count}",
                        "input": generator.generate(
                            97,
                            index,
                            difficulty=band,
                            grid_h=side,
                            grid_w=side + 1,
                            corner=corner,
                            n_markers=count,
                        ),
                    })
    return rows


def main() -> int:
    canonical = canonical_source()
    generator = load_generator()
    legacy = {}
    raw = {}
    file_rows = []
    for relative in AUTHORITY_FILES:
        payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        target = payload["racket_target"]
        legacy[relative] = target["target_code"]
        raw[relative] = target["raw_code"]
        file_rows.append({
            "path": relative,
            "file_sha256": sha((ROOT / relative).read_bytes()),
            "raw_code_sha256": sha(target["raw_code"]),
            "target_code_sha256": sha(target["target_code"]),
        })

    cases = case_rows(generator)
    source_map = {"canonical": canonical, **{f"legacy:{name}": source for name, source in legacy.items()}}
    mismatches = []
    canonical_label_failures = []
    by_kind = {}
    executors = {name: make_executor(source) for name, source in source_map.items()}
    try:
        canonical_rows = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        for index, case in enumerate(cases):
            outputs = {name: run_rule(executor, case["input"]) for name, executor in executors.items()}
            by_kind[case["kind"]] = by_kind.get(case["kind"], 0) + 1
            for name, output in outputs.items():
                if output != outputs["canonical"]:
                    mismatches.append({"case_index": index, "case_kind": case["kind"], "case_id": case["id"], "source": name})
            if case["kind"] == "canonical":
                pair = canonical_rows[index]
                if outputs["canonical"] != pair["output"]:
                    canonical_label_failures.append(case["id"])
    finally:
        for executor in executors.values():
            executor.close()

    result = {
        "schema": "task-local-authority-equivalence-probe-v1",
        "task_id": TASK_ID,
        "status": "finite_probe_only",
        "canonical_source_sha256": sha(canonical),
        "files_before_manual_sync": file_rows,
        "runtime": racket_runtime_status(),
        "case_counts": by_kind,
        "total_cases": len(cases),
        "source_count": len(source_map),
        "racket_evaluations": len(cases) * len(source_map),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:20],
        "canonical_label_failure_count": len(canonical_label_failures),
        "canonical_label_failures": canonical_label_failures,
        "manual_review": {
            "legacy_training_differences": [
                "custom-parser shorthand (for/or (d diag-cells) ...) versus canonical Racket binding syntax",
                "cell-at versus the prelude alias at",
                "(= x 0) versus (zero? x)",
                "comments and formatting",
            ],
            "decision_scope": "replace selected racket_target.target_code only; preserve both archival raw_code strings",
            "proof_limit": "Finite domain probe plus source review; canonical program_solution remains the authority.",
        },
    }
    out = Path(__file__).with_name("manual_equivalence_probe.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("total_cases", "racket_evaluations", "mismatch_count", "canonical_label_failure_count")}, sort_keys=True))
    return 0 if not mismatches and not canonical_label_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
