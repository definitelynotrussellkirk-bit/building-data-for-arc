#!/usr/bin/env python3
"""Bounded replay of the retained a0e364b16592 blocker-segmentation audit."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TICKET_ID = "ticket-abdbdbca9ff76d39"
TASK_ID = "a0e364b16592"
RETURN_ID = "review-88c7a032551f492e:v0001"
EXPECTED_SOURCE_SHA256 = "ef8a2f160f6d5bdbcb9ec90ea9386db674688001eedba51fce050a5df56d482f"
EXPECTED_INDEX_SHA256 = "361d2280882113792ce0d075e2d137b582e8b8b1c760d1f004fcc2aaf35d134f"
EXPECTED_ASSETS_SHA256 = "1741ee3e68858a819e865bd9f845706c3944aebd3b6ad142ca0864f4941aadf3"
EXPECTED_AUDIT_RECORD_SHA256 = "4fa24de0dd6d76a7d568350810947e2a4da9424dfbbd31ae45aeb9db98b69504"
EXPECTED_RULE_HASH = "f2466dabadf4"
TICKET_SEED = "1ab5185236689c62884f781c5002b0f5fe0aaeb064f4ded3743e60c0b4ac972b"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def compact_json_sha256(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(body)


def canonical_source(root: Path) -> str:
    sources = set()
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
            sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one canonical source, got {len(sources)}")
    return sources.pop()


def grid_literal(grid: Any) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in normalize_grid(grid))
    return f"'({rows})"


def execute(source: str, grid: Any, bridge: RacketBridge) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {grid_literal(grid)})"))


def rival_global_bottom_preserve_5(grid: Any) -> list[list[int]]:
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        vals = [grid[r][c] for r in range(h) if grid[r][c] not in (0, 5)]
        for r in range(h):
            if grid[r][c] == 5:
                out[r][c] = 5
        start = h - len(vals)
        for r, value in enumerate(vals, start=start):
            out[r][c] = value
    return out


def select_64(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    limits = {"easy": 22, "medium": 21, "hard": 21}
    used: Counter[str] = Counter()
    selected = []
    for row in rows:
        band = row["band"]
        if used[band] < limits[band]:
            selected.append(row)
            used[band] += 1
    if len(selected) != 64:
        raise ValueError(f"selected {len(selected)} rows")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    task_root = root / "generators" / TASK_ID
    audit_root = task_root / "counterexamples" / "review-88c7a032551f492e-v0001"
    index_path = task_root / "evidence" / "review_index.json"
    assets_path = audit_root / "audit_assets.json"

    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assets = json.loads(assets_path.read_text(encoding="utf-8"))
    audit = next(row for row in index["audits"] if row.get("return_id") == RETURN_ID)

    identity = {
        "source_sha256": source_sha256,
        "source_matches": source_sha256 == EXPECTED_SOURCE_SHA256,
        "audit_index_sha256": sha256_path(index_path),
        "audit_index_matches": sha256_path(index_path) == EXPECTED_INDEX_SHA256,
        "assets_manifest_sha256": sha256_path(assets_path),
        "assets_manifest_matches": sha256_path(assets_path) == EXPECTED_ASSETS_SHA256,
        "audit_record_sha256": compact_json_sha256(audit),
        "audit_record_matches": compact_json_sha256(audit) == EXPECTED_AUDIT_RECORD_SHA256,
        "audit_source_matches": audit.get("source_sha256") == EXPECTED_SOURCE_SHA256,
        "audit_assets_binding_matches": audit.get("assets_manifest_sha256") == EXPECTED_ASSETS_SHA256,
    }

    asset_checks = []
    for row in assets["files"]:
        path = root / row["path"]
        actual_sha = sha256_path(path)
        actual_bytes = path.stat().st_size
        asset_checks.append({
            "path": row["path"],
            "expected_sha256": row["sha256"],
            "actual_sha256": actual_sha,
            "expected_bytes": row["bytes"],
            "actual_bytes": actual_bytes,
            "matches": actual_sha == row["sha256"] and actual_bytes == row["bytes"],
        })

    retained = audit_root / "retained" / "checks" / "audit" / TASK_ID
    retained_inputs = json.loads((retained / "generated_inputs_64.json").read_text())["inputs"]
    retained_rivals = json.loads((retained / "rival_generated_outputs_64.json").read_text())["outputs"]
    counter_input = json.loads((retained / "input.json").read_text())
    retained_counter_racket = json.loads((retained / "racket.json").read_text())["results"][0]["output"]
    retained_counter_rival = json.loads((retained / "rival_counterexample_output.json").read_text())["output"]

    generated = []
    for band_idx, band in enumerate(("easy", "medium", "hard")):
        for i in range(100):
            seed = band_idx * 100_000 + i
            grid = normalize_grid(generator.generate(seed, i, difficulty=band))
            errors = list(generator.self_check(grid, difficulty=band, meta={}))
            generated.append({"band": band, "seed": seed, "sample_index": i, "grid": grid, "errors": errors})
    selected = select_64(generated)
    selected_inputs = [row["grid"] for row in selected]
    rival_outputs = [rival_global_bottom_preserve_5(grid) for grid in selected_inputs]

    source = canonical_source(root)
    with RacketBridge(max_calls_before_restart=256) as bridge:
        racket_outputs = [execute(source, grid, bridge) for grid in selected_inputs]
        counter_racket = execute(source, counter_input, bridge)
        runtime_identity = bridge.runtime_identity

    counter_rival = rival_global_bottom_preserve_5(counter_input)
    sampler = {
        "draws": len(generated),
        "self_check_failures": sum(bool(row["errors"]) for row in generated),
        "generated_with_color_5": sum(any(cell == 5 for line in row["grid"] for cell in line) for row in generated),
        "generated_without_color_5": sum(not any(cell == 5 for line in row["grid"] for cell in line) for row in generated),
        "selected_inputs_match_retained": selected_inputs == retained_inputs,
        "selected_inputs_sha256": compact_json_sha256(selected_inputs),
    }
    shortcut = {
        "generated_sample_count": len(selected_inputs),
        "generated_matches": sum(actual == rival for actual, rival in zip(racket_outputs, rival_outputs)),
        "generated_outputs_all_match_rival": all(actual == rival for actual, rival in zip(racket_outputs, rival_outputs)),
        "rival_outputs_match_retained": rival_outputs == retained_rivals,
        "counterexample_self_check": list(generator.self_check(counter_input, difficulty=None, meta={})),
        "counterexample_racket_matches_retained": counter_racket == retained_counter_racket,
        "counterexample_rival_matches_retained": counter_rival == retained_counter_rival,
        "counterexample_differs": counter_racket != counter_rival,
    }
    reproduced = (
        all(value for key, value in identity.items() if key.endswith("_matches"))
        and all(row["matches"] for row in asset_checks)
        and sampler["draws"] == 300
        and sampler["self_check_failures"] == 0
        and sampler["generated_with_color_5"] == 0
        and sampler["selected_inputs_match_retained"]
        and shortcut["generated_sample_count"] == 64
        and shortcut["generated_matches"] == 64
        and shortcut["rival_outputs_match_retained"]
        and shortcut["counterexample_self_check"] == []
        and shortcut["counterexample_racket_matches_retained"]
        and shortcut["counterexample_rival_matches_retained"]
        and shortcut["counterexample_differs"]
    )
    result = {
        "schema": "arcpuzzles-audit-replay-v1",
        "ticket_id": TICKET_ID,
        "type": "audit_replay",
        "consumer": "existing_audit_assessment",
        "task_id": TASK_ID,
        "ticket_seed": TICKET_SEED,
        "source_path": source_path.relative_to(root).as_posix(),
        "expected_rule_hash": EXPECTED_RULE_HASH,
        "canonical_source_sha256": sha256_bytes(source.encode()),
        "identity": identity,
        "asset_checks": asset_checks,
        "sampler": sampler,
        "shortcut": shortcut,
        "runtime_identity": runtime_identity,
        "reproduced": reproduced,
        "status": "completed" if reproduced else "unknown",
        "conclusion": (
            "Reproduced the pinned audit: 0/300 production draws contain blocker color 5; "
            "the global-bottom rival matches all 64 retained generated inputs; the retained "
            "validator-accepted blocker counterexample differs under exact canonical Racket."
            if reproduced
            else "One or more pinned audit claims did not reproduce; inspect the failed flags."
        ),
        "scope": "Bounded replay only; does not clear, broaden, or independently resolve the existing audit.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "status": result["status"],
        "reproduced": reproduced,
        "generated_with_color_5": sampler["generated_with_color_5"],
        "generated_matches": shortcut["generated_matches"],
        "counterexample_differs": shortcut["counterexample_differs"],
    }, sort_keys=True))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
