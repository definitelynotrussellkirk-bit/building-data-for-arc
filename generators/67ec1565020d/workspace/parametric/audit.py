"""Bounded source-bound teaching and protected-Racket audit for the family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "adapter.py"
COUNTERFACTUAL_PATH = HERE / "raw_wide_count.rkt"
MODES = ("canonical", "wide_region_relay")


def _load_adapter():
    name = "_67ec_parametric_audit_adapter_" + hashlib.sha256(str(ADAPTER_PATH).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def run_audit(*, seed_start: int = 0, seed_count: int = 32, racket_seed_count: int = 2) -> dict[str, Any]:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative exact integer")
    if type(seed_count) is not int or not 1 <= seed_count <= 256:
        raise ValueError("seed_count must be an exact integer in 1..256")
    if type(racket_seed_count) is not int or not 0 <= racket_seed_count <= seed_count:
        raise ValueError("racket_seed_count must be an exact integer in 0..seed_count")
    if seed_start + seed_count - 1 > 2**63 - 1:
        raise ValueError("seed range exceeds adapter bounds")

    adapter = _load_adapter()
    lesson_failures: list[dict[str, Any]] = []
    racket_failures: list[dict[str, Any]] = []
    region_counts: set[int] = set()
    distinct_inputs: set[str] = set()
    episodes = 0

    for seed in range(seed_start, seed_start + seed_count):
        generated = {
            mode: adapter.generate(seed, {"mode": mode}, 2, 4)
            for mode in MODES
        }
        episodes += len(generated)
        canonical_inputs = _inputs(generated["canonical"])
        if canonical_inputs != _inputs(generated["wide_region_relay"]):
            lesson_failures.append({"seed": seed, "failure": "settings changed inputs"})
        for grid in canonical_inputs:
            distinct_inputs.add(json.dumps(grid, separators=(",", ":")))
            try:
                region_counts.add(int(adapter.explain_dependency(grid)["wide_regions_after"]))
            except Exception as error:  # retained as a concrete finite audit failure
                lesson_failures.append({"seed": seed, "failure": "dependency analysis", "error": str(error)})
        for mode, episode in generated.items():
            try:
                certificate = adapter.certificate(
                    episode["train"], [pair["input"] for pair in episode["test"]]
                )
                if certificate["survivors"] != [mode]:
                    lesson_failures.append(
                        {"seed": seed, "mode": mode, "failure": "ambiguous demos", "certificate": certificate}
                    )
            except Exception as error:
                lesson_failures.append({"seed": seed, "mode": mode, "failure": "certificate", "error": str(error)})
        relay_query = generated["wide_region_relay"]["test"][3]
        if relay_query["output"] == adapter.transform(relay_query["input"], "raw_wide_count"):
            lesson_failures.append({"seed": seed, "failure": "30x30 causal ablation did not change output"})

    racket_evaluations = 0
    racket_identity: dict[str, Any] | None = None
    if racket_seed_count:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        wrapped: dict[str, str] = {}
        with RacketBridge(timeout=20) as bridge:
            racket_identity = {
                key: bridge.runtime_identity[key]
                for key in (
                    "schema",
                    "backend",
                    "protected",
                    "binary_sha256",
                    "prelude_sha256",
                    "bridge_sha256",
                    "boot_script_sha256",
                    "candidate_symbol_policy_sha256",
                )
                if key in bridge.runtime_identity
            }
            if racket_identity.get("protected") is not True:
                raise ValueError("audit requires protected Racket")

            def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
                nonlocal racket_evaluations
                racket_evaluations += 1
                wrapped.setdefault(program, wrap_rule(program))
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                return bridge.eval_text(f"({wrapped[program]} {literal})")

            for seed in range(seed_start, seed_start + racket_seed_count):
                for mode in MODES:
                    episode = adapter.generate(seed, {"mode": mode}, 3, 4)
                    selected_program = adapter.program({"mode": mode})
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            try:
                                actual = execute(selected_program, pair["input"])
                                if actual != pair["output"]:
                                    racket_failures.append(
                                        {"seed": seed, "mode": mode, "split": split, "index": index, "failure": "label mismatch"}
                                    )
                            except Exception as error:
                                racket_failures.append(
                                    {"seed": seed, "mode": mode, "split": split, "index": index, "failure": "execution", "error": str(error)}
                                )
                relay = adapter.generate(seed, {"mode": "wide_region_relay"}, 3, 4)["test"][3]
                try:
                    counter = execute(COUNTERFACTUAL_PATH.read_text(encoding="utf-8"), relay["input"])
                    if counter == relay["output"]:
                        racket_failures.append({"seed": seed, "failure": "counterfactual matched actual output"})
                    elif counter != adapter.transform(relay["input"], "raw_wide_count"):
                        racket_failures.append({"seed": seed, "failure": "counterfactual disagreed with independent mirror"})
                except Exception as error:
                    racket_failures.append({"seed": seed, "failure": "counterfactual execution", "error": str(error)})

    status = "passed" if not lesson_failures and not racket_failures and region_counts == {1, 2, 3} else "failed"
    return {
        "schema": "arcpuzzles-67ec1565020d-parametric-audit-v1",
        "status": status,
        "task_id": "67ec1565020d",
        "seed_start": seed_start,
        "seed_count": seed_count,
        "racket_seed_count": racket_seed_count,
        "episodes": episodes,
        "distinct_inputs": len(distinct_inputs),
        "declared_hypotheses": list(adapter.HYPOTHESES),
        "region_counts": sorted(region_counts),
        "lesson_failures": lesson_failures,
        "racket_evaluations": racket_evaluations,
        "racket_failures": racket_failures,
        "racket": racket_identity,
        "source_sha256": {
            "adapter.py": _sha(ADAPTER_PATH),
            "canonical.rkt": _sha(HERE / "canonical.rkt"),
            "wide_region_relay.rkt": _sha(HERE / "wide_region_relay.rkt"),
            "raw_wide_count.rkt": _sha(COUNTERFACTUAL_PATH),
        },
        "limits": "Finite declared-rival and selected-seed evidence; not universal identifiability.",
    }


def write_report(path: Path | str, report: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--racket-seed-count", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_audit(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        racket_seed_count=args.racket_seed_count,
    )
    write_report(args.out, report)
    print(json.dumps({key: report[key] for key in ("status", "episodes", "distinct_inputs", "racket_evaluations", "region_counts")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
