#!/usr/bin/env python3
"""Reproduce the two assignment audit targets' advertised-axis defects.

This probe is intentionally read-only: it dynamically loads the frozen target
sources, records exact seeds/overrides and emitted grids, and writes compact JSON
reports. Run from the packet's ``repo`` directory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
PACKET_ROOT = REPO.parent
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _grid_sha(grid: Any) -> str:
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    return _sha_bytes(raw)


def _load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _attempt(fn: Callable[[], Any], *, seed: int, sample_index: int,
             difficulty: str | None, overrides: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
    }
    try:
        value = fn()
    except Exception as exc:  # This is the contract failure being recorded.
        record.update({
            "status": "raised",
            "exception": type(exc).__name__,
            "message": str(exc),
        })
    else:
        record.update({"status": "returned", "value": value})
    return record


def _metadata(task_id: str, source: Path) -> dict[str, Any]:
    manifest = json.loads((PACKET_ROOT / "PACKET-MANIFEST.json").read_text())
    row = manifest["generators"][task_id]
    source_sha = _sha_bytes(source.read_bytes())
    if source_sha != row["generator_sha256"]:
        raise RuntimeError(
            f"audit target changed: {task_id} {source_sha} != {row['generator_sha256']}"
        )
    return {
        "task_id": task_id,
        "generator_sha256": source_sha,
        "rule_hash": row["rule_hash"],
        "source": source.relative_to(PACKET_ROOT).as_posix(),
        "command": [
            "python3",
            "generators/fd277c567993/workspace/audit_contract_probe.py",
            "--out",
            "../checks/audit",
        ],
        "cwd": "repo",
    }


def probe_rows() -> dict[str, Any]:
    task_id = "2a5919c40197"
    gen, source = _load(task_id)
    report = _metadata(task_id, source)
    report["classification"] = (
        "reproduced advertised-domain and declared-degenerate defects"
    )

    seed, index = 271828, 11
    report["probes"] = {
        "advertised_grid_h_18_easy": _attempt(
            lambda: gen.generate(seed, index, difficulty="easy", grid_h=18),
            seed=seed,
            sample_index=index,
            difficulty="easy",
            overrides={"grid_h": 18},
        ),
        "advertised_palette_size_10_medium": _attempt(
            lambda: gen.generate(
                seed, index, difficulty="medium", palette_size=10
            ),
            seed=seed,
            sample_index=index,
            difficulty="medium",
            overrides={"palette_size": 10},
        ),
    }
    grid = gen.generate(seed, index, difficulty="medium", texture="all_uniform")
    report["probes"]["declared_texture_all_uniform"] = {
        "seed": seed,
        "sample_index": index,
        "difficulty": "medium",
        "overrides": {"texture": "all_uniform"},
        "shape": [len(grid), len(grid[0])],
        "grid": grid,
        "grid_sha256": _grid_sha(grid),
        "self_check": gen.self_check(grid, difficulty="medium"),
    }
    return report


def probe_diagonals() -> dict[str, Any]:
    task_id = "0db6c0c84cfa"
    gen, source = _load(task_id)
    report = _metadata(task_id, source)
    report["classification"] = (
        "reproduced inert control, advertised-domain, and declared-degenerate defects"
    )

    seed, index = 314159, 26
    grids = {
        name: gen.generate(
            seed,
            index,
            difficulty="medium",
            **({} if name == "default" else {"palette_kind": name}),
        )
        for name in ("default", "warm", "cool", "varied")
    }
    report["probes"] = {
        "palette_kind_inert": {
            "seed": seed,
            "sample_index": index,
            "difficulty": "medium",
            "overrides_tested": [
                {},
                {"palette_kind": "warm"},
                {"palette_kind": "cool"},
                {"palette_kind": "varied"},
            ],
            "hashes": {name: _grid_sha(grid) for name, grid in grids.items()},
            "all_identical": len(
                {
                    json.dumps(grid, separators=(",", ":"))
                    for grid in grids.values()
                }
            )
            == 1,
            "representative_grid": grids["default"],
        },
        "advertised_segments_8_easy": _attempt(
            lambda: gen.generate(seed, index, difficulty="easy", segments=8),
            seed=seed,
            sample_index=index,
            difficulty="easy",
            overrides={"segments": 8},
        ),
        "advertised_grid_h_5_hard": _attempt(
            lambda: gen.generate(seed, index, difficulty="hard", grid_h=5),
            seed=seed,
            sample_index=index,
            difficulty="hard",
            overrides={"grid_h": 5},
        ),
    }
    grid = gen.generate(seed, index, difficulty="easy", texture="no_pairs")
    report["probes"]["declared_texture_no_pairs"] = {
        "seed": seed,
        "sample_index": index,
        "difficulty": "easy",
        "overrides": {"texture": "no_pairs"},
        "grid": grid,
        "grid_sha256": _grid_sha(grid),
        "self_check": gen.self_check(grid, difficulty="easy"),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    reports = (probe_rows(), probe_diagonals())
    for report in reports:
        path = out / report["task_id"] / "probe.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
