#!/usr/bin/env python3
"""Bounded sampler/privacy stress probe for the db63430eeffa path-mode prototype."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def load_prototype(root: Path):
    path = root / "generators/db63430eeffa/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("db63430eeffa_path_stress", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(root: Path, *, seeds: int) -> dict:
    p = load_prototype(root)
    records = []
    input_signatures = {}
    public_ids = set()
    for seed in range(seeds):
        per_seed = {}
        for mode in p.PATH_MODES:
            episode = p.generate_episode(seed, path_mode=mode, root=root)
            analysis = p.analyze_episode(episode)
            assert analysis["identified"], (seed, mode, analysis)
            assert analysis["all_queries_distinct"]
            assert analysis["queries_disjoint_from_demos"]
            assert len(episode["train"]) == 3 and len(episode["test"]) == 4
            pair_input_hashes = tuple(
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            )
            per_seed[mode] = pair_input_hashes
            public = p.public_challenge(episode)
            assert set(public) == {"train", "test"}
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            before = p.public_id(episode)
            altered = copy.deepcopy(episode)
            altered["program"] = "private-change"
            altered["meta"]["seed"] = seed + 100000
            for pair in altered["test"]:
                pair["output"] = [[9]]
            assert p.public_id(altered) == before
            assert hashlib.sha256(p.public_bytes(episode)).hexdigest() == before
            assert before not in public_ids
            public_ids.add(before)
            records.append(
                {
                    "seed": seed,
                    "path_mode": mode,
                    "public_id": before,
                    "surviving_modes": analysis["surviving_modes"],
                    "input_hashes": pair_input_hashes,
                }
            )
        assert len(set(per_seed.values())) == 1, (seed, per_seed)
        input_signatures[seed] = next(iter(per_seed.values()))
    assert len(set(input_signatures.values())) == len(input_signatures)
    return {
        "schema": "arcpuzzles-path-selection-adversarial-v1",
        "status": "pass",
        "seeds_checked": seeds,
        "settings_checked": list(p.PATH_MODES),
        "episodes_checked": len(records),
        "pairs_checked": len(records) * 7,
        "unique_public_ids": len(public_ids),
        "unique_input_sets": len(set(input_signatures.values())),
        "checks": [
            "three demos identify exactly one declared setting",
            "four queries are distinct and disjoint from demos",
            "all settings share identical sampled inputs for a seed",
            "public projection contains no setting, program, sampling, or query outputs",
            "public id is SHA-256 of exact visible bytes and ignores private mutations",
            f"all {seeds} seeds yield distinct seven-input episode signatures",
        ],
        "record_digest_sha256": hashlib.sha256(
            json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds <= 0:
        raise ValueError("seeds must be positive")
    report = run(args.root.resolve(), seeds=args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
