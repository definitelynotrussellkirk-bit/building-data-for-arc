#!/usr/bin/env python3
"""Replay frozen baseline visible bytes without modifying the selected task."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
TASK = "506e262f9354"
BASELINE = (
    WORK / ".review/baseline/repo/generators" / TASK / "workspace/parametric/prototype.py"
)
BASELINE_GENERATOR = WORK / ".review/baseline/repo/generators" / TASK / "generator.py"
CURRENT_GENERATOR = REPO / "generators" / TASK / "generator.py"
TEMP_PARENT = REPO / "generators" / TASK / "workspace/parametric"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path, default=HERE / "baseline-seed-1")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError(out)
    if sha256(BASELINE_GENERATOR) != sha256(CURRENT_GENERATOR):
        raise RuntimeError("baseline replay requires the unchanged production generator")

    temp_dir = Path(tempfile.mkdtemp(prefix=".baseline-replay-", dir=TEMP_PARENT))
    temp_module = temp_dir / "prototype.py"
    try:
        temp_module.write_bytes(BASELINE.read_bytes())
        spec = importlib.util.spec_from_file_location("baseline_parametric_506e262f9354", temp_module)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load frozen baseline prototype")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pending = []
        with module.RacketBridge() as bridge:
            for direction in module.ALLOWED_DIRECTIONS:
                episode = module.make_episode(
                    args.seed,
                    expansion_direction=direction,
                    root=REPO,
                    bridge=bridge,
                )
                visible_id = module.public_id(episode)
                pending.append((visible_id, module.public_bytes(episode), direction))
        public = out / "public"
        public.mkdir(parents=True)
        rows = []
        for visible_id, payload, direction in sorted(pending):
            path = public / f"challenge-{visible_id}.json"
            path.write_bytes(payload)
            rows.append(
                {
                    "direction": direction,
                    "path": path.relative_to(out).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
        receipt = {
            "schema": "arcpuzzles-frozen-baseline-public-replay-v1",
            "task_id": TASK,
            "seed": args.seed,
            "baseline_prototype_sha256": sha256(BASELINE),
            "generator_sha256": sha256(CURRENT_GENERATOR),
            "files": rows,
            "scope": "visible challenge bytes only; no approval or production change",
        }
        (out / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, sort_keys=True))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
