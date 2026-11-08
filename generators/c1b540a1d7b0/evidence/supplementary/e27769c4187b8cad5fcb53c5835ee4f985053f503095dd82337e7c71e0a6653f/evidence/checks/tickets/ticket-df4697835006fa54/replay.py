#!/usr/bin/env python3
"""Bounded replay of the pinned c1b540a1d7b0 audit witness."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "c1b540a1d7b0"
TICKET_ID = "ticket-df4697835006fa54"
EXPECTED_SOURCE_SHA256 = "d1b226159005a11632c5b3f034899a7caa9a27034356e29db2edd081c97e2bb1"
EXPECTED_RULE_HASH = "e925582a7078"
EXPECTED_INDEX_SHA256 = "2a1b922d8b69e8df8a0b54ebd712e9b2a7de1aa2995f3aedebc26f51b204f54f"
EXPECTED_ASSETS_SHA256 = "9597b66982cb331fac2e497bf7a9f8202249b3c712c5656a830db9e8d8334be4"
EXPECTED_AUDIT_RECORD_SHA256 = "23e92bf5c32a7928e24e26d44ebace57e3799bc790ff6e1a8df90026acabbb3e"
RETURN_ID = "review-ee712525c29d5227:v0001"
INDEX_REL = Path("generators/c1b540a1d7b0/evidence/review_index.json")
ASSETS_REL = Path("generators/c1b540a1d7b0/counterexamples/review-ee712525c29d5227-v0001/audit_assets.json")
RETAINED_REL = Path("generators/c1b540a1d7b0/counterexamples/review-ee712525c29d5227-v0001/retained/checks/audit-c1b540a1d7b0-counterexample.json")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_row(root: Path) -> dict:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task missing: {TASK_ID}")


def components(grid, value=5):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] != value or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in CARDINAL:
                    nxt = row + drow, col + dcol
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == value):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(cells)
    return result


def normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return (row0, col0), tuple(sorted((row - row0, col - col0) for row, col in cells))


def racket_output(program: str, grid):
    callable_rule = wrap_rule(program)
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        bridge.eval_text(f"(define __ticket_rule {callable_rule})")
        bridge.define_grid("__ticket_input", grid)
        return bridge.eval_text("(__ticket_rule __ticket_input)")


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    index_path = root / INDEX_REL
    assets_path = root / ASSETS_REL
    retained_path = root / RETAINED_REL
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assets = json.loads(assets_path.read_text(encoding="utf-8"))
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    audit_record = next(row for row in index["audits"] if row.get("return_id") == RETURN_ID)
    audit_record_sha256 = hashlib.sha256(
        json.dumps(audit_record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    asset_checks = []
    for row in assets["files"]:
        path = root / row["path"]
        asset_checks.append({
            "path": row["path"],
            "exists": path.is_file(),
            "bytes_match": path.is_file() and path.stat().st_size == row["bytes"],
            "sha256_match": path.is_file() and sha256(path) == row["sha256"],
        })

    canonical = canonical_row(root)
    normalized_rule = " ".join(canonical["program_solution"].split())
    rule_hash = hashlib.sha256(normalized_rule.encode()).hexdigest()[:12]
    seed, sample_index, difficulty = 123_002, 15, "medium"
    grid = generator.generate(seed, sample_index, difficulty=difficulty)

    official_pair = next(
        pair for pair in canonical["train"]
        if len(pair["input"]) == 8
        and len(pair["input"][0]) == 9
        and len(components(pair["input"])) == 2
    )
    templates = {}
    for component in components(official_pair["input"]):
        (row0, col0), shape = normalize(component)
        templates[shape] = {
            (row - row0, col - col0): official_pair["output"][row][col]
            for row, col in component
        }
    rival = [[0 for _ in source_row] for source_row in grid]
    replay_shapes = []
    for component in components(grid):
        (row0, col0), shape = normalize(component)
        replay_shapes.append([list(point) for point in shape])
        template = templates.get(shape)
        if template is None:
            continue
        for (drow, dcol), color in template.items():
            rival[row0 + drow][col0 + dcol] = color
    actual = racket_output(canonical["program_solution"], grid)

    checks = {
        "source_identity_matches_ticket": source_sha256 == EXPECTED_SOURCE_SHA256,
        "rule_identity_matches_ticket": rule_hash == EXPECTED_RULE_HASH == generator.RULE_HASH,
        "audit_index_identity_matches_ticket": sha256(index_path) == EXPECTED_INDEX_SHA256,
        "assets_manifest_identity_matches_ticket": sha256(assets_path) == EXPECTED_ASSETS_SHA256,
        "audit_record_identity_matches_ticket": audit_record_sha256 == EXPECTED_AUDIT_RECORD_SHA256,
        "all_retained_assets_match_manifest": all(
            row["exists"] and row["bytes_match"] and row["sha256_match"] for row in asset_checks
        ),
        "generated_input_matches_retained_witness": grid == retained["input"],
        "validator_accepts": generator.self_check(grid) == [],
        "racket_output_matches_retained_witness": actual == retained["actual_racket_output"],
        "template_rival_matches_retained_witness": rival == retained["rival_output"],
        "template_rival_matches_current_racket": rival == actual,
    }
    result = {
        "schema": "arcpuzzles-bounded-audit-replay-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "audit_return_id": RETURN_ID,
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha256,
            "expected_sha256": EXPECTED_SOURCE_SHA256,
        },
        "rule_hash_12": rule_hash,
        "identity": {
            "review_index_sha256": sha256(index_path),
            "assets_manifest_sha256": sha256(assets_path),
            "audit_record_sha256": audit_record_sha256,
        },
        "asset_checks": asset_checks,
        "generation": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {},
        },
        "input": grid,
        "normalized_component_shapes": replay_shapes,
        "actual_racket_output": actual,
        "template_rival_output": rival,
        "checks": checks,
        "all_passed": all(checks.values()),
        "interpretation": (
            "The pinned lawful default witness reproduced under the retained source, rule, "
            "index, audit-record, and asset identities. A bitmap-template rival exactly matches "
            "the current canonical Racket output; this replay does not clear or broaden the audit."
        ),
    }
    output_path = Path(__file__).with_name("replay.json")
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_passed": result["all_passed"],
        "assets_verified": len(asset_checks),
        "template_rival_matches_current_racket": checks["template_rival_matches_current_racket"],
        "output": str(output_path),
    }, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
