"""Build exact hash-named public projections for the marker-role family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]


def _load_prototype():
    path = HOME / "prototype.py"
    name = "_arc_7c2b3290ba62_public_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _public_episode(episode: dict) -> dict:
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def run(output: Path, *, seed: int = 0, demos: int = 3) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing existing output: {output}")
    output.mkdir(parents=True)
    aggregate_dir = output / "public"
    turn_dir = output / "turns"
    aggregate_dir.mkdir()
    turn_dir.mkdir()

    sys.path[:0] = [str(ROOT / "shared/runtime")]
    from reviewer_support import public_challenge_bytes

    prototype = _load_prototype()
    settings_report = []
    for mode in prototype.MODES:
        episode = prototype.generate(seed, {"marker_mode": mode}, demos, 4)
        aggregate = _public_episode(episode)
        aggregate_bytes = public_challenge_bytes(aggregate)
        aggregate_id = hashlib.sha256(aggregate_bytes).hexdigest()
        (aggregate_dir / f"challenge-{aggregate_id}.json").write_bytes(aggregate_bytes)

        turn_ids = []
        for query_index in range(4):
            turn = prototype.public_turn(episode, query_index)
            turn_bytes = public_challenge_bytes(turn)
            turn_id = hashlib.sha256(turn_bytes).hexdigest()
            (turn_dir / f"challenge-{turn_id}.json").write_bytes(turn_bytes)
            turn_ids.append(turn_id)
        first_turn = prototype.public_turn(episode, 0)
        direct = {
            "train": aggregate["train"],
            "test": [aggregate["test"][0]],
        }
        settings_report.append({
            "marker_mode": mode,
            "demo_count": demos,
            "stored_query_count": 4,
            "queries_revealed_per_turn": [1, 1, 1, 1],
            "aggregate_public_id": aggregate_id,
            "turn_public_ids": turn_ids,
            "first_turn_matches_direct_projection": first_turn == direct,
        })

    report = {
        "schema": "7c2b3290ba62-public-projection-v1",
        "private_fields_excluded": ["settings", "seed", "program_solution", "test.output"],
        "settings": settings_report,
    }
    (output / "public_projection.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args(argv)
    report = run(args.out, seed=args.seed, demos=args.demos)
    print(json.dumps({"status": "passed", "settings": len(report["settings"]), "report": str(args.out / "public_projection.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
