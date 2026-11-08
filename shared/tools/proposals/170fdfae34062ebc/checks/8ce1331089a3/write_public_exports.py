#!/usr/bin/env python3
"""Write canonical public challenge bytes for both 8ce1331089a3 settings."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes  # noqa: E402


def load_adapter():
    path = REPO / "generators/8ce1331089a3/workspace/parametric/adapter.py"
    name = "_public_projection_8ce1331089a3_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()

    out = args.out.resolve()
    summary = args.summary.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    summary.parent.mkdir(parents=True, exist_ok=True)

    adapter = load_adapter()
    rows = []
    for path_rule in ("wall_endpoint", "dominant_trace"):
        episode = adapter.generate(
            args.seed,
            {"path_rule": path_rule},
            args.demos,
            args.queries,
        )
        payload = public_challenge_bytes(episode)
        digest = hashlib.sha256(payload).hexdigest()
        destination = out / f"{digest}.json"
        destination.write_bytes(payload)
        rows.append({
            "path_rule": path_rule,
            "public_path": str(destination.relative_to(WORK)),
            "public_sha256": digest,
            "bytes": len(payload),
            "demonstrations": args.demos,
            "queries": args.queries,
        })

    report = {
        "schema": "arcpuzzles-public-projection-samples-v1",
        "task_id": "8ce1331089a3",
        "seed": args.seed,
        "status": "written",
        "files": rows,
        "limits": "Saved public projections only; labels and private metadata remain in qualification evidence.",
    }
    summary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
