"""Bounded protected-Racket teaching audit for the route-action family.

This is deliberately small: two seeds, the minimum two demonstrations, four
queries, and a finite list of plausible selector shortcuts.  It is reusable by
future reviewers but does not claim universal identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root

HOME = Path(__file__).resolve().parent
ROOT = find_root(__file__)
RIVALS = (
    "wall_endpoint",
    "trace_all",
    "least_frequent",
    "fixed_top",
    "fixed_bottom",
    "fixed_left",
    "fixed_right",
)


def _load_adapter():
    path = HOME / "adapter.py"
    name = "_audit_8ce1331089a3_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run(out: Path, seeds=(0, 17), demos=2, queries=4):
    if out.exists():
        raise FileExistsError(out)
    adapter = _load_adapter()
    selected_settings = {"path_rule": "dominant_trace"}
    selected_program = adapter.program(selected_settings)
    rival_programs = {
        "wall_endpoint": adapter.program({"path_rule": "wall_endpoint"}),
        **{name: adapter.rival_program(name) for name in RIVALS if name != "wall_endpoint"},
    }
    episodes = []
    witness = None
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=128) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("audit requires protected Racket")

        cache = {}

        def execute(program, grid):
            wrapped = cache.setdefault(program, wrap_rule(program))
            return bridge.eval_text(f"({wrapped} {_literal(grid)})")

        for seed in seeds:
            episode = adapter.generate(seed, selected_settings, demos, queries)
            pairs = episode["train"] + episode["test"]
            for index, pair in enumerate(pairs):
                actual = execute(selected_program, pair["input"])
                if actual != pair["output"]:
                    raise AssertionError(f"selected Racket label mismatch at seed {seed}, pair {index}")
            rivals = {}
            for name, program in rival_programs.items():
                demo_mismatches = []
                query_mismatches = []
                for index, pair in enumerate(episode["train"]):
                    if execute(program, pair["input"]) != pair["output"]:
                        demo_mismatches.append(index)
                for index, pair in enumerate(episode["test"]):
                    if execute(program, pair["input"]) != pair["output"]:
                        query_mismatches.append(index)
                rivals[name] = {
                    "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                    "demo_mismatches": demo_mismatches,
                    "query_mismatches": query_mismatches,
                    "fits_all_demos": not demo_mismatches,
                    "changes_a_query": bool(query_mismatches),
                }
            bad = [name for name, row in rivals.items() if row["fits_all_demos"] and row["changes_a_query"]]
            if bad:
                raise AssertionError(f"query-changing demo survivors at seed {seed}: {bad}")
            analyses = [adapter.analyze(pair["input"]) for pair in pairs]
            episodes.append({
                "seed": seed,
                "settings": selected_settings,
                "counts": {"demos": demos, "queries": queries},
                "dominant_routes": {
                    "train": [row["dominant_route"] for row in analyses[:demos]],
                    "test": [row["dominant_route"] for row in analyses[demos:]],
                },
                "rivals": rivals,
                "query_changing_demo_survivors": bad,
            })
            if witness is None:
                for split in ("train", "test"):
                    for pair_index, pair in enumerate(episode[split]):
                        facts = adapter.analyze(pair["input"])
                        if facts["dominant_route"] == "top":
                            continue
                        counterfactual = rival_programs["fixed_top"]
                        counterfactual_output = execute(counterfactual, pair["input"])
                        if counterfactual_output == pair["output"]:
                            continue
                        witness = {
                            "settings": selected_settings,
                            "program": selected_program,
                            "input": pair["input"],
                            "output": pair["output"],
                            "counterfactual_program": counterfactual,
                            "counterfactual_output": counterfactual_output,
                            "intermediate_value": {
                                "dominant_route": facts["dominant_route"],
                                "route_counts": facts["route_counts"],
                            },
                            "ablation": "wrong_intermediate",
                            "selection": {
                                "seed": seed,
                                "split": split,
                                "pair_index": pair_index,
                            },
                        }
                        break
                    if witness is not None:
                        break
    if witness is None:
        raise AssertionError("no wrong-intermediate witness found")
    report = {
        "schema": "arcpuzzles-parametric-teaching-audit-v1",
        "task_id": "8ce1331089a3",
        "status": "passed",
        "scope": {
            "seeds": list(seeds),
            "demos": demos,
            "queries": queries,
            "rivals": list(RIVALS),
            "universal_identifiability": False,
        },
        "source": {
            "adapter": "generators/8ce1331089a3/workspace/parametric/adapter.py",
            "adapter_sha256": _sha(HOME / "adapter.py"),
            "native_sha256": _sha(HOME / "native.py"),
            "canonical_sha256": _sha(HOME / "canonical.rkt"),
            "selected_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
        },
        "racket": {
            key: identity[key]
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
            if key in identity
        },
        "episodes": episodes,
        "query_changing_demo_survivors": [],
        "limits": "Finite rival set and two seeds only; no universal uniqueness claim.",
    }
    out.mkdir(parents=True, exist_ok=False)
    _write(out / "self_audit.json", report)
    _write(out / "audited_case.json", witness)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({
        "status": report["status"],
        "episodes": len(report["episodes"]),
        "query_changing_demo_survivors": report["query_changing_demo_survivors"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
