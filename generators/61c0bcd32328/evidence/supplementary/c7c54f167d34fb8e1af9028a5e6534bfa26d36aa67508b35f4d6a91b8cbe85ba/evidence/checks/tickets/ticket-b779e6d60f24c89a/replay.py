#!/usr/bin/env python3
"""One-probe replay of the pinned singleton-corner audit for 61c0bcd32328."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "61c0bcd32328"
TICKET_ID = "ticket-b779e6d60f24c89a"
RETURN_ID = "review-18e44a66ec02e372:v0001"
SOURCE_SHA256 = "3c0cd7f5e883c70aa52eb73b2672bada64daf54461a909f0ed0e7fb0e058220a"
ASSET_MANIFEST_SHA256 = "964da18e037708ea4755537cab0cb2b412be047bf6cb56594a5e209a785b92e5"
AUDIT_INDEX_SHA256 = "085192535359319437137a3aa8e0073ce75815b8ff6aa8f95fdb2b98b94767d3"
AUDIT_RECORD_SHA256 = "f1141c48c6adbdf4bfc37cd3aab338ffc14b0d4537b8ce404478770c3153652d"
RULE_HASH = "e3835c9a174e"
BASE = REPO / "generators" / TASK / "counterexamples" / "review-18e44a66ec02e372-v0001"
SOURCE = REPO / "generators" / TASK / "generator.py"
ASSET_MANIFEST = BASE / "audit_assets.json"
AUDIT_INDEX = REPO / "generators" / TASK / "evidence" / "review_index.json"
OUT = HERE / "replay.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode())[:12]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_generator_61c0", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def components(grid, background):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == background or (r, c) in seen:
                continue
            color = grid[r][c]
            cells = {(r, c)}
            seen.add((r, c))
            todo = [(r, c)]
            while todo:
                rr, cc = todo.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        todo.append((nr, nc))
            result.append((color, sorted(cells)))
    return result


def ignore_singletons_rival(grid):
    """Copy corner components exactly as authority does, except singleton noise."""
    h, w = len(grid), len(grid[0])
    background = Counter(v for row in grid for v in row if v != 0).most_common(1)[0][0]
    out = [row[:] for row in grid]
    for color, cells in components(grid, background):
        if len(cells) == 1:
            continue
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        if r1 == 0 and c1 == 0:
            dr, dc = 0, w - 1 - c2
        elif r1 == 0 and c2 == w - 1:
            dr, dc = h - 1 - r2, 0
        elif r2 == h - 1 and c2 == w - 1:
            dr, dc = 0, -c1
        elif r2 == h - 1 and c1 == 0:
            dr, dc = -r1, 0
        else:
            continue
        for r, c in cells:
            out[r + dr][c + dc] = color
    return out


def canonical_record():
    rows = []
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        if TASK not in line:
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    assert rows
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    pairs: dict[tuple[tuple[int, ...], ...], list[list[int]]] = {}
    occurrences = 0
    for row in rows:
        for split in ("train", "test"):
            examples = row[split]
            if isinstance(examples, dict):
                examples = [examples]
            for pair in examples:
                occurrences += 1
                inp = tuple(tuple(int(v) for v in values) for values in pair["input"])
                pairs.setdefault(inp, [[int(v) for v in values] for values in pair["output"]])
    return next(iter(programs)), pairs, occurrences


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)

    assert sha256_file(SOURCE) == SOURCE_SHA256
    assert sha256_file(ASSET_MANIFEST) == ASSET_MANIFEST_SHA256
    assert sha256_file(AUDIT_INDEX) == AUDIT_INDEX_SHA256

    manifest = json.loads(ASSET_MANIFEST.read_text())
    assert manifest["return_id"] == RETURN_ID
    assert manifest["audited_generator_sha256"] == SOURCE_SHA256
    verified_assets = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        actual = sha256_file(path)
        assert actual == row["sha256"], (path, actual, row["sha256"])
        verified_assets.append({
            "path": str(path.relative_to(REPO)),
            "sha256": actual,
            "bytes": path.stat().st_size,
        })

    index = json.loads(AUDIT_INDEX.read_text())
    matching = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
    assert len(matching) == 1
    audit_record = matching[0]
    assert sha256_json(audit_record) == AUDIT_RECORD_SHA256
    assert audit_record["source_sha256"] == SOURCE_SHA256
    assert audit_record["resolution"] == "unresolved"

    generator = load_module(SOURCE)
    overrides = {"scene_profile": "single_tl"}
    control = generator.generate(0, 0, difficulty="easy", **overrides)
    analysis = generator._analysis(control)
    assert len(analysis["corner_parts"]) == 1
    corner, part = analysis["corner_parts"][0]
    assert corner == "tl" and (0, 0) in part["cells"] and len(part["cells"]) >= 2
    witness = [row[:] for row in control]
    removed = sorted(part["cells"] - {(0, 0)})
    for r, c in removed:
        witness[r][c] = analysis["background"]
    inputs = [control, witness]

    validations = [generator.self_check(grid, difficulty="easy") for grid in inputs]
    observations = [generator.observe_overrides(grid) for grid in inputs]
    assert validations == [[], []]
    assert observations == [overrides, overrides]

    program, canonical_pairs, occurrences = canonical_record()
    assert normalized_rule_hash(program) == RULE_HASH == generator.RULE_HASH
    canonical_agreement = [
        ignore_singletons_rival([list(row) for row in inp]) == expected
        for inp, expected in canonical_pairs.items()
    ]
    assert all(canonical_agreement)

    bridge = RacketBridge(timeout=30, max_calls_before_restart=16)
    try:
        runtime = bridge.runtime_identity
        bridge.eval_text(f"(define __ticket_rule {wrap_rule(program)})")
        actual_outputs = []
        for index_value, grid in enumerate(inputs):
            name = f"__ticket_input_{index_value}"
            bridge.define_grid(name, grid)
            actual_outputs.append(bridge.eval_text(f"(__ticket_rule {name})"))
    finally:
        bridge.shutdown()

    mirrors = [generator.rule_mirror(grid) for grid in inputs]
    rivals = [ignore_singletons_rival(grid) for grid in inputs]
    assert actual_outputs == mirrors
    assert actual_outputs[0] == rivals[0]
    assert actual_outputs[1] != rivals[1]
    differences = [
        {"row": r, "col": c, "racket": value, "rival": rivals[1][r][c]}
        for r, row in enumerate(actual_outputs[1])
        for c, value in enumerate(row)
        if value != rivals[1][r][c]
    ]
    assert differences == [{"row": 0, "col": 7, "racket": 1, "rival": 4}]

    report = {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "reproduced",
        "task_id": TASK,
        "audit_return_id": RETURN_ID,
        "audit_not_cleared": True,
        "claim": (
            "A lawful singleton top-left corner mutation is accepted under the same "
            "profile; exact Racket copies it to (0,7), while the ignore-singletons rival does not."
        ),
        "source_binding": {
            "generator_sha256": SOURCE_SHA256,
            "assets_manifest_sha256": ASSET_MANIFEST_SHA256,
            "audit_index_sha256": AUDIT_INDEX_SHA256,
            "audit_record_sha256": AUDIT_RECORD_SHA256,
            "rule_hash": RULE_HASH,
        },
        "asset_files_verified": verified_assets,
        "witness": {
            "seed": 0,
            "sample_index": 0,
            "difficulty": "easy",
            "overrides": overrides,
            "removed_cells": [list(cell) for cell in removed],
            "control_input_sha256": sha256_json(control),
            "singleton_input_sha256": sha256_json(witness),
            "self_check": validations,
            "observed_overrides": observations,
            "canonical_unique_pairs": len(canonical_pairs),
            "canonical_pair_occurrences": occurrences,
            "rival_matches_canonical": canonical_agreement,
            "racket_output_sha256": sha256_json(actual_outputs[1]),
            "rival_output_sha256": sha256_json(rivals[1]),
            "differences": differences,
        },
        "racket_runtime": runtime,
        "limitations": [
            "One generated control and one one-cell mutation only; no random-seed census or peer battery.",
            "Reproduction confirms the bounded witness and does not automatically clear or broaden the audit.",
        ],
        "command": f"python3 review.py run python3 ../checks/tickets/{TICKET_ID}/replay.py",
        "probe_sha256": sha256_file(Path(__file__)),
    }
    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "reproduced", "differences": differences, "out": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
