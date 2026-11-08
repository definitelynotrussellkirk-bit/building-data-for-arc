#!/usr/bin/env python3
"""Bounded Racket-backed probe for the d3c9 rewrite-mode prototype."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_d3c9_rewrite_probe", HERE / "prototype.py")
proto = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(proto)


def run_probe(*, out: Path | None = None) -> dict:
    from arc_repl.racket_bridge import RacketBridge

    requests = []
    failures = []
    with RacketBridge(timeout=20, startup_timeout=60) as bridge:
        for mode in proto.MODES:
            for seed, demos in ((0, 2), (17, 3), (91, 6)):
                try:
                    episode = proto.generate_episode(
                        seed, mode=mode, n_demo=demos, n_query=4, bridge=bridge
                    )
                    certificate = proto.lesson_certificate(episode)
                    requests.append(
                        {
                            "mode": mode,
                            "seed": seed,
                            "demos": demos,
                            "queries": len(episode["test"]),
                            "query_shapes": [
                                [len(pair["input"]), len(pair["input"][0])]
                                for pair in episode["test"]
                            ],
                            "survivors": certificate["survivors"],
                        }
                    )
                except Exception as exc:  # retained bounded evidence, not concealment
                    failures.append(
                        {"mode": mode, "seed": seed, "demos": demos, "error": repr(exc)}
                    )
        # Adversarial surface 1: shifted legend defeats fixed-origin parsing.
        shifted = proto.sample_input(5, 1, height=8, width=30, stream="adversarial")
        fixed = proto._rival("fixed_origin_once", shifted)
        canonical = proto.transform(shifted, mode="once")
        shifted_refutes_fixed_origin = fixed != canonical
        # Adversarial surface 2: exact 30x30 mode divergence and Racket parity.
        large = proto.sample_input(5, 9, height=30, width=30, stream="adversarial")
        large_outputs = {
            mode: proto.racket_label(bridge, proto.materialize_program(mode=mode), large)
            for mode in proto.MODES
        }
        large_distinct = large_outputs["once"] != large_outputs["cascade"]
        runtime = proto.runtime_identity(bridge)
    report = {
        "schema": "d3c9fc4479d8-parametric-probe-v1",
        "status": "pass"
        if not failures and shifted_refutes_fixed_origin and large_distinct
        else "fail",
        "requests": requests,
        "failures": failures,
        "shifted_refutes_fixed_origin": shifted_refutes_fixed_origin,
        "large_30x30_distinct": large_distinct,
        "runtime": runtime,
        "limits": [
            "Finite declared-rival and six-request probe, not universal identifiability.",
            "The separate parametric sampler is denser and larger than the canonical production distribution.",
        ],
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(out=args.out)
    print(json.dumps(report, sort_keys=True))
    return int(report["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
