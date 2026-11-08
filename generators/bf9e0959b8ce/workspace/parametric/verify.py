#!/usr/bin/env python3
"""Bounded authoring audit for the bf9 count-relay parametric family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Callable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"


def _load_prototype():
    body = PROTOTYPE_PATH.read_bytes()
    name = "_bf9_count_relay_verify_" + hashlib.sha256(body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(PROTOTYPE_PATH), "exec"), module.__dict__)
    return module


P = _load_prototype()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _route_all(grid: list[list[int]], destination: str | None) -> list[list[int]]:
    info = P.analyze(grid)
    out = _copy_grid(grid)
    for dot in info["dots"]:
        r, c, color = dot
        out[r][c] = info["source_bg"]
        if destination is None:
            continue
        edge = info[destination]
        if info["orientation"] == "row":
            out[edge][c] = color
        else:
            out[r][edge] = color
    return out


def _row_only(grid: list[list[int]], mode: str) -> list[list[int]]:
    return P.transform(grid, mode) if P.analyze(grid)["orientation"] == "row" else _copy_grid(grid)


def _col_only(grid: list[list[int]], mode: str) -> list[list[int]]:
    return P.transform(grid, mode) if P.analyze(grid)["orientation"] == "col" else _copy_grid(grid)


def _forced_last(grid: list[list[int]]) -> list[list[int]]:
    info = P.analyze(grid)
    return P.relay_with_forced_count(grid, info["nonmatch_count"])


def _forced_middle(grid: list[list[int]]) -> list[list[int]]:
    info = P.analyze(grid)
    return P.relay_with_forced_count(grid, (info["nonmatch_count"] + 1) // 2)


def _rivals(mode: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    common = {
        "identity": _copy_grid,
        "always_near": lambda grid: _route_all(grid, "near"),
        "always_far": lambda grid: _route_all(grid, "far"),
        "erase_source": lambda grid: _route_all(grid, None),
        "row_only": lambda grid: _row_only(grid, mode),
        "col_only": lambda grid: _col_only(grid, mode),
    }
    if mode == "canonical":
        common["near_count_relay"] = lambda grid: P.transform(grid, "near_count_relay")
    else:
        common.update(
            {
                "canonical_skip_b": P.canonical_transform,
                "force_intermediate_1": lambda grid: P.relay_with_forced_count(grid, 1),
                "force_intermediate_2": lambda grid: P.relay_with_forced_count(grid, 2),
                "force_intermediate_3": lambda grid: P.relay_with_forced_count(grid, 3),
                "use_far_count": _forced_last,
                "use_middle_far_rank": _forced_middle,
            }
        )
    return common


class RacketExecutor:
    def __init__(self) -> None:
        self.bridge = RacketBridge()
        self.evaluations = 0
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError(f"protected Racket required, got {identity}")
        self.identity = {
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
        }
        self.symbols: dict[str, str] = {}

    def close(self) -> None:
        self.bridge.shutdown()

    def define(self, label: str, program: str) -> str:
        digest = _sha(program.encode())[:16]
        symbol = f"__bf9_{label}_{digest}"
        if program not in self.symbols:
            body = strip_rule_wrapper(program)
            self.bridge.eval_text(f"(define {symbol} {body})")
            self.symbols[program] = symbol
        return self.symbols[program]

    def apply(self, label: str, program: str, grid: list[list[int]]) -> list[list[int]]:
        symbol = self.define(label, program)
        input_name = f"__bf9_input_{self.evaluations}"
        self.bridge.define_grid(input_name, grid)
        self.evaluations += 1
        return self.bridge.eval_text(f"({symbol} {input_name})")


def verify(out_path: Path) -> dict[str, Any]:
    out_path = out_path.resolve()
    evidence_dir = out_path.parent
    public_dir = HERE / "public"
    # The review return format forbids deleting baseline artifacts.  Preserve
    # the two superseded episode-*.json files from the earlier proposal and
    # write the current content-addressed four-query exports alongside them.
    # Only the hash-named files listed in this audit are current exports.
    public_dir.mkdir(parents=True, exist_ok=True)
    turn_dir = evidence_dir / "public-turns"
    if turn_dir.exists():
        shutil.rmtree(turn_dir)
    turn_dir.mkdir(parents=True, exist_ok=True)

    settings = [{P.PARAMETER_NAME: mode} for mode in P.ALLOWED_MODES]
    programs = {mode: P.program({P.PARAMETER_NAME: mode}) for mode in P.ALLOWED_MODES}
    wrong_program = (HERE / "wrong_count_one.rkt").read_text(encoding="utf-8")
    if programs["canonical"] != (HERE / "canonical.rkt").read_text(encoding="utf-8"):
        raise AssertionError("canonical program bytes drifted")

    executor = RacketExecutor()
    try:
        parity_rows: list[dict[str, Any]] = []
        example_files: dict[str, dict[str, str]] = {}
        for seed in (0, 17):
            for mode in P.ALLOWED_MODES:
                episode = P.generate(seed, {P.PARAMETER_NAME: mode}, 6, 4)
                pairs = episode["train"] + episode["test"]
                racket_outputs = [
                    executor.apply(mode, programs[mode], pair["input"])
                    for pair in pairs
                ]
                expected = [pair["output"] for pair in pairs]
                if racket_outputs != expected:
                    raise AssertionError(f"Racket/Python mismatch seed={seed} mode={mode}")
                other = next(value for value in P.ALLOWED_MODES if value != mode)
                other_demo_outputs = [
                    executor.apply(other, programs[other], pair["input"])
                    for pair in episode["train"][:2]
                ]
                if all(
                    output == pair["output"]
                    for output, pair in zip(other_demo_outputs, episode["train"][:2], strict=True)
                ):
                    raise AssertionError(f"two-demo prefix does not distinguish mode {mode}")
                parity_rows.append(
                    {
                        "seed": seed,
                        "mode": mode,
                        "labels": len(pairs),
                        "two_demo_other_mode_rejected": True,
                        "program_sha256": _sha(programs[mode].encode()),
                    }
                )
                if seed == 0:
                    example = evidence_dir / f"example-{mode}.json"
                    _write(
                        example,
                        {
                            "settings": {P.PARAMETER_NAME: mode},
                            "train": episode["train"][:3],
                            "test": episode["test"],
                            "program_sha256": _sha(programs[mode].encode()),
                            "racket_outputs": racket_outputs[:3] + racket_outputs[6:],
                        },
                    )
                    example_files[mode] = {
                        "path": example.relative_to(HERE.parents[3]).as_posix(),
                        "sha256": _sha(example.read_bytes()),
                    }

        count_checks: list[dict[str, Any]] = []
        for mode in P.ALLOWED_MODES:
            settings_value = {P.PARAMETER_NAME: mode}
            baseline = P.generate(1234, settings_value, 6, 4)
            for demos in range(2, 7):
                for queries in range(1, 5):
                    candidate = P.generate(1234, settings_value, demos, queries)
                    if candidate["train"] != baseline["train"][:demos]:
                        raise AssertionError("demonstration prefix changed with requested count")
                    if candidate["test"] != baseline["test"][:queries]:
                        raise AssertionError("query prefix changed with requested count")
                    count_checks.append(
                        {"mode": mode, "demos": demos, "queries": queries, "status": "passed"}
                    )

        rival_rows: list[dict[str, Any]] = []
        ambiguities: list[dict[str, Any]] = []
        for seed in range(16):
            for mode in P.ALLOWED_MODES:
                episode = P.generate(seed, {P.PARAMETER_NAME: mode}, 6, 4)
                for demos in range(2, 7):
                    visible = episode["train"][:demos]
                    for name, rival in _rivals(mode).items():
                        demo_fit = all(rival(pair["input"]) == pair["output"] for pair in visible)
                        query_diff = any(rival(pair["input"]) != pair["output"] for pair in episode["test"])
                        row = {
                            "seed": seed,
                            "mode": mode,
                            "demos": demos,
                            "rival": name,
                            "demo_fit": demo_fit,
                            "query_diff": query_diff,
                        }
                        rival_rows.append(row)
                        if demo_fit and query_diff:
                            ambiguities.append(row)
        if ambiguities:
            raise AssertionError(f"named rival ambiguity survives: {ambiguities[:3]}")

        witness_episode = P.generate(0, {P.PARAMETER_NAME: "near_count_relay"}, 3, 4)
        witness_input = witness_episode["test"][3]["input"]
        explanation = P.explain_relay(witness_input)
        if explanation["near_count"] == 1:
            raise AssertionError("witness needs a non-one intermediate")
        stage_a = executor.apply("canonical", programs["canonical"], witness_input)
        correct = executor.apply("relay", programs["near_count_relay"], witness_input)
        counterfactual = executor.apply("wrong_count_one", wrong_program, witness_input)
        if stage_a != explanation["stage_a"] or correct != explanation["final"]:
            raise AssertionError("Racket witness does not match Python staged explanation")
        if correct == counterfactual:
            raise AssertionError("wrong-intermediate witness did not change final output")
        witness_case = {
            "input": witness_input,
            "settings": {P.PARAMETER_NAME: "near_count_relay"},
            "intermediate_value": explanation["near_count"],
            "stage_a_output": stage_a,
            "far_candidates": [list(item) for item in explanation["far_candidates"]],
            "selected_far_candidate": list(explanation["selected_far_candidate"]),
            "output": correct,
            "counterfactual_output": counterfactual,
            "ablation": "wrong_intermediate",
            "program": programs["near_count_relay"],
            "counterfactual_program": wrong_program,
        }
        witness_case_path = evidence_dir / "causal-case.json"
        _write(witness_case_path, witness_case)

        public_files: list[dict[str, Any]] = []
        turn_files: list[dict[str, Any]] = []
        for mode in P.ALLOWED_MODES:
            episode = P.generate(0, {P.PARAMETER_NAME: mode}, 3, 4)
            single = P.generate(0, {P.PARAMETER_NAME: mode}, 3, 1)
            if single["test"][0] != episode["test"][0]:
                raise AssertionError("single-query first turn differs from four-query first turn")
            batch = P.public_batch(episode)
            batch_raw = public_challenge_bytes(batch)
            batch_id = public_challenge_id(batch)
            batch_path = public_dir / f"{batch_id}.json"
            batch_path.write_bytes(batch_raw)
            public_files.append(
                {
                    "mode": mode,
                    "queries": 4,
                    "path": batch_path.relative_to(HERE.parents[3]).as_posix(),
                    "sha256": _sha(batch_path.read_bytes()),
                }
            )
            for query_index in range(4):
                challenge = P.public_challenge(episode, query_index=query_index)
                raw = json.dumps(challenge, sort_keys=True)
                for forbidden in (
                    "rule_mode",
                    "near_count_relay",
                    "program_solution",
                    "near_count",
                    "query_count",
                ):
                    if forbidden in raw:
                        raise AssertionError(f"public projection leaks {forbidden}")
                path = turn_dir / f"{mode}-turn-{query_index + 1}.json"
                _write(path, challenge)
                turn_files.append(
                    {
                        "mode": mode,
                        "turn": query_index + 1,
                        "path": path.relative_to(HERE.parents[3]).as_posix(),
                        "sha256": _sha(path.read_bytes()),
                    }
                )

        large = P.generate(0, {P.PARAMETER_NAME: "near_count_relay"}, 3, 4)["test"][3]
        large_info = P.analyze(large["input"])
        report = {
            "schema": "bf9e0959b8ce-count-relay-audit-v1",
            "status": "passed",
            "scope": "bounded reviewer authoring evidence; not owner acceptance or training admission",
            "parameter": {
                "name": P.PARAMETER_NAME,
                "values": list(P.ALLOWED_MODES),
                "default": P.DEFAULT_MODE,
            },
            "sequential_dependency": {
                "step_a": "Canonical separator/key routing creates the near-edge and far-edge result sets.",
                "intermediate": "The number of routed dots occupying the near edge (1, 2, or 3).",
                "step_b": "Order far-edge result dots by aligned coordinate; relay the intermediate-th dot one cell inward.",
                "why_b_depends_on_a": "The far candidate chosen in B is indexed by the population measured from A's routed near-edge output; forcing the wrong count selects a different far dot and changes the final grid.",
                "case_path": witness_case_path.relative_to(HERE.parents[3]).as_posix(),
                "case_sha256": _sha(witness_case_path.read_bytes()),
            },
            "racket": executor.identity,
            "racket_evaluations": executor.evaluations,
            "parity": parity_rows,
            "count_prefix_checks": count_checks,
            "rival_audit": {
                "seeds": 16,
                "demo_counts": [2, 3, 4, 5, 6],
                "checks": len(rival_rows),
                "ambiguous_named_rivals": 0,
                "rivals_by_mode": {
                    mode: sorted(_rivals(mode)) for mode in P.ALLOWED_MODES
                },
                "limits": "Finite named rivals only; not a proof of unique induction.",
            },
            "large_query": {
                "height": len(large["input"]),
                "width": len(large["input"][0]),
                "orientation": large_info["orientation"],
                "match_count": large_info["match_count"],
                "nonmatch_count": large_info["nonmatch_count"],
                "far_candidate_coordinates": [item[0] for item in large_info["far_candidates"]],
            },
            "examples": example_files,
            "public_files": public_files,
            "sequential_turn_files": turn_files,
            "programs": {
                mode: _sha(program.encode()) for mode, program in programs.items()
            },
            "source_hashes": {
                path.name: _sha(path.read_bytes())
                for path in (
                    HERE / "prototype.py",
                    HERE / "adapter.py",
                    HERE / "promotion.json",
                    HERE / "canonical.rkt",
                    HERE / "near_count_relay.rkt",
                    HERE / "wrong_count_one.rkt",
                    HERE / "verify.py",
                )
            },
        }
        _write(out_path, report)
        return report
    finally:
        executor.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "racket_evaluations": report["racket_evaluations"],
                "named_rival_checks": report["rival_audit"]["checks"],
                "large_query": report["large_query"],
                "evidence": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
