#!/usr/bin/env python3
"""Materialize the packet replay witness from detailed Racket evidence and qualification."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def _load_prototype(repo: Path):
    path = repo / "generators/db63430eeffa/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("_db63430eeffa_witness_builder", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--detail", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    prototype = _load_prototype(repo)
    detail = json.loads(args.detail.read_text(encoding="utf-8"))
    qualification = json.loads(args.qualification.read_text(encoding="utf-8"))
    setting_key = json.dumps(
        detail["setting"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    digest = hashlib.sha256(detail["correct_program"].encode("utf-8")).hexdigest()
    if qualification.get("programs", {}).get(setting_key) != digest:
        raise ValueError("detailed witness program is not the qualified setting program")

    witness = prototype.build_admission_witness(
        detail,
        qualification["source_binding"],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(
        json.dumps(witness, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.out)
    print(json.dumps({
        "status": "written",
        "path": str(args.out),
        "cases": len(witness["cases"]),
        "differing_cell_count": witness["cases"][0]["differing_cell_count"],
        "program_sha256": digest,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
