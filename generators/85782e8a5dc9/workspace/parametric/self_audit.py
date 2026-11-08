"""Bounded learnability and boundary audit for the transfer-count adapter."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType


HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "adapter.py"


def _load_adapter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_85782e8a5dc9_transfer_count_audit_adapter", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict[str, object]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def run_audit(*, seeds: int = 64) -> dict[str, object]:
    if type(seeds) is not int or not 1 <= seeds <= 1024:
        raise ValueError("seeds must be an exact integer in 1..1024")
    adapter = _load_adapter()
    failures: list[dict[str, object]] = []
    transforms: Counter[str] = Counter()
    episodes = 0
    stress = 0
    pair_count = 0
    for seed in range(seeds):
        for demos in (2, 3, 6):
            try:
                generated = {
                    setting: adapter.generate(seed, {"applications": setting}, demos, 4)
                    for setting in adapter.APPLICATIONS
                }
                once_inputs = _inputs(generated["once"])
                if once_inputs != _inputs(generated["twice"]):
                    raise AssertionError("inputs differ across settings")
                for setting, episode in generated.items():
                    certificate = adapter.certificate(
                        episode["train"], [pair["input"] for pair in episode["test"]]
                    )
                    if certificate["survivors"] != [setting]:
                        raise AssertionError(f"unexpected survivors for {setting}: {certificate['survivors']}")
                    if len(episode["test"][-1]["input"]) != 30 or len(episode["test"][-1]["input"][0]) != 30:
                        raise AssertionError("fourth query is not 30x30")
                    stress += 1
                    episodes += 1
                    pair_count += len(episode["train"]) + len(episode["test"])
                    transforms.update(adapter.observe(pair["input"])["transform"] for pair in episode["train"] + episode["test"])
                if any(
                    left["output"] == right["output"]
                    for left, right in zip(generated["once"]["test"], generated["twice"]["test"])
                ):
                    raise AssertionError("at least one query does not distinguish once from twice")
            except Exception as exc:  # Preserve the bounded failing seed/count for replay.
                failures.append({
                    "seed": seed,
                    "demos": demos,
                    "type": type(exc).__name__,
                    "message": str(exc),
                })
    return {
        "schema": "85782e8a5dc9-transfer-count-self-audit-v1",
        "status": "passed" if not failures else "failed",
        "adapter_sha256": hashlib.sha256(ADAPTER_PATH.read_bytes()).hexdigest(),
        "seed_count": seeds,
        "demo_counts": [2, 3, 6],
        "settings": list(adapter.APPLICATIONS),
        "episodes": episodes,
        "pairs": pair_count,
        "stress_30x30": stress,
        "transform_counts": dict(sorted(transforms.items())),
        "declared_hypotheses": list(adapter.HYPOTHESES),
        "failures": failures,
        "scope": "Finite declared rivals and deterministic seeds only; no universal uniqueness claim.",
    }


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _args()
    report = run_audit(seeds=args.seeds)
    data = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(data, encoding="utf-8")
    else:
        print(data, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
