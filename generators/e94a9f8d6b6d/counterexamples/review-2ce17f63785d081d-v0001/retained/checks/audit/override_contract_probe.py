#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def attempt(fn):
    try:
        grid = fn()
        return {
            "status": "returned",
            "shape": [len(grid), len(grid[0]) if grid else 0],
            "grid_sha256": digest(grid),
        }
    except Exception as exc:
        return {
            "status": "raised",
            "exception": type(exc).__name__,
            "message": str(exc),
        }


def observe_query_key(mod, grid):
    frames = sorted(mod._find_marker_frames(grid, 2, 3, 4), key=lambda frame: frame[0][0])
    if len(frames) != 3:
        return {"error": f"expected 3 source frames, got {len(frames)}"}

    def motif(frame):
        origin, vx, vy = frame
        cells = []
        for u, v in mod._LOCAL_CELLS:
            r, c = mod._gpos(origin, vx, vy, u, v)
            if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] == 8:
                cells.append([u, v])
        return sorted(cells)

    motifs = [motif(frame) for frame in frames]
    observed = 0 if motifs[2] == motifs[0] else 1 if motifs[2] == motifs[1] else None
    return {"source_motifs": motifs, "observed_query_key": observed}


def main() -> int:
    repo = Path.cwd()
    out_root = Path(sys.argv[1])
    out_root.mkdir(parents=True, exist_ok=True)

    p58 = repo / "generators/58e533041a8e/generator.py"
    g58 = load(p58, "audit_58")
    report58 = {
        "schema": "arc-audit-override-contract-v1",
        "task_id": "58e533041a8e",
        "generator_sha256": hashlib.sha256(p58.read_bytes()).hexdigest(),
        "canonical_rule_hash": "4148ae94058b",
        "command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audit/override_contract_probe.py", "../checks/audit"
        ],
        "cwd": "packet_root",
        "declared_axes": g58.AXES,
        "cases": [
            {
                "name": "advertised_grid_h_rejected_in_easy",
                "seed": 17,
                "sample_index": 0,
                "difficulty": "easy",
                "overrides": {"grid_h": 10},
                "result": attempt(lambda: g58.generate(17, 0, difficulty="easy", grid_h=10)),
            },
            {
                "name": "advertised_palette_size_lower_bound_rejected",
                "seed": 17,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": {"palette_size": 1},
                "result": attempt(lambda: g58.generate(17, 0, difficulty="medium", palette_size=1)),
            },
            {
                "name": "unknown_override_silently_accepted",
                "seed": 17,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": {"__override_contract_unknown_axis__": 1},
                "result": attempt(lambda: g58.generate(17, 0, difficulty="medium", __override_contract_unknown_axis__=1)),
            },
        ],
    }
    (out_root / "58e533041a8e" / "override_contract_probe.json").write_text(
        json.dumps(report58, indent=2) + "\n"
    )

    pe = repo / "generators/e94a9f8d6b6d/generator.py"
    ge = load(pe, "audit_e94")
    seed, sample_index = 20261004, 11
    q0 = ge.generate(seed, sample_index, difficulty="medium", query_key=0)
    q1 = ge.generate(seed, sample_index, difficulty="medium", query_key=1)
    v0 = ge.generate(seed, sample_index, difficulty="medium", variant=0)
    v3 = ge.generate(seed, sample_index, difficulty="medium", variant=3)
    report_e = {
        "schema": "arc-audit-override-contract-v1",
        "task_id": "e94a9f8d6b6d",
        "generator_sha256": hashlib.sha256(pe.read_bytes()).hexdigest(),
        "canonical_rule_hash": ge.RULE_HASH,
        "command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audit/override_contract_probe.py", "../checks/audit"
        ],
        "cwd": "packet_root",
        "declared_axes": ge.AXES,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "query_key_case": {
            "requested": [0, 1],
            "byte_identical": q0 == q1,
            "grid_sha256": [digest(q0), digest(q1)],
            "observed_q0": observe_query_key(ge, q0),
            "observed_q1": observe_query_key(ge, q1),
            "self_check_q0": ge.self_check(q0),
            "self_check_q1": ge.self_check(q1),
            "input_grid": q0,
        },
        "variant_case": {
            "requested": [0, 3],
            "byte_identical": v0 == v3,
            "grid_sha256": [digest(v0), digest(v3)],
        },
        "unknown_override": attempt(
            lambda: ge.generate(seed, sample_index, difficulty="medium", __override_contract_unknown_axis__=1)
        ),
    }
    (out_root / "e94a9f8d6b6d" / "override_contract_probe.json").write_text(
        json.dumps(report_e, indent=2) + "\n"
    )
    print(json.dumps({
        "58e533041a8e": report58["cases"],
        "e94a9f8d6b6d": {
            "query_key_byte_identical": q0 == q1,
            "observed": [observe_query_key(ge, q0)["observed_query_key"], observe_query_key(ge, q1)["observed_query_key"]],
            "variant_byte_identical": v0 == v3,
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
